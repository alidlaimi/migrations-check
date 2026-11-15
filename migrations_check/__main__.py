"""Einstiegspunkt: python -m migrations_check <vorher> <nachher>

Ablauf:
  1. Mapping und Prüfregeln lesen
  2. Beide Datenbanken in die fachliche Sicht laden
  3. Prüfungen ausführen
  4. Bericht schreiben
  5. Exit-Code setzen: 0 = ok/Warnungen, 1 = Fehler gefunden,
                       2 = technisches Problem (z.B. Datenbank nicht erreichbar)
"""

import argparse
import sys
from pathlib import Path

import psycopg
import yaml

from . import bericht, db, mapping
from .ergebnis import FEHLER
from .pruefungen import PRUEFUNGEN

PROJEKT = Path(__file__).resolve().parent.parent


def daten_laden(datenbank: str, seite: str, objekte: dict, benoetigt: set) -> dict:
    """Lädt alle benötigten Objekte einer Datenbank: {objekt: {schluessel: zeile}}."""
    daten = {}
    with db.verbinden(datenbank) as verbindung:
        for name in sorted(benoetigt):
            zeilen = db.abfragen(verbindung, mapping.sql_fuer(objekte[name], seite))
            daten[name] = {z.pop("_schluessel"): z for z in zeilen}
    return daten


def benoetigte_objekte(regeln: list[dict]) -> set:
    """Welche Objekte brauchen die Prüfungen? Nur diese werden geladen."""
    objekte = set()
    for regel in regeln:
        objekte.update(regel.get("objekte", []))
        for schluessel in ("objekt", "ziel"):
            if schluessel in regel:
                objekte.add(regel[schluessel])
    return objekte


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="migrations_check",
        description="Vergleicht zwei PostgreSQL-Datenbanken vor und nach einem ERP-Upgrade.",
    )
    parser.add_argument("vorher", help="Name der Datenbank vor dem Upgrade")
    parser.add_argument("nachher", help="Name der Datenbank nach dem Upgrade")
    parser.add_argument("--mapping", type=Path, default=PROJEKT / "config/mapping.yaml")
    parser.add_argument("--pruefungen", type=Path, default=PROJEKT / "config/pruefungen.yaml")
    parser.add_argument("--bericht", type=Path, default=PROJEKT / "reports/bericht.md",
                        help="Pfad für den Markdown-Bericht")
    args = parser.parse_args()

    objekte = mapping.laden(args.mapping)
    with open(args.pruefungen, encoding="utf-8") as datei:
        regeln = yaml.safe_load(datei)["pruefungen"]

    benoetigt = benoetigte_objekte(regeln)
    try:
        daten = {
            "vorher": daten_laden(args.vorher, "vorher", objekte, benoetigt),
            "nachher": daten_laden(args.nachher, "nachher", objekte, benoetigt),
        }
    except psycopg.Error as fehler:
        # Technisches Problem ist etwas anderes als "Fehler in den Daten gefunden":
        # darum eigener Exit-Code 2 statt 1.
        print(f"Datenbankfehler: {fehler}", file=sys.stderr)
        return 2

    ergebnisse = []
    for regel in regeln:
        ergebnisse += PRUEFUNGEN[regel["typ"]](regel, daten)

    args.bericht.parent.mkdir(parents=True, exist_ok=True)
    args.bericht.write_text(bericht.markdown(ergebnisse, args.vorher, args.nachher), encoding="utf-8")

    status = bericht.gesamtstatus(ergebnisse)
    print(f"Gesamtergebnis: {status.upper()} – Bericht: {args.bericht}")
    return 1 if status == FEHLER else 0


if __name__ == "__main__":
    sys.exit(main())
