"""Integrationstests: Upgrade-Skripte + Check gegen die Mini-Datenbank.

Das ist der Nachweis aus der Projekt-Zielsetzung:
  1. Bei einer fehlerfreien Migration meldet der Check NICHTS (keine falschen Alarme).
  2. Bei der Migration mit eingebauten Fehlern findet er ALLE (F01–F09).
"""

import pytest

from migrations_check.bericht import gesamtstatus
from migrations_check.ergebnis import FEHLER, OK


def details_von(ergebnisse, pruefung: str, objekt: str) -> list[str]:
    treffer = [e for e in ergebnisse if e.pruefung == pruefung and e.objekt == objekt]
    assert treffer, f"Prüfung '{pruefung}' auf '{objekt}' wurde nicht ausgeführt"
    return [d for e in treffer for d in e.details]


def test_saubere_migration_ohne_falschen_alarm(ergebnis_sauber):
    abweichungen = [(e.pruefung, e.objekt, e.details) for e in ergebnis_sauber if e.status != OK]
    assert abweichungen == []
    assert gesamtstatus(ergebnis_sauber) == OK


def test_fehlerhafte_migration_wird_blockiert(ergebnis_nachher):
    assert gesamtstatus(ergebnis_nachher) == FEHLER


# Jeder eingebaute Fehler: (Nr, Prüfung, Objekt, Text, der in den Details stehen muss)
# Die IDs beziehen sich auf tests/testdaten/mini_vorher.sql.
ERWARTET = [
    ("F01", "Fehlende oder neue Datensätze", "partner", "fehlt nachher: id 4"),
    ("F01", "Fehlende oder neue Datensätze", "partner", "fehlt nachher: id 5"),
    ("F02", "Fehlende oder neue Datensätze", "produkt", "fehlt nachher: id 5"),
    ("F03", "Bestandsmenge", "bestand.menge", "vorher 50.00, nachher 45.00"),
    ("F04", "Preise", "produkt", "id 2 (Chair): einstandspreis vorher 20.5, nachher 21"),
    ("F04", "Preise", "produkt", "id 3 (Lamp): einstandspreis vorher 25.5, nachher 26"),
    ("F05", "Offene Rechnungen", "rechnung", "INV/1): total vorher 1150.55, nachher 1250.55"),
    ("F06", "Offene Rechnungen", "rechnung", "INV/2): vorher offen, nachher nicht mehr"),
    ("F07", "Verwaiste Verknüpfung", "auftragszeile.produkt_id → produkt", "produkt_id=999999"),
    ("F08", "Dubletten", "produkt.artikelnummer", "'FURN_1' kommt 2× vor: ids 1, 900001"),
    ("F09", "Pflichtfeld leer", "partner.name", "id 2: 'name' ist leer"),
]


@pytest.mark.parametrize("nr, pruefung, objekt, text", ERWARTET, ids=[e[0] for e in ERWARTET])
def test_eingebauter_fehler_wird_gefunden(ergebnis_nachher, nr, pruefung, objekt, text):
    details = details_von(ergebnis_nachher, pruefung, objekt)
    assert any(text in d for d in details), f"{nr} nicht gefunden. Details: {details}"
