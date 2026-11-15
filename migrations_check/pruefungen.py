"""Die einzelnen Prüfungen.

Jede Prüfung bekommt
  - ihre Einstellungen aus config/pruefungen.yaml (regel)
  - die Daten beider Seiten in fachlicher Sicht:
      daten["vorher"]["partner"] = {schluessel: {"name": ..., "email": ...}, ...}
und gibt eine Liste von Ergebnissen zurück.
"""

import random
from collections import defaultdict
from decimal import Decimal

from .ergebnis import OK, Ergebnis


def ist_leer(wert) -> bool:
    """Leer heisst: NULL oder nur Leerzeichen. '' und NULL gelten gleich (siehe F09)."""
    return wert is None or (isinstance(wert, str) and wert.strip() == "")


def ist_zahl(wert) -> bool:
    return isinstance(wert, (int, float, Decimal)) and not isinstance(wert, bool)


def gleich(a, b, toleranz: Decimal) -> bool:
    """Vergleicht zwei Werte. Zahlen dürfen um die Toleranz abweichen.

    Decimal statt float: Geldbeträge exakt rechnen, ohne Rundungsfehler
    wie 0.1 + 0.2 = 0.30000000000000004.
    """
    if ist_zahl(a) and ist_zahl(b):
        return abs(Decimal(str(a)) - Decimal(str(b))) <= toleranz
    return a == b


def als_text(wert) -> str:
    """Wert für den Bericht: Zahlen ohne Decimal('...'), Texte in Anführungszeichen."""
    return str(wert) if ist_zahl(wert) else repr(wert)


def toleranz_von(regel: dict) -> Decimal:
    return Decimal(str(regel.get("toleranz", 0)))


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


# ---------------------------------------------------------------------------
# Summe: Werte gruppiert vergleichen, z.B. Bestandsmenge je Produkt und Lagerort
# ---------------------------------------------------------------------------
def summen_je_gruppe(zeilen: dict, gruppe: list, feld: str) -> dict:
    summen = defaultdict(Decimal)
    for zeile in zeilen.values():
        schluessel = tuple(zeile[g] for g in gruppe)
        summen[schluessel] += Decimal(str(zeile[feld] or 0))
    return summen


def summe(regel: dict, daten: dict) -> list[Ergebnis]:
    objekt, gruppe, feld = regel["objekt"], regel["gruppe"], regel["feld"]
    toleranz = toleranz_von(regel)
    vorher = summen_je_gruppe(daten["vorher"][objekt], gruppe, feld)
    nachher = summen_je_gruppe(daten["nachher"][objekt], gruppe, feld)

    details = []
    for schluessel in sorted(vorher.keys() | nachher.keys(), key=str):
        alt, neu = vorher.get(schluessel, Decimal(0)), nachher.get(schluessel, Decimal(0))
        if abs(neu - alt) > toleranz:
            gruppe_text = ", ".join(f"{g}={w}" for g, w in zip(gruppe, schluessel))
            details.append(f"{gruppe_text}: vorher {alt:.2f}, nachher {neu:.2f} (Differenz {neu - alt:+.2f})")

    total_alt, total_neu = sum(vorher.values(), Decimal(0)), sum(nachher.values(), Decimal(0))
    return [Ergebnis(
        pruefung=regel["titel"],
        objekt=f"{objekt}.{feld}",
        status=regel["schweregrad"] if details else OK,
        zusammenfassung=(f"{len(details)} von {len(vorher.keys() | nachher.keys())} Gruppen weichen ab; "
                         f"Total vorher {total_alt:.2f}, nachher {total_neu:.2f}"),
        erklaerung=regel["erklaerung"],
        details=details,
    )]


