"""Unit-Tests: einzelne Prüfungen mit kleinen, von Hand gebauten Daten – ohne Datenbank."""

from decimal import Decimal

from migrations_check.ergebnis import FEHLER, OK
from migrations_check.pruefungen import (dubletten, feldvergleich, gleich, ist_leer,
                                         offene_belege, referenz, summe)


def regel(**einstellungen):
    """Minimale Prüfregel; die Tests setzen nur, was sie brauchen."""
    return {"titel": "Test", "schweregrad": FEHLER, "erklaerung": "-", **einstellungen}


def test_leer_erkennt_null_und_leeren_text():
    assert ist_leer(None)
    assert ist_leer("")
    assert ist_leer("   ")
    assert not ist_leer("Gemini Furniture")
    assert not ist_leer(0)


def test_gleich_beachtet_toleranz():
    assert gleich(Decimal("20.50"), Decimal("20.504"), Decimal("0.005"))
    assert not gleich(Decimal("20.50"), Decimal("21"), Decimal("0.005"))
    assert gleich(12.5, Decimal("12.5000"), Decimal(0))   # gleiche Zahl, anderer Typ
    assert not gleich("not_paid", "paid", Decimal(0))


def test_dubletten_nur_neue_melden():
    vorher = {1: {"code": "A"}, 2: {"code": "B"}, 3: {"code": "B"}}   # B war schon doppelt
    nachher = {1: {"code": "A"}, 2: {"code": "B"}, 3: {"code": "B"}, 9: {"code": "A"}}
    [e] = dubletten(regel(objekt="p", feld="code"),
                    {"vorher": {"p": vorher}, "nachher": {"p": nachher}})
    assert e.status == FEHLER
    assert len(e.details) == 1 and "'A'" in e.details[0]


def test_summe_mit_toleranz():
    vorher = {1: {"g": "x", "wert": Decimal("10.00")}}
    nachher_rundung = {1: {"g": "x", "wert": Decimal("10.004")}}
    nachher_fehler = {1: {"g": "x", "wert": Decimal("9.00")}}
    pruefung = regel(objekt="b", gruppe=["g"], feld="wert", toleranz=0.01)

    [ok] = summe(pruefung, {"vorher": {"b": vorher}, "nachher": {"b": nachher_rundung}})
    [fehler] = summe(pruefung, {"vorher": {"b": vorher}, "nachher": {"b": nachher_fehler}})
    assert ok.status == OK
    assert fehler.status == FEHLER


def test_offene_belege_erkennt_falschen_status():
    vorher = {1: {"status": "posted", "zahl": "not_paid", "total": Decimal(100)}}
    nachher = {1: {"status": "posted", "zahl": "paid", "total": Decimal(100)}}
    [e] = offene_belege(
        regel(objekt="r", offen_wenn={"status": ["posted"], "zahl": ["not_paid"]}, betraege=["total"]),
        {"vorher": {"r": vorher}, "nachher": {"r": nachher}})
    assert e.status == FEHLER
    assert "nicht mehr" in e.details[0]


def test_referenz_meldet_nur_neu_verwaiste():
    produkte = {1: {}, 2: {}}
    vorher = {10: {"produkt": 1}, 11: {"produkt": 77}}     # 77 war schon vorher verwaist
    nachher = {10: {"produkt": 99}, 11: {"produkt": 77}}
    [e] = referenz(regel(objekt="z", feld="produkt", ziel="p"),
                   {"vorher": {"z": vorher, "p": produkte}, "nachher": {"z": nachher, "p": produkte}})
    assert len(e.details) == 1 and "produkt=99" in e.details[0]


def test_stichprobe_ist_reproduzierbar():
    zeilen = {i: {"wert": i} for i in range(100)}
    daten = {"vorher": {"x": zeilen}, "nachher": {"x": zeilen}}
    erste = feldvergleich(regel(objekt="x", stichprobe=5), daten)
    zweite = feldvergleich(regel(objekt="x", stichprobe=5), daten)
    assert erste[0].zusammenfassung == zweite[0].zusammenfassung
