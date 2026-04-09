# Strategische Analyse: Wissensbibliothek-Promptbausteine

---

## Kurzfazit

Das Repository ist strukturell solide und technisch konsistent — aber es ist auf einem Kurs, der von der eigenen Designvision signifikant abweicht. Die Bibliothek hat sich in sechs Tagen von einem schlanken, pragmatischen Taxonomie-Werkzeug zu einem 25-Slot-System mit 10 Dimensionen, 18 Constraints, mehrwertigen Slots und einer lokalen Web-App entwickelt. Die ursprüngliche Vision — 6 Hauptbausteine, ein Slot gleich ein Wert, GitHub Pages, 1–2-Wochen-Pflegerhythmus — ist an mehreren kritischen Stellen nicht mehr erkennbar. Das ist kein Versagen: Es ist ein klassisches Phänomen des Scope Creep in Einzelprojekten ohne externen Gegendruck. Das Problem ist nicht die Komplexität an sich, sondern dass die Komplexität ohne Validierungsrahmen entstanden ist. Strukturelle Integrität ist kein Beweis für operative Wirksamkeit.

---

## Befunde

### Ausgangsbedingungen (belastbar)

**Taxonomie-Architektur**

Das Repository enthält eine vollständige, intern konsistente Prompt-Bibliothek: 10 Dimensionen, 25 Slots, rund 120 Werte, 8 Templates, 18 semantische Constraints, 7 vollständig befüllte Goldstandard-Beispielinstanzen. Die Integrität wird durch `validate_integrity.py` geprüft — dieser Lauf schlägt nicht an. JSON Schema Validation + Pre-commit-Hooks sichern Konsistenz bei jedem Commit.

**Entwicklungsgeschwindigkeit**

50 Commits in 6 Tagen (3.–9. April 2026), alle von einem einzelnen Autor. Version 2.8.1. Das `meta.created`-Feld im JSON lautet `2026-04-08T16:05:00Z`, während die ersten Git-Commits auf den 3. April datieren. Es existieren keine Git-Release-Tags.

**Toolchain**

5 Abhängigkeiten für den Normalbetrieb: Node.js 18+, ajv-cli (npm), Python 3.9+, pre-commit, Git. Node.js wird ausschließlich für JSON Schema Validation verwendet. Python-native Alternative (`jsonschema`) würde diese Abhängigkeit eliminieren.

**Lizenz**

README, Zeile 388: „Noch keine Lizenz definiert." Rechtsstatus: unklar.

**PocketFlow-Integration**

`pocketflow/__init_.py` enthält 100 Zeilen vollständiges PocketFlow-Async-Flow-Framework. Der Dateiname hat einen Typo (ein Unterstrich statt zwei): Das Modul ist als Python-Package nicht importierbar. Kein anderer Code im Repository nutzt es. Keine Dokumentation, keine Abhängigkeit in requirements.txt.

**Fallspezifische Dateien**

Git-History zeigt: `falktron_2026_04_02.case.json` und `case-context.schema.json` wurden angelegt und dann bewusst gelöscht. Commit-Sequenz: „migrate_library_to_core_only.py erstellen" → Case-Dateien löschen. Das ist eine dokumentierte Entscheidung für einen generischen Core ohne fallspezifische Einlagerung.

---

### Abweichungen Vision vs. Ist-Zustand (belastbar)

