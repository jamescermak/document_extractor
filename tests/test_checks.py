from app.checks import validate_invoice
from app.schemas import Invoice
import copy
from decimal import Decimal

def test_happy_path(raw_invoice):
      invoice = Invoice(**raw_invoice)
      errors = validate_invoice(invoice)
      assert not errors

def test_incorrect_total(raw_invoice):
    invoice_copy = copy.deepcopy(raw_invoice)
    invoice_copy['total'] = '10.00'
    invoice = Invoice(**invoice_copy)
    errors = validate_invoice(invoice)
    assert errors[0].startswith('error when computing total')

def test_one_cent_tolerance(raw_invoice):
    invoice_copy = copy.deepcopy(raw_invoice)
    total = invoice_copy['total']
    total = Decimal(total) - Decimal('0.01')
    invoice_copy['total'] = total
    invoice = Invoice(**invoice_copy)
    errors = validate_invoice(invoice)
    assert not errors
    