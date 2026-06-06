import fitz
import json
import urllib.request


doc = fitz.open()
page = doc.new_page()
page.insert_text((72, 72), 'Action Items:\n1. Review Q3 report\n2. Schedule team meeting\n3. Update project timeline')
pdf_bytes = doc.tobytes()
doc.close()

boundary = "----TestBoundary7788"
body = (
    f"--{boundary}\r\n"
    f"Content-Disposition: form-data; name=\"file\"; filename=\"test.pdf\"\r\n"
    f"Content-Type: application/pdf\r\n\r\n"
).encode("utf-8") + pdf_bytes + f"\r\n--{boundary}--\r\n".encode("utf-8")

req = urllib.request.Request(
    "http://localhost:8000/api/v1/pdf/upload",
    data=body,
    headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
)
resp = json.loads(urllib.request.urlopen(req).read())
r = resp["result"]
print("Method:", r["method"])
print("Confidence:", r["confidence"])
print("Pages:", r["page_count"])
print("Chars:", r["char_count"])
print("pdf_id:", r["pdf_id"])
print("Preview:", repr(r["preview"][:120]))
