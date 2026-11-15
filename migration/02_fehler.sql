-- =====================================================================
-- 02_fehler.sql – gezielt eingebaute Migrationsfehler
-- =====================================================================
-- Läuft NACH 01_upgrade.sql. Jeder Fehler hat eine Nummer (F01–F09) und
-- steht in docs/eingebaute-fehler.md mit dem, was der Check finden muss.
--
-- Die betroffenen Datensätze werden nach festen Regeln gewählt (ORDER BY id),
-- damit jeder Lauf dieselben Fehler erzeugt. Die Regeln stellen sicher,
-- dass sich die Fehler nicht gegenseitig überdecken.
--
-- Am Ende gibt das Skript ein Protokoll aus: welcher Fehler welchen
-- Datensatz getroffen hat. Dieses Protokoll liegt NICHT in der Datenbank –
-- der Check muss die Fehler selbst finden.
-- =====================================================================

BEGIN;

SET LOCAL client_min_messages = warning;  -- Hinweise (NOTICE) unterdrücken

-- Fremdschlüssel-Prüfungen für diese Transaktion abschalten – wie bei einem
-- Massenimport, der Constraints aus Geschwindigkeitsgründen deaktiviert.
-- Nur so können verwaiste Verknüpfungen überhaupt entstehen.
SET LOCAL session_replication_role = replica;

CREATE TEMP TABLE fehlerprotokoll (
    nr          text,
    fehler      text,
    betroffen   text
) ON COMMIT DROP;

-- ---------------------------------------------------------------------
-- F01  Zwei Kontakte verloren (Stammdaten)
--      Gewählt: Personen ohne Aufträge, Bestellungen, Rechnungen und
--      ohne Benutzerkonto – damit der Verlust keine weiteren Fehler auslöst.
-- ---------------------------------------------------------------------
CREATE TEMP TABLE f01 ON COMMIT DROP AS
SELECT p.id, p.name
FROM res_partner p
WHERE NOT p.is_company
  AND p.active
  AND NOT EXISTS (SELECT 1 FROM sale_order s
                  WHERE p.id IN (s.partner_id, s.partner_invoice_id, s.partner_shipping_id))
  AND NOT EXISTS (SELECT 1 FROM purchase_order o WHERE o.partner_id = p.id)
  AND NOT EXISTS (SELECT 1 FROM account_move m
                  WHERE p.id IN (m.partner_id, m.commercial_partner_id))
  AND NOT EXISTS (SELECT 1 FROM res_users u      WHERE u.partner_id = p.id)
  AND NOT EXISTS (SELECT 1 FROM res_company c    WHERE c.partner_id = p.id)
ORDER BY p.id
LIMIT 2;

DELETE FROM partner_address WHERE partner_id IN (SELECT id FROM f01);
DELETE FROM res_partner     WHERE id         IN (SELECT id FROM f01);

INSERT INTO fehlerprotokoll
SELECT 'F01', 'Kontakt verloren', 'res_partner.id=' || id || ' (' || name || ')' FROM f01;

-- ---------------------------------------------------------------------
-- F02  Ein Produkt verloren (Stammdaten)
--      Gewählt: Produkt ohne Bestand und ohne Belegzeilen.
-- ---------------------------------------------------------------------
CREATE TEMP TABLE f02 ON COMMIT DROP AS
SELECT p.id, p.name
FROM product p
WHERE NOT EXISTS (SELECT 1 FROM stock_level q         WHERE q.product_id = p.id)
  AND NOT EXISTS (SELECT 1 FROM sale_order_line l     WHERE l.product_id = p.id)
  AND NOT EXISTS (SELECT 1 FROM purchase_order_line l WHERE l.product_id = p.id)
  AND NOT EXISTS (SELECT 1 FROM account_move_line l   WHERE l.product_id = p.id)
ORDER BY p.id
LIMIT 1;

