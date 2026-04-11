#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any


DEFAULT_INPUT = Path("data/library.json")

PLACEHOLDER_RE = re.compile(r"\[([A-Z0-9_]+)\]")


class IntegrityError(Exception):
    pass


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


def build_dimension_index(data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    dimensions = ensure_list(data.get("dimensions"), "dimensions")
    index: dict[str, dict[str, Any]] = {}
    seen_ids: set[str] = set()

    for idx, dim_any in enumerate(dimensions):
        dim = ensure_dict(dim_any, f"dimensions[{idx}]")
        dim_id = dim.get("id")
        dim_key = dim.get("key")

        if not isinstance(dim_id, str) or not dim_id:
            raise IntegrityError(f"dimensions[{idx}] hat keine gültige id.")
        if dim_id in seen_ids:
            raise IntegrityError(f"Doppelte Dimension-ID erkannt: {dim_id}")
        seen_ids.add(dim_id)

        if not isinstance(dim_key, str) or not dim_key:
            raise IntegrityError(f"dimensions[{idx}] hat keinen gültigen key.")
        if dim_key in index:
            raise IntegrityError(f"Doppelter Dimension-Key erkannt: {dim_key}")

        slot_order = ensure_list(dim.get("slot_order"), f"dimensions[{idx}].slot_order")
        slot_order_clean: list[str] = []
        for pos, slot_any in enumerate(slot_order):
            if not isinstance(slot_any, str) or not slot_any:
                raise IntegrityError(f"Ungültiger slot_order-Eintrag in dimensions[{idx}] an Position {pos}")
            slot_order_clean.append(slot_any)

        index[dim_key] = {
            "id": dim_id,
            "key": dim_key,
            "slot_order": slot_order_clean,
            "raw": dim,
        }

    return index


def build_slot_index(data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    slots = ensure_list(data.get("slots"), "slots")
    value_sets = ensure_dict(data.get("values"), "values")

    index: dict[str, dict[str, Any]] = {}
    seen_ids: set[str] = set()

    for idx, slot_any in enumerate(slots):
        slot = ensure_dict(slot_any, f"slots[{idx}]")
        slot_id = slot.get("id")
        slot_key = slot.get("key")
        dimension = slot.get("dimension")
        value_set_name = slot.get("value_set")
        multi = slot.get("multi")

        if not isinstance(slot_id, str) or not slot_id:
            raise IntegrityError(f"slots[{idx}] hat keine gültige id.")
        if slot_id in seen_ids:
            raise IntegrityError(f"Doppelte Slot-ID erkannt: {slot_id}")
        seen_ids.add(slot_id)

        if not isinstance(slot_key, str) or not slot_key:
            raise IntegrityError(f"slots[{idx}] hat keinen gültigen key.")
        if slot_key in index:
            raise IntegrityError(f"Doppelter Slot-Key erkannt: {slot_key}")

        if not isinstance(dimension, str) or not dimension:
            raise IntegrityError(f"Slot '{slot_key}' hat keine gültige dimension.")
        if not isinstance(value_set_name, str) or not value_set_name:
            raise IntegrityError(f"Slot '{slot_key}' hat kein gültiges value_set.")
        if value_set_name not in value_sets:
            raise IntegrityError(f"Slot '{slot_key}' referenziert unbekanntes value_set '{value_set_name}'.")

        if multi is not False:
            raise IntegrityError(f"Slot '{slot_key}' verletzt die Single-Select-Regel. multi muss exakt false sein.")

        value_set = ensure_list(value_sets[value_set_name], f"values.{value_set_name}")
        allowed_values: set[str] = set()
        for val_idx, val_any in enumerate(value_set):
            val = ensure_dict(val_any, f"values.{value_set_name}[{val_idx}]")
            value_key = val.get("key")
            if not isinstance(value_key, str) or not value_key:
                raise IntegrityError(f"Wert ohne gültigen key unter values.{value_set_name}[{val_idx}]")
            if value_key in allowed_values:
                raise IntegrityError(f"Doppelter Wert '{value_key}' im value_set '{value_set_name}'")
            allowed_values.add(value_key)

        index[slot_key] = {
            "id": slot_id,
            "key": slot_key,
            "dimension": dimension,
            "required": bool(slot.get("required", False)),
            "value_set": value_set_name,
            "allowed_values": allowed_values,
            "raw": slot,
        }

    return index


def validate_dimensions_against_slots(dimension_index, slot_index, errors):
    slots_by_dimension: dict[str, list[str]] = {}
    for slot_key, meta in slot_index.items():
        slots_by_dimension.setdefault(meta["dimension"], []).append(slot_key)

    for dim_key, dim_meta in dimension_index.items():
        ordered = dim_meta["slot_order"]
        ordered_set = set(ordered)
        actual_set = set(slots_by_dimension.get(dim_key, []))

        missing_in_order = sorted(actual_set - ordered_set)
        if missing_in_order:
            errors.append(f"Dimension '{dim_key}' enthält Slots, die nicht in slot_order stehen: {', '.join(missing_in_order)}")

        unknown_in_order = sorted(ordered_set - set(slot_index))
        if unknown_in_order:
            errors.append(f"Dimension '{dim_key}' enthält unbekannte Slots in slot_order: {', '.join(unknown_in_order)}")

        wrong_dimension = sorted(slot for slot in ordered if slot in slot_index and slot_index[slot]["dimension"] != dim_key)
        if wrong_dimension:
            errors.append(f"Dimension '{dim_key}' führt Slots in slot_order mit anderer Slot-Dimension: {', '.join(wrong_dimension)}")

        if len(ordered) != len(ordered_set):
            dupes = [slot for slot, count in Counter(ordered).items() if count > 1]
            errors.append(f"Dimension '{dim_key}' enthält doppelte Slots in slot_order: {', '.join(sorted(dupes))}")


def validate_values(data, slot_index, errors):
    values = ensure_dict(data.get("values"), "values")
    referenced_value_sets = {meta["value_set"] for meta in slot_index.values()}

    extra_value_sets = sorted(set(values) - referenced_value_sets)
    if extra_value_sets:
        errors.append(f"Nicht referenzierte value_sets vorhanden: {', '.join(extra_value_sets)}")

    for value_set_name, value_set_any in values.items():
        value_set = ensure_list(value_set_any, f"values.{value_set_name}")
        if not value_set:
            errors.append(f"value_set '{value_set_name}' ist leer.")
            continue

        seen_labels: set[str] = set()
        for idx, val_any in enumerate(value_set):
            val = ensure_dict(val_any, f"values.{value_set_name}[{idx}]")
            value_key = val.get("key")
            label = val.get("label")

            if not isinstance(value_key, str) or not value_key:
                errors.append(f"Wert ohne gültigen key unter values.{value_set_name}[{idx}]")
            elif not re.fullmatch(r"[a-z0-9_]+", value_key):
                errors.append(f"Wert '{value_key}' in values.{value_set_name} verletzt snake_case/API-Regel.")

            if not isinstance(label, str) or not label.strip():
                errors.append(f"Wert '{value_key}' in values.{value_set_name} hat kein gültiges label.")
            elif label in seen_labels:
                errors.append(f"Doppeltes Label '{label}' in values.{value_set_name}")
            else:
                seen_labels.add(label)


def validate_templates(data, slot_index, errors):
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
            errors.append(f"Template '{tpl_id}' enthält unbekannte Platzhalter: {', '.join(unknown_placeholders)}")

        missing_in_text = sorted(slot for slot in used_set if slot not in placeholder_set)
        if missing_in_text:
            errors.append(f"Template '{tpl_id}' führt Slots in slots_used, die im Text nicht vorkommen: {', '.join(missing_in_text)}")

        missing_in_slots_used = sorted(slot for slot in placeholder_set if slot not in used_set)
        if missing_in_slots_used:
            errors.append(f"Template '{tpl_id}' enthält Platzhalter, die nicht in slots_used stehen: {', '.join(missing_in_slots_used)}")


def validate_generator(data, slot_index, template_ids, errors):
    generator = ensure_dict(data.get("generator"), "generator")

    default_template_id = generator.get("default_template_id")
    if not isinstance(default_template_id, str) or default_template_id not in template_ids:
        errors.append("generator.default_template_id referenziert kein gültiges Template.")

    slot_sequence = ensure_list(generator.get("slot_sequence"), "generator.slot_sequence")
    required_slots = ensure_list(generator.get("required_slots"), "generator.required_slots")
    modes = ensure_list(generator.get("modes"), "generator.modes")

    sequence_clean: list[str] = []
    for slot_any in slot_sequence:
        if not isinstance(slot_any, str) or slot_any not in slot_index:
            errors.append(f"generator.slot_sequence enthält unbekannten Slot: {slot_any}")
            continue
        sequence_clean.append(slot_any)

    if len(sequence_clean) != len(set(sequence_clean)):
        dupes = [slot for slot, count in Counter(sequence_clean).items() if count > 1]
        errors.append(f"generator.slot_sequence enthält doppelte Slots: {', '.join(sorted(dupes))}")

    all_slots = set(slot_index)
    sequence_set = set(sequence_clean)

    missing_in_sequence = sorted(all_slots - sequence_set)
    if missing_in_sequence:
        errors.append(f"generator.slot_sequence enthält nicht alle Slots des Modells. Fehlend: {', '.join(missing_in_sequence)}")

    for slot_any in required_slots:
        if not isinstance(slot_any, str) or slot_any not in slot_index:
            errors.append(f"generator.required_slots enthält unbekannten Slot: {slot_any}")
            continue
        if slot_any not in sequence_set:
            errors.append(f"generator.required_slots enthält Slot außerhalb von slot_sequence: {slot_any}")

    missing_declared_required = sorted(slot for slot, meta in slot_index.items() if meta["required"] and slot not in set(required_slots))
    if missing_declared_required:
        errors.append(f"generator.required_slots deckt nicht alle required-Slots ab: {', '.join(missing_declared_required)}")

    if len(required_slots) != len(set(required_slots)):
        dupes = [slot for slot, count in Counter(required_slots).items() if count > 1]
        errors.append(f"generator.required_slots enthält doppelte Slots: {', '.join(sorted(dupes))}")

    mode_values: list[str] = []
    for mode_any in modes:
        if not isinstance(mode_any, str) or not mode_any:
            errors.append("generator.modes enthält einen ungültigen Eintrag.")
            continue
        mode_values.append(mode_any)

    if "standard" not in mode_values:
        errors.append("generator.modes muss 'standard' enthalten.")
    if len(mode_values) != len(set(mode_values)):
        dupes = [mode for mode, count in Counter(mode_values).items() if count > 1]
        errors.append(f"generator.modes enthält doppelte Einträge: {', '.join(sorted(dupes))}")


def validate_workflows(data, slot_index, template_index, errors):
    workflows = ensure_list(data.get("workflows"), "workflows")
    seen_ids: set[str] = set()

    generator = ensure_dict(data.get("generator"), "generator")
    required_slots = set(ensure_list(generator.get("required_slots"), "generator.required_slots"))

    for idx, wf_any in enumerate(workflows):
        wf = ensure_dict(wf_any, f"workflows[{idx}]")
        wf_id = wf.get("id")
        if not isinstance(wf_id, str) or not wf_id:
            errors.append(f"workflows[{idx}] hat keine gültige id.")
            continue
        if wf_id in seen_ids:
            errors.append(f"Doppelte Workflow-ID erkannt: {wf_id}")
        seen_ids.add(wf_id)

        template_id = wf.get("template_id")
        if not isinstance(template_id, str) or template_id not in template_index:
            errors.append(f"Workflow '{wf_id}' referenziert kein gültiges template_id.")
            continue

        values = ensure_dict(wf.get("values"), f"workflows[{idx}].values")
        workflow_slots = set(values)

        unknown_slots = sorted(slot for slot in workflow_slots if slot not in slot_index)
        if unknown_slots:
            errors.append(f"Workflow '{wf_id}' enthält unbekannte Slots: {', '.join(unknown_slots)}")
            continue

        for slot, raw_value in values.items():
            if not isinstance(raw_value, str):
                errors.append(f"Workflow '{wf_id}': Slot '{slot}' erwartet genau einen String-Wert.")
                continue
            if raw_value not in slot_index[slot]["allowed_values"]:
                errors.append(f"Workflow '{wf_id}': Ungültiger Wert '{raw_value}' für Slot '{slot}'.")

        missing_required = sorted(slot for slot in required_slots if slot not in workflow_slots)
        if missing_required:
            errors.append(f"Workflow '{wf_id}' fehlt generator.required_slots: {', '.join(missing_required)}")

        tpl_slots = set(template_index[template_id]["slots_used"])
        missing_template_slots = sorted(slot for slot in tpl_slots if slot not in workflow_slots)
        if missing_template_slots:
            errors.append(f"Workflow '{wf_id}' fehlt Template-Slots aus '{template_id}': {', '.join(missing_template_slots)}")


def validate_heuristics(data, errors):
    heuristics = ensure_dict(data.get("heuristics"), "heuristics")
    enabled = heuristics.get("enabled")
    if not isinstance(enabled, bool):
        errors.append("heuristics.enabled muss boolean sein.")
    if not isinstance(heuristics.get("recommendations"), list):
        errors.append("heuristics.recommendations muss eine Liste sein.")
    if not isinstance(heuristics.get("constraints"), list):
        errors.append("heuristics.constraints muss eine Liste sein.")
    if not isinstance(heuristics.get("meta"), dict):
        errors.append("heuristics.meta muss ein Objekt sein.")


def run_checks(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    dimension_index = build_dimension_index(data)
    slot_index = build_slot_index(data)
    validate_dimensions_against_slots(dimension_index, slot_index, errors)
    validate_values(data, slot_index, errors)
    validate_templates(data, slot_index, errors)

    templates = ensure_list(data.get("templates"), "templates")
    template_index = {tpl["id"]: tpl for tpl in templates if isinstance(tpl, dict) and isinstance(tpl.get("id"), str)}

    validate_generator(data, slot_index, set(template_index), errors)
    validate_workflows(data, slot_index, template_index, errors)
    validate_heuristics(data, errors)
    return errors


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prüft semantische Integrität des aktuellen Bibliotheksmodells über das JSON-Schema hinaus.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT, help=f"Pfad zur Bibliotheksdatei (Default: {DEFAULT_INPUT})")
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
        print("  Geprüft: dimensions, slots, values, templates, generator, workflows, heuristics")
        return 0

    except IntegrityError as exc:
        print(f"✘ Fehler: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"✘ Unerwarteter Fehler: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())