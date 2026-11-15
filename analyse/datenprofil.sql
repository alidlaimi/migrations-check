-- Datenprofil der Odoo-Datenbank
-- Zweck: Vor einer Migration wissen, was in den fachlich relevanten Tabellen steckt.
-- Aufruf: docker compose exec -T db psql -U odoo -d <datenbank> < analyse/datenprofil.sql

\echo '=== Partner (Kunden / Lieferanten) ==='
SELECT count(*)                                  AS total,
       count(*) FILTER (WHERE is_company)        AS firmen,
       count(*) FILTER (WHERE customer_rank > 0) AS kunden,
       count(*) FILTER (WHERE supplier_rank > 0) AS lieferanten,
       count(*) FILTER (WHERE NOT active)        AS inaktiv,
       count(*) FILTER (WHERE email IS NULL)     AS ohne_email
FROM res_partner;

\echo '=== Produkte ==='
SELECT (SELECT count(*) FROM product_template)                      AS vorlagen,
       (SELECT count(*) FROM product_product)                       AS varianten,
       (SELECT count(*) FROM product_template WHERE is_storable)    AS lagergefuehrt,
       (SELECT count(*) FROM product_product WHERE default_code IS NULL) AS ohne_artikelnr;

\echo '=== Beispiel Einstandspreis (standard_price ist jsonb je Firma) ==='
SELECT id, default_code, standard_price FROM product_product
WHERE standard_price IS NOT NULL ORDER BY id LIMIT 5;

\echo '=== Bestaende nach Lagerort-Typ ==='
SELECT l.usage, count(*) AS zeilen, sum(q.quantity) AS menge
FROM stock_quant q JOIN stock_location l ON l.id = q.location_id
GROUP BY l.usage ORDER BY l.usage;

\echo '=== Interne Lagerorte mit Bestand ==='
SELECT l.complete_name, count(*) AS zeilen, sum(q.quantity) AS menge
FROM stock_quant q JOIN stock_location l ON l.id = q.location_id
WHERE l.usage = 'internal'
GROUP BY l.complete_name ORDER BY l.complete_name;

\echo '=== Verkaufsauftraege nach Status ==='
SELECT state, invoice_status, count(*), sum(amount_total) AS summe
FROM sale_order GROUP BY state, invoice_status ORDER BY state, invoice_status;

\echo '=== Auftragszeilen ==='
SELECT coalesce(display_type, '(produktzeile)') AS typ,
       count(*), count(*) FILTER (WHERE product_id IS NULL) AS ohne_produkt
FROM sale_order_line GROUP BY 1 ORDER BY 1;

\echo '=== Bestellungen nach Status ==='
SELECT state, invoice_status, count(*), sum(amount_total) AS summe
FROM purchase_order GROUP BY state, invoice_status ORDER BY state, invoice_status;

\echo '=== Rechnungen nach Typ, Status, Zahlstatus ==='
SELECT move_type, state, payment_state, count(*),
       sum(amount_total) AS summe, sum(amount_residual) AS offen
FROM account_move
WHERE move_type IN ('out_invoice', 'in_invoice', 'out_refund', 'in_refund')
GROUP BY move_type, state, payment_state ORDER BY 1, 2, 3;
