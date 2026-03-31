#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


DEFAULT_INPUT = Path("data/library.json")


class PromptRenderError(Exception):
    pass


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise PromptRenderError(f"Eingabedatei nicht gefunden: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise PromptRenderError(f"Ungültiges JSON in {path}: {exc}") from exc


def ensure_dict(value: Any, path: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise PromptRenderError(f"Erwartet Objekt unter '{path}', gefunden: {type(value).__name__}")
    return value


def ensure_list(value: Any, path: str) -> list[Any]:
    if not isinstance(value, list):
        raise PromptRenderError(f"Erwartet Liste unter '{path}', gefunden: {type(value).__name__}")
    return value


def lower_first(text: str) -> str:
    return text[:1].lower() + text[1:] if text else text


def humanize_key(value: str) -> str:
    return value.replace("_", " ")


def parse_assignment(raw: str) -> tuple[str, str]:
    if "=" not in raw:
        raise PromptRenderError(f"Ungültiges --set Format: '{raw}'. Erwartet SLOT=value")
    slot, value = raw.split("=", 1)
    slot = slot.strip()
    value = value.strip()
    if not slot or not value:
        raise PromptRenderError(f"Ungültiges --set Format: '{raw}'. Erwartet SLOT=value")
    return slot, value


def build_indexes(data: dict[str, Any]) -> tuple[
    dict[str, dict[str, Any]],
    list[dict[str, Any]],
    dict[str, dict[str, Any]],
    dict[str, dict[str, Any]],
]:
    library = ensure_dict(data.get("library"), "library")
    templates = ensure_list(data.get("templates", []), "templates")
    examples = ensure_list(data.get("example_instances", []), "example_instances")

    slot_index: dict[str, dict[str, Any]] = {}
    dimension_order: list[dict[str, Any]] = []

    for dim_key, dim_obj_any in library.items():
        dim_obj = ensure_dict(dim_obj_any, f"library.{dim_key}")
        dim_label = dim_obj.get("label", dim_key)
        subdimensions = ensure_dict(dim_obj.get("subdimensions"), f"library.{dim_key}.subdimensions")

        dim_info = {
            "dimension_key": dim_key,
            "dimension_label": dim_label,
            "slots": [],
        }

        for sub_key, sub_obj_any in subdimensions.items():
            sub_obj = ensure_dict(sub_obj_any, f"library.{dim_key}.subdimensions.{sub_key}")
            slot = sub_obj.get("slot", sub_key)
            if not isinstance(slot, str) or not slot:
                raise PromptRenderError(f"Ungültiger Slot in library.{dim_key}.subdimensions.{sub_key}")

            values = ensure_list(sub_obj.get("values"), f"library.{dim_key}.subdimensions.{sub_key}.values")
            allowed_values: dict[str, dict[str, str]] = {}

            for idx, value_obj_any in enumerate(values):
                value_obj = ensure_dict(
                    value_obj_any,
                    f"library.{dim_key}.subdimensions.{sub_key}.values[{idx}]",
                )
                value_key = value_obj.get("key")
                value_label = value_obj.get("label", value_key)
                value_description = value_obj.get("description", "")

                if not isinstance(value_key, str) or not value_key:
                    raise PromptRenderError(
                        f"Fehlender oder ungültiger 'key' unter "
                        f"library.{dim_key}.subdimensions.{sub_key}.values[{idx}]"
                    )

                allowed_values[value_key] = {
                    "label": value_label if isinstance(value_label, str) else value_key,
                    "description": value_description if isinstance(value_description, str) else "",
                }

            slot_meta = {
                "slot": slot,
                "dimension_key": dim_key,
                "dimension_label": dim_label,
                "subdimension_key": sub_key,
                "subdimension_label": sub_obj.get("label", sub_key),
                "required": bool(sub_obj.get("required", False)),
                "multi": bool(sub_obj.get("multi", False)),
                "allowed_values": allowed_values,
            }
            slot_index[slot] = slot_meta
            dim_info["slots"].append(slot)

        dimension_order.append(dim_info)

    template_index: dict[str, dict[str, Any]] = {}
    for idx, tpl_any in enumerate(templates):
        tpl = ensure_dict(tpl_any, f"templates[{idx}]")
        tpl_id = tpl.get("id")
        if not isinstance(tpl_id, str) or not tpl_id:
            raise PromptRenderError(f"Fehlende oder ungültige Template-ID unter templates[{idx}]")
        template_index[tpl_id] = tpl

    example_index: dict[str, dict[str, Any]] = {}
    for idx, ex_any in enumerate(examples):
        ex = ensure_dict(ex_any, f"example_instances[{idx}]")
        ex_id = ex.get("id")
        if not isinstance(ex_id, str) or not ex_id:
            raise PromptRenderError(f"Fehlende oder ungültige Example-ID unter example_instances[{idx}]")
        example_index[ex_id] = ex

    return slot_index, dimension_order, template_index, example_index


def load_instance_values(example_index: dict[str, dict[str, Any]], instance_id: str) -> dict[str, Any]:
    if instance_id not in example_index:
        valid = ", ".join(sorted(example_index.keys())) or "keine"
        raise PromptRenderError(f"Unbekannte Example-Instance '{instance_id}'. Verfügbar: {valid}")

    values = ensure_dict(example_index[instance_id].get("values"), f"example_instances[{instance_id}].values")
    return dict(values)


def merge_assignments(
    base_assignments: dict[str, Any],
    set_args: list[str],
    slot_index: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    assignments = dict(base_assignments)

    for raw in set_args:
        slot, value_raw = parse_assignment(raw)

        if slot not in slot_index:
            valid = ", ".join(sorted(slot_index.keys()))
            raise PromptRenderError(f"Unbekannter Slot '{slot}'. Gültige Slots: {valid}")

        slot_meta = slot_index[slot]
        if slot_meta["multi"]:
            values = [v.strip() for v in value_raw.split(",") if v.strip()]
            if not values:
                raise PromptRenderError(f"Multi-Slot '{slot}' benötigt mindestens einen Wert.")
            assignments[slot] = values
        else:
            assignments[slot] = value_raw

    return assignments


def validate_assignments(assignments: dict[str, Any], slot_index: dict[str, dict[str, Any]]) -> None:
    for slot, raw_value in assignments.items():
        if slot not in slot_index:
            valid = ", ".join(sorted(slot_index.keys()))
            raise PromptRenderError(f"Unbekannter Slot '{slot}'. Gültige Slots: {valid}")

        slot_meta = slot_index[slot]
        allowed_values = slot_meta["allowed_values"]

        if slot_meta["multi"]:
            if not isinstance(raw_value, list):
                raise PromptRenderError(f"Slot '{slot}' erwartet eine Liste von Werten.")
            for item in raw_value:
                if item not in allowed_values:
                    valid = ", ".join(sorted(allowed_values.keys()))
                    raise PromptRenderError(
                        f"Ungültiger Wert '{item}' für Slot '{slot}'. Gültige Werte: {valid}"
                    )
        else:
            if not isinstance(raw_value, str):
                raise PromptRenderError(f"Slot '{slot}' erwartet genau einen String-Wert.")
            if raw_value not in allowed_values:
                valid = ", ".join(sorted(allowed_values.keys()))
                raise PromptRenderError(
                    f"Ungültiger Wert '{raw_value}' für Slot '{slot}'. Gültige Werte: {valid}"
                )


def check_constraints(data: dict[str, Any], assignments: dict[str, Any]) -> list[str]:
    warnings: list[str] = []
    constraints = ensure_list(data.get("constraints", []), "constraints")

    for idx, cons_any in enumerate(constraints):
        cons = ensure_dict(cons_any, f"constraints[{idx}]")
        cons_type = cons.get("type")
        cond = ensure_dict(cons.get("if"), f"constraints[{idx}].if")
        cond_slot = cond.get("slot")
        cond_equals = cond.get("equals")

        if not isinstance(cond_slot, str) or not isinstance(cond_equals, str):
            raise PromptRenderError(f"Ungültige Constraint-Bedingung unter constraints[{idx}]")

        assigned = assignments.get(cond_slot)
        condition_matches = assigned == cond_equals

        if cons_type == "incompatibility" and condition_matches:
            then_not = ensure_dict(cons.get("then_not"), f"constraints[{idx}].then_not")
            target_slot = then_not.get("slot")
            forbidden_value = then_not.get("contains")

            if not isinstance(target_slot, str) or not isinstance(forbidden_value, str):
                raise PromptRenderError(f"Ungültige Inkompatibilitätsregel unter constraints[{idx}]")

            target_value = assignments.get(target_slot)
            if isinstance(target_value, list) and forbidden_value in target_value:
                raise PromptRenderError(
                    f"Inkompatible Kombination: {cond_slot}={cond_equals} widerspricht "
                    f"{target_slot} enthält {forbidden_value}"
                )

        elif cons_type == "recommendation" and condition_matches:
            then_obj = ensure_dict(cons.get("then"), f"constraints[{idx}].then")
            recommended_slots = ensure_list(
                then_obj.get("recommended_slots", []),
                f"constraints[{idx}].then.recommended_slots",
            )
            recommended_values = ensure_dict(
                then_obj.get("recommended_values", {}),
                f"constraints[{idx}].then.recommended_values",
            )

            missing_slots = [slot for slot in recommended_slots if slot not in assignments]
            if missing_slots:
                warnings.append(
                    f"Empfehlung bei {cond_slot}={cond_equals}: ergänze idealerweise "
                    f"{', '.join(missing_slots)}"
                )

            for rec_slot, rec_vals_any in recommended_values.items():
                rec_vals = ensure_list(rec_vals_any, f"constraints[{idx}].then.recommended_values.{rec_slot}")
                if rec_slot in assignments:
                    current = assignments[rec_slot]
                    if isinstance(current, str) and current not in rec_vals:
                        warnings.append(
                            f"Empfehlung bei {cond_slot}={cond_equals}: für {rec_slot} "
                            f"sind eher {', '.join(rec_vals)} sinnvoll"
                        )

    return warnings


def value_to_structured_text(slot: str, value: Any, slot_index: dict[str, dict[str, Any]]) -> str:
    meta = slot_index[slot]
    allowed = meta["allowed_values"]

    if isinstance(value, list):
        return ", ".join(allowed[item]["label"] for item in value)
    return allowed[value]["label"]


def value_to_template_text(slot: str, value: Any, slot_index: dict[str, dict[str, Any]]) -> str:
    meta = slot_index[slot]
    allowed = meta["allowed_values"]

    def render_one(item: str) -> str:
        label = allowed[item]["label"]
        if label and label[0].isupper():
            return lower_first(label)
        return humanize_key(item)

    if isinstance(value, list):
        return ", ".join(render_one(item) for item in value)
    return render_one(value)


def render_structured_prompt(
    assignments: dict[str, Any],
    dimension_order: list[dict[str, Any]],
    slot_index: dict[str, dict[str, Any]],
) -> str:
    lines: list[str] = ["Erstelle eine Antwort anhand der folgenden Vorgaben:"]

    for dim in dimension_order:
        rendered_slot_lines: list[str] = []

        for slot in dim["slots"]:
            if slot in assignments:
                meta = slot_index[slot]
                slot_label = meta["subdimension_label"]
                slot_value = value_to_structured_text(slot, assignments[slot], slot_index)
                rendered_slot_lines.append(f"- {slot_label}: {slot_value}")

        if rendered_slot_lines:
            lines.append("")
            lines.append(f"{dim['dimension_label']}:")
            lines.extend(rendered_slot_lines)

    return "\n".join(lines).strip()


def render_template_prompt(
    template_id: str,
    assignments: dict[str, Any],
    template_index: dict[str, dict[str, Any]],
    slot_index: dict[str, dict[str, Any]],
) -> str:
    if template_id not in template_index:
        valid = ", ".join(sorted(template_index.keys())) or "keine"
        raise PromptRenderError(f"Unbekanntes Template '{template_id}'. Verfügbar: {valid}")

    tpl = template_index[template_id]
    tpl_text = tpl.get("text")
    slots_used = ensure_list(tpl.get("slots_used", []), f"templates.{template_id}.slots_used")

    if not isinstance(tpl_text, str) or not tpl_text:
        raise PromptRenderError(f"Template '{template_id}' hat keinen gültigen Text.")

    missing = [slot for slot in slots_used if slot not in assignments]
    if missing:
        raise PromptRenderError(
            f"Für Template '{template_id}' fehlen Werte für: {', '.join(missing)}"
        )

    rendered = tpl_text
    for slot in slots_used:
        value_text = value_to_template_text(slot, assignments[slot], slot_index)
        rendered = rendered.replace(f"[{slot}]", value_text)

    unresolved = re.findall(r"\[([A-Z0-9_]+)\]", rendered)
    if unresolved:
        raise PromptRenderError(
            f"Template '{template_id}' enthält noch unaufgelöste Platzhalter: {', '.join(sorted(set(unresolved)))}"
        )

    return rendered.strip()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Rendert komplette Prompts aus Slots auf Basis von data/library.json."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT,
        help=f"Pfad zur library.json (Default: {DEFAULT_INPUT})",
    )
    parser.add_argument(
        "--instance",
        type=str,
        help="Example-Instance-ID aus example_instances als Ausgangsbasis",
    )
    parser.add_argument(
        "--set",
        action="append",
        default=[],
        help="Slot setzen oder überschreiben, Format: SLOT=value oder SLOT=a,b",
    )
    parser.add_argument(
        "--mode",
        choices=["structured", "template"],
        default="structured",
        help="structured = mehrzeiliger vollständiger Prompt, template = Template-Text rendern",
    )
    parser.add_argument(
        "--template",
        type=str,
        help="Template-ID für --mode template",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optionaler Ausgabepfad für den gerenderten Prompt",
    )
    parser.add_argument(
        "--list-templates",
        action="store_true",
        help="Verfügbare Templates auflisten und beenden",
    )
    parser.add_argument(
        "--list-instances",
        action="store_true",
        help="Verfügbare Example-Instances auflisten und beenden",
    )
    parser.add_argument(
        "--list-slots",
        action="store_true",
        help="Verfügbare Slots auflisten und beenden",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        data = load_json(args.input)
        slot_index, dimension_order, template_index, example_index = build_indexes(data)

        if args.list_templates:
            for tpl_id in sorted(template_index.keys()):
                print(tpl_id)
            return 0

        if args.list_instances:
            for ex_id in sorted(example_index.keys()):
                print(ex_id)
            return 0

        if args.list_slots:
            for slot in sorted(slot_index.keys()):
                print(slot)
            return 0

        base_assignments: dict[str, Any] = {}
        if args.instance:
            base_assignments = load_instance_values(example_index, args.instance)

        assignments = merge_assignments(base_assignments, args.set, slot_index)
        if not assignments:
            raise PromptRenderError("Keine Slots gesetzt. Nutze --instance und/oder --set SLOT=value")

        validate_assignments(assignments, slot_index)
        warnings = check_constraints(data, assignments)

        if args.mode == "template":
            if not args.template:
                raise PromptRenderError("Für --mode template ist --template TEMPLATE_ID erforderlich.")
            rendered = render_template_prompt(args.template, assignments, template_index, slot_index)
        else:
            rendered = render_structured_prompt(assignments, dimension_order, slot_index)

        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(rendered + "\n", encoding="utf-8")
        else:
            print(rendered)

        for warning in warnings:
            print(f"Warnung: {warning}", file=sys.stderr)

        return 0

    except PromptRenderError as exc:
        print(f"Fehler: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"Unerwarteter Fehler: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())