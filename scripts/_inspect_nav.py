import pandas as pd

df = pd.read_excel(
    "/mnt/c/Users/d.boeckle/Downloads/pilanda-navigation_v15.xlsx",
    sheet_name="Navigation",
)

print("=== TOP-LEVEL MODULES (dedup, ordered) ===")
seen = set()
rows = []
for _, r in df.iterrows():
    key = (r["Zone"], r["Top-Level"])
    if key in seen or pd.isna(r["Top-Level"]):
        continue
    seen.add(key)
    quelle = r.get("Quelle (App)", "")
    if isinstance(quelle, float):
        quelle = ""
    rows.append(
        {
            "Zone":   r["Zone"],
            "Top":    r["Top-Level"],
            "Phase":  r["Phase"],
            "Pfad":   r["Pfad"],
            "Quelle": str(quelle)[:80],
        }
    )

for r in rows:
    print(
        f"  Zone {str(r['Zone']):>4s}  |  {str(r['Top']):<28s}  |  "
        f"Phase {r['Phase']}  |  Pfad {r['Pfad']:>25s}  |  Quelle: {r['Quelle']}"
    )

print()
print("=== ZONE SUMMARY ===")
print(df.groupby("Zone")["Top-Level"].nunique())

print()
print("=== ZONE C (Support) — every Top-Level, every Sub-Level ===")
c = df[df["Zone"] == "C"]
for _, r in c.iterrows():
    print(
        f"  {str(r['Top-Level']):<28s} | {str(r['Sub-Level']):<28s} | "
        f"path={r['Pfad']:>20s} | quelle={str(r.get('Quelle (App)', ''))[:40]}"
    )

print()
print("=== ZONE D (Wissen) — every Top-Level, every Sub-Level ===")
d = df[df["Zone"] == "D"]
for _, r in d.iterrows():
    print(
        f"  {str(r['Top-Level']):<28s} | {str(r['Sub-Level']):<28s} | "
        f"path={r['Pfad']:>20s} | quelle={str(r.get('Quelle (App)', ''))[:40]}"
    )
