"""Datenstruktur für das Ergebnis einer Prüfung."""

from dataclasses import dataclass, field

OK = "ok"
WARNUNG = "warnung"
FEHLER = "fehler"


@dataclass
class Ergebnis:
    pruefung: str          # z.B. "Anzahl Datensätze"
    objekt: str            # z.B. "partner"
    status: str            # OK, WARNUNG oder FEHLER
    zusammenfassung: str   # ein Satz für die Übersicht
    erklaerung: str        # warum das fachlich relevant ist
    details: list[str] = field(default_factory=list)  # betroffene Datensätze
