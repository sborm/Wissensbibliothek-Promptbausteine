# Wissensbibliothek Promptbausteine

Eine taxonomisch strukturierte Prompt-Bibliothek für wiederverwendbare Prompt-Bausteine, validiert per JSON Schema und ergänzt um einen Generator für VS-Code-Snippets.

## Ziel

Dieses Projekt stellt eine kleine, aber saubere Pipeline für Prompt-Bausteine bereit:

- `data/library.json` als Single Source of Truth
- `schema/prompt-library.schema.json` zur Schema-Validierung
- `scripts/build_vscode_snippets.py` zum Generieren von VS-Code-Snippets
- `.pre-commit-config.yaml` für automatische Checks beim Commit

## Projektstruktur

```text
.
├── .pre-commit-config.yaml
├── data/
│   └── library.json
├── schema/
│   └── prompt-library.schema.json
└── scripts/
    └── build_vscode_snippets.py