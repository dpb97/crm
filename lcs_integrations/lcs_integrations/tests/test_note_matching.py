"""
Systematic matching benchmark for dispatch_note.

Fires 12 realistic sample notes at the matcher and reports per-case:
  expected project  (what a human would pick)
  winner           (what the matcher picked)
  score + confidence
  reasons          (which signals contributed)
  verdict          PASS | MISS | WRONG

Run with:
  bench --site lcs.local execute lcs_integrations.tests.test_note_matching.run
"""

import frappe
from lcs_integrations.notes.api import dispatch_note


CASES = [
    # (expected project_name, note text, category)
    ("SB-SADDN",            "Call mit Techint Chile zu SB-SADDN, Liefertermin 30.06.", "exact name"),
    ("SB-SADDN",            "Techint hat sich gemeldet, Saddan Lieferung bestätigt",   "fuzzy name"),
    ("SB-SADDN",            "In Chile beim Projekt 90021 wird die Seilbahn fertig",    "abbr + country"),
    ("SB-JINNO",            "Ginno von Nippon Cable hat gefragt wann wir liefern",     "mis-heard + org"),
    ("SB-TATA",             "Meeting mit Tata Projects nächste Woche",                 "org match"),
    ("SB-CAPU",             "Productos del Aire aus Guatemala meldet sich zur Capu",   "org + country"),
    ("AS_BGW2000-HONGKONG", "Ngong Ping 360 will die Winde prüfen",                    "org + type hint"),
    ("AS_EC-Kufstein",      "Festung Kufstein ruft wegen Wartung an",                  "org"),
    ("Lannemezan Workshop", "Mecamont Hydro Workshop in Lannemezan läuft",             "location"),
    ("QX-CM",               "Civil Master Brasilien, QX-CM Status-Call",               "number match"),
    ("SB-BOIL",             "ABL Holding will Update zur Seilbahn haben",              "org + type hint"),
    ("SB-MTM",              "Doppelmayr NZ hat uns zu MTM angerufen",                  "org match"),
]


def run():
    print("\n=== Note matching benchmark ===\n")
    passes = 0
    misses = 0
    wrongs = 0
    lines = []

    for expected, text, category in CASES:
        # dry_run so we just get candidates back, no comments persist
        payload = dispatch_note(text=text, dry_run=True)
        top = payload["candidates"][0] if payload["candidates"] else None
        if not top:
            verdict = "MISS"
            misses += 1
            lines.append((category, expected, text, "", 0.0, "", verdict))
            continue
        actual = top["project_name"]
        if actual == expected:
            verdict = "PASS"
            passes += 1
        else:
            verdict = "WRONG"
            wrongs += 1
        lines.append((
            category, expected, text, actual, top["score"],
            ", ".join(top["reasons"]), verdict,
        ))

    # Print table
    for category, expected, text, actual, score, reasons, verdict in lines:
        marker = {"PASS": "✓", "WRONG": "✗", "MISS": "?"}[verdict]
        print(f"[{marker}] {verdict:5}  {category:20}  → {actual or '(no match)':25} (score {score:.2f})")
        print(f"        Expected: {expected}")
        print(f"        Text:     {text[:80]}")
        print(f"        Reasons:  {reasons}")
        print()

    total = len(CASES)
    print("=" * 60)
    print(f"  {passes}/{total} correct  ·  {wrongs} wrong  ·  {misses} no match")
    print(f"  Accuracy: {100 * passes / total:.0f}%")
    print("=" * 60)

    return {
        "total": total,
        "passes": passes,
        "wrongs": wrongs,
        "misses": misses,
        "accuracy": round(100 * passes / total, 1),
    }
