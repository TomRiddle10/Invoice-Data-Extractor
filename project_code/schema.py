from pydantic import BaseModel, Field, ConfigDict
from typing import List

class LineItem(BaseModel):
    model_config = ConfigDict(extra="ignore")
    description: str = ""
    quantity: float = 0.0
    unit_price: float = 0.0
    line_total: float = 0.0

class Invoice(BaseModel):
    model_config = ConfigDict(extra="ignore")
    source_file: str = "unknown"
    invoice_number: str = "NOT_FOUND"
    invoice_date: str = ""
    vendor_name: str = "Unknown Vendor"
    currency: str = ""
    subtotal: float = 0.0
    tax: float = 0.0
    total: float = 0.0
    items: List[LineItem] = Field(default_factory=list)
