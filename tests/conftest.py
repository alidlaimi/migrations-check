"""Gemeinsame Test-Vorbereitung.

Baut aus tests/testdaten/mini_vorher.sql drei kleine Test-Datenbanken:
  mc_test_vorher    Ausgangszustand
  mc_test_sauber    + migration/01_upgrade.sql
  mc_test_nachher   + migration/01_upgrade.sql + migration/02_fehler.sql
Genau so, wie nachher-erstellen.sh es mit der Odoo-Datenbank macht.

Verbindung über die Umgebungsvariablen PGHOST, PGUSER, PGPASSWORD (aus .env).
"""

from pathlib import Path

import psycopg
import pytest
import yaml

from migrations_check import check, mapping

PROJEKT = Path(__file__).resolve().parent.parent
VORHER, SAUBER, NACHHER = "mc_test_vorher", "mc_test_sauber", "mc_test_nachher"


def sql_ausfuehren(datenbank: str, datei: Path) -> None:
    with psycopg.connect(dbname=datenbank, autocommit=True) as verbindung:
        verbindung.execute(datei.read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def test_datenbanken():
    """Legt die drei Test-Datenbanken einmal pro Testlauf neu an."""
    try:
        server = psycopg.connect(dbname="postgres", autocommit=True)
    except psycopg.OperationalError as fehler:
        pytest.skip(f"Kein PostgreSQL erreichbar – Datenbank-Tests übersprungen ({fehler})")

    with server:
        for name in (VORHER, SAUBER, NACHHER):
            server.execute(f"DROP DATABASE IF EXISTS {name}")
        server.execute(f"CREATE DATABASE {VORHER}")
        sql_ausfuehren(VORHER, PROJEKT / "tests/testdaten/mini_vorher.sql")

        # Kopien von "vorher" anlegen (TEMPLATE = Datenbank als Vorlage kopieren)
        server.execute(f"CREATE DATABASE {SAUBER} TEMPLATE {VORHER}")
        server.execute(f"CREATE DATABASE {NACHHER} TEMPLATE {VORHER}")

    sql_ausfuehren(SAUBER, PROJEKT / "migration/01_upgrade.sql")
    sql_ausfuehren(NACHHER, PROJEKT / "migration/01_upgrade.sql")
    sql_ausfuehren(NACHHER, PROJEKT / "migration/02_fehler.sql")
    return VORHER, SAUBER, NACHHER


@pytest.fixture(scope="session")
def konfiguration():
    objekte = mapping.laden(PROJEKT / "config/mapping.yaml")
    with open(PROJEKT / "config/pruefungen.yaml", encoding="utf-8") as datei:
        regeln = yaml.safe_load(datei)["pruefungen"]
    return objekte, regeln


@pytest.fixture(scope="session")
def ergebnis_sauber(test_datenbanken, konfiguration):
    vorher, sauber, _ = test_datenbanken
    return check.pruefen(vorher, sauber, *konfiguration)


@pytest.fixture(scope="session")
def ergebnis_nachher(test_datenbanken, konfiguration):
    vorher, _, nachher = test_datenbanken
    return check.pruefen(vorher, nachher, *konfiguration)
