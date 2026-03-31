# Wissensbibliothek Promptbausteine

Eine taxonomisch strukturierte Prompt-Bibliothek für wiederverwendbare Prompt-Bausteine, validiert per JSON Schema und ergänzt um einen Generator für VS-Code-Snippets.

## Ziel

Dieses Projekt stellt eine kleine, saubere und lokal nutzbare Pipeline für Prompt-Bausteine bereit:

- `data/library.json` als Single Source of Truth
- `schema/prompt-library.schema.json` zur Schema-Validierung
- `scripts/build_vscode_snippets.py` zum Generieren von VS-Code-Snippets
- `.pre-commit-config.yaml` für automatische Checks beim Commit

## Variante A

Dieses Repository nutzt **Variante A**:

- die Snippets werden **lokal erzeugt**
- die generierte Datei `.vscode/prompt-library.code-snippets` wird **nicht als Quellbestandteil gepflegt**
- `library.json` bleibt die zentrale Datenquelle

Das hält das Repository schlank und vermeidet unnötige Merge-Konflikte.

## Projektstruktur

~~~text
.
├── .pre-commit-config.yaml
├── data/
│   └── library.json
├── schema/
│   └── prompt-library.schema.json
└── scripts/
    └── build_vscode_snippets.py
~~~

## Voraussetzungen

### Allgemein

- Git
- Python 3.9 oder neuer
- Node.js 18 oder neuer
- `ajv-cli`
- `pre-commit`
- VS Code

### Wofür die Tools gebraucht werden

| Tool | Zweck |
|---|---|
| Git | Versionsverwaltung |
| Python | Ausführung des Snippet-Generators |
| Node.js | Installation von `ajv-cli` |
| `ajv-cli` | JSON-Schema-Validierung |
| `pre-commit` | Git-Hooks |
| VS Code | Nutzung der generierten Snippets |

## Installation unter macOS / Linux

### 1. Grundtools installieren

Beispiel mit Homebrew:

~~~bash
brew install git python node
npm install -g ajv-cli
pip install pre-commit
~~~

## Installation unter Windows

Beispiel mit Chocolatey:

~~~bash
choco install git python nodejs
npm install -g ajv-cli
pip install pre-commit
~~~

## Installation unter Android (Termux)

Für Android empfiehlt sich die Nutzung über **Termux**.

### 1. Termux vorbereiten

~~~bash
pkg update && pkg upgrade -y
pkg install -y git python nodejs
python -m pip install --upgrade pip
pip install pre-commit
npm install -g ajv-cli
~~~

### 2. Repository klonen

~~~bash
git clone https://github.com/sborm/Wissensbibliothek-Promptbausteine.git
cd Wissensbibliothek-Promptbausteine
~~~

### 3. Git-Hooks aktivieren

~~~bash
pre-commit install
~~~

### 4. JSON validieren

~~~bash
ajv validate -s schema/prompt-library.schema.json -d data/library.json
~~~

### 5. Snippets erzeugen

~~~bash
python scripts/build_vscode_snippets.py
~~~

## Schnellstart

### 1. Repository klonen

~~~bash
git clone https://github.com/sborm/Wissensbibliothek-Promptbausteine.git
cd Wissensbibliothek-Promptbausteine
~~~

### 2. Git-Hooks installieren

~~~bash
pre-commit install
~~~

### 3. Bibliothek validieren

~~~bash
ajv validate -s schema/prompt-library.schema.json -d data/library.json
~~~

Erwartetes Ergebnis:

~~~text
data/library.json valid
~~~

### 4. VS-Code-Snippets erzeugen

~~~bash
python scripts/build_vscode_snippets.py
~~~

Erwartetes Ergebnis:

~~~text
✔ Snippets erstellt
  Datei: .vscode/prompt-library.code-snippets
~~~

### 5. Optional: alle Hooks manuell ausführen

~~~bash
pre-commit run --all-files
~~~

## Verwendung in VS Code

Nach dem Build liegt die generierte Datei hier:

~~~text
.vscode/prompt-library.code-snippets
~~~

Diese Datei wird lokal erzeugt und kann im Workspace verwendet werden.

Falls VS Code die Snippets nicht sofort erkennt:

- VS Code neu laden
- prüfen, ob die Datei wirklich existiert
- prüfen, ob der Generator erfolgreich gelaufen ist

