"""Liest config/mapping.yaml und baut daraus die SQL-Abfragen je Objekt.

Das Mapping übersetzt beide Datenbanken in dieselbe fachliche Sicht:
gleiche Objekte, gleiche Feldnamen, gleiche Einheiten.
"""

from pathlib import Path

import yaml


def laden(pfad: Path) -> dict:
    """Gibt die Objekte aus der Mapping-Datei zurück."""
    with open(pfad, encoding="utf-8") as datei:
        return yaml.safe_load(datei)["objekte"]


def sql_fuer(objekt: dict, seite: str) -> str:
    """Baut die SELECT-Abfrage für ein Objekt auf der Seite 'vorher' oder 'nachher'.

    Ergebnis z.B.:
      SELECT t.id AS _schluessel, (t.name) AS "name", ... FROM res_partner t WHERE ...
    """
    quelle = objekt[seite]
    spalten = ", ".join(
        f'({ausdruck[seite]}) AS "{feld}"' for feld, ausdruck in objekt["felder"].items()
    )
    sql = f"SELECT {objekt['schluessel']} AS _schluessel, {spalten} FROM {quelle['von']}"
    if quelle.get("filter"):
        sql += f" WHERE {quelle['filter']}"
    return sql
