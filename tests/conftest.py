import pytest
from app import create_app
from app.config import TestConfig
from app.db import db
from app.models import Document
from datetime import datetime
from types import SimpleNamespace
import anthropic
import json
import os


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

@pytest.fixture
def claude_message():
    def mock_message(*, invoice, input_tokens, output_tokens, stop_reason, model):
        return SimpleNamespace(
            usage=SimpleNamespace(input_tokens=input_tokens, output_tokens=output_tokens),
            stop_reason=stop_reason,
            content=[anthropic.types.TextBlock(text=json.dumps(invoice), type='text')],
            model=model
        )
    yield mock_message


@pytest.fixture
def make_db_row(test_pdf, app):
    def make_row():
        original_filename = test_pdf.name
        file_path = os.path.abspath(test_pdf.name)
        doc_type = 'invoice'
        
        doc = Document(
            original_filename=original_filename,
            file_path=file_path,
            doc_type=doc_type,
            status='uploaded'
        )
        with app.app_context():
            db.session.add(doc)
            db.session.commit() 
    yield make_row