| Designprinzip (Vision) | Ist-Zustand (Repository) | Abweichung |
|---|---|---|
| 6 Hauptbausteine: ZIEL, KONTEXT, PROZESS, OUTPUT, STIL, KRITERIEN | 10 Dimensionen: ZIEL, AUFGABE, KONTEXT, OUTPUT_FORM, PROZESS, QUALITAETSKRITERIEN, ROLLE, GRENZEN, ADRESSAT, INTERAKTIONSMODUS | Erheblich — ROLLE, GRENZEN, ADRESSAT sind ohne Entsprechung in der Vision |
| „Ein Slot = ein Wert, keine Mischformen" | 3 Multi-Value-Slots: STILREGELN, INHALTLICHE_AUSSCHLUESSE, FORMALE_AUSSCHLUESSE | Direkter Verstoß gegen das Design-Prinzip |
| Web-UI auf GitHub Pages mit Copy-Button | Lokale HTTP-Server-Lösung (`python -m http.server 8080`) | UI nicht deployed |
| Werte kurz, nach Muster Substantiv+Adjektiv | Teils lange Compound-Strings: `erst_befunde_dann_interpretation_dann_empfehlung`, `keine_ueberdehnung_der_datenlage` | Inkonsistent |
| Pflegerhythmus alle 1–2 Wochen | 50 Commits in 6 Tagen | Faktor 7–14 überschritten |
| Maximal 3 Hierarchieebenen | 3 Datenebenen + indirekte Schichten (slot_schema, constraints, templates, evidence_metadata) | Formal korrekt, de facto komplexer |

---

### Chancen (belastbar ableitbar)

1. **Solide strukturelle Grundlage:** Die Datenarchitektur ist sauber. Library.json, Schema, Integrity-Check — dieses Fundament trägt.
2. **Pre-commit-Automatisierung:** Qualitätssicherung ist in den Entwicklungsworkflow integriert. Strukturelle Fehler werden vor dem Commit blockiert.
3. **Rendering-Engine:** `render_prompt.py` ist funktionsfähig und unterstützt mehrere Ausgabeformate. Grundlage für automatisierte Pipelines vorhanden.
4. **PocketFlow-Potenzial:** Das Framework wäre bei korrekter Integration die Basis für eine vollautomatische Prompt-Assembly-Pipeline ohne manuelle UI-Interaktion.
5. **Selbstkritische Haltung sichtbar:** Das README benennt explizit den nächsten Schritt als Härtung, nicht Erweiterung. Das ist ein Reifesignal.

---

### Risiken und operative Engpässe (belastbar)

1. **Kein empirischer Nachweis der Wirksamkeit:** Es gibt keine Dokumentation dafür, dass Prompts, die mit diesem System erzeugt werden, tatsächlich bessere KI-Ausgaben liefern als selbst formulierte Prompts. Das gesamte System ruht auf struktureller Plausibilität, nicht auf gemessenem Nutzen.

2. **Selbstreferenzielle Evidenz-Metadaten:** Slots tragen `evidence_strength`-Werte (stark/mittel/schwach) und `confidence`-Scores (0.74–0.92). Die Quellen lauten „community_guide", „repo_practice", „practitioner_blog" — alle ohne URL, ohne Zitation, nicht nachprüfbar. Diese Scores simulieren epistemische Präzision, die nicht vorhanden ist. Sie könnten dazu führen, dass Entscheidungen auf Basis von Scheingewissheiten getroffen werden.

3. **Pocketflow-Typo als Symptom:** Ein einziger falscher Unterstrich macht ein Framework unnutzbar. Dieser Fehler wäre mit einem `python -c "import pocketflow"` sofort auffindbar. Dass er bis v2.8.1 bestehen bleibt, zeigt: Das System wird strukturell, nicht funktional geprüft.

4. **Constraint-Dünnheit:** 18 Constraints decken einen kleinen Bruchteil der möglichen 25-Slot-Kombinationen ab. Das Constraint-System gibt den Eindruck semantischer Absicherung, ohne den tatsächlich zu liefern. Fehlanwendungen werden nicht erkannt.

5. **Setup-Overhead für ein Personal-Tool:** 5 Abhängigkeiten, pre-commit-Installation, lokaler Webserver — dieser Einstiegsaufwand ist für eine Einzelperson unverhältnismäßig. Jeder Neuaufsetzer (anderes Gerät, neue Umgebung) durchläuft dieselbe Setupstrecke.

