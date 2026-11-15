# Migrations-Check – Bericht

- **Vorher:** `odoo_vorher`
- **Nachher:** `odoo_nachher`
- **Erstellt:** 15.11.2026 21:44

## 🔴 Gesamtergebnis: FEHLER

Fehler gefunden – Go-Live blockiert, bis die Abweichungen geklärt sind.

🟢 16 ok · 🟡 0 Warnungen · 🔴 11 Fehler

## Übersicht

| | Prüfung | Objekt | Ergebnis |
|---|---|---|---|
| 🔴 | Anzahl Datensätze | `partner` | vorher 43, nachher 41 (Differenz -2) |
| 🟢 | Anzahl Datensätze | `produkt` | vorher 43, nachher 43 (Differenz +0) |
| 🟢 | Anzahl Datensätze | `bestand` | vorher 19, nachher 19 (Differenz +0) |
| 🟢 | Anzahl Datensätze | `verkaufsauftrag` | vorher 24, nachher 24 (Differenz +0) |
| 🟢 | Anzahl Datensätze | `auftragszeile` | vorher 50, nachher 50 (Differenz +0) |
| 🟢 | Anzahl Datensätze | `bestellung` | vorher 11, nachher 11 (Differenz +0) |
| 🟢 | Anzahl Datensätze | `rechnung` | vorher 14, nachher 14 (Differenz +0) |
| 🔴 | Fehlende oder neue Datensätze | `partner` | 2 fehlen, 0 neu |
| 🔴 | Fehlende oder neue Datensätze | `produkt` | 1 fehlen, 1 neu |
| 🔴 | Pflichtfeld leer | `partner.name` | 1 Datensätze neu ohne Wert |
| 🟢 | Pflichtfeld leer | `produkt.name` | 0 Datensätze neu ohne Wert |
| 🔴 | Dubletten | `produkt.artikelnummer` | 1 neue Dubletten |
| 🔴 | Bestandsmenge | `bestand.menge` | 1 von 18 Gruppen weichen ab; Total vorher 1188.00, nachher 1183.00 |
| 🔴 | Bestandswert | `bestand.wert` | 2 von 18 Gruppen weichen ab; Total vorher 527720.50, nachher 523357.00 |
| 🔴 | Preise | `produkt` | alle 42 Datensätze × 2 Felder geprüft, 3 Abweichungen |
| 🔴 | Offene Rechnungen | `rechnung` | offen vorher 13, nachher 12; total vorher 250304.54, nachher 208654.54; offen vorher 250304.54, nachher 208554.54 |
| 🟢 | Offene Verkaufsaufträge | `verkaufsauftrag` | offen vorher 19, nachher 19; total vorher 27660.50, nachher 27660.50 |
| 🟢 | Offene Bestellungen | `bestellung` | offen vorher 4, nachher 4; total vorher 28406.50, nachher 28406.50 |
| 🔴 | Verwaiste Verknüpfung | `auftragszeile.produkt_id → produkt` | 1 neu verwaiste Verweise |
| 🟢 | Verwaiste Verknüpfung | `auftragszeile.auftrag_id → verkaufsauftrag` | 0 neu verwaiste Verweise |
| 🟢 | Verwaiste Verknüpfung | `bestand.produkt_id → produkt` | 0 neu verwaiste Verweise |
| 🟢 | Verwaiste Verknüpfung | `verkaufsauftrag.kunde_id → partner` | 0 neu verwaiste Verweise |
| 🟢 | Verwaiste Verknüpfung | `bestellung.lieferant_id → partner` | 0 neu verwaiste Verweise |
| 🟢 | Verwaiste Verknüpfung | `rechnung.partner_id → partner` | 0 neu verwaiste Verweise |
| 🟢 | Stichprobe | `partner` | Stichprobe 10 Datensätze × 8 Felder geprüft, 0 Abweichungen |
| 🔴 | Stichprobe | `produkt` | Stichprobe 10 Datensätze × 8 Felder geprüft, 2 Abweichungen |
| 🟢 | Stichprobe | `verkaufsauftrag` | Stichprobe 10 Datensätze × 5 Felder geprüft, 0 Abweichungen |

## Details zu den Abweichungen

### 🔴 Anzahl Datensätze – `partner`

**Ergebnis:** vorher 43, nachher 41 (Differenz -2)

**Warum relevant:** Ein Upgrade darf keine Datensätze verlieren oder erfinden. Eine abweichende Anzahl ist der schnellste Hinweis auf verlorene oder doppelte Daten. Gleiche Anzahl heisst aber nicht, dass alles stimmt – darum folgen weitere Prüfungen.

### 🔴 Fehlende oder neue Datensätze – `partner`

**Ergebnis:** 2 fehlen, 0 neu

**Warum relevant:** Fehlende Kunden, Lieferanten oder Kontakte bedeuten verlorene Ansprechpartner und Belege, die ins Leere laufen.

**Betroffene Datensätze:**

- fehlt nachher: id 17 (Willie Burke)
- fehlt nachher: id 18 (Ron Gibson)

### 🔴 Fehlende oder neue Datensätze – `produkt`

