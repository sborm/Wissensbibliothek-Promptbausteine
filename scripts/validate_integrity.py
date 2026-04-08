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

PLACEHOLDER_RE = re.compile(r"\[([A-Z0-9_]+)\]")


class IntegrityError(Exception):
    """Raised when semantic integrity checks fail."""


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise IntegrityError(f"Eingabedatei nicht gefunden: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise IntegrityError(f"Ungültiges JSON in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise IntegrityError(f"Top-Level von {path} muss ein JSON-Objekt sein.")
    return data


def ensure_dict(value: Any, path: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise IntegrityError(f"Erwartet Objekt unter '{path}', gefunden: {type(value).__name__}")
    return value


def ensure_list(value: Any, path: str) -> list[Any]:
    if not isinstance(value, list):
        raise IntegrityError(f"Erwartet Liste unter '{path}', gefunden: {type(value).__name__}")
    return value


def optional_fields(sub_obj: dict[str, Any]) -> dict[str, Any]:
    fields = {}
    for key in (
        "origin",
        "evidence_strength",
        "auto_recommendation_tier",
        "recommendation_notes",
        "heuristic_scope",
        "confidence",
    ):
        if key in sub_obj:
            fields[key] = sub_obj[key]
    return fields


def build_expected_slot_schema(data: dict[str, Any]) -> list[dict[str, Any]]:
    library = ensure_dict(data.get("library"), "library")
    expected: list[dict[str, Any]] = []

    seen_slots: set[str] = set()

    for dim_key, dim_any in library.items():
        dim_obj = ensure_dict(dim_any, f"library.{dim_key}")
        subdimensions = ensure_dict(dim_obj.get("subdimensions"), f"library.{dim_key}.subdimensions")

        for sub_key, sub_any in subdimensions.items():
            sub_obj = ensure_dict(sub_any, f"library.{dim_key}.subdimensions.{sub_key}")
            slot = sub_obj.get("slot", sub_key)

            if not isinstance(slot, str) or not slot:
                raise IntegrityError(f"Ungültiger oder leerer Slot unter library.{dim_key}.subdimensions.{sub_key}")

            if slot in seen_slots:
                raise IntegrityError(f"Doppelter Slot erkannt: {slot}")
            seen_slots.add(slot)

            values = ensure_list(sub_obj.get("values"), f"library.{dim_key}.subdimensions.{sub_key}.values")
            if not values:
                raise IntegrityError(f"Slot {slot} hat keine Werte.")

            value_keys: set[str] = set()
            for idx, value_any in enumerate(values):
                value_obj = ensure_dict(
                    value_any,
                    f"library.{dim_key}.subdimensions.{sub_key}.values[{idx}]",
                )
                value_key = value_obj.get("key")
                if not isinstance(value_key, str) or not value_key:
                    raise IntegrityError(
                        f"Fehlender oder ungültiger value.key unter "
                        f"library.{dim_key}.subdimensions.{sub_key}.values[{idx}]"
                    )
                if value_key in value_keys:
                    raise IntegrityError(f"Doppelter Wert '{value_key}' im Slot {slot}")
                value_keys.add(value_key)

            slot_item = {
                "slot": slot,
                "dimension": dim_key,
                "subdimension": sub_key,
                "required": bool(sub_obj.get("required", False)),
                "multi": bool(sub_obj.get("multi", False)),
            }
            slot_item.update(optional_fields(sub_obj))
            expected.append(slot_item)

    return expected


def build_slot_index(data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    library = ensure_dict(data.get("library"), "library")
    slot_index: dict[str, dict[str, Any]] = {}

    for dim_key, dim_any in library.items():
        dim_obj = ensure_dict(dim_any, f"library.{dim_key}")
        subdimensions = ensure_dict(dim_obj.get("subdimensions"), f"library.{dim_key}.subdimensions")

        for sub_key, sub_any in subdimensions.items():
            sub_obj = ensure_dict(sub_any, f"library.{dim_key}.subdimensions.{sub_key}")
            slot = sub_obj.get("slot", sub_key)
            if not isinstance(slot, str) or not slot:
                raise IntegrityError(f"Ungültiger oder leerer Slot unter library.{dim_key}.subdimensions.{sub_key}")

            values = ensure_list(sub_obj.get("values"), f"library.{dim_key}.subdimensions.{sub_key}.values")
            allowed_values: set[str] = set()

            for idx, value_any in enumerate(values):
                value_obj = ensure_dict(
                    value_any,
                    f"library.{dim_key}.subdimensions.{sub_key}.values[{idx}]",
                )
                value_key = value_obj.get("key")
                if not isinstance(value_key, str) or not value_key:
                    raise IntegrityError(
                        f"Fehlender oder ungültiger value.key unter "
                        f"library.{dim_key}.subdimensions.{sub_key}.values[{idx}]"
                    )
                allowed_values.add(value_key)

            slot_index[slot] = {
                "dimension": dim_key,
                "subdimension": sub_key,
                "required": bool(sub_obj.get("required", False)),
                "multi": bool(sub_obj.get("multi", False)),
                "allowed_values": allowed_values,
            }

    return slot_index


def validate_slot_schema(data: dict[str, Any], errors: list[str]) -> None:
    actual = ensure_list(data.get("slot_schema"), "slot_schema")
    expected = build_expected_slot_schema(data)

    if actual != expected:
        errors.append(
            "slot_schema driftet von library ab. "
            "Erzeuge slot_schema neu oder korrigiere manuelle Änderungen."
        )


def validate_templates(data: dict[str, Any], slot_index: dict[str, dict[str, Any]], errors: list[str]) -> None:
    templates = ensure_list(data.get("templates"), "templates")
    seen_ids: set[str] = set()

    for idx, tpl_any in enumerate(templates):
        tpl = ensure_dict(tpl_any, f"templates[{idx}]")
        tpl_id = tpl.get("id")
        if not isinstance(tpl_id, str) or not tpl_id:
            errors.append(f"templates[{idx}] hat keine gültige id.")
            continue
        if tpl_id in seen_ids:
            errors.append(f"Doppelte Template-ID erkannt: {tpl_id}")
        seen_ids.add(tpl_id)

        slots_used = ensure_list(tpl.get("slots_used"), f"templates[{idx}].slots_used")
        tpl_text = tpl.get("text")
        if not isinstance(tpl_text, str) or not tpl_text:
            errors.append(f"Template '{tpl_id}' hat keinen gültigen text.")
            continue

        used_slots: list[str] = []
        for slot_any in slots_used:
            if not isinstance(slot_any, str) or not slot_any:
                errors.append(f"Template '{tpl_id}' enthält einen ungültigen slots_used-Eintrag.")
                continue
            if slot_any not in slot_index:
                errors.append(f"Template '{tpl_id}' referenziert unbekannten Slot in slots_used: {slot_any}")
            used_slots.append(slot_any)

        placeholders = PLACEHOLDER_RE.findall(tpl_text)
        placeholder_set = set(placeholders)
        used_set = set(used_slots)

        unknown_placeholders = sorted(slot for slot in placeholder_set if slot not in slot_index)
        if unknown_placeholders:
            errors.append(
                f"Template '{tpl_id}' enthält unbekannte Platzhalter: {', '.join(unknown_placeholders)}"
            )

        missing_in_text = sorted(slot for slot in used_set if slot not in placeholder_set)
        if missing_in_text:
            errors.append(
                f"Template '{tpl_id}' führt Slots in slots_used, die im Text nicht vorkommen: "
                f"{', '.join(missing_in_text)}"
            )

        missing_in_slots_used = sorted(slot for slot in placeholder_set if slot not in used_set)
        if missing_in_slots_used:
            errors.append(
                f"Template '{tpl_id}' enthält Platzhalter, die nicht in slots_used stehen: "
                f"{', '.join(missing_in_slots_used)}"
            )


def validate_examples(data: dict[str, Any], slot_index: dict[str, dict[str, Any]], errors: list[str]) -> None:
    examples = ensure_list(data.get("example_instances"), "example_instances")
    seen_ids: set[str] = set()

    for idx, ex_any in enumerate(examples):
        ex = ensure_dict(ex_any, f"example_instances[{idx}]")
        ex_id = ex.get("id")
        if not isinstance(ex_id, str) or not ex_id:
            errors.append(f"example_instances[{idx}] hat keine gültige id.")
            continue
        if ex_id in seen_ids:
            errors.append(f"Doppelte Example-ID erkannt: {ex_id}")
        seen_ids.add(ex_id)

        values = ensure_dict(ex.get("values"), f"example_instances[{idx}].values")

        for slot, raw_value in values.items():
            if slot not in slot_index:
                errors.append(f"Example '{ex_id}' nutzt unbekannten Slot: {slot}")
                continue

            meta = slot_index[slot]
            if meta["multi"]:
                if not isinstance(raw_value, list):
                    errors.append(f"Example '{ex_id}': Multi-Slot '{slot}' erwartet eine Liste.")
                    continue
                for item in raw_value:
                    if not isinstance(item, str):
                        errors.append(
                            f"Example '{ex_id}': Multi-Slot '{slot}' enthält einen nicht-string Wert."
                        )
                        continue
                    if item not in meta["allowed_values"]:
                        errors.append(
                            f"Example '{ex_id}': Ungültiger Wert '{item}' für Slot '{slot}'."
                        )
            else:
                if not isinstance(raw_value, str):
                    errors.append(f"Example '{ex_id}': Slot '{slot}' erwartet genau einen String-Wert.")
                    continue
                if raw_value not in meta["allowed_values"]:
                    errors.append(
                        f"Example '{ex_id}': Ungültiger Wert '{raw_value}' für Slot '{slot}'."
                    )


def validate_constraints(data: dict[str, Any], slot_index: dict[str, dict[str, Any]], errors: list[str]) -> None:
    constraints = ensure_list(data.get("constraints"), "constraints")
    seen_ids: set[str] = set()

    for idx, cons_any in enumerate(constraints):
        cons = ensure_dict(cons_any, f"constraints[{idx}]")
        cons_id = cons.get("id")
        cons_type = cons.get("type")

        if not isinstance(cons_id, str) or not cons_id:
            errors.append(f"constraints[{idx}] hat keine gültige id.")
        elif cons_id in seen_ids:
            errors.append(f"Doppelte Constraint-ID erkannt: {cons_id}")
        else:
            seen_ids.add(cons_id)

        cond = ensure_dict(cons.get("if"), f"constraints[{idx}].if")
        cond_slot = cond.get("slot")
        cond_equals = cond.get("equals")

        if not isinstance(cond_slot, str) or cond_slot not in slot_index:
            errors.append(f"Constraint '{cons_id or idx}' referenziert unbekannten if.slot.")
            continue
        if not isinstance(cond_equals, str) or cond_equals not in slot_index[cond_slot]["allowed_values"]:
            errors.append(
                f"Constraint '{cons_id or idx}' nutzt ungültigen if.equals-Wert für Slot '{cond_slot}'."
            )

        if cons_type == "recommendation":
            then_obj = ensure_dict(cons.get("then"), f"constraints[{idx}].then")
            recommended_slots = ensure_list(
                then_obj.get("recommended_slots"),
                f"constraints[{idx}].then.recommended_slots",
            )
            recommended_values = ensure_dict(
                then_obj.get("recommended_values"),
                f"constraints[{idx}].then.recommended_values",
            )

            for slot_any in recommended_slots:
                if not isinstance(slot_any, str) or slot_any not in slot_index:
                    errors.append(
                        f"Constraint '{cons_id or idx}' referenziert unbekannten recommended_slot: {slot_any}"
                    )

            for rec_slot, rec_vals_any in recommended_values.items():
                if rec_slot not in slot_index:
                    errors.append(
                        f"Constraint '{cons_id or idx}' referenziert unbekannten Slot in recommended_values: {rec_slot}"
                    )
                    continue
                rec_vals = ensure_list(
                    rec_vals_any,
                    f"constraints[{idx}].then.recommended_values.{rec_slot}",
                )
                for value_any in rec_vals:
                    if not isinstance(value_any, str) or value_any not in slot_index[rec_slot]["allowed_values"]:
                        errors.append(
                            f"Constraint '{cons_id or idx}' nutzt ungültigen Empfehlungswert "
                            f"'{value_any}' für Slot '{rec_slot}'."
                        )

        elif cons_type == "incompatibility":
            then_not = ensure_dict(cons.get("then_not"), f"constraints[{idx}].then_not")
            target_slot = then_not.get("slot")
            forbidden_value = then_not.get("contains")

            if not isinstance(target_slot, str) or target_slot not in slot_index:
                errors.append(f"Constraint '{cons_id or idx}' referenziert unbekannten then_not.slot.")
                continue
            if not slot_index[target_slot]["multi"]:
                errors.append(
                    f"Constraint '{cons_id or idx}' nutzt contains auf Nicht-Multi-Slot '{target_slot}'."
                )
            if not isinstance(forbidden_value, str) or forbidden_value not in slot_index[target_slot]["allowed_values"]:
                errors.append(
                    f"Constraint '{cons_id or idx}' nutzt ungültigen then_not.contains-Wert für Slot '{target_slot}'."
                )
        else:
            errors.append(f"Constraint '{cons_id or idx}' hat einen unbekannten Typ: {cons_type}")


def run_checks(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    slot_index = build_slot_index(data)

    validate_slot_schema(data, errors)
    validate_templates(data, slot_index, errors)
    validate_examples(data, slot_index, errors)
    validate_constraints(data, slot_index, errors)

    return errors


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Prüft semantische Integrität von data/library.json über das JSON-Schema hinaus."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT,
        help=f"Pfad zur library.json (Default: {DEFAULT_INPUT})",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        data = load_json(args.input)
        errors = run_checks(data)

        if errors:
            print("✘ Integritätsfehler gefunden:", file=sys.stderr)
            for error in errors:
                print(f"  - {error}", file=sys.stderr)
            return 1

        print("✔ Integritätsprüfung erfolgreich")
        print(f"  Datei: {args.input}")
        print("  Geprüft: slot_schema, templates, constraints, example_instances")
        return 0

    except IntegrityError as exc:
        print(f"✘ Fehler: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"✘ Unerwarteter Fehler: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
