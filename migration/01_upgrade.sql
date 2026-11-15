-- =====================================================================
-- 01_upgrade.sql – nachgebildetes ERP-Upgrade (ohne Fehler)
-- =====================================================================
-- Bildet typische Strukturänderungen eines Versions-Upgrades nach.
-- Läuft in EINER Transaktion: Entweder gelingen alle Änderungen oder keine.
-- Die Zuordnung alt -> neu ist in config/mapping.yaml beschrieben.
-- =====================================================================

BEGIN;

-- Hinweise (NOTICE) unterdrücken, z.B. die lange Liste von DROP ... CASCADE
SET LOCAL client_min_messages = warning;

-- ---------------------------------------------------------------------
-- U1  Tabelle und Spalte umbenannt
--     stock_quant -> stock_level, quantity -> qty_on_hand
-- ---------------------------------------------------------------------
ALTER TABLE stock_quant RENAME TO stock_level;
ALTER TABLE stock_level RENAME COLUMN quantity TO qty_on_hand;

-- ---------------------------------------------------------------------
-- U2  Tabellen zusammengelegt
--     product_template (Vorlage) + product_product (Variante) -> product
--     Eine Zeile pro Variante; die ID der Variante bleibt erhalten,
--     damit Verweise aus Aufträgen und Beständen weiter stimmen.
-- U4  Datentypen und Einheiten (Produkt)
--     standard_price: jsonb je Firma -> numeric cost_price (Firma 1)
--     weight: kg -> weight_g in Gramm
-- U5  Neues Pflichtfeld abc_class mit Standardwert 'C'
-- ---------------------------------------------------------------------
CREATE TABLE product (
    id           integer PRIMARY KEY,
    template_id  integer NOT NULL,
    name         text    NOT NULL,
    default_code varchar,
    type         varchar NOT NULL,
    is_storable  boolean,
    list_price   numeric,
    cost_price   numeric,
    weight_g     numeric,
    active       boolean,
    abc_class    char(1) NOT NULL DEFAULT 'C'
);

INSERT INTO product (id, template_id, name, default_code, type, is_storable,
                     list_price, cost_price, weight_g, active)
SELECT pp.id,
       pt.id,
       coalesce(pt.name ->> 'de_CH', pt.name ->> 'en_US'),  -- Übersetzung -> Klartext
       pp.default_code,
       pt.type,
       pt.is_storable,
       pt.list_price,
       (pp.standard_price ->> '1')::numeric,               -- Wert der Firma 1
       coalesce(pp.weight, pt.weight) * 1000,              -- kg -> g
       pp.active AND pt.active
FROM product_product pp
JOIN product_template pt ON pt.id = pp.product_tmpl_id;

-- Die alten Tabellen entfallen. CASCADE entfernt auch die Fremdschlüssel,
-- die auf sie zeigten. Das Upgrade legt diese Verknüpfungen bewusst nicht
-- neu an – wie bei vielen Massenimporten. Genau deshalb braucht es die
-- Integritätsprüfung des Migrations-Checks.
DROP TABLE product_product, product_template CASCADE;

-- ---------------------------------------------------------------------
-- U3  Tabelle aufgeteilt
--     Adressfelder aus res_partner -> neue Tabelle partner_address
--     dabei umbenannt: street2 -> address_line2
-- ---------------------------------------------------------------------
CREATE TABLE partner_address (
    partner_id    integer PRIMARY KEY REFERENCES res_partner (id) ON DELETE CASCADE,
    street        varchar,
    address_line2 varchar,
    zip           varchar,
    city          varchar
);

INSERT INTO partner_address (partner_id, street, address_line2, zip, city)
SELECT id, street, street2, zip, city
FROM res_partner;

ALTER TABLE res_partner
    DROP COLUMN street  CASCADE,
    DROP COLUMN street2 CASCADE,
    DROP COLUMN zip     CASCADE,
    DROP COLUMN city    CASCADE;

-- ---------------------------------------------------------------------
-- U4  Datentyp und Einheit (Rechnungen)
--     Beträge in CHF (numeric) -> Rappen (bigint, ganze Zahl)
-- ---------------------------------------------------------------------
ALTER TABLE account_move
    ADD COLUMN amount_untaxed_cents  bigint,
    ADD COLUMN amount_total_cents    bigint,
    ADD COLUMN amount_residual_cents bigint;

UPDATE account_move
SET amount_untaxed_cents  = round(amount_untaxed  * 100),
    amount_total_cents    = round(amount_total    * 100),
    amount_residual_cents = round(amount_residual * 100);

ALTER TABLE account_move
    DROP COLUMN amount_untaxed  CASCADE,
    DROP COLUMN amount_total    CASCADE,
    DROP COLUMN amount_residual CASCADE;

COMMIT;
