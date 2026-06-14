"""Kalkulations-Rechenkern (Kern-Primitive) — Formeln 1:1 aus Dossier 11.

Backend-only (E-5); das Vue-Frontend zeigt nur an. Diese Funktionen sind **reine
Funktionen** (kein DB-Zugriff) und damit isoliert testbar — die Basis fuer den
spaeteren Golden-Master gegen die Referenzquote `03c6eb4dfc` (🔒 Prototyp).

Konvention hier: Saetze als **Bruch** (0.05 = 5 %). Im DocType werden Saetze als
`Percent` (5 = 5 %) gefuehrt -> beim Aufruf /100 (E-25).
"""

from __future__ import annotations


def gross_up(base: float, rate: float) -> float:
    """Zuschlag, dessen Satz vom ERGEBNIS gerechnet ist: base * r/(1-r) (Dossier 11 §0).

    Beispiel (Glossar): 5 % Gross-up auf 100 = 5.263… (= 5 % von 105.26).
    """
    if rate <= 0 or rate >= 1:
        return 0.0
    return base * rate / (1.0 - rate)


def vk_cascade(prime: float, m: dict) -> float:
    """VK-Cascade (8 Schritte) auf die Summe der Prime-Kosten (Dossier 11 §3.1).

    t1..t5 = prime * Π(1+Satz) fuer indirect_material/general_admin/engineering/
    indirect_distribution/markup; danach 3 **Gross-ups** discount_surcharge, rebate,
    project_surcharge. Saetze als Bruch in `m`.
    """
    t = prime
    t *= 1 + m.get("indirect_material_cost", 0)
    t *= 1 + m.get("general_admin_cost", 0)
    t *= 1 + m.get("engineering_cost", 0)
    t *= 1 + m.get("indirect_distribution", 0)
    t *= 1 + m.get("markup", 0)
    t += gross_up(t, m.get("discount_surcharge", 0))
    t += gross_up(t, m.get("rebate", 0))
    t += gross_up(t, m.get("project_surcharge", 0))
    return t


def commission(vk_base: float, rate: float) -> float:
    """Commission = Gross-up auf den VK; erscheint in HK UND VK (DB-neutral, §6)."""
    return gross_up(vk_base, rate)


def withholding_tax(base: float, rate: float, gross_up_enabled: bool = False) -> float:
    """WHT (Dossier 11 §7): gross_up -> base*r/(1-r); sonst base*r.

    Verifiziertes Beispiel: base 140000, r=5 % -> 7000 (ohne) / 7368.42 (mit Gross-up).
    """
    return gross_up(base, rate) if gross_up_enabled else base * rate


def import_duty(material_vk: float, rate: float) -> float:
    """Einfuhrzoll auf den Material-VK (Dossier 11 §8); EK=VK -> DB-neutral."""
    return material_vk * rate


def financing_line(base: float, pct: float, risk: float, months: float, fee: float = 0.0) -> float:
    """Garantie-/Versicherungszeile (Dossier 11 §9.1): base*(pct+risk)*months/12 + fee.

    pct/risk als Bruch (% p.a.).
    """
    return base * (pct + risk) * months / 12.0 + fee


def buyback_amount(vk_equipment: float, pct: float) -> float:
    """Buyback-Betrag = Σ VK Equipment × pct (Dossier 11 §11). pct als Bruch."""
    return vk_equipment * pct


def buyback_rate_at(pct_points: float, duration_months: int, month: int) -> float:
    """Buyback-Degression (Dossier 11 §11): Satz konstant bis `duration_months`,
    danach -1 %-Punkt pro Monat bis 0. `pct_points` in Prozentpunkten (z. B. 15).
    """
    if month <= duration_months:
        return pct_points
    return max(0.0, pct_points - (month - duration_months))


def pmt_monthly(annual_rate: float, months: int, pv: float = 1.0) -> float:
    """Monats-Annuitaet (Backend-Variante, Dossier 11 §5.2): PMT(r_m, n) mit r_m=annual/12.

    Beispiel: 5 %/a, 36 Mon -> ~0.02997 (2.997 %/Mon).
    """
    r = annual_rate / 12.0
    if r == 0:
        return pv / months
    f = (1.0 + r) ** months
    return pv * r * f / (f - 1.0)
