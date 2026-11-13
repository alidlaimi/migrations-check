# CLAUDE.md – Arbeitsregeln für das Projekt «Migrations-Check»

## Zweck
Portfolio-Projekt für Vorstellungsgespräche (Bewerbung SIA, «ERP Systems Specialist»).
Ein Werkzeug vergleicht zwei PostgreSQL-Datenbanken – «vorher» und «nachher» – und findet
fachlich relevante Abweichungen nach einem ERP-Upgrade (Stammdaten, Bestände, offene Belege,
referenzielle Integrität, Stichproben), nicht nur Zeilenzahlen.
Testobjekt: Odoo-Datenbank mit **nachgebildetem** Upgrade (eigenes Migrationsskript mit
dokumentierten, absichtlich eingebauten Fehlern). So wird es auch in README und Bewerbung genannt.

## Arbeitsweise
- Schritt für Schritt bis zu einem vorführbaren Stand; jeder Meilenstein endet lauffähig.
- Bei jedem Schritt kurz das **Warum** erklären: Ali muss jede Komponente im Gespräch in
  eigenen Worten erklären können. Keine Komponente einbauen, die nicht erklärt wurde.
- Linux und Bash lernt Ali in diesem Projekt: Befehle nicht nur liefern, sondern kurz erklären
  (was macht der Befehl, was bedeuten die Optionen).
- Lieber einfach und erklärbar als clever. Keine unnötigen Abhängigkeiten.
- Zeitbudget gesamt: 10–15 Stunden. Umfang daran ausrichten.

## Sprache
- Deutsch mit Schweizer Rechtschreibung: immer «ss», nie «ß».
- Gilt für Erklärungen, Kommentare, README, Berichte und Commit-Vorschläge.

## Git
- Commits macht Ali selbst. Claude schlägt nur Commit-Nachrichten vor (kurz, Deutsch,
  Imperativ, z.B. «Repository-Struktur und README-Gerüst anlegen»).
- Nie Zugangsdaten committen: Passwörter und Verbindungsdaten nur in `.env`
  (steht in `.gitignore`), Vorlage als `.env.example`.

## Umgebung
- Windows mit VS Code, gearbeitet wird in **WSL2 (Ubuntu)** – Befehle sind Linux-Befehle.
- Docker für Odoo und PostgreSQL.
- Stack: Python, PostgreSQL, Bash, YAML (Konfiguration/Mapping), pytest, GitHub Actions.
- Zeilenenden: LF (über `.gitattributes`), sonst laufen Bash-Skripte unter Linux nicht.

## Meilensteine
1. WSL2 und Docker eingerichtet, Repository-Struktur, CLAUDE.md, README-Gerüst
2. Odoo mit Demodaten → Abzug als «vorher»-Datenbank
3. Migrationsskript mit Upgrade-Änderungen und eingebauten Fehlern → «nachher»-Datenbank, Mapping (YAML)
4. Erste Prüfungen (Stammdaten, Zeilenzahlen) + Markdown-Bericht
5. Bestände, offene Belege, Integrität, Stichproben; YAML-Konfiguration
6. HTML-Bericht, Exit-Codes, Bash-Einstieg (`./migrations-check.sh vorher nachher`) mit Logging
7. Tests (pytest) + GitHub Actions (Tests + Beispiel-Lauf, Bericht als Artefakt)
8. README fertig (Zweck, Architektur, Installation, Screenshot, Fehlerliste mit Fund-Status, Grenzen)

## Fachliche Regeln für die Prüfungen
- Jede Prüfung: Toleranz, Schweregrad (Fehler/Warnung) und verständliche Erklärung,
  warum die Abweichung für ein Go-Live relevant ist.
- Jeder eingebaute Fehler ist dokumentiert; Nachweis: alle gefunden, und bei einer
  fehlerfreien Migration keine falschen Alarme.
- Exit-Code ≠ 0 bei Fehlern.

## Ziel «fertig für das Gespräch»
- Öffentliches Repository, grüne Pipeline, Beispielbericht.
- 5-Minuten-Demo: Bash-Skript starten → Bericht öffnen → Abweichung erklären → warum sie ein Go-Live blockiert.
- Ali kann die wichtigsten Bash- und PostgreSQL-Befehle im Projekt selbst erklären.
