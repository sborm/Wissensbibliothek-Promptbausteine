#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Migriert das V2-Prompt-Bibliotheksmodell in das V3-Zielmodell.

Bekannte Mapping-Lücken (keine Warnings, aber beim ajv-Lauf prüfen):
- ZIELGRUPPE: V2-Werte 'extern'/'internal' existieren in V3 nicht.
  In den 7 Beispielinstanzen nicht verwendet, daher kein Blocking.
- INHALTSQUALITAET: V2-Wert 'fokussiert' hat kein direktes V3-Äquivalent.
  In den 7 Beispielinstanzen nicht verwendet.
- METHODIK: neuer V3-Slot ohne V2-Quelle, wird nicht befüllt.
  Templates, die [METHODIK] referenzieren, rendern den Platzhalter literal,
  bis der Slot manuell gesetzt wird.
"""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any, Dict, List, Optional


ROLE_MAP: Dict[tuple, str] = {
    ("analyst", "neutral"): "neutraler_analyst",
    ("analyst", "beratend"): "neutraler_analyst",
    ("analyst", "hinterfragend"): "kritischer_analyst",
    ("analyst", "herausfordernd"): "kritischer_analyst",
    ("strategieberater", "neutral"): "strategischer_berater",
    ("strategieberater", "beratend"): "strategischer_berater",
    ("strategieberater", "hinterfragend"): "kritischer_sparringspartner",
    ("strategieberater", "herausfordernd"): "kritischer_sparringspartner",
    ("lehrer", "neutral"): "didaktischer_erklaerer",
    ("lehrer", "beratend"): "didaktischer_erklaerer",
    ("lehrer", "hinterfragend"): "didaktischer_erklaerer",
    ("lehrer", "herausfordernd"): "didaktischer_erklaerer",
    ("lektor", "neutral"): "sprachlicher_optimierer",
    ("lektor", "beratend"): "sprachlicher_optimierer",
    ("lektor", "hinterfragend"): "sprachlicher_optimierer",
    ("lektor", "herausfordernd"): "sprachlicher_optimierer",
}

ERGEBNISFOKUS_MAP: Dict[str, str] = {
    "nur_ergebnis": "nur_ergebnis",
    "ergebnis_plus_begruendung": "ergebnis_mit_begruendung",
    "ergebnis_plus_alternativen": "ergebnis_mit_alternativen",
    "ergebnis_plus_naechste_schritte": "ergebnis_mit_naechsten_schritten",
}

# V2 UMFANG hatte "lang"; V3 verwendet "ausfuehrlich".
UMFANG_MAP: Dict[str, str] = {
    "lang": "ausfuehrlich",
}

TARGET_DEFAULTS: Dict[str, str] = {
    "TABELLENREGEL": "tabellen_erlaubt",
    "LISTENREGEL": "listen_erlaubt",
    "BEISPIELREGEL": "beispiele_erlaubt",
    "METAREGEL": "meta_erlaubt",
    "REDUNDANZREGEL": "wiederholungen_erlaubt",
    "EVIDENZREGEL": "offen",
}

TARGET_SLOT_SEQUENCE: List[str] = [
    "ZIEL_TYP", "ZIEL_REIFE",
    "AUFGABENTYP", "AUFGABENSTRUKTUR",
    "SITUATIONSKONTEXT", "ZIELGRUPPE", "WISSENSNIVEAU", "RAHMENBEDINGUNG",
    "PROZESSLOGIK", "METHODIK", "INTERAKTIONSMODUS", "STEUERUNGSGRAD", "ARBEITSMODUS",
    "FORMAT", "UMFANG", "ERGEBNISFOKUS",
    "TONALITAET", "DIREKTHEIT", "ROLLENSTIMME",
    "QUALITAETSFOKUS", "PRIORISIERUNG", "TIEFENGRAD",
    "EVIDENZREGEL", "TABELLENREGEL", "LISTENREGEL", "BEISPIELREGEL", "METAREGEL", "REDUNDANZREGEL",
]


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def choose_template(values: Dict[str, str]) -> str:
    aufgabentyp = values.get("AUFGABENTYP")
    ziel_typ = values.get("ZIEL_TYP")
    situationskontext = values.get("SITUATIONSKONTEXT")

    if aufgabentyp == "umformulieren":
        return "rewrite_v1"
    if ziel_typ in {"entscheiden", "priorisieren"} or situationskontext == "entscheiden":
        return "decision_v1"
    if ziel_typ == "umsetzen" or situationskontext == "operativ_umsetzen":
        return "implementation_v1"
    if aufgabentyp in {"analysieren", "pruefen"}:
        return "analysis_v1"
    return "default_v1"


def map_wissensniveau(
    old_values: Dict[str, Any], warnings: List[str], ctx: str
) -> Optional[str]:
    wk = old_values.get("WISSENSKONTEXT")
    wa = old_values.get("WISSENSSTAND_ADRESSAT")
    if wk and wa and wk != wa:
        warnings.append(
            f"{ctx}: WISSENSKONTEXT='{wk}' und WISSENSSTAND_ADRESSAT='{wa}' weichen ab; "
            "WISSENSSTAND_ADRESSAT wurde bevorzugt."
        )
    return wa or wk


def map_rollenstimme(
    old_values: Dict[str, Any], warnings: List[str], ctx: str
) -> Optional[str]:
    funktion = old_values.get("FUNKTIONSROLLE")
    intervention = old_values.get("INTERVENTIONSTIEFE")
    if not funktion and not intervention:
        return None
    if not funktion:
        warnings.append(
            f"{ctx}: INTERVENTIONSTIEFE gesetzt, FUNKTIONSROLLE fehlt; "
            "Rollenstimme nicht eindeutig ableitbar."
        )
        return None
    if not intervention:
        intervention = "beratend"
        warnings.append(
            f"{ctx}: FUNKTIONSROLLE='{funktion}' ohne INTERVENTIONSTIEFE; "
            "Default 'beratend' angenommen."
        )
    return ROLE_MAP.get((funktion, intervention))


def map_evidenzregel(old_values: Dict[str, Any]) -> str:
    vals = [v for v in (old_values.get("INHALTLICHE_AUSSCHLUESSE") or []) if v]
    if len(vals) >= 2:
        return "strikt_belegt"
    if not vals:
        return TARGET_DEFAULTS["EVIDENZREGEL"]
    return {
        "keine_spekulation": "keine_spekulation",
        "keine_unbelegten_behauptungen": "nur_belegte_aussagen",
        "keine_ueberdehnung_der_datenlage": "unsicherheiten_offen_markieren",
    }.get(vals[0], TARGET_DEFAULTS["EVIDENZREGEL"])


def apply_formal_rules(old_values: Dict[str, Any], target_values: Dict[str, str]) -> None:
    vals = set(old_values.get("FORMALE_AUSSCHLUESSE") or [])
    target_values["TABELLENREGEL"] = (
        "keine_tabellen" if "keine_tabellen" in vals else TARGET_DEFAULTS["TABELLENREGEL"]
    )
    target_values["LISTENREGEL"] = (
        "keine_listen" if "keine_listen" in vals else TARGET_DEFAULTS["LISTENREGEL"]
    )
    target_values["BEISPIELREGEL"] = (
        "keine_beispiele" if "keine_beispiele" in vals else TARGET_DEFAULTS["BEISPIELREGEL"]
    )


def apply_stilregeln(old_values: Dict[str, Any], target_values: Dict[str, str]) -> None:
    vals = set(old_values.get("STILREGELN") or [])
    if "direkt_zum_punkt" in vals:
        target_values["DIREKTHEIT"] = "direkt"
    if "alltagstaugliche_sprache" in vals and "TONALITAET" not in target_values:
        target_values["TONALITAET"] = "alltagstauglich"
    if "ohne_meta_erklaerungen" in vals:
        target_values["METAREGEL"] = "keine_meta_erklaerungen"
    if "ohne_wiederholungen" in vals:
        target_values["REDUNDANZREGEL"] = "keine_wiederholungen"


def migrate_example_instance(
    example: Dict[str, Any], warnings: List[str]
) -> Dict[str, Any]:
    old_values = example.get("values", {})
    ctx = f"example_instance:{example.get('id', 'unknown')}"
    new_values: Dict[str, str] = {}

    direct_map = {
        "ZIEL_TYP": "ZIEL_TYP",
        "HANDLUNGSREIFE": "ZIEL_REIFE",
        "AUFGABENTYP": "AUFGABENTYP",
        "AUFGABENSTRUKTUR": "AUFGABENSTRUKTUR",
        "SITUATIONSKONTEXT": "SITUATIONSKONTEXT",
        "ZIELGRUPPE": "ZIELGRUPPE",
        "RAHMENBEDINGUNG": "RAHMENBEDINGUNG",
        "PROZESSLOGIK": "PROZESSLOGIK",
        "MODUS": "INTERAKTIONSMODUS",
        "STEUERUNGSGRAD": "STEUERUNGSGRAD",
        "DENKMODUS": "ARBEITSMODUS",
        "FORMAT": "FORMAT",
        # UMFANG: separat behandelt wegen "lang" -> "ausfuehrlich"
        "SPRACHQUALITAET": "TONALITAET",
        "INHALTSQUALITAET": "QUALITAETSFOKUS",
        "PRIORISIERUNG": "PRIORISIERUNG",
        "ANALYSETIEFE": "TIEFENGRAD",
    }

    for old_key, new_key in direct_map.items():
        val = old_values.get(old_key)
        if val:
            new_values[new_key] = val

    # UMFANG: Wert-Mapping bevor Eintrag gesetzt wird
    if old_values.get("UMFANG"):
        new_values["UMFANG"] = UMFANG_MAP.get(old_values["UMFANG"], old_values["UMFANG"])

    if old_values.get("ERGEBNISORIENTIERUNG"):
        mapped = ERGEBNISFOKUS_MAP.get(old_values["ERGEBNISORIENTIERUNG"])
        if mapped:
            new_values["ERGEBNISFOKUS"] = mapped
        else:
            warnings.append(
                f"{ctx}: Unbekannter ERGEBNISORIENTIERUNG-Wert "
                f"'{old_values['ERGEBNISORIENTIERUNG']}'."
            )

    wissensniveau = map_wissensniveau(old_values, warnings, ctx)
    if wissensniveau:
        new_values["WISSENSNIVEAU"] = wissensniveau

    rollenstimme = map_rollenstimme(old_values, warnings, ctx)
    if rollenstimme:
        new_values["ROLLENSTIMME"] = rollenstimme
    elif old_values.get("FUNKTIONSROLLE") or old_values.get("INTERVENTIONSTIEFE"):
        warnings.append(f"{ctx}: Rollenstimme konnte nicht eindeutig gemappt werden.")

    new_values["EVIDENZREGEL"] = map_evidenzregel(old_values)
    apply_formal_rules(old_values, new_values)
    apply_stilregeln(old_values, new_values)

    for slot, default in TARGET_DEFAULTS.items():
        new_values.setdefault(slot, default)

    ordered_values = {k: new_values[k] for k in TARGET_SLOT_SEQUENCE if k in new_values}
    return {
        "id": example["id"].replace("example_", "workflow_"),
        "label": example.get("label", example["id"]),
        "template_id": choose_template(ordered_values),
        "values": ordered_values,
    }


def build_target_from_template(
    target_template: Dict[str, Any],
    old_source: Dict[str, Any],
    migrated_workflows: List[Dict[str, Any]],
) -> Dict[str, Any]:
    payload = copy.deepcopy(target_template)
    payload["meta"]["version"] = "3.0.0-migrated"
    payload["meta"]["description"] = (
        "Aus einem V2-Modell migriertes V3-Zielmodell. "
        "Der Kern bildet eine single-select Taxonomie mit getrenntem Generator- "
        "und optionalem Heuristik-Layer."
    )
    payload["workflows"] = migrated_workflows
    payload["heuristics"]["enabled"] = False
    return payload


def make_report(
    old_source: Dict[str, Any],
    new_payload: Dict[str, Any],
    warnings: List[str],
) -> Dict[str, Any]:
    return {
        "source_version": old_source.get("meta", {}).get("version"),
        "target_version": new_payload.get("meta", {}).get("version"),
        "migrated_example_instances": len(old_source.get("example_instances", [])),
        "generated_workflows": len(new_payload.get("workflows", [])),
        "slot_count_target": len(new_payload.get("slots", [])),
        "warning_count": len(warnings),
        "warnings": warnings,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Migriert das alte Prompt-Bibliotheksmodell in das V3-Zielmodell."
    )
    parser.add_argument("--source", required=True, help="Pfad zur alten library.json")
    parser.add_argument(
        "--target-template", required=True, help="Pfad zur V3-Zieldatei als Template"
    )
    parser.add_argument(
        "--output", required=True, help="Pfad fuer die migrierte V3-Datei"
    )
    parser.add_argument(
        "--report", required=False, help="Optionaler Pfad fuer einen Migrationsreport als JSON"
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    source_path = Path(args.source)
    target_template_path = Path(args.target_template)
    output_path = Path(args.output)

    old_source = load_json(source_path)
    target_template = load_json(target_template_path)

    warnings: List[str] = []
    migrated_workflows = [
        migrate_example_instance(example, warnings)
        for example in old_source.get("example_instances", [])
    ]
    new_payload = build_target_from_template(target_template, old_source, migrated_workflows)
    save_json(output_path, new_payload)

    if args.report:
        report = make_report(old_source, new_payload, warnings)
        save_json(Path(args.report), report)

    print(
        f"Migrated {len(old_source.get('example_instances', []))} example_instances "
        f"-> {len(migrated_workflows)} workflows"
    )
    print(f"Output: {output_path}")


if __name__ == "__main__":
    main()
