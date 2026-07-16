"""Unit-Tests des Kalkulations-Rechenkerns gegen die verifizierten Zahlenbeispiele
aus Dossier 11 (kein DB-Zugriff, reine Funktionen). pytest-Stil.

Lauf:  ./env/bin/python -m pytest apps/pilanda_sales/pilanda_sales/calculation/test_engine.py
"""

from pilanda_sales.calculation import engine as e

MARKUP_DEFAULTS = {
    "indirect_material_cost": 0.14,
    "general_admin_cost": 0.10,
    "engineering_cost": 0.02,
    "indirect_distribution": 0.13,
    "markup": 0.20,
    "discount_surcharge": 0.03,
    "rebate": 0.0,
    "project_surcharge": 0.02,
}


def _close(a, b, tol=0.01):
    return abs(a - b) <= tol


def test_gross_up_glossar_example():
    assert _close(e.gross_up(100, 0.05), 5.2631, 0.001)


def test_gross_up_edges():
    assert e.gross_up(100, 0) == 0.0
    assert e.gross_up(100, 1) == 0.0


def test_wht_verified_examples():
    assert _close(e.withholding_tax(140000, 0.05, False), 7000.0)
    assert _close(e.withholding_tax(140000, 0.05, True), 7368.42)


def test_commission_is_db_neutral_grossup():
    assert _close(e.commission(1000, 0.05), e.gross_up(1000, 0.05))


def test_vk_cascade_with_defaults():
    # prime 100 -> ~182.46 (sequentielle Schritte inkl. 2 Gross-ups, rebate 0)
    assert _close(e.vk_cascade(100.0, MARKUP_DEFAULTS), 182.46, 0.05)


def test_pmt_monthly_5pct_36m():
    assert _close(e.pmt_monthly(0.05, 36), 0.02997, 0.0003)


def test_pmt_zero_rate():
    assert _close(e.pmt_monthly(0.0, 36, pv=1.0), 1 / 36)


def test_buyback_degression():
    assert e.buyback_rate_at(15, 36, 36) == 15
    assert e.buyback_rate_at(15, 36, 40) == 11
    assert e.buyback_rate_at(15, 36, 60) == 0


def test_import_duty_linear():
    assert _close(e.import_duty(50000, 0.07), 3500.0)


def test_financing_line():
    # 100000 * (0.02+0.01) * 12/12 + 500 = 3000 + 500 = 3500
    assert _close(e.financing_line(100000, 0.02, 0.01, 12, 500), 3500.0)
