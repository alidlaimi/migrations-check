"""Die einzelnen Prüfungen.

Jede Prüfung bekommt
  - ihre Einstellungen aus config/pruefungen.yaml (regel)
  - die Daten beider Seiten in fachlicher Sicht:
      daten["vorher"]["partner"] = {schluessel: {"name": ..., "email": ...}, ...}
und gibt eine Liste von Ergebnissen zurück.
"""

from collections import defaultdict

from .ergebnis import OK, Ergebnis


def ist_leer(wert) -> bool:
    """Leer heisst: NULL oder nur Leerzeichen. '' und NULL gelten gleich (siehe F09)."""
    return wert is None or (isinstance(wert, str) and wert.strip() == "")


def bezeichnung(zeile: dict, feld: str | None, schluessel) -> str:
    """Lesbare Bezeichnung eines Datensatzes für den Bericht, z.B. 'id 17 (Willie Burke)'."""
    if feld and not ist_leer(zeile.get(feld)):
        return f"id {schluessel} ({zeile[feld]})"
    return f"id {schluessel}"


# ---------------------------------------------------------------------------
# Anzahl Datensätze je Objekt
# ---------------------------------------------------------------------------
def anzahl(regel: dict, daten: dict) -> list[Ergebnis]:
    ergebnisse = []
    for objekt in regel["objekte"]:
        vorher = len(daten["vorher"][objekt])
        nachher = len(daten["nachher"][objekt])
        differenz = nachher - vorher
        abweichung = abs(differenz) > regel.get("toleranz", 0)
        ergebnisse.append(Ergebnis(
            pruefung=regel["titel"],
            objekt=objekt,
            status=regel["schweregrad"] if abweichung else OK,
            zusammenfassung=f"vorher {vorher}, nachher {nachher} (Differenz {differenz:+d})",
            erklaerung=regel["erklaerung"],
        ))
    return ergebnisse


# ---------------------------------------------------------------------------
# Vollständigkeit: welche Datensätze fehlen nachher, welche sind neu?
# ---------------------------------------------------------------------------
def vollstaendigkeit(regel: dict, daten: dict) -> list[Ergebnis]:
    objekt = regel["objekt"]
    vorher = daten["vorher"][objekt]
    nachher = daten["nachher"][objekt]
    anzeige = regel.get("anzeige")

    fehlend = sorted(vorher.keys() - nachher.keys())
    neu = sorted(nachher.keys() - vorher.keys())

    details = [f"fehlt nachher: {bezeichnung(vorher[s], anzeige, s)}" for s in fehlend]
    details += [f"neu nachher: {bezeichnung(nachher[s], anzeige, s)}" for s in neu]

    return [Ergebnis(
        pruefung=regel["titel"],
        objekt=objekt,
        status=regel["schweregrad"] if details else OK,
        zusammenfassung=f"{len(fehlend)} fehlen, {len(neu)} neu",
        erklaerung=regel["erklaerung"],
        details=details,
    )]


# ---------------------------------------------------------------------------
# Pflichtfeld: Datensätze, deren Feld nachher leer ist, vorher aber nicht
# ---------------------------------------------------------------------------
def pflichtfeld(regel: dict, daten: dict) -> list[Ergebnis]:
    objekt, feld = regel["objekt"], regel["feld"]
    vorher = daten["vorher"][objekt]
    nachher = daten["nachher"][objekt]

    details = []
    for schluessel, zeile in sorted(nachher.items()):
        if ist_leer(zeile[feld]):
            alt = vorher.get(schluessel, {}).get(feld)
            if not ist_leer(alt):  # nur NEU leere Felder sind ein Migrationsfehler
                details.append(f"id {schluessel}: '{feld}' ist leer (vorher: {alt!r})")

    return [Ergebnis(
        pruefung=regel["titel"],
        objekt=f"{objekt}.{feld}",
        status=regel["schweregrad"] if details else OK,
        zusammenfassung=f"{len(details)} Datensätze neu ohne Wert",
        erklaerung=regel["erklaerung"],
        details=details,
    )]


# ---------------------------------------------------------------------------
# Dubletten: gleicher Wert in einem Feld, das eindeutig sein sollte
# ---------------------------------------------------------------------------
def gruppen_mit_dubletten(zeilen: dict, feld: str) -> dict:
    gruppen = defaultdict(list)
    for schluessel, zeile in zeilen.items():
        if not ist_leer(zeile[feld]):
            gruppen[zeile[feld]].append(schluessel)
    return {wert: sorted(ids) for wert, ids in gruppen.items() if len(ids) > 1}


def dubletten(regel: dict, daten: dict) -> list[Ergebnis]:
    objekt, feld = regel["objekt"], regel["feld"]
    vorher = gruppen_mit_dubletten(daten["vorher"][objekt], feld)
    nachher = gruppen_mit_dubletten(daten["nachher"][objekt], feld)

    # Nur Dubletten melden, die durch die Migration entstanden sind
    details = [
        f"'{wert}' kommt {len(ids)}× vor: ids {', '.join(map(str, ids))}"
        for wert, ids in sorted(nachher.items())
        if vorher.get(wert) != ids
    ]

    return [Ergebnis(
        pruefung=regel["titel"],
        objekt=f"{objekt}.{feld}",
        status=regel["schweregrad"] if details else OK,
        zusammenfassung=f"{len(details)} neue Dubletten",
        erklaerung=regel["erklaerung"],
        details=details,
    )]


# Welche Funktion zu welchem "typ" in pruefungen.yaml gehört
PRUEFUNGEN = {
    "anzahl": anzahl,
    "vollstaendigkeit": vollstaendigkeit,
    "pflichtfeld": pflichtfeld,
    "dubletten": dubletten,
}