6. **GitHub Pages fehlt:** Der im Workflow zentrale „Kopieren → Chat einfügen → fertig"-Zyklus funktioniert nur lokal. Das schränkt die Nutzbarkeit auf stationäre Umgebungen ein.

7. **Ungültiger Wert im System-Prompt:** `system/system-prompt.txt` Zeile 25 enthielt `[ZIEL_TYP:entscheidung_vorbereiten]` — ein Key, der in der Bibliothek nicht existiert. Das Beispiel, mit dem KI-Systeme auf die Bibliothek eingewiesen werden, war damit selbst bibliothekswidrig. *(In diesem Commit behoben.)*

8. **Strukturlücke `implementation_plan_v1`:** Das einzige Template ohne `AUFGABENTYP` in `slots_used`. Der Template-Text begann mit „Bitte arbeite so, dass das Ergebnis beim [ZIEL_TYP] hilft…" — ohne zu spezifizieren, was getan werden soll. Alle anderen Templates folgen dem Muster „Bitte [AUFGABENTYP], damit…". *(In diesem Commit behoben.)*

9. **Goldstandard-Beispiele: Vollspezifikation statt repräsentativer Referenz:** Alle 7 `example_instances` belegen exakt 25/25 Slots. Reale Prompts brauchen 3–12 Slots. Die Beispiele zeigen die maximale Befüllung — nicht, welche Slots für welchen Use Case tatsächlich ausreichen. Eine Minimalkonfiguration ist aus den Beispielen nicht ableitbar.

10. **Semantische Redundanz `WISSENSKONTEXT` / `WISSENSSTAND_ADRESSAT`:** Identische Wertemengen (`anfaenger / fortgeschritten / experte`) in zwei unterschiedlichen Dimensionen (KONTEXT vs. ADRESSAT). Keine Constraint-Regel greift bei gegensätzlicher Belegung ein (z.B. WISSENSKONTEXT=experte, WISSENSSTAND_ADRESSAT=anfaenger). Ohne explizite Demarkationslinie ist systematische Fehlbelegung wahrscheinlich.

---

### Zielkonflikte (belastbar)

**Vollständigkeit vs. Geschwindigkeit**

Das System strebt nach taxonomischer Vollständigkeit (25 Slots, 8 Templates, 18 Constraints). Die Vision strebt nach operativer Schnelligkeit (Sekunden-Workflow, einfache Auswahl). Diese Ziele sind in Spannung, nicht in Harmonie.

**Generischer Core vs. praktische Verankerung**

Die Entfernung der Falktron-Case-Files schafft einen sauberen, generischen Core. Sie entfernt aber gleichzeitig den einzigen dokumentierten Beweis für reale Anwendung. Ein generischer Core ohne Praxisverifikation ist eine Abstraktion ohne Grounding.

**Kanonisierungsimpuls vs. Validierungslücke**

Das README ruft zur Härtung des Kerns auf. Härtung bedeutet: bestehende Strukturen konsolidieren. Das Problem: Konsolidiert wird ein System, dessen Wirksamkeit nicht gemessen wurde. Härtung ohne Validierung ist das Stabilisieren eines Fundaments, bevor geprüft wurde, ob es trägt.

---

### Annahmen unter Prüfvorbehalt

Die folgenden Punkte sind plausibel, aber nicht direkt aus dem Repository ableitbar — sie müssen vom Nutzer bewertet werden:

1. **Wird das System tatsächlich für Prompt-Erstellung im Alltag verwendet?** Es gibt keinen Nutzungsnachweis im Repository. Die Goldstandard-Beispiele zeigen, wie das System funktioniert, nicht dass es genutzt wird.

2. **Hat die Falktron-Case-Arbeit Grounding geliefert oder war sie ein Scheitern?** Der Entschluss zur Entfernung kann beides bedeuten: architektonische Reife oder Enttäuschung mit dem fallspezifischen Ansatz.

