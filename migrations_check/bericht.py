"""Erstellt den Bericht als Markdown."""

from datetime import datetime

from .ergebnis import FEHLER, OK, WARNUNG, Ergebnis

SYMBOL = {OK: "🟢", WARNUNG: "🟡", FEHLER: "🔴"}
MAX_DETAILS = 25  # mehr Zeilen je Prüfung machen den Bericht unlesbar


def gesamtstatus(ergebnisse: list[Ergebnis]) -> str:
    """Der schlechteste Einzelstatus bestimmt den Gesamtstatus."""
    if any(e.status == FEHLER for e in ergebnisse):
        return FEHLER
    if any(e.status == WARNUNG for e in ergebnisse):
        return WARNUNG
    return OK


def markdown(ergebnisse: list[Ergebnis], vorher: str, nachher: str) -> str:
    status = gesamtstatus(ergebnisse)
    anzahl = {s: sum(e.status == s for e in ergebnisse) for s in (OK, WARNUNG, FEHLER)}
    fazit = {
        OK: "Keine Abweichungen – aus Sicht der Daten bereit für das Go-Live.",
        WARNUNG: "Warnungen vorhanden – vor dem Go-Live fachlich beurteilen.",
        FEHLER: "Fehler gefunden – Go-Live blockiert, bis die Abweichungen geklärt sind.",
    }[status]

    zeilen = [
        "# Migrations-Check – Bericht",
        "",
        f"- **Vorher:** `{vorher}`",
        f"- **Nachher:** `{nachher}`",
        f"- **Erstellt:** {datetime.now():%d.%m.%Y %H:%M}",
        "",
        f"## {SYMBOL[status]} Gesamtergebnis: {status.upper()}",
        "",
        fazit,
        "",
        f"{SYMBOL[OK]} {anzahl[OK]} ok · {SYMBOL[WARNUNG]} {anzahl[WARNUNG]} Warnungen · "
        f"{SYMBOL[FEHLER]} {anzahl[FEHLER]} Fehler",
        "",
        "## Übersicht",
        "",
        "| | Prüfung | Objekt | Ergebnis |",
        "|---|---|---|---|",
    ]
    for e in ergebnisse:
        zeilen.append(f"| {SYMBOL[e.status]} | {e.pruefung} | `{e.objekt}` | {e.zusammenfassung} |")

    abweichungen = [e for e in ergebnisse if e.status != OK]
    if abweichungen:
        zeilen += ["", "## Details zu den Abweichungen"]
        for e in abweichungen:
            zeilen += [
                "",
                f"### {SYMBOL[e.status]} {e.pruefung} – `{e.objekt}`",
                "",
                f"**Ergebnis:** {e.zusammenfassung}",
                "",
                f"**Warum relevant:** {e.erklaerung.strip()}",
            ]
            if e.details:
                zeilen += ["", "**Betroffene Datensätze:**", ""]
                zeilen += [f"- {d}" for d in e.details[:MAX_DETAILS]]
                if len(e.details) > MAX_DETAILS:
                    zeilen.append(f"- … und {len(e.details) - MAX_DETAILS} weitere")

    return "\n".join(zeilen) + "\n"
