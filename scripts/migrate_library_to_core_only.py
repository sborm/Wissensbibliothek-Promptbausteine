#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_INPUT = Path("data/library.json")
DEFAULT_OUTPUT = Path("data/library.json")
TARGET_VERSION = "2.5.0"
TARGET_DESCRIPTION = (
    "Taxonomisch strukturierte Prompt-Bibliothek mit geschärfter Slotlogik für Ziel, "
    "Aufgabe, Kontext, Output-Form, Prozess, Qualitätskriterien, Rolle, Grenzen, "
    "Adressat und Interaktionsmodus. Die Bibliothek trennt klar zwischen Ziel, "
    "Operation, Denklogik, fachlicher Funktion, Interventionsintensität und echten "
    "Ausschlüssen. Ergänzt um Templates, Beispielinstanzen, Konfliktregeln und "
    "Provenienzmetadaten."
)


class MigrationError(Exception):
    pass


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise MigrationError(f"Datei nicht gefunden: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise MigrationError(f"Ungültiges JSON in {path}: {exc}") from exc


def ensure_dict(value: Any, path: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise MigrationError(f"Erwartet Objekt unter '{path}', gefunden: {type(value).__name__}")
    return value


def rebuild_slot_schema(library: dict[str, Any]) -> list[dict[str, Any]]:
    slot_schema: list[dict[str, Any]] = []

    for dim_key, dim_obj_any in library.items():
        dim_obj = ensure_dict(dim_obj_any, f"library.{dim_key}")
        subdimensions = ensure_dict(dim_obj.get("subdimensions"), f"library.{dim_key}.subdimensions")

        for sub_key, sub_obj_any in subdimensions.items():
            sub_obj = ensure_dict(sub_obj_any, f"library.{dim_key}.subdimensions.{sub_key}")
            slot = sub_obj.get("slot", sub_key)
            if not isinstance(slot, str) or not slot:
                raise MigrationError(f"Ungültiger Slot in {dim_key}.{sub_key}")

            item: dict[str, Any] = {
                "slot": slot,
                "dimension": dim_key,
                "subdimension": sub_key,
                "required": bool(sub_obj.get("required", False)),
                "multi": bool(sub_obj.get("multi", False)),
            }
            for key in (
                "origin",
                "evidence_strength",
                "auto_recommendation_tier",
                "recommendation_notes",
                "heuristic_scope",
                "confidence",
            ):
                if key in sub_obj:
                    item[key] = sub_obj[key]
            slot_schema.append(item)

    return slot_schema


def migrate(data: dict[str, Any]) -> dict[str, Any]:
    library = ensure_dict(data.get("library"), "library")
    meta = ensure_dict(data.get("meta"), "meta")

    meta["version"] = TARGET_VERSION
    meta["created"] = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    meta["description"] = TARGET_DESCRIPTION

    data.pop("context_integration", None)
    data.pop("linked_case_sources", None)
    data["slot_schema"] = rebuild_slot_schema(library)
    return data


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Entfernt den Case-Sonderpfad aus data/library.json und regeneriert slot_schema."
    )
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT, help=f"Eingabedatei (Default: {DEFAULT_INPUT})")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help=f"Ausgabedatei (Default: {DEFAULT_OUTPUT})")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    data = load_json(args.input)
    migrated = migrate(data)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(migrated, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"✔ Core-only library geschrieben: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
