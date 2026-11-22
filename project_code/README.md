# Invoice Data Extractor

A college assignment project that extracts structured invoice information from PDF/TXT files, validates it against a fixed schema, displays a table, and exports Excel.

## Features
- Multiple PDF and TXT uploads
- PDF text extraction with PyMuPDF
- Optional LLM-based extraction using an OpenAI API key
- Local rule-based fallback for offline demonstrations
- JSON parsing with `json.loads()` and validation using Pydantic
- Invoice summary and line-item tables
- Excel workbook with `Invoices` and `Line Items` sheets
- JSON download

## Requirements
- Python 3.10 or newer
- pip

## Setup (Windows PowerShell)
```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```
Open the local URL printed by Streamlit (usually http://localhost:8501).

## Optional AI mode
Copy `.env.example` to `.env`, add your API key, and load it into the environment before launching Streamlit:
```powershell
$env:OPENAI_API_KEY="your_api_key_here"
$env:OPENAI_MODEL="gpt-4o-mini"
streamlit run app.py
```
Never commit API keys to GitHub. AI mode sends invoice text to the configured provider. Use only data you are authorized to share.

## Demo without an API key
Upload `samples/sample_invoice_1.txt` and `samples/sample_invoice_2.txt`. The local extractor recognizes the sample format and common invoice labels. For arbitrary invoice layouts, AI mode generally improves extraction, but every result should be reviewed.

## Scanned PDFs / OCR
This version extracts selectable PDF text. For scanned-image PDFs, install Tesseract OCR separately and extend `read_invoice_text()` with `pytesseract` and page rendering. The app reports when no selectable text is available rather than silently returning empty results.

## Project structure
```text
project_code/
├── app.py
├── extractor.py
├── schema.py
├── requirements.txt
├── .env.example
├── README.md
├── samples/
│   ├── sample_invoice_1.txt
│   └── sample_invoice_2.txt
└── tests/
    └── test_extractor.py
```

## Test
```powershell
python -m unittest discover -s tests -v
```

## Limitations
- Rule-based extraction is template-sensitive.
- Date formats and totals may vary between vendors.
- Scanned PDFs need OCR.
- AI extraction may occasionally misread values; manually verify totals and line items.