DELETE FROM product WHERE id IN (SELECT id FROM f02);

INSERT INTO fehlerprotokoll
SELECT 'F02', 'Produkt verloren', 'product.id=' || id || ' (' || name || ')' FROM f02;

-- ---------------------------------------------------------------------
-- F03  Bestandsmenge verändert (Bestände)
--      Gewählt: Lagerzeile in einem internen Lager, deren Produkt einen
--      Einstandspreis ohne Rappen hat (damit F04 sie nicht überlagert).
-- ---------------------------------------------------------------------
WITH ziel AS (
    SELECT q.id, q.product_id, q.qty_on_hand AS alt
    FROM stock_level q
    JOIN stock_location l ON l.id = q.location_id
    JOIN product p        ON p.id = q.product_id
    WHERE l.usage = 'internal'
      AND q.qty_on_hand >= 10
      AND p.cost_price = round(p.cost_price)
    ORDER BY q.id
    LIMIT 1
), geaendert AS (
    UPDATE stock_level q
    SET qty_on_hand = q.qty_on_hand - 5
    FROM ziel
    WHERE q.id = ziel.id
    RETURNING q.id, q.product_id, ziel.alt, q.qty_on_hand AS neu
)
INSERT INTO fehlerprotokoll
SELECT 'F03', 'Bestandsmenge verändert',
       'stock_level.id=' || id || ' (product.id=' || product_id || '): ' || alt || ' -> ' || neu
FROM geaendert;

-- ---------------------------------------------------------------------
-- F04  Rundungsfehler beim Einstandspreis (Bestände: Wert)
--      Beim Umwandeln wurden Rappen abgeschnitten, z.B. 20.50 -> 21.
-- ---------------------------------------------------------------------
WITH ziel AS (
    SELECT id, cost_price AS alt
    FROM product
    WHERE cost_price <> round(cost_price)
), geaendert AS (
    UPDATE product p
    SET cost_price = round(p.cost_price)
    FROM ziel
    WHERE p.id = ziel.id
    RETURNING p.id, ziel.alt, p.cost_price AS neu
)
INSERT INTO fehlerprotokoll
SELECT 'F04', 'Einstandspreis gerundet',
       'product.id=' || id || ': ' || alt || ' -> ' || neu
FROM geaendert;

-- ---------------------------------------------------------------------
-- F05  Offene Kundenrechnung mit falscher Summe (Offene Belege)
--      Erste offene Kundenrechnung: Total um CHF 100.00 zu hoch.
-- ---------------------------------------------------------------------
WITH ziel AS (
    SELECT id, amount_total_cents AS alt
    FROM account_move
    WHERE move_type = 'out_invoice' AND state = 'posted' AND payment_state = 'not_paid'
    ORDER BY id
    LIMIT 1
), geaendert AS (
    UPDATE account_move m
    SET amount_total_cents = m.amount_total_cents + 10000
    FROM ziel
    WHERE m.id = ziel.id
    RETURNING m.id, m.name, ziel.alt, m.amount_total_cents AS neu
)
INSERT INTO fehlerprotokoll
SELECT 'F05', 'Rechnungssumme falsch',
       'account_move.id=' || id || ' (' || coalesce(name, '-') || '): ' || alt || ' -> ' || neu || ' Rappen'
FROM geaendert;

-- ---------------------------------------------------------------------
-- F06  Offene Kundenrechnung fälschlich als bezahlt markiert (Offene Belege)
--      Zweite offene Kundenrechnung: Zahlstatus 'paid', Restbetrag 0.
-- ---------------------------------------------------------------------
WITH ziel AS (
    SELECT id
    FROM account_move
    WHERE move_type = 'out_invoice' AND state = 'posted' AND payment_state = 'not_paid'
    ORDER BY id
    OFFSET 1
    LIMIT 1
), geaendert AS (
    UPDATE account_move m
    SET payment_state = 'paid',
        amount_residual_cents = 0
    FROM ziel
    WHERE m.id = ziel.id
    RETURNING m.id, m.name
)
INSERT INTO fehlerprotokoll
SELECT 'F06', 'Rechnung fälschlich bezahlt',
       'account_move.id=' || id || ' (' || coalesce(name, '-') || '): not_paid -> paid'
