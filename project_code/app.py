import io
import json
from datetime import datetime
import pandas as pd
import streamlit as st
from extractor import extract_invoice
from schema import Invoice

st.set_page_config(page_title="Invoice Data Extractor", page_icon="🧾", layout="wide")
st.title("🧾 Invoice Data Extractor")
st.caption("Upload invoice PDFs or text files, extract structured data, review it, and export to Excel.")

with st.sidebar:
    st.header("How it works")
    st.markdown("1. Upload invoice files\n2. Extract text from each file\n3. Convert text into structured JSON\n4. Review the results\n5. Export to Excel")
    st.info("For AI-powered extraction, add OPENAI_API_KEY to your environment. Without it, the app uses a local rule-based extractor.")
    st.caption("Do not upload confidential invoices to an AI service unless you are authorized to do so.")

uploads = st.file_uploader("Upload invoice files (PDF or TXT)", type=["pdf", "txt"], accept_multiple_files=True)
if "records" not in st.session_state:
    st.session_state.records = []

if st.button("Extract invoice data", type="primary", disabled=not uploads):
    records, errors = [], []
    progress = st.progress(0)
    for i, uploaded in enumerate(uploads):
        try:
            raw = uploaded.read()
            result = extract_invoice(uploaded.name, raw)
            # Validate against the fixed schema before displaying.
            validated = Invoice.model_validate(result)
            records.append(validated.model_dump())
        except Exception as exc:
            errors.append(f"{uploaded.name}: {exc}")
        progress.progress((i + 1) / len(uploads))
    st.session_state.records = records
    if records:
        st.success(f"Successfully processed {len(records)} invoice(s).")
    for error in errors:
        st.error(error)

records = st.session_state.records
if records:
    st.subheader("Extracted invoice data")
    summary_rows = []
    for item in records:
        summary_rows.append({
            "File": item["source_file"],
            "Invoice Number": item["invoice_number"],
            "Invoice Date": item["invoice_date"],
            "Vendor": item["vendor_name"],
            "Subtotal": item["subtotal"],
            "Tax": item["tax"],
            "Total": item["total"],
            "Currency": item["currency"]
        })
    st.dataframe(pd.DataFrame(summary_rows), use_container_width=True, hide_index=True)

    with st.expander("View line items and complete JSON"):
        for item in records:
            st.markdown(f"**{item['source_file']}**")
            if item["items"]:
                st.dataframe(pd.DataFrame(item["items"]), use_container_width=True, hide_index=True)
            else:
                st.caption("No line items were detected.")
            st.json(item)

    flat_items = []
    for inv in records:
        for line in inv["items"]:
            flat_items.append({
                "Source File": inv["source_file"],
                "Invoice Number": inv["invoice_number"],
                "Description": line["description"],
                "Quantity": line["quantity"],
                "Unit Price": line["unit_price"],
                "Line Total": line["line_total"]
            })
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        pd.DataFrame(summary_rows).to_excel(writer, index=False, sheet_name="Invoices")
        pd.DataFrame(flat_items, columns=["Source File", "Invoice Number", "Description", "Quantity", "Unit Price", "Line Total"]).to_excel(writer, index=False, sheet_name="Line Items")
    st.download_button("⬇️ Download Excel workbook", data=output.getvalue(),
                       file_name=f"invoices_{datetime.now():%Y%m%d_%H%M%S}.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    st.download_button("⬇️ Download JSON", data=json.dumps(records, indent=2),
                       file_name="extracted_invoices.json", mime="application/json")
else:
    st.info("Upload one or more sample invoices to get started.")
    st.markdown("Try the sample files in `samples/` after starting the application.")
