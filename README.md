# Wissensbibliothek Promptbausteine

Eine taxonomisch strukturierte Prompt-Bibliothek für wiederverwendbare Prompt-Bausteine, validiert per JSON Schema, ergänzt um Integritätsprüfung, Prompt-Rendering, eine lokale UI und einen Generator für VS-Code-Snippets.

## Ziel

Dieses Repository ist der **Core** der Prompt-Bibliothek.

Es enthält die allgemeine Bibliothekslogik und die zentralen Werkzeuge zur Pflege, Prüfung und Nutzung:

- `data/library.json` als zentrale Bibliotheksquelle
- `schema/prompt-library.schema.json` zur Schema-Validierung
- `scripts/validate_integrity.py` zur Integritätsprüfung zwischen Bibliothek, Slots, Templates, Constraints und Beispielinstanzen
- `scripts/render_prompt.py` zum Rendern vollständiger Prompts
- `scripts/build_vscode_snippets.py` zum Generieren von VS-Code-Snippets
- `ui/index.html` als lokale Konfigurationsoberfläche

Nicht Teil des Core-Repos sind fall- oder projektspezifische Sonderpfade.

## Projektstruktur

~~~text
.
├── .pre-commit-config.yaml
├── README.md
├── data/
│   └── library.json
├── schema/
│   └── prompt-library.schema.json
├── scripts/
│   ├── build_vscode_snippets.py
│   ├── render_prompt.py
│   └── validate_integrity.py
└── ui/
    └── index.html
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
| Python | Skripte und lokale Hilfstools |
| Node.js | Installation von `ajv-cli` |
| `ajv-cli` | JSON-Schema-Validierung |
| `pre-commit` | Git-Hooks |
| VS Code | Nutzung der generierten Snippets |

## Schnellstart

### 1. Repository klonen

~~~bash
git clone https://github.com/sborm/Wissensbibliothek-Promptbausteine.git
cd Wissensbibliothek-Promptbausteine
~~~

### 2. Benötigte Tools installieren

~~~bash
npm install -g ajv-cli
pip install pre-commit
~~~

### 3. Git-Hooks installieren

~~~bash
pre-commit install
~~~

### 4. Bibliothek per Schema validieren

~~~bash
ajv validate -s schema/prompt-library.schema.json -d data/library.json
~~~

Erwartetes Ergebnis:

~~~text
data/library.json valid
~~~

### 5. Bibliotheksintegrität prüfen

~~~bash
python scripts/validate_integrity.py
~~~

### 6. VS-Code-Snippets erzeugen

~~~bash
python scripts/build_vscode_snippets.py
~~~

### 7. Prompt rendern

Beispiel mit Example-Instance:

~~~bash
python scripts/render_prompt.py --instance example_01
~~~

Beispiel mit manuell gesetzten Slots:

~~~bash
python scripts/render_prompt.py \
  --set ZIEL_TYP=entscheiden \
  --set AUFGABENTYP=vergleichen \
  --set FORMAT=tabelle
~~~

### 8. UI lokal starten

Im Repo-Stammverzeichnis:

~~~bash
python -m http.server 8080
~~~

Danach im Browser öffnen:

~~~text
http://localhost:8080/ui/
~~~

## Verwendung in VS Code

Nach dem Build liegt die generierte Datei hier:

~~~text
.vscode/prompt-library.code-snippets
~~~

Diese Datei wird lokal erzeugt und kann direkt im Workspace verwendet werden.

## Was generiert wird

Der Snippet-Generator erzeugt drei Arten von Snippets.

### 1. Wert-Snippets

Beispiel:

- Prefix: `ziel_typ.entscheiden`
- Ausgabe: `[ZIEL_TYP:entscheiden]`

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
[ZIEL_TYP:entscheiden]
[AUFGABENTYP:vergleichen]
[FORMAT:tabelle]
~~~

### Beispiel: mit Snippets in VS Code

Einfach nacheinander tippen:

~~~text
ziel_typ.entscheiden
aufgabentyp.vergleichen
format.tabelle
~~~

und mit Tab vervollständigen.

## Workflow bei Änderungen

Wenn du die Bibliothek erweiterst oder änderst, halte diese Reihenfolge ein:

### 1. `data/library.json` bearbeiten

Hier pflegst du insbesondere:

- Dimensionen
- Subdimensionen
- Werte
- Templates
- Constraints
- Beispielinstanzen

### 2. JSON per Schema validieren

~~~bash
ajv validate -s schema/prompt-library.schema.json -d data/library.json
~~~

### 3. Bibliotheksintegrität prüfen

~~~bash
python scripts/validate_integrity.py
~~~

### 4. Snippets neu generieren

~~~bash
python scripts/build_vscode_snippets.py
~~~

### 5. Rendering prüfen

~~~bash
python scripts/render_prompt.py --list-slots
python scripts/render_prompt.py --list-templates
python scripts/render_prompt.py --instance example_01
~~~

### 6. Alle Hooks lokal ausführen

~~~bash
pre-commit run --all-files
~~~

### 7. Änderungen committen

~~~bash
git add .
git commit -m "Update prompt library core"
~~~

## Pre-commit-Verhalten

Die Git-Hooks führen aktuell aus:

- Schema-Validierung für `data/library.json`
- Integritätsprüfung der Bibliothek
- Neuaufbau der VS-Code-Snippets

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

## UI-Grundidee

Die UI führt in vier Schritten durch die Bibliothek:

1. Pflichtangaben
2. Sinnvolle Ergänzungen
3. Verfeinern
4. Ausschlüsse

Zusätzlich zeigt sie:

- eine Prompt-Vorschau
- eine lesbare Zusammenfassung der Auswahl
- eine technische Slot-Ansicht
- eine interne Gesamtbewertung

## Typische Befehle

### Validieren

~~~bash
ajv validate -s schema/prompt-library.schema.json -d data/library.json
~~~

### Integrität prüfen

~~~bash
python scripts/validate_integrity.py
~~~

### Snippets bauen

~~~bash
python scripts/build_vscode_snippets.py
~~~

### Prompts rendern

~~~bash
python scripts/render_prompt.py --instance example_01
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

### UI lädt nicht sauber

Prüfen:

- startest du einen lokalen Webserver im Repo-Stamm?
- existiert `data/library.json`?
- ist `library.json` gültiges JSON?

### JSON ist ungültig

Dann zeigt `ajv` einen Validierungsfehler. In diesem Fall zuerst `data/library.json` korrigieren und dann erneut validieren.

### Integritätsprüfung schlägt fehl

Dann liegt ein inhaltlicher Widerspruch im Modell vor, zum Beispiel zwischen:

- `slot_schema` und tatsächlichen Slots
- `templates` und `slots_used`
- `constraints` und referenzierten Slots
- `example_instances` und definierten Schlüsselwerten

In diesem Fall zuerst die gemeldete Referenz oder Inkonsistenz in `data/library.json` korrigieren und dann erneut prüfen.

## Nächste sinnvolle Ausbaurichtung

Der nächste sinnvolle Ausbau im Core ist **nicht weitere Sonderlogik**, sondern die **Kanonisierung und Härtung des bestehenden Kerns**:

- Referenzfälle in `example_instances` als belastbare Goldstandards schärfen
- Templates enger auf die tatsächlich relevanten Kernslots rückbinden
- Smoke-Tests für mehrere Referenzinstanzen ergänzen
- Dokumentation, Beispiele und Modelllogik konsequent synchron halten

## Lizenz

Noch keine Lizenz definiert.