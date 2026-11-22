import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import unittest
from extractor import rule_based_extract
from schema import Invoice

class ExtractorTests(unittest.TestCase):
    def test_sample_invoice(self):
        text = (Path(__file__).resolve().parents[1] / "samples" / "sample_invoice_1.txt").read_text()
        data = rule_based_extract(text, "sample_invoice_1.txt")
        invoice = Invoice.model_validate(data)
        self.assertEqual(invoice.invoice_number, "INV-2026-001")
        self.assertEqual(invoice.total, 1758.20)
        self.assertEqual(len(invoice.items), 2)

if __name__ == "__main__":
    unittest.main()
