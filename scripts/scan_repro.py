"""Reproduce the real-card layout + log what each step extracts.
Saves the synthetic image too so we can eyeball what the OCR sees."""
from PIL import Image, ImageDraw, ImageFont
import io, base64, json, urllib.request

W, H = 1200, 700
img = Image.new("RGB", (W, H), (252, 252, 252))
d = ImageDraw.Draw(img)
big   = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 38)
small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
body  = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 26)
addr  = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 26)

# Logo top-right (similar to ʌLCS pattern)
d.text((W-160, 60), "LCS", fill=(20, 30, 50), font=big)
d.polygon([(W-200, 78), (W-180, 60), (W-160, 78)], fill=(20, 30, 50))

# Name + designation (all caps, like the real card)
d.text((100, 230), "DOMINIK BÖCKLE", fill=(20, 30, 50), font=big)
d.text((100, 290), "HEAD OF IT", fill=(20, 30, 50), font=small)

# Block
d.text((100, 360), "LCS Cable Cranes GmbH", fill=(20, 30, 50), font=body)
d.text((100, 400), "Loruens 34, 6700 Loruens, Austria", fill=(20, 30, 50), font=addr)
d.text((100, 440), "T +43 5552 215 77 - 67 / M +43 676 4485875", fill=(20, 30, 50), font=addr)
d.text((100, 480), "d.boeckle@lcs-group.com", fill=(20, 30, 50), font=addr)
d.text((100, 520), "www.lcs-cablecranes.com", fill=(20, 30, 50), font=addr)

img.save("/tmp/test_card.png")
buf = io.BytesIO(); img.save(buf, "JPEG", quality=92)
b64 = base64.b64encode(buf.getvalue()).decode()

req = urllib.request.Request("http://localhost:8089/scan-base64",
    data=json.dumps({"image_base64": b64}).encode(),
    headers={"Content-Type": "application/json"})
out = json.loads(urllib.request.urlopen(req, timeout=180).read())
print("ENGINE:", out.get("engine"))
print("CONFIDENCE:", out.get("confidence"))
print()
print("--- raw_text ---")
print(out.get("raw_text"))
print()
print("--- parsed ---")
for k, v in out.items():
    if k not in ("raw_text",):
        print(f"  {k}: {v!r}")
