"""Seed the three demo Chancen from the klickdummy so the Chancen page is
demonstrable before the Pilot scout (pilanda_salesbot) is live.

Idempotent: skips entirely once any LCS Chance exists, so it never duplicates
and never overwrites real scout data once that arrives.
"""

import frappe

CHANCES = [
	{
		"chance_no": "CH-123", "title": "Seilkran Staumauer-Sanierung Grimsel",
		"source": "Notiz (intern)", "source_detail": "Notiz · M. Berger (Schnellnotiz)",
		"client": "Kraftwerke Oberhasli AG", "company": "Kraftwerke Oberhasli AG", "country": "CH",
		"order_value": 1900000, "score": 64, "relevance": "hoch", "status": "Relevant",
		"category": "Seilkran · Staumauer",
		"reasoning": "Score 64: bestehender Kontakt, Sanierung im Kernprofil.",
		"summary_de": "Sanierung der Staumauer; Seilkran für Materialtransport an der Mauerkrone.",
		"latitude": 46.57500, "longitude": 8.33700, "geo_confidence": "Anlage (exakt)",
		"published_on": "2026-06-20", "last_synced": "2026-06-20",
	},
	{
		"chance_no": "CH-125", "title": "Seilkran Lawinenverbauung Gasteinertal",
		"source": "Anfrage (Mail/Telefon)", "source_detail": "Kontakt · Land Salzburg",
		"client": "Wildbach- und Lawinenverbauung", "company": "Wildbach- und Lawinenverbauung", "country": "AT",
		"external_id": "WLV-2026-0417", "cpv_codes": "45234200 (Seilbahnanlagen)",
		"order_value": 800000, "published_on": "2026-06-27", "deadline": "2026-09-12",
		"score": 66, "relevance": "hoch", "status": "Neu", "category": "Seilkran · Schutzbauten",
		"reasoning": "Score 66: passgenaue Referenzen Arlberg; kleine Losgrößen.",
		"summary_de": "Verbauungsprogramm 2027–2029, Lose je Hangbereich; Seilkran als Vorzugslösung genannt.",
		"description_original": "Anfrage der Gebietsbauleitung: Verbauungsprogramm in 4 Losen, Seilkran-Transport für Stahlschneebrücken; Bauzeitfenster jeweils Juni–Oktober.",
		"latitude": 47.11028, "longitude": 13.12917, "geo_confidence": "Hangbereich (gut)",
		"last_synced": "2026-06-27",
	},
	{
		"chance_no": "CH-126", "title": "Materialseilbahn Kraftwerk Obervermunt",
		"source": "Empfehlung", "source_detail": "Empfehlung · Illwerke",
		"client": "Illwerke VKW AG", "company": "Illwerke VKW AG", "country": "AT",
		"order_value": 2600000, "published_on": "2026-06-18", "deadline": "2026-11-28",
		"score": 78, "relevance": "hoch", "status": "Relevant", "category": "Materialseilbahn · Wasserkraft",
		"reasoning": "Score 78: bestehender Kundenkontakt, technisch Kernprofil MSB-8.",
		"summary_de": "Ersatz der Bestandsbahn im Zuge der Kraftwerkserweiterung; Vorstudie liegt vor.",
		"description_original": "Empfehlung aus laufendem Projekt: Ersatzneubau der Werksbahn (Nutzlast 6 t, 1,9 km) parallel zur Kraftwerkserweiterung; Vorstudie der Illwerke liegt vor.",
		"latitude": 46.90972, "longitude": 10.09167, "geo_confidence": "Anlage (exakt)",
		"responsible": "M. Berger",
		"sales_note": "Vorstudie liegt im Netzwerk-Ordner; Termin mit Illwerke-Projektleitung anfragen.",
		"last_synced": "2026-06-18",
	},
]


def execute():
	if frappe.db.count("LCS Chance"):
		return
	for c in CHANCES:
		doc = frappe.new_doc("LCS Chance")
		doc.update(c)
		doc.insert(ignore_permissions=True)
