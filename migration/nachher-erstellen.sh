#!/usr/bin/env bash
# =====================================================================
# nachher-erstellen.sh – erzeugt eine "nachher"-Datenbank
# =====================================================================
# Spielt den vorher-Abzug in eine neue Datenbank ein und wendet darauf
# das nachgebildete Upgrade an – mit oder ohne eingebaute Fehler.
#
# Aufruf (aus dem Projektordner):
#   ./migration/nachher-erstellen.sh            -> odoo_nachher        (Upgrade + Fehler F01–F09)
#   ./migration/nachher-erstellen.sh --sauber   -> odoo_nachher_sauber (nur Upgrade)
# =====================================================================

set -euo pipefail   # bei Fehler abbrechen (-e), leere Variablen sind Fehler (-u),
                    # Fehler in Pipes nicht verschlucken (-o pipefail)

# In den Projektordner wechseln – egal, von wo das Skript aufgerufen wird
cd "$(dirname "$0")/.."

# Zugangsdaten aus .env laden (set -a: alle Variablen automatisch exportieren)
if [[ ! -f .env ]]; then
    echo "Fehler: .env fehlt (Vorlage: .env.example)" >&2
    exit 1
fi
set -a
source .env
set +a

abzug="dumps/odoo_vorher.dump"
if [[ ! -f "$abzug" ]]; then
    echo "Fehler: $abzug fehlt – zuerst den vorher-Abzug erstellen" >&2
    exit 1
fi

# Argument auswerten
case "${1:-}" in
    "")
        ziel="$DB_NACHHER"
        mit_fehlern=true
        ;;
    --sauber)
        ziel="${DB_NACHHER}_sauber"
        mit_fehlern=false
        ;;
    *)
        echo "Aufruf: $0 [--sauber]" >&2
        exit 2
        ;;
esac

# Hilfsfunktion: SQL aus einer Datei in der Ziel-Datenbank ausführen
psql_ziel() {
    docker compose exec -T db psql -U "$PGUSER" -d "$ziel" -v ON_ERROR_STOP=1 -q
}

echo "1/4 Datenbank $ziel neu anlegen"
docker compose exec -T db dropdb   -U "$PGUSER" --if-exists "$ziel"
docker compose exec -T db createdb -U "$PGUSER" "$ziel"

echo "2/4 Abzug $abzug einspielen"
docker compose exec -T db pg_restore -U "$PGUSER" -d "$ziel" --no-owner < "$abzug"

echo "3/4 Upgrade anwenden (migration/01_upgrade.sql)"
psql_ziel < migration/01_upgrade.sql

if [[ "$mit_fehlern" == true ]]; then
    echo "4/4 Fehler einbauen (migration/02_fehler.sql)"
    psql_ziel < migration/02_fehler.sql
else
    echo "4/4 Keine Fehler – saubere Migration"
fi

echo "Fertig: $ziel"