## Was generiert wird

Der Snippet-Generator erzeugt drei Arten von Snippets.

### 1. Wert-Snippets

Beispiel:

- Prefix: `ziel_typ.analysieren`
- Ausgabe: `[ZIEL_TYP:analysieren]`

### 2. Slot-Snippets

Beispiel:

- Prefix: `slot.ziel_typ`
- Ausgabe: `[ZIEL_TYP:${1}]`

### 3. Template-Snippets

Beispiel:

- Prefix: `template.default_v1`
- Ausgabe: kompletter Template-Text aus `library.json`

## Arbeiten mit der Bibliothek

### Beispiel: direkte Prompt-Bausteine

~~~text
[ZIEL_TYP:entscheidung_vorbereiten]
[FORMAT:tabelle]
[UMFANG:kurz]
~~~

### Beispiel: mit Snippets in VS Code

Einfach nacheinander tippen:

~~~text
ziel_typ.entscheidung_vorbereiten
format.tabelle
umfang.kurz
~~~

und mit Tab vervollständigen.

## Workflow bei Änderungen

Wenn du die Bibliothek erweiterst oder änderst:

### 1. `data/library.json` bearbeiten

Hier pflegst du neue:

- Dimensionen
- Subdimensionen
- Werte
- Templates
- Constraints
- Beispielinstanzen

### 2. JSON validieren

~~~bash
ajv validate -s schema/prompt-library.schema.json -d data/library.json
~~~

### 3. Snippets neu generieren

~~~bash
python scripts/build_vscode_snippets.py
~~~

### 4. Änderungen committen

~~~bash
git add .
git commit -m "Update prompt library"
~~~

Durch `pre-commit` werden die konfigurierten Prüfungen automatisch ausgeführt.

## Pre-commit-Verhalten

Die Git-Hooks führen aktuell aus:

- Schema-Validierung für `data/library.json`
- Neuaufbau der VS-Code-Snippets

Damit werden ungültige Änderungen früh erkannt.

## Datenmodell

Die Bibliothek enthält diese Hauptbereiche:

- `meta`
- `library`
- `slot_schema`
- `templates`
- `constraints`
- `example_instances`

### Beispielhafte Hauptdimensionen

- `ZIEL`
- `AUFGABE`
- `KONTEXT`
- `OUTPUT_FORM`
- `PROZESS`
- `QUALITAETSKRITERIEN`
- `ROLLE`
- `GRENZEN`
- `ADRESSAT`
- `INTERAKTIONSMODUS`

## Beispiel-System-Prompt

Ein möglicher System-Prompt für die Nutzung dieser Bibliothek:

~~~text
Du arbeitest mit einer festen Prompt-Bibliothek.
Verwende nur die definierten Slots und Werte aus der Bibliothek.
Wenn ein notwendiger Slot fehlt, frage gezielt nach.
Wenn ein Wert ungültig ist, weise darauf hin und nutze nur gültige Werte.
Interpretiere Platzhalter im Format [SLOT:wert].
~~~

## Typische Befehle

### Validieren

~~~bash
ajv validate -s schema/prompt-library.schema.json -d data/library.json
~~~

### Snippets bauen

~~~bash
python scripts/build_vscode_snippets.py
~~~

### Alle Hooks ausführen

~~~bash
pre-commit run --all-files
~~~

## Häufige Probleme

### `ajv: command not found`

`ajv-cli` ist nicht installiert oder nicht im Pfad.

~~~bash
npm install -g ajv-cli
~~~

### `pre-commit: command not found`

`pre-commit` ist nicht installiert.

~~~bash
pip install pre-commit
~~~

### VS Code zeigt keine Snippets

Prüfen:

- wurde der Generator ausgeführt?
- existiert `.vscode/prompt-library.code-snippets`?
- wurde VS Code neu geladen?

### JSON ist ungültig

Dann zeigt `ajv` einen Validierungsfehler.  
In diesem Fall zuerst `data/library.json` korrigieren und dann erneut validieren.

## Empfohlene Ergänzungen

Sinnvolle nächste Dateien für das Repository:

- `system/system-prompt.txt`
- `.gitignore`

## Beispiel für `.gitignore` in Variante A

~~~gitignore
.vscode/prompt-library.code-snippets
__pycache__/
*.pyc
~~~

## Lizenz

Noch keine Lizenz definiert.