3. **Hat PocketFlow eine konkrete Roadmap?** Die Einbindung könnte eine geplante automatische Prompt-Assembly-Pipeline signalisieren — oder ein Experiment, das nie weitergeführt wurde.

---

## Interpretation

### Was strategisch besonders relevant ist

Der entscheidende Befund ist nicht die technische Qualität des Systems — die ist gegeben. Der entscheidende Befund ist die **Schere zwischen Designvision und Ist-Zustand**: Das System hat sich vom klaren, schlanken Werkzeug zu einem komplexen Taxonomie-Framework entwickelt, ohne dass dieser Schritt explizit entschieden oder validiert wurde. Es ist nicht falsch, komplex zu sein. Es ist falsch, komplex zu werden, ohne zu wissen ob die Komplexität Nutzen bringt.

### Muster und Spannungen

**Komplexitäts-Drift ohne Entscheidungspunkt**

Die Dimension-Erweiterung von 6 auf 10, die Einführung von Multi-Value-Slots entgegen dem Prinzip „ein Slot = ein Wert", die wachsende Constraint-Liste — all das ist iterativ entstanden, nicht strategisch beschlossen. Das ist typisch für Solo-Projekte ohne externen Gegendruck: Jede Ergänzung löst ein lokales Problem (dieser Use-Case braucht ROLLE, jener ADRESSAT) ohne den Gesamtrahmen zu prüfen.

**Strukturelle Integrität als Scheinsicherheit**

Der Integritätscheck besteht. Das JSON-Schema ist valide. Die Pre-commit-Hooks laufen. Das vermittelt ein Gefühl von Kontrolle. Diese Kontrolle ist real — aber sie ist strukturell, nicht semantisch. Sie sagt, dass die Bibliothek formal korrekt ist. Sie sagt nichts darüber, ob sie für den beschriebenen Zweck taugt.

**Das Falktron-Experiment als Schlüssel**

Die Entscheidung, case-spezifische Dateien zu entfernen und auf generischen Core umzusteigen, ist die wichtigste strategische Entscheidung im Repo — und sie ist undokumentiert. Was hat die Falktron-Case-Arbeit gezeigt? War der fallspezifische Ansatz zu starr? Hat er gut funktioniert und wurde trotzdem als „nicht Core" aussortiert? War er das Validierungsexperiment, das den Kernel tatsächlich getestet hat? Die Antwort auf diese Fragen bestimmt, ob der generische Core ein Schritt vorwärts oder rückwärts ist.

**Die Confidence-Scores als kognitiver Fallstrick**

Ein `confidence: 0.74` auf dem FUNKTIONSROLLE-Slot suggeriert eine quantifizierte Unsicherheit. Das ist epistemisch irreführend: Die Zahl ist keine Messung, sondern eine Schätzung des Autors über die eigene Einschätzung. In der Praxis kann das dazu führen, dass Tier-A-Slots als verlässlicher behandelt werden als es die Datenlage erlaubt. Das ist kein technisches Problem — es ist ein Denkrahmen-Problem.

**PocketFlow: Spur einer ungenutzten Vision**

100 Zeilen eines Async-Flow-Frameworks, im Dateinamen beschädigt, ohne Integration, ohne Dokumentation. Das ist kein Zufall. Das ist eine konkrete technische Richtungsentscheidung, die nie abgeschlossen wurde. Wenn PocketFlow Teil der Zukunft dieses Systems ist (automatisches Prompt-Assembly als Agent), dann fehlt dieser Architekturpfad vollständig in der Dokumentation. Wenn er es nicht ist, gehört der Code nicht ins Repository.

---

## Empfehlung

### Priorisierung

**P0 — Vor allem anderen: Grundentscheidung dokumentieren**

Die wichtigste Maßnahme hat keine Zeile Code. Sie lautet: **Scope-Entscheidung schriftlich festhalten.** Drei Fragen, die schriftlich beantwortet sein müssen, bevor weitere Entwicklung sinnvoll ist:

