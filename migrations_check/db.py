"""Verbindung zu PostgreSQL.

Zugangsdaten (Host, Port, Benutzer, Passwort) kommen NICHT aus dem Code,
sondern aus den Umgebungsvariablen PGHOST, PGPORT, PGUSER, PGPASSWORD.
Die liest der PostgreSQL-Treiber selbst – sie stehen in der Datei .env.
"""

import psycopg
from psycopg.rows import dict_row


def verbinden(datenbank: str) -> psycopg.Connection:
    """Öffnet eine Verbindung zur angegebenen Datenbank (nur lesend genutzt)."""
    verbindung = psycopg.connect(dbname=datenbank, row_factory=dict_row)
    verbindung.read_only = True  # Sicherheitsnetz: der Check ändert nie Daten
    return verbindung


def abfragen(verbindung: psycopg.Connection, sql: str) -> list[dict]:
    """Führt eine Abfrage aus und gibt die Zeilen als Liste von Dictionaries zurück."""
    with verbindung.cursor() as cursor:
        cursor.execute(sql)
        return cursor.fetchall()
