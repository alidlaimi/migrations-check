# Nachgebildetes Upgrade und eingebaute Fehler

Grundlage: Odoo 18 mit Demodaten (Module Verkauf, Einkauf, Lager, Buchhaltung) als
Datenbank `odoo_vorher`. Daraus erzeugt `migration/nachher-erstellen.sh` zwei Varianten:

| Datenbank | Inhalt | Erwartung an den Check |
|---|---|---|
| `odoo_nachher` | Upgrade (`01_upgrade.sql`) + Fehler (`02_fehler.sql`) | findet alle Fehler F01–F09 |
| `odoo_nachher_sauber` | nur Upgrade (`01_upgrade.sql`) | meldet **keine** Abweichung |

## Upgrade-Änderungen (gewollt, kein Fehler)

| Nr | Art | Vorher | Nachher |
|---|---|---|---|
| U1 | Tabelle/Spalte umbenannt | `stock_quant.quantity` | `stock_level.qty_on_hand` |
| U2 | Tabellen zusammengelegt | `product_template` + `product_product` | `product` (ID der Variante bleibt) |
| U3 | Tabelle aufgeteilt | Adressfelder in `res_partner` | `partner_address`, `street2` → `address_line2` |
| U4 | Datentyp / Einheit | Einstandspreis `jsonb`, Gewicht in kg, Rechnungsbeträge in CHF | `cost_price numeric`, `weight_g` in Gramm, Beträge in Rappen (`bigint`) |
| U5 | Neues Pflichtfeld | – | `product.abc_class` NOT NULL, Standard `'C'` |

Der Check darf diese Änderungen **nicht** als Fehler melden. Dafür beschreibt
`config/mapping.yaml`, welche Tabelle und Spalte vorher welcher nachher entspricht.

## Eingebaute Fehler

Die betroffenen Datensätze stammen aus dem Protokoll von `02_fehler.sql`
(Lauf vom 15.11.2026 auf den Odoo-18-Demodaten).

| Nr | Fehler | Betroffen | Muss gefunden werden durch | Warum blockiert das ein Go-Live? |
|---|---|---|---|---|
| F01 | 2 Kontakte verloren | `res_partner` 17 (Willie Burke), 18 (Ron Gibson) | Stammdaten: Anzahl und fehlende Datensätze | Ansprechpartner fehlen; Korrespondenz und künftige Belege laufen ins Leere |
| F02 | 1 Produkt verloren | `product` 1 (Restaurant Expenses) | Stammdaten: Anzahl und fehlende Datensätze | Produkt kann nicht mehr bestellt, verkauft oder abgerechnet werden |
| F03 | Bestandsmenge verändert | `stock_level` 1 (Produkt 30): 16 → 11 | Bestände: Menge je Produkt und Lagerort | Buchbestand stimmt nicht mehr mit dem physischen Bestand überein |
| F04 | Einstandspreis auf ganze Franken gerundet | `product` 21 (120.50 → 121), 3 (20.50 → 21), 4 (25.50 → 26) | Bestände: Wert; Stichprobe | Lagerbewertung und Margen in der Buchhaltung falsch |
| F05 | Offene Rechnung mit falscher Summe | `INV/2026/00001`: 31'750.00 → 31'850.00 | Offene Belege: Summen | Debitorenstand falsch; Kunde erhält falsche Mahnung |
| F06 | Offene Rechnung fälschlich «bezahlt» | `INV/2026/00002`: `not_paid` → `paid` | Offene Belege: Anzahl und Status | Forderung verschwindet aus dem Mahnwesen – Geld wird nie eingefordert |
| F07 | Auftragszeile ohne gültiges Produkt | `sale_order_line` 8: Produkt 3 → 999999 | Referenzielle Integrität | Auftrag kann nicht geliefert oder fakturiert werden |
| F08 | Produkt-Dublette nach Zusammenlegen | `product` 900008 = Kopie von 8 (`FURN_7800`) | Stammdaten: Dubletten | Bestand und Umsatz verteilen sich auf zwei Datensätze |
| F09 | Kundenname leer | `res_partner` 11 (Gemini Furniture → leerer Text) | Stammdaten: Pflichtfelder | Belege ohne Kundennamen; leerer Text umgeht die CHECK-Regel von Odoo |

## Erkenntnisse beim Bau

- **CHECK-Regeln greifen auch bei deaktivierten Fremdschlüsseln.** Der erste Versuch, den
  Namen bei F09 auf `NULL` zu setzen, scheiterte an `res_partner_check_name`. Dank der
  Transaktion wurde dabei nichts halb geändert. Ein leerer Text `''` rutscht dagegen durch –
  so, wie es bei Importen aus Excel oder CSV passiert. Der Check behandelt deshalb `''` und
  `NULL` gleich.
- **Fehler dürfen sich nicht überdecken.** Die Dublette (F08) erhält die ID 900000 + Original,
  damit sie nicht die ID des gelöschten Produkts (F02) wiederverwendet und den Verlust tarnt.
