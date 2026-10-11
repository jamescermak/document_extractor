from decimal import Decimal
from datetime import date
from .schemas import Invoice

TOLERANCE = Decimal('0.01')

def validate_invoice(invoice: Invoice) -> list[str]:
    errors = []
    
    tax = invoice.tax
    actual_subtotal = invoice.subtotal
    line_items = invoice.line_items
    expected_subtotal = Decimal('0')
    
    for item in line_items:
        if abs((item.unit_price * item.quantity) - item.line_total) > TOLERANCE:
            errors.append(f'error computing line total for item {item.description}')

        expected_subtotal += (item.line_total)
    
    if abs(actual_subtotal - expected_subtotal) > TOLERANCE:
        errors.append(f'error when computing subtotal, {expected_subtotal=}, {actual_subtotal=}')
    
    expected_total = actual_subtotal + tax
    actual_total = invoice.total
    
    if abs(actual_total - expected_total) > TOLERANCE:
        errors.append(f'error when computing total, {expected_total=}, {actual_total=}')

    if invoice.date > date.today():
        errors.append(f'error when retrieving date; invoice date is in the future')
    
    return errors