1. Ist dieses System ein persönliches Produktivitätswerkzeug, das genau für eine Person optimal sein soll — oder soll es von anderen genutzt, geteilt oder als Standard verstanden werden?
2. Ist die Vision (6 Bausteine, ein Wert pro Slot, GitHub Pages) noch der Zielzustand — oder wurde sie durch die Entwicklung der letzten Woche absichtlich erweitert?
3. Was sind die 3–5 Use Cases, für die das System täglich genutzt wird oder werden soll?

Ohne diese Entscheidungen arbeitet das System an sich selbst, nicht für einen Nutzer.

**P1 — Empirische Grundlage schaffen**

Fünf echte Prompts mit dem System bauen — nicht als Demonstration, sondern als strukturiertes Experiment: Prompt konfigurieren → KI-Output dokumentieren → Output qualitativ bewerten → mit einem direkt formulierten Prompt vergleichen. Wenn das System keinen messbaren Unterschied macht, ist das eine strategisch wichtige Information. Wenn es einen macht, ist das die Grundlage für die Kanonisierung.

**P2 — Soll-Ist-Divergenz aktiv auflösen**

Die Abweichungen zwischen Vision und Ist-Zustand müssen explizit entschieden werden — nicht implizit fortbestehen:

- Multi-Value-Slots entweder aus dem Design-Prinzip ausklammern (Prinzip anpassen) oder in Single-Value-Slots überführen (Slots aufteilen oder zusammenführen). Beides ist vertretbar — aber nicht beides gleichzeitig.
- GitHub Pages Deployment entscheiden: entweder umsetzen (GitHub Actions + Pages = 1–2 Stunden Aufwand) oder aus der Vision streichen.
- Die 4 zusätzlichen Dimensionen (ROLLE, GRENZEN, ADRESSAT, INTERAKTIONSMODUS) daraufhin prüfen, ob sie im tatsächlichen Nutzungsworkflow Mehrwert liefern oder die Einstiegshürde erhöhen.

**P3 — Technische Schulden bereinigen**

Diese Maßnahmen sind einfach, je 5–30 Minuten:

- `pocketflow/__init_.py` → umbenennen in `__init__.py` und Roadmap-Satz ins README, oder Verzeichnis löschen
- Lizenz definieren: MIT für Open-Source-Intent, proprietär für rein persönlichen Einsatz
- Node.js-Abhängigkeit eliminieren: `ajv-cli` durch `pip install jsonschema` und Python-Validation ersetzen

**P4 — Evidence-Metadata ehrlich machen**

`evidence_strength: stark` und `confidence: 0.92` sind interne Einschätzungen ohne externe Grundlage. Zwei Optionen:
- Felder löschen, da sie keine echten Informationen tragen
- Oder: Quellen-URLs ergänzen, damit die Behauptung prüfbar wird

Der aktuelle Zustand (Scores ohne Basis) ist schlechter als keine Scores.

---

## Nächste Schritte

Die folgenden Schritte sind priorisiert, voneinander abgegrenzt und direkt umsetzbar.

---

### Schritt 1 — Scope-Dokument anlegen (30 Minuten)

Datei: `ENTSCHEIDUNGEN.md` im Repository-Stamm  
Inhalt: Beantwortung der drei P0-Fragen (Zielgruppe, Soll-Vision, Use Cases)  
Kriterium: Erledigt wenn die drei Fragen schriftlich beantwortet sind — unabhängig davon wie die Antwort lautet

---

### Schritt 2 — Multi-Value-Slots auflösen (1–2 Stunden)

Betroffene Slots: `STILREGELN`, `INHALTLICHE_AUSSCHLUESSE`, `FORMALE_AUSSCHLUESSE`  
Entscheidung treffen: Werden sie zu mehreren Single-Value-Slots aufgeteilt, oder wird das Design-Prinzip um Multi-Value-Slots erweitert?  
Umsetzung je nach Entscheidung in `data/library.json` — Schema und Integrity-Check passen sich automatisch durch Pre-commit-Hooks an  
Kriterium: Alle Slots sind Single-Value oder die Designregel ist explizit angepasst

