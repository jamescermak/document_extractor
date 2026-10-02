from app.schemas import Invoice, LineItem, Receipt, get_schema_from_doc
from decimal import Decimal
import pytest
from datetime import datetime
import pydantic

def test_invoice(raw_invoice):
    invoice = Invoice.model_validate(raw_invoice)
    assert (isinstance(invoice.total, Decimal) and 
            isinstance(invoice.line_items[0], LineItem) and 
            invoice.date == datetime.now().date())

def test_missing_total(raw_invoice):
    raw_invoice.pop('total')
    with pytest.raises(pydantic.ValidationError):
        Invoice(**raw_invoice)

def test_coercion():
    data = dict(description='steak', quantity=2, unit_price='10.00', line_total='20.00')
    line_item = LineItem(**data)
    assert line_item.unit_price == Decimal('10.00') and line_item.line_total == Decimal('20.00')

def test_get_schema():
    assert get_schema_from_doc('invoice') == Invoice and get_schema_from_doc('receipt') == Receipt