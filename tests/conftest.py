import pytest
from app import create_app
from app.config import TestConfig
from datetime import datetime
from decimal import Decimal


@pytest.fixture
def app(tmp_path):
    app = create_app(TestConfig)
    app.config['UPLOAD_FOLDER'] = tmp_path
    yield app

@pytest.fixture
def client(app):
    yield app.test_client()
    
@pytest.fixture
def test_pdf(tmp_path):
    pdf_file = tmp_path / "test.pdf"
    pdf_file.write_bytes(b"%PDF-1.4 The Test PDF")
    with pdf_file.open('rb') as pdf:
        yield pdf
        
@pytest.fixture
def raw_lineitem():
    yield {
        'description': 'steak', 
        'quantity': 2, 
        'unit_price': '10.50', 
        'line_total': '21'  
    }
    
@pytest.fixture
def raw_invoice(raw_lineitem):
    yield {
        'vendor': 'Costco', 
        'date': datetime.now().date().isoformat(), 
        'line_items': [raw_lineitem], 
        'subtotal': '21.00', 
        'tax': '8.00', 
        'total': '29.00', 
        'currency': 'USD'
        }