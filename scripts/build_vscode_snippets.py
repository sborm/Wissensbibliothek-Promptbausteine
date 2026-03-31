#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


DEFAULT_INPUT = Path("data/library.json")
DEFAULT_OUTPUT = Path(".vscode/prompt-library.code-snippets")


class LibraryError(Exception):
    pass


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise LibraryError(f"Eingabedatei nicht gefunden: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise LibraryError(f"Ungültiges JSON in {path}: {exc}") from exc


def ensure_dict(value: Any, path: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise LibraryError(f"Erwartet Objekt unter '{path}', gefunden: {type(value).__name__}")
    return value


def ensure_list(value: Any, path: str) -> list[Any]:
    if not isinstance(value, list):
        raise LibraryError(f"Erwartet Liste unter '{path}', gefunden: {type(value).__name__}")
    return value


def normalize_prefix_part(text: str) -> str:
    return text.strip().lower()


def add_snippet(
    snippets: dict[str, dict[str, Any]],
    used_prefixes: set[str],
    name: str,
    prefix: str,
    body: str | list[str],
    description: str,
) -> None:
    if prefix in used_prefixes:
        raise LibraryError(f"Doppelter Snippet-Prefix erkannt: {prefix}")

    used_prefixes.add(prefix)
    snippets[name] = {
        "prefix": prefix,
        "body": body.splitlines() if isinstance(body, str) else body,
        "description": description,
    }


def iter_dimensions(data: dict[str, Any]):
    library = ensure_dict(data.get("library"), "library")
    for dim_key, dim_obj in library.items():
        yield dim_key, ensure_dict(dim_obj, f"library.{dim_key}")


def build_value_snippets(
    data: dict[str, Any],
    snippets: dict[str, dict[str, Any]],
    used_prefixes: set[str],
) -> int:
    count = 0

    for dim_key, dim_obj in iter_dimensions(data):
        subdimensions = ensure_dict(dim_obj.get("subdimensions"), f"library.{dim_key}.subdimensions")

        for sub_key, sub_obj in subdimensions.items():
            sub_obj = ensure_dict(sub_obj, f"library.{dim_key}.subdimensions.{sub_key}")
            slot = sub_obj.get("slot", sub_key)
            values = ensure_list(sub_obj.get("values"), f"library.{dim_key}.subdimensions.{sub_key}.values")

            for idx, value_obj in enumerate(values):
                value_obj = ensure_dict(
                    value_obj,
                    f"library.{dim_key}.subdimensions.{sub_key}.values[{idx}]",
                )

                value_key = value_obj.get("key")
                value_label = value_obj.get("label", value_key)
                value_description = value_obj.get("description", "")

                if not isinstance(value_key, str) or not value_key:
                    raise LibraryError(
                        f"Fehlender oder ungültiger 'key' unter "
                        f"library.{dim_key}.subdimensions.{sub_key}.values[{idx}]"
                    )

                prefix = f"{normalize_prefix_part(slot)}.{normalize_prefix_part(value_key)}"
                body = f"[{slot}:{value_key}]"
                description = f"{dim_key} → {sub_key} → {value_label}"
                if value_description:
                    description += f" — {value_description}"

                name = f"Wert | {slot} | {value_key}"
                add_snippet(snippets, used_prefixes, name, prefix, body, description)
                count += 1

    return count


def build_slot_snippets(
    data: dict[str, Any],
    snippets: dict[str, dict[str, Any]],
    used_prefixes: set[str],
) -> int:
    count = 0
    slot_schema = ensure_list(data.get("slot_schema", []), "slot_schema")

    for idx, slot_obj in enumerate(slot_schema):
        slot_obj = ensure_dict(slot_obj, f"slot_schema[{idx}]")
        slot = slot_obj.get("slot")
        dimension = slot_obj.get("dimension", "")
        subdimension = slot_obj.get("subdimension", "")
        required = bool(slot_obj.get("required", False))
        multi = bool(slot_obj.get("multi", False))

        if not isinstance(slot, str) or not slot:
            raise LibraryError(f"Fehlender oder ungültiger 'slot' unter slot_schema[{idx}]")

        prefix = f"slot.{normalize_prefix_part(slot)}"
        body = f"[{slot}:${{1:value1,value2}}]" if multi else f"[{slot}:${{1}}]"
        description = f"Slot {slot} ({dimension} → {subdimension}, {'Pflichtfeld' if required else 'optional'}, {'mehrfach' if multi else 'einfach'})"
        name = f"Slot | {slot}"

        add_snippet(snippets, used_prefixes, name, prefix, body, description)
        count += 1

    return count


def build_template_snippets(
    data: dict[str, Any],
    snippets: dict[str, dict[str, Any]],
    used_prefixes: set[str],
) -> int:
    count = 0
    templates = ensure_list(data.get("templates", []), "templates")

    for idx, tpl in enumerate(templates):
        tpl = ensure_dict(tpl, f"templates[{idx}]")
        tpl_id = tpl.get("id")
        tpl_label = tpl.get("label", tpl_id)
        tpl_text = tpl.get("text")
        tpl_description = tpl.get("description", "")

        if not isinstance(tpl_id, str) or not tpl_id:
            raise LibraryError(f"Fehlende oder ungültige 'id' unter templates[{idx}]")
        if not isinstance(tpl_text, str) or not tpl_text:
            raise LibraryError(f"Fehlender oder ungültiger 'text' unter templates[{idx}]")

        prefix = f"template.{normalize_prefix_part(tpl_id)}"
        description = f"Template: {tpl_label}"
        if tpl_description:
            description += f" — {tpl_description}"

        name = f"Template | {tpl_id}"
        add_snippet(snippets, used_prefixes, name, prefix, tpl_text, description)
        count += 1

    return count


def save_snippets(snippets: dict[str, dict[str, Any]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    sorted_snippets = dict(sorted(snippets.items(), key=lambda item: item[0].lower()))
    output_path.write_text(
        json.dumps(sorted_snippets, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Erzeugt VS-Code-Snippets aus data/library.json.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT, help=f"Pfad zur library.json (Default: {DEFAULT_INPUT})")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help=f"Pfad zur VS-Code-Snippet-Datei (Default: {DEFAULT_OUTPUT})")
    parser.add_argument("--no-slots", action="store_true", help="Keine Slot-Snippets erzeugen")
    parser.add_argument("--no-templates", action="store_true", help="Keine Template-Snippets erzeugen")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        data = load_json(args.input)
        snippets: dict[str, dict[str, Any]] = {}
        used_prefixes: set[str] = set()

        value_count = build_value_snippets(data, snippets, used_prefixes)
        slot_count = 0 if args.no_slots else build_slot_snippets(data, snippets, used_prefixes)
        template_count = 0 if args.no_templates else build_template_snippets(data, snippets, used_prefixes)

        save_snippets(snippets, args.output)

        total = value_count + slot_count + template_count
        print("✔ Snippets erstellt")
        print(f"  Datei: {args.output}")
        print(f"  Wert-Snippets: {value_count}")
        print(f"  Slot-Snippets: {slot_count}")
        print(f"  Template-Snippets: {template_count}")
        print(f"  Gesamt: {total}")
        return 0

    except LibraryError as exc:
        print(f"✘ Fehler: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"✘ Unerwarteter Fehler: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())