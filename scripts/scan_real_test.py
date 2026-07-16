"""Generate a realistic test card image, run it through both engines,
print the parsed result."""
from PIL import Image, ImageDraw, ImageFont
import io, base64, json, urllib.request

# Build a small business card programatically with text Tesseract
# typically struggles on (italics-like spacing, mixed sizes, multi-line).
img = Image.new("RGB", (1000, 600), "white")
d = ImageDraw.Draw(img)
try:
    title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 44)
    name_font  = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 38)
    body_font  = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 26)
    small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 22)
except OSError:
    title_font = name_font = body_font = small_font = ImageFont.load_default()

# Header band
d.rectangle([(0, 0), (1000, 90)], fill=(11, 58, 111))
d.text((40, 22), "LCS Cable Cranes GmbH", fill="white", font=title_font)

d.text((40, 140), "Dr. Anna Schmidt", fill=(11, 58, 111), font=name_font)
d.text((40, 200), "Head of Sales / Vertriebsleitung", fill=(80, 80, 80), font=body_font)

d.text((40, 280), "Mobil:  +49 171 5551234", fill="black", font=small_font)
d.text((40, 320), "Tel.:   +49 7531 88-0",   fill="black", font=small_font)
d.text((40, 360), "E-Mail: a.schmidt@lcs-group.com", fill="black", font=small_font)
d.text((40, 400), "Web:    www.lcs-group.com", fill="black", font=small_font)
d.text((40, 460), "Mainaustraße 42 · 78464 Konstanz", fill="black", font=small_font)

buf = io.BytesIO()
img.save(buf, "JPEG", quality=92)
b64 = base64.b64encode(buf.getvalue()).decode()

req = urllib.request.Request(
    "http://localhost:8089/scan-base64",
    data=json.dumps({"image_base64": b64, "mime_type": "image/jpeg"}).encode(),
    headers={"Content-Type": "application/json"},
)
r = urllib.request.urlopen(req, timeout=120)
out = json.loads(r.read())
print(json.dumps({k: v for k, v in out.items() if k != "raw_text"}, indent=2, ensure_ascii=False))
print()
print("--- raw OCR text ---")
print(out.get("raw_text", "")[:600])