FROM geaendert;

-- ---------------------------------------------------------------------
-- F07  Auftragszeile ohne gültiges Produkt (Referenzielle Integrität)
--      Erste Zeile eines bestätigten Auftrags zeigt auf eine Produkt-ID,
--      die es nicht gibt.
-- ---------------------------------------------------------------------
WITH ziel AS (
    SELECT l.id, l.product_id AS alt
    FROM sale_order_line l
    JOIN sale_order s ON s.id = l.order_id
    WHERE s.state = 'sale' AND l.display_type IS NULL
    ORDER BY l.id
    LIMIT 1
), geaendert AS (
    UPDATE sale_order_line l
    SET product_id = 999999
    FROM ziel
    WHERE l.id = ziel.id
    RETURNING l.id, ziel.alt
)
INSERT INTO fehlerprotokoll
SELECT 'F07', 'Auftragszeile verwaist',
       'sale_order_line.id=' || id || ': product_id ' || alt || ' -> 999999'
FROM geaendert;

-- ---------------------------------------------------------------------
-- F08  Dublette nach dem Zusammenlegen (Stammdaten: Dubletten)
--      Ein Produkt mit Artikelnummer und Bestand wurde doppelt übernommen.
--      Die Kopie erhält die ID 900000 + Original-ID, damit sie nie eine
--      ID belegt, die vorher einem anderen Produkt gehörte.
-- ---------------------------------------------------------------------
WITH quelle AS (
    SELECT p.*
    FROM product p
    WHERE p.default_code IS NOT NULL
      AND EXISTS (SELECT 1 FROM stock_level q WHERE q.product_id = p.id)
    ORDER BY p.id
    LIMIT 1
), kopie AS (
    INSERT INTO product (id, template_id, name, default_code, type, is_storable,
                         list_price, cost_price, weight_g, active, abc_class)
    SELECT 900000 + id, template_id, name, default_code, type,
           is_storable, list_price, cost_price, weight_g, active, abc_class
    FROM quelle
    RETURNING id, default_code
)
INSERT INTO fehlerprotokoll
SELECT 'F08', 'Produkt-Dublette',
       'product.id=' || k.id || ' ist Kopie von product.id=' || q.id || ' (' || k.default_code || ')'
FROM kopie k, quelle q;

-- ---------------------------------------------------------------------
-- F09  Pflichtfeld leer (Stammdaten: Pflichtfelder)
--      Kunde des ersten bestätigten Auftrags verliert seinen Namen.
--      Leerer Text '' statt NULL: Odoo schützt den Namen mit einer
--      CHECK-Regel gegen NULL (res_partner_check_name). Leere Texte aus
--      Importen rutschen aber durch – darum muss der Check '' und NULL
--      gleich behandeln.
-- ---------------------------------------------------------------------
WITH ziel AS (
    SELECT p.id, p.name AS alt
    FROM res_partner p
    WHERE p.id = (SELECT partner_id FROM sale_order WHERE state = 'sale' ORDER BY id LIMIT 1)
), geaendert AS (
    UPDATE res_partner p
    SET name = ''
    FROM ziel
    WHERE p.id = ziel.id
    RETURNING p.id, ziel.alt
)
INSERT INTO fehlerprotokoll
SELECT 'F09', 'Kundenname leer', 'res_partner.id=' || id || ' (' || alt || ' -> leer)'
FROM geaendert;

-- Protokoll ausgeben
SELECT nr, fehler, betroffen FROM fehlerprotokoll ORDER BY nr, betroffen;

COMMIT;