---

### Schritt 3 — GitHub Pages aktivieren (1–2 Stunden)

Voraussetzung: `ENTSCHEIDUNGEN.md` bestätigt GitHub Pages als gewolltes Deployment-Ziel  
Umsetzung: GitHub Actions Workflow in `.github/workflows/pages.yml`, der bei Push auf `main` die `ui/`-Datei publiziert  
Kein Backend, kein Build-Schritt nötig — die UI ist bereits statisches HTML  
Kriterium: UI ist unter `https://sborm.github.io/Wissensbibliothek-Promptbausteine/ui/` erreichbar und lädt `library.json` korrekt

---

### Schritt 4 — Empirischen Vergleich durchführen (2–3 Stunden)

3 verschiedene Aufgabentypen wählen (z.B. analysieren, entscheiden, umformulieren)  
Für jeden Aufgabentyp: (a) Prompt mit dem System konfigurieren und rendern, (b) Prompt direkt und spontan formulieren  
Beide Prompts an dieselbe KI senden, Outputs dokumentieren  
Qualitative Einschätzung: Ist die System-Variante deutlich besser, gleichwertig, oder schlechter?  
Ergebnis in `VALIDIERUNG.md` festhalten  
Kriterium: 3 dokumentierte Vergleiche mit qualitativem Urteil

---

### Schritt 5 — PocketFlow entscheiden (15 Minuten)

Entweder:  
(a) `pocketflow/` löschen, wenn keine konkrete Roadmap existiert  
(b) `pocketflow/__init_.py` → `__init__.py` umbenennen + Roadmap-Abschnitt im README ergänzen: was soll hier entstehen?  
Kriterium: Das Verzeichnis ist entweder sauber nutzbar oder nicht mehr vorhanden

---

### Schritt 6 — Node.js-Abhängigkeit eliminieren (30–60 Minuten)

`pip install jsonschema` in einen `requirements.txt` eintragen  
Python-Validierungsskript schreiben (10–15 Zeilen) oder `validate_integrity.py` erweitern  
`ajv`-Hook in `.pre-commit-config.yaml` ersetzen  
Node.js und ajv-cli aus README-Voraussetzungen entfernen  
Kriterium: Schema-Validation läuft ohne Node.js

---

### Schritt 7 — Wert-Benennung bereinigen (1 Stunde)

Alle Werte prüfen, die länger als 25 Zeichen sind  
Kandidaten für Umbenennung: `erst_befunde_dann_interpretation_dann_empfehlung` → `befunde_dann_empfehlung` o.ä.  
Beispielinstanzen und Templates entsprechend aktualisieren (Pre-commit-Hooks validieren Konsistenz)  
Kriterium: Kein Wert-Key ist länger als 30 Zeichen

---

## Offene Prüfbedarfe

Diese Punkte können nicht aus dem Repository heraus beantwortet werden und erfordern Selbstauskunft:

1. **Nutzungsnachweis:** Wird das System täglich für echte Prompts verwendet — oder ist es primär ein strukturelles Bauprojekt?
2. **Falktron-Ergebnis:** Was hat die Falktron-Case-Arbeit inhaltlich ergeben? War sie der geplante Praxistest oder eine Sackgasse?
3. **PocketFlow-Roadmap:** Existiert ein konkretes Szenario, in dem PocketFlow zum Einsatz kommen soll?
4. **Vision-Update:** Ist die 6-Baustein-Vision nach wie vor der Zielzustand, oder wurde sie durch die Entwicklung der letzten Tage bewusst erweitert?

---

*Analyse erstellt auf Basis des Repository-Zustands vom 9. April 2026, Branch `claude/analyze-prompt-library-CNMPI`.*
