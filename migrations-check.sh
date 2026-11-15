#!/usr/bin/env bash
# =====================================================================
# migrations-check.sh – Einstieg in den Migrations-Check
# =====================================================================
# Vergleicht zwei PostgreSQL-Datenbanken vor und nach einem ERP-Upgrade,
# schreibt einen Bericht (HTML + Markdown) und eine Logdatei.
#
# Exit-Codes (für Pipelines und Go-Live-Freigaben):
#   0  keine Fehler (höchstens Warnungen)
#   1  Fehler in den Daten gefunden – Go-Live blockieren
#   2  technisches Problem (Aufruf, Konfiguration, Datenbank nicht erreichbar)
# =====================================================================

set -euo pipefail

# --- Hilfe-Text --------------------------------------------------------
hilfe() {
    cat <<HILFE
Aufruf: ./migrations-check.sh [Optionen] <vorher> <nachher>

Vergleicht die Datenbank <vorher> mit <nachher> und meldet fachliche
Abweichungen: Stammdaten, Bestände, offene Belege, Integrität, Stichproben.

Argumente:
  <vorher>             Name der Datenbank vor dem Upgrade,  z.B. odoo_vorher
  <nachher>            Name der Datenbank nach dem Upgrade, z.B. odoo_nachher

Optionen:
  -o, --ausgabe DIR    Ordner für den Bericht (Standard: reports)
  -h, --help           diese Hilfe anzeigen

Zugangsdaten kommen aus .env (PGHOST, PGPORT, PGUSER, PGPASSWORD)
oder aus bereits gesetzten Umgebungsvariablen.

Exit-Codes:
  0  keine Fehler      1  Fehler gefunden (Go-Live blockieren)      2  technisches Problem

Beispiel:
  ./migrations-check.sh odoo_vorher odoo_nachher
HILFE
}

# --- Ins Projektverzeichnis wechseln (Skript liegt dort) ---------------
cd "$(dirname "$0")"

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') | $*"
}

abbruch() {
    log "FEHLER: $*"
    log "Abbruch mit Exit-Code 2${logdatei:+ – Log: $logdatei}"
    exit 2
}

# Unerwarteter Fehler irgendwo im Skript (set -e greift): Zeile melden
trap 'log "FEHLER: unerwarteter Abbruch in Zeile $LINENO"; exit 2' ERR

# --- Argumente auswerten ----------------------------------------------
logdatei=""
ausgabe="reports"
positionen=()

while [[ $# -gt 0 ]]; do
    case "$1" in
        -h|--help)
            hilfe
            exit 0
            ;;
        -o|--ausgabe)
            [[ $# -ge 2 ]] || abbruch "Option $1 braucht einen Ordner"
            ausgabe="$2"
            shift 2
            ;;
        -*)
            abbruch "Unbekannte Option: $1 (Hilfe: ./migrations-check.sh --help)"
            ;;
        *)
            positionen+=("$1")
            shift
            ;;
    esac
done

if [[ ${#positionen[@]} -ne 2 ]]; then
    hilfe
    abbruch "Es braucht genau zwei Datenbanknamen: <vorher> <nachher>"
fi
vorher="${positionen[0]}"
nachher="${positionen[1]}"

# --- Logdatei: ein Lauf = eine Datei mit Zeitstempel im Namen ----------
mkdir -p logs
logdatei="logs/migrations-check_$(date +%Y%m%d_%H%M%S).log"

# Ab hier geht jede Ausgabe (stdout und stderr) auf den Bildschirm
# UND zusätzlich in die Logdatei.
exec > >(tee -a "$logdatei") 2>&1

log "Migrations-Check gestartet: $vorher -> $nachher"

# --- Voraussetzungen prüfen -------------------------------------------
if [[ -f .env ]]; then
    set -a
    source .env
    set +a
    log "Zugangsdaten aus .env geladen"
fi

for variable in PGHOST PGUSER PGPASSWORD; do
    [[ -n "${!variable:-}" ]] || abbruch "Umgebungsvariable $variable fehlt (.env anlegen, Vorlage: .env.example)"
done

# Python aus der virtuellen Umgebung, falls vorhanden (lokal); sonst python3 (z.B. Pipeline)
if [[ -x .venv/bin/python ]]; then
    python=".venv/bin/python"
else
    python="$(command -v python3)" || abbruch "python3 nicht gefunden"
fi

"$python" -c "import psycopg, yaml" 2>/dev/null \
    || abbruch "Python-Pakete fehlen – installieren mit: pip install -r requirements.txt"

for datei in config/mapping.yaml config/pruefungen.yaml; do
    [[ -f "$datei" ]] || abbruch "Konfiguration fehlt: $datei"
done

log "Voraussetzungen ok (Python: $python, Datenbank-Server: ${PGHOST}:${PGPORT:-5432})"

# --- Check ausführen --------------------------------------------------
# Der Exit-Code von Python wird aufgefangen statt das Skript abzubrechen:
# Exit-Code 1 ("Fehler gefunden") ist ein gültiges Ergebnis, kein Absturz.
code=0
"$python" -m migrations_check "$vorher" "$nachher" --ausgabe "$ausgabe" || code=$?

case "$code" in
    0) log "Ergebnis: keine Fehler – Go-Live aus Datensicht freigegeben" ;;
    1) log "Ergebnis: FEHLER gefunden – Go-Live blockiert" ;;
    *) log "Ergebnis: technisches Problem (Exit-Code $code) – kein Bericht erstellt" ; code=2 ;;
esac

[[ "$code" -eq 2 ]] || log "Bericht: $ausgabe/bericht.html"
log "Log:     $logdatei"
exit "$code"
