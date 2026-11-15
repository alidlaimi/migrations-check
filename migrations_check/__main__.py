"""Einstiegspunkt: python -m migrations_check <vorher> <nachher>

Ablauf:
  1. Mapping und Prüfregeln lesen
  2. Beide Datenbanken in die fachliche Sicht laden und prüfen (check.py)
  3. Bericht schreiben (Markdown und HTML)
  4. Exit-Code setzen: 0 = ok/Warnungen, 1 = Fehler gefunden,
                       2 = technisches Problem (z.B. Datenbank nicht erreichbar)
"""

import argparse
import sys
from pathlib import Path

import psycopg
import yaml

from . import bericht, check, mapping
from .ergebnis import FEHLER

PROJEKT = Path(__file__).resolve().parent.parent


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="migrations_check",
        description="Vergleicht zwei PostgreSQL-Datenbanken vor und nach einem ERP-Upgrade.",
    )
    parser.add_argument("vorher", help="Name der Datenbank vor dem Upgrade")
    parser.add_argument("nachher", help="Name der Datenbank nach dem Upgrade")
    parser.add_argument("--mapping", type=Path, default=PROJEKT / "config/mapping.yaml")
    parser.add_argument("--pruefungen", type=Path, default=PROJEKT / "config/pruefungen.yaml")
    parser.add_argument("--ausgabe", type=Path, default=PROJEKT / "reports",
                        help="Ordner für bericht.md und bericht.html (Standard: reports/)")
    args = parser.parse_args()

    objekte = mapping.laden(args.mapping)
    with open(args.pruefungen, encoding="utf-8") as datei:
        regeln = yaml.safe_load(datei)["pruefungen"]

    try:
        ergebnisse = check.pruefen(args.vorher, args.nachher, objekte, regeln)
    except psycopg.Error as fehler:
        # Technisches Problem ist etwas anderes als "Fehler in den Daten gefunden":
        # darum eigener Exit-Code 2 statt 1.
        print(f"Datenbankfehler: {fehler}", file=sys.stderr)
        return 2

    args.ausgabe.mkdir(parents=True, exist_ok=True)
    (args.ausgabe / "bericht.md").write_text(
        bericht.markdown(ergebnisse, args.vorher, args.nachher), encoding="utf-8")
    (args.ausgabe / "bericht.html").write_text(
        bericht.html(ergebnisse, args.vorher, args.nachher), encoding="utf-8")

    status = bericht.gesamtstatus(ergebnisse)
    print(f"Gesamtergebnis: {status.upper()} – Bericht: {args.ausgabe / 'bericht.html'}")
    return 1 if status == FEHLER else 0


if __name__ == "__main__":
    sys.exit(main())
