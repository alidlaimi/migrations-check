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


# ---------------------------------------------------------------------------
# HTML-Bericht: eine einzige Datei mit eingebettetem CSS, öffnet in jedem Browser
# ---------------------------------------------------------------------------
FARBE = {OK: "#1a7f37", WARNUNG: "#b7791f", FEHLER: "#c62828"}

CSS = """
body { font-family: system-ui, sans-serif; margin: 2rem auto; max-width: 1100px; color: #222; padding: 0 1rem; }
h1 { margin-bottom: .2rem; }
.meta { color: #666; margin-bottom: 1.5rem; }
.banner { color: #fff; padding: 1rem 1.5rem; border-radius: 8px; margin-bottom: 1.5rem; }
.banner h2 { margin: 0 0 .3rem 0; }
table { border-collapse: collapse; width: 100%; margin-bottom: 2rem; }
th, td { text-align: left; padding: .45rem .6rem; border-bottom: 1px solid #e5e5e5; vertical-align: top; }
th { background: #f6f6f6; }
code { background: #f2f2f2; padding: .1rem .3rem; border-radius: 4px; }
.punkt { display: inline-block; width: .8rem; height: .8rem; border-radius: 50%; }
details { border: 1px solid #e5e5e5; border-left-width: 6px; border-radius: 6px; padding: .6rem 1rem; margin-bottom: .8rem; }
summary { cursor: pointer; font-weight: 600; }
.warum { color: #444; margin: .6rem 0; }
ul { margin: .3rem 0 0 0; }
"""


def html(ergebnisse: list[Ergebnis], vorher: str, nachher: str) -> str:
    from html import escape  # wandelt <, >, & um, damit Daten das HTML nicht zerstören

    status = gesamtstatus(ergebnisse)
    anzahl = {s: sum(e.status == s for e in ergebnisse) for s in (OK, WARNUNG, FEHLER)}
    fazit = {
        OK: "Keine Abweichungen – aus Sicht der Daten bereit für das Go-Live.",
        WARNUNG: "Warnungen vorhanden – vor dem Go-Live fachlich beurteilen.",
        FEHLER: "Fehler gefunden – Go-Live blockiert, bis die Abweichungen geklärt sind.",
    }[status]

    def punkt(s: str) -> str:
        return f'<span class="punkt" style="background:{FARBE[s]}"></span>'

    zeilen = "\n".join(
        f"<tr><td>{punkt(e.status)}</td><td>{escape(e.pruefung)}</td>"
        f"<td><code>{escape(e.objekt)}</code></td><td>{escape(e.zusammenfassung)}</td></tr>"
        for e in ergebnisse
    )

    abschnitte = []
    for e in (e for e in ergebnisse if e.status != OK):
        liste = "".join(f"<li>{escape(d)}</li>" for d in e.details[:MAX_DETAILS])
        if len(e.details) > MAX_DETAILS:
            liste += f"<li>… und {len(e.details) - MAX_DETAILS} weitere</li>"
        abschnitte.append(
            f'<details open style="border-left-color:{FARBE[e.status]}">'
            f"<summary>{escape(e.pruefung)} – <code>{escape(e.objekt)}</code>: "
            f"{escape(e.zusammenfassung)}</summary>"
            f'<p class="warum"><strong>Warum relevant:</strong> {escape(e.erklaerung.strip())}</p>'
            + (f"<strong>Betroffene Datensätze:</strong><ul>{liste}</ul>" if liste else "")
            + "</details>"
        )
    details_html = "<h2>Details zu den Abweichungen</h2>\n" + "\n".join(abschnitte) if abschnitte else ""

    return f"""<!DOCTYPE html>
<html lang="de-CH">
<head>
<meta charset="utf-8">
<title>Migrations-Check – {escape(vorher)} → {escape(nachher)}</title>
<style>{CSS}</style>
</head>
<body>
<h1>Migrations-Check</h1>
<div class="meta">Vorher <code>{escape(vorher)}</code> → Nachher <code>{escape(nachher)}</code>
 · erstellt {datetime.now():%d.%m.%Y %H:%M}</div>

<div class="banner" style="background:{FARBE[status]}">
<h2>Gesamtergebnis: {status.upper()}</h2>
{escape(fazit)}<br>
{anzahl[OK]} ok · {anzahl[WARNUNG]} Warnungen · {anzahl[FEHLER]} Fehler
</div>

<h2>Übersicht</h2>
<table>
<tr><th></th><th>Prüfung</th><th>Objekt</th><th>Ergebnis</th></tr>
{zeilen}
</table>

{details_html}
</body>
</html>
"""