**Ergebnis:** 1 fehlen, 1 neu

**Warum relevant:** Ein fehlendes Produkt kann nicht mehr bestellt, verkauft oder abgerechnet werden. Ein unerwartet neues Produkt deutet auf eine Dublette hin.

**Betroffene Datensätze:**

- fehlt nachher: id 1 (Restaurant Expenses)
- neu nachher: id 900008 (Desk Combination)

### 🔴 Pflichtfeld leer – `partner.name`

**Ergebnis:** 1 Datensätze neu ohne Wert

**Warum relevant:** Ein Partner ohne Namen erscheint auf Rechnungen, Lieferscheinen und Mahnungen ohne Empfänger. Leerer Text zählt wie ein fehlender Wert.

**Betroffene Datensätze:**

- id 11: 'name' ist leer (vorher: 'Gemini Furniture')

### 🔴 Dubletten – `produkt.artikelnummer`

**Ergebnis:** 1 neue Dubletten

**Warum relevant:** Dieselbe Artikelnummer zweimal verteilt Bestand und Umsatz auf zwei Datensätze; Lager und Auswertungen stimmen nicht mehr. Typisch nach dem Zusammenlegen von Tabellen.

**Betroffene Datensätze:**

- 'FURN_7800' kommt 2× vor: ids 8, 900008

### 🔴 Bestandsmenge – `bestand.menge`

**Ergebnis:** 1 von 18 Gruppen weichen ab; Total vorher 1188.00, nachher 1183.00

**Warum relevant:** Weicht die Menge je Produkt und Lagerort ab, stimmt der Buchbestand nicht mehr mit dem physischen Bestand überein: Lieferungen werden falsch zugesagt, die nächste Inventur zeigt Differenzen.

**Betroffene Datensätze:**

- produkt_id=30, lagerort=WH/Stock: vorher 16.00, nachher 11.00 (Differenz -5.00)

### 🔴 Bestandswert – `bestand.wert`

**Ergebnis:** 2 von 18 Gruppen weichen ab; Total vorher 527720.50, nachher 523357.00

**Warum relevant:** Der Bestandswert (Menge × Einstandspreis) fliesst direkt in die Bilanz. Eine Abweichung verfälscht Lagerbewertung und Margen.

**Betroffene Datensätze:**

- produkt_id=21: vorher 3976.50, nachher 3993.00 (Differenz +16.50)
- produkt_id=30: vorher 14016.00, nachher 9636.00 (Differenz -4380.00)

### 🔴 Preise – `produkt`

**Ergebnis:** alle 42 Datensätze × 2 Felder geprüft, 3 Abweichungen

**Warum relevant:** Preise werden bei einem Upgrade oft umgewandelt (Datentyp, Währung, Einheit). Rundungsfehler betreffen dann nicht einen Artikel, sondern alle mit demselben Muster – darum werden hier alle Produkte geprüft, nicht nur eine Stichprobe.

**Betroffene Datensätze:**

- id 3 (Virtual Interior Design): einstandspreis vorher 20.5, nachher 21
- id 4 (Virtual Home Staging): einstandspreis vorher 25.5, nachher 26
- id 21 (Cabinet with Doors): einstandspreis vorher 120.5, nachher 121

### 🔴 Offene Rechnungen – `rechnung`

**Ergebnis:** offen vorher 13, nachher 12; total vorher 250304.54, nachher 208654.54; offen vorher 250304.54, nachher 208554.54

**Warum relevant:** Offene Rechnungen sind Forderungen und Verbindlichkeiten. Eine fälschlich als bezahlt markierte Rechnung fällt aus dem Mahnwesen – das Geld wird nie eingefordert. Eine falsche Summe führt zu falschen Mahnungen und Zahlungen.

**Betroffene Datensätze:**

- id 2 (INV/2026/00002): vorher offen, nachher nicht mehr (status=posted, zahlstatus=paid)
- id 1 (INV/2026/00001): total vorher 31750.00, nachher 31850.00 (Differenz +100.00)

### 🔴 Verwaiste Verknüpfung – `auftragszeile.produkt_id → produkt`

**Ergebnis:** 1 neu verwaiste Verweise

**Warum relevant:** Eine Auftragszeile ohne gültiges Produkt kann weder geliefert noch fakturiert werden. Entsteht typischerweise, wenn bei einem Massenimport Fremdschlüssel abgeschaltet waren.

**Betroffene Datensätze:**

- id 8: produkt_id=999999 existiert nicht in 'produkt'

### 🔴 Stichprobe – `produkt`

**Ergebnis:** Stichprobe 10 Datensätze × 8 Felder geprüft, 2 Abweichungen

**Warum relevant:** Zufällig gewählte Produkte über alle Felder, inklusive umgerechneter Einheiten (Gewicht in kg). Prüft, ob das Mapping die Upgrade-Änderungen richtig abbildet.

**Betroffene Datensätze:**

- id 3 (Virtual Interior Design): einstandspreis vorher 20.5, nachher 21
- id 21 (Cabinet with Doors): einstandspreis vorher 120.5, nachher 121