# ---------------------------------------------------------------------------
# Offene Belege: welche Belege sind offen, und stimmen ihre Beträge?
# ---------------------------------------------------------------------------
def offene_belege(regel: dict, daten: dict) -> list[Ergebnis]:
    objekt, anzeige = regel["objekt"], regel.get("anzeige")
    bedingung = regel["offen_wenn"]           # z.B. {status: [posted], zahlstatus: [not_paid, partial]}
    betraege = regel.get("betraege", [])
    toleranz = toleranz_von(regel)

    def ist_offen(zeile: dict) -> bool:
        return all(zeile[feld] in werte for feld, werte in bedingung.items())

    alle_vorher, alle_nachher = daten["vorher"][objekt], daten["nachher"][objekt]
    vorher = {s: z for s, z in alle_vorher.items() if ist_offen(z)}
    nachher = {s: z for s, z in alle_nachher.items() if ist_offen(z)}

    def zustand(zeile: dict | None) -> str:
        if zeile is None:
            return "fehlt"
        return ", ".join(f"{feld}={zeile[feld]}" for feld in bedingung)

    details = []
    for s in sorted(vorher.keys() - nachher.keys()):
        details.append(f"{bezeichnung(vorher[s], anzeige, s)}: vorher offen, nachher nicht mehr "
                       f"({zustand(alle_nachher.get(s))})")
    for s in sorted(nachher.keys() - vorher.keys()):
        details.append(f"{bezeichnung(nachher[s], anzeige, s)}: nachher neu offen "
                       f"(vorher {zustand(alle_vorher.get(s))})")
    for s in sorted(vorher.keys() & nachher.keys()):
        for feld in betraege:
            alt, neu = vorher[s][feld], nachher[s][feld]
            if not gleich(alt, neu, toleranz):
                details.append(f"{bezeichnung(nachher[s], anzeige, s)}: {feld} vorher {alt:.2f}, "
                               f"nachher {neu:.2f} (Differenz {Decimal(str(neu)) - Decimal(str(alt)):+.2f})")

    def summe_von(zeilen: dict, feld: str) -> Decimal:
        return sum((Decimal(str(z[feld] or 0)) for z in zeilen.values()), Decimal(0))

    summen = "; ".join(f"{feld} vorher {summe_von(vorher, feld):.2f}, nachher {summe_von(nachher, feld):.2f}"
                       for feld in betraege)
    return [Ergebnis(
        pruefung=regel["titel"],
        objekt=objekt,
        status=regel["schweregrad"] if details else OK,
        zusammenfassung=f"offen vorher {len(vorher)}, nachher {len(nachher)}" + (f"; {summen}" if summen else ""),
        erklaerung=regel["erklaerung"],
        details=details,
    )]


# ---------------------------------------------------------------------------
# Referenzielle Integrität: zeigt ein Verweis auf einen existierenden Datensatz?
# ---------------------------------------------------------------------------
def verwaiste(zeilen: dict, feld: str, ziel: dict) -> dict:
    return {s: z[feld] for s, z in zeilen.items() if z[feld] is not None and z[feld] not in ziel}


def referenz(regel: dict, daten: dict) -> list[Ergebnis]:
    objekt, feld, ziel = regel["objekt"], regel["feld"], regel["ziel"]
    vorher = verwaiste(daten["vorher"][objekt], feld, daten["vorher"][ziel])
    nachher = verwaiste(daten["nachher"][objekt], feld, daten["nachher"][ziel])

    # Nur Verweise melden, die durch die Migration kaputtgegangen sind
    details = [f"id {s}: {feld}={wert} existiert nicht in '{ziel}'"
               for s, wert in sorted(nachher.items()) if s not in vorher]

    return [Ergebnis(
        pruefung=regel["titel"],
        objekt=f"{objekt}.{feld} → {ziel}",
        status=regel["schweregrad"] if details else OK,
        zusammenfassung=f"{len(details)} neu verwaiste Verweise",
        erklaerung=regel["erklaerung"],
        details=details,
    )]


# ---------------------------------------------------------------------------
# Feldvergleich: Datensatz für Datensatz, Feld für Feld
#   - ohne 'stichprobe': alle Datensätze (z.B. Preise lückenlos prüfen)
#   - mit 'stichprobe: n': n zufällige Datensätze (Stichprobe über alle Felder)
# ---------------------------------------------------------------------------
def feldvergleich(regel: dict, daten: dict) -> list[Ergebnis]:
    objekt, anzeige = regel["objekt"], regel.get("anzeige")
    vorher, nachher = daten["vorher"][objekt], daten["nachher"][objekt]
    toleranz = toleranz_von(regel)

    gemeinsam = sorted(vorher.keys() & nachher.keys())
    felder = regel.get("felder") or list(next(iter(vorher.values()), {}).keys())

    if "stichprobe" in regel:
        # Fester Startwert: jeder Lauf zieht dieselbe Stichprobe -> Bericht ist reproduzierbar
        zufall = random.Random(regel.get("startwert", 42))
        gemeinsam = sorted(zufall.sample(gemeinsam, min(regel["stichprobe"], len(gemeinsam))))

    details = []
    for s in gemeinsam:
        for feld in felder:
            alt, neu = vorher[s][feld], nachher[s][feld]
            if not gleich(alt, neu, toleranz):
                details.append(f"{bezeichnung(vorher[s], anzeige, s)}: {feld} vorher {als_text(alt)}, nachher {als_text(neu)}")

    art = f"Stichprobe {len(gemeinsam)}" if "stichprobe" in regel else f"alle {len(gemeinsam)}"
    return [Ergebnis(
        pruefung=regel["titel"],
        objekt=objekt,
        status=regel["schweregrad"] if details else OK,
        zusammenfassung=f"{art} Datensätze × {len(felder)} Felder geprüft, {len(details)} Abweichungen",
        erklaerung=regel["erklaerung"],
        details=details,
    )]


# Welche Funktion zu welchem "typ" in pruefungen.yaml gehört
PRUEFUNGEN = {
    "anzahl": anzahl,
    "vollstaendigkeit": vollstaendigkeit,
    "pflichtfeld": pflichtfeld,
    "dubletten": dubletten,
    "summe": summe,
    "offene_belege": offene_belege,
    "referenz": referenz,
    "feldvergleich": feldvergleich,
}
