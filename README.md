# Wissensbibliothek Promptbausteine

Eine interaktive Wissensbibliothek für Prompt-Bausteine mit kanonischer Taxonomie, Generator-Layer und optionalem Heuristik-Layer.

## Grundsatz

In diesem Repository gelten immer die **Originaldateinamen** als aktuelle Wahrheit.
Es gibt im laufenden Stand keine Versionssuffixe in produktiven Dateinamen.

Aktuelle Kernpfade:

- `data/library.json`
- `schema/library.schema.json`
- `scripts/validate_integrity.py`
- `ui/index.html`
- `system/system-prompt.txt`

## Schnellstart

```bash
npm install -g ajv-cli
python -m pip install pre-commit
pre-commit install
ajv validate -s schema/library.schema.json -d data/library.json
python scripts/validate_integrity.py
```

## Modell

Der aktuelle Kern erwartet:

- `dimensions`
- `slots`
- `values`
- `templates`
- `generator`
- `workflows`
- `heuristics`

## UI

Die UI lädt die Bibliothek aus:

- `../data/library.json`

## Integritätsprüfung

Der aktuelle Checker ist:

- `scripts/validate_integrity.py`

Der Default-Input ist:

- `data/library.json`

## Lizenz

MIT. Siehe `LICENSE`.
