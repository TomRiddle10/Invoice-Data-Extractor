import io
import json
import os
import re
from pathlib import Path
import fitz
from schema import Invoice

def read_invoice_text(filename: str, content: bytes) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix == ".txt":
        return content.decode("utf-8", errors="replace")
    if suffix == ".pdf":
        doc = fitz.open(stream=content, filetype="pdf")
        pages = [page.get_text("text") for page in doc]
        text = "\n".join(pages).strip()
        if not text:
            raise ValueError("No selectable text found. This scanned PDF needs OCR; see README for optional OCR setup.")
        return text
    raise ValueError("Unsupported file type. Upload PDF or TXT.")

def _money(value):
    if value is None:
        return 0.0
    cleaned = str(value).replace(",", "").replace("₹", "").replace("$", "").replace("€", "").strip()
    try:
        return round(float(cleaned), 2)
    except ValueError:
        return 0.0

def rule_based_extract(text: str, filename: str) -> dict:
    def find(pattern, default=""):
        m = re.search(pattern, text, flags=re.I | re.M)
        return m.group(1).strip() if m else default

    invoice_no = find(r"(?:invoice\s*(?:number|no\.?|#)|inv\s*#)\s*[:\-]?\s*([A-Z0-9\-\/]+)", "NOT_FOUND")
    date = find(r"(?:invoice\s*)?date\s*[:\-]?\s*(\d{4}[/-]\d{1,2}[/-]\d{1,2}|\d{1,2}[/-]\d{1,2}[/-]\d{2,4})", "")
    vendor = find(r"(?:vendor|from|seller)\s*[:\-]\s*(.+)", "Unknown Vendor")
    currency = "INR" if "₹" in text or "INR" in text.upper() else ("EUR" if "€" in text else ("USD" if "$" in text else ""))
    subtotal = _money(find(r"(?:sub\s*total|subtotal)\s*[:\-]?\s*[₹$€]?\s*([\d,]+\.?\d*)", "0"))
    tax = _money(find(r"(?:tax|gst|vat)\s*[:\-]?\s*[₹$€]?\s*([\d,]+\.?\d*)", "0"))
    total = _money(find(r"\b(?:grand\s*total|total\s*due|amount\s*due|total)\b\s*[:\-]?\s*[₹$€]?\s*([\d,]+\.?\d*)", "0"))

    items = []
    # Sample-friendly line format: ITEM: Description | quantity | unit price | line total
    for line in text.splitlines():
        m = re.match(r"\s*ITEM\s*:\s*(.*?)\s*\|\s*(\d+(?:\.\d+)?)\s*\|\s*([\d,.]+)\s*\|\s*([\d,.]+)\s*$", line, re.I)
        if m:
            items.append({
                "description": m.group(1).strip(),
                "quantity": float(m.group(2)),
                "unit_price": _money(m.group(3)),
                "line_total": _money(m.group(4))
            })
    return {
        "source_file": filename, "invoice_number": invoice_no, "invoice_date": date,
        "vendor_name": vendor, "currency": currency, "subtotal": subtotal,
        "tax": tax, "total": total, "items": items
    }

def ai_extract(text: str, filename: str) -> dict:
    from openai import OpenAI
    client = OpenAI()
    schema = {
        "type": "object",
        "properties": {
            "invoice_number": {"type": "string"},
            "invoice_date": {"type": "string"},
            "vendor_name": {"type": "string"},
            "currency": {"type": "string"},
            "subtotal": {"type": "number"},
            "tax": {"type": "number"},
            "total": {"type": "number"},
            "items": {"type": "array", "items": {"type": "object", "properties": {
                "description": {"type": "string"}, "quantity": {"type": "number"},
                "unit_price": {"type": "number"}, "line_total": {"type": "number"}
            }, "required": ["description", "quantity", "unit_price", "line_total"], "additionalProperties": False}}
        },
        "required": ["invoice_number", "invoice_date", "vendor_name", "currency", "subtotal", "tax", "total", "items"],
        "additionalProperties": False
    }
    response = client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": "Extract invoice fields from the supplied text. Return only valid JSON matching this structure. Do not guess missing values: use empty strings or 0.0. Preserve currency and line items. Schema description: " + json.dumps(schema)},
            {"role": "user", "content": text[:25000]}
        ],
        temperature=0
    )
    # Explicit JSON parsing as required by the assignment.
    parsed = json.loads(response.choices[0].message.content)
    parsed["source_file"] = filename
    return parsed

def extract_invoice(filename: str, content: bytes) -> dict:
    text = read_invoice_text(filename, content)
    if os.getenv("OPENAI_API_KEY"):
        try:
            data = ai_extract(text, filename)
            return Invoice.model_validate(data).model_dump()
        except Exception:
            # Fallback ensures the demo remains usable if AI/API parsing fails.
            pass
    data = rule_based_extract(text, filename)
    return Invoice.model_validate(data).model_dump()
