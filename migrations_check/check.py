"""Der eigentliche Ablauf ohne Kommandozeile – wird von __main__.py und den Tests genutzt."""

from . import db, mapping
from .ergebnis import Ergebnis
from .pruefungen import PRUEFUNGEN


def benoetigte_objekte(regeln: list[dict]) -> set:
    """Welche Objekte brauchen die Prüfungen? Nur diese werden geladen."""
    objekte = set()
    for regel in regeln:
        objekte.update(regel.get("objekte", []))
        for schluessel in ("objekt", "ziel"):
            if schluessel in regel:
                objekte.add(regel[schluessel])
    return objekte


def daten_laden(datenbank: str, seite: str, objekte: dict, benoetigt: set) -> dict:
    """Lädt alle benötigten Objekte einer Datenbank: {objekt: {schluessel: zeile}}."""
    daten = {}
    with db.verbinden(datenbank) as verbindung:
        for name in sorted(benoetigt):
            zeilen = db.abfragen(verbindung, mapping.sql_fuer(objekte[name], seite))
            daten[name] = {z.pop("_schluessel"): z for z in zeilen}
    return daten


def pruefen(vorher: str, nachher: str, objekte: dict, regeln: list[dict]) -> list[Ergebnis]:
    """Lädt beide Datenbanken und führt alle Prüfungen aus."""
    benoetigt = benoetigte_objekte(regeln)
    daten = {
        "vorher": daten_laden(vorher, "vorher", objekte, benoetigt),
        "nachher": daten_laden(nachher, "nachher", objekte, benoetigt),
    }
    ergebnisse = []
    for regel in regeln:
        ergebnisse += PRUEFUNGEN[regel["typ"]](regel, daten)
    return ergebnisse
