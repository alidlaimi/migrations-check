-- =====================================================================
-- Mini-Datenbank für die Tests
-- =====================================================================
-- Bildet die Tabellen und Spalten von Odoo 18 nach, die der Check und das
-- Migrationsskript nutzen – mit wenigen, gut überschaubaren Datensätzen.
-- So laufen die Tests in Sekunden und ohne Odoo-Installation.
-- Enthält auch die CHECK-Regel res_partner_check_name von Odoo (siehe F09).
-- =====================================================================
CREATE TABLE res_partner (id serial primary key, name varchar, complete_name varchar, is_company bool, active bool,
  customer_rank int, supplier_rank int, email varchar, parent_id int, type varchar DEFAULT 'contact', street varchar, street2 varchar, zip varchar, city varchar,
  CONSTRAINT res_partner_check_name CHECK ((type = 'contact' AND name IS NOT NULL) OR type <> 'contact'));
CREATE TABLE res_users (id serial primary key, partner_id int references res_partner(id));
CREATE TABLE res_company (id serial primary key, partner_id int references res_partner(id));
CREATE TABLE product_template (id serial primary key, name jsonb not null, default_code varchar, type varchar not null, is_storable bool, list_price numeric, weight numeric, active bool);
CREATE TABLE product_product (id serial primary key, product_tmpl_id int not null references product_template(id) on delete cascade, default_code varchar, standard_price jsonb, weight numeric, active bool);
CREATE TABLE stock_location (id serial primary key, name varchar, complete_name varchar, usage varchar, active bool, location_id int);
CREATE TABLE stock_quant (id serial primary key, product_id int not null references product_product(id), location_id int not null references stock_location(id), quantity numeric);
CREATE TABLE sale_order (id serial primary key, name varchar, partner_id int references res_partner(id), partner_invoice_id int references res_partner(id), partner_shipping_id int references res_partner(id), state varchar, invoice_status varchar, amount_total numeric);
CREATE TABLE sale_order_line (id serial primary key, order_id int references sale_order(id), product_id int references product_product(id), display_type varchar, product_uom_qty numeric, price_unit numeric);
CREATE TABLE purchase_order (id serial primary key, name varchar, partner_id int references res_partner(id), state varchar, invoice_status varchar, amount_total numeric);
CREATE TABLE purchase_order_line (id serial primary key, order_id int references purchase_order(id), product_id int references product_product(id));
CREATE TABLE account_move (id serial primary key, name varchar, move_type varchar, state varchar, payment_state varchar, partner_id int references res_partner(id), commercial_partner_id int references res_partner(id),
  amount_untaxed numeric, amount_total numeric, amount_residual numeric);
CREATE TABLE account_move_line (id serial primary key, move_id int references account_move(id), product_id int references product_product(id));
-- Views wie in Odoo: das Upgrade muss sie per CASCADE mitentfernen können
CREATE VIEW report_x AS SELECT m.id, m.amount_total, p.street FROM account_move m JOIN res_partner p ON p.id=m.partner_id;
CREATE VIEW report_p AS SELECT pp.id, pt.name FROM product_product pp JOIN product_template pt ON pt.id=pp.product_tmpl_id;

INSERT INTO res_partner (name,is_company,active,street,street2,zip,city) VALUES
 ('My Company',true,true,'Weg 1',null,'8000','Zürich'),('Azure Interior',true,true,'Str 2','Hof','8302','Kloten'),
 ('Deco Addict',true,true,'Str 3',null,'8001','Zürich'),('Brandon Freeman',false,true,'x',null,'1','A'),
 ('Colleen Diaz',false,true,'y',null,'2','B'),('Nicole Ford',false,true,null,null,null,null),('Admin',false,true,null,null,null,null);
INSERT INTO res_company (partner_id) VALUES (1);
INSERT INTO res_users (partner_id) VALUES (7);
INSERT INTO product_template (name,default_code,type,is_storable,list_price,weight,active) VALUES
 ('{"en_US":"Desk"}','FURN_1','consu',true,500,12.5,true),('{"en_US":"Chair"}','FURN_2','consu',true,100,3,true),
 ('{"en_US":"Lamp"}',null,'consu',true,40,1,true),('{"en_US":"Service"}',null,'service',false,80,0,true),('{"en_US":"Unused"}','X9','consu',false,10,0,true);
INSERT INTO product_product (product_tmpl_id,default_code,standard_price,weight,active) VALUES
 (1,'FURN_1','{"1":400.0}',12.5,true),(2,'FURN_2','{"1":20.5}',3,true),(3,null,'{"1":25.5}',1,true),(4,null,'{"1":8.0}',0,true),(5,'X9','{"1":5}',0,true);
INSERT INTO stock_location (name,complete_name,usage,active) VALUES ('Stock','WH/Stock','internal',true),('Inv','Virtual/Inventory','inventory',true);
INSERT INTO stock_quant (product_id,location_id,quantity) VALUES (1,1,50),(1,2,-50),(2,1,30),(2,2,-30),(3,1,12),(3,2,-12);
INSERT INTO sale_order (name,partner_id,partner_invoice_id,partner_shipping_id,state,invoice_status,amount_total) VALUES
 ('S1',2,2,2,'sale','no',600),('S2',3,3,3,'draft','no',100);
INSERT INTO sale_order_line (order_id,product_id,product_uom_qty,price_unit) VALUES (1,1,1,500),(1,2,1,100),(2,2,1,100);
INSERT INTO purchase_order (name,partner_id,state,amount_total) VALUES ('P1',3,'purchase',400);
INSERT INTO purchase_order_line (order_id,product_id) VALUES (1,1);
INSERT INTO account_move (name,move_type,state,payment_state,partner_id,commercial_partner_id,amount_untaxed,amount_total,amount_residual) VALUES
 ('INV/1','out_invoice','posted','not_paid',2,2,1000,1150.55,1150.55),('INV/2','out_invoice','posted','not_paid',3,3,500,575,575),
 ('INV/3','out_invoice','posted','not_paid',2,2,10,11.5,11.5),('BILL/1','in_invoice','posted','not_paid',3,3,300,326.13,326.13);
INSERT INTO account_move_line (move_id,product_id) VALUES (1,1),(2,2),(3,3),(4,4);
