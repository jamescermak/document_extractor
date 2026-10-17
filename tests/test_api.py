import pytest
from app.schemas import Invoice
from app.db import db
from app.models import Document
import json
from decimal import Decimal
import pydantic

def test_api_success(make_db_row, raw_invoice, app, client):
    make_db_row()
    with app.app_context():
        doc = db.session.get(Document, 1)
        doc.status = 'extracted'
        doc.extracted_JSON = Invoice(**raw_invoice).model_dump(mode='json')
        doc.flags_JSON = []
        doc.model_name = 'test-claude'
        doc.input_tokens = 100
        doc.output_tokens = 100
        doc.cost = Decimal('0.0068')
        doc.latency_ms = 4000.01
        db.session.commit()
    
    response = client.get('api/documents/1')
    data_dict = json.loads(response.get_data(as_text=True))


    errors = []
    
    if not data_dict['status'] == 'extracted':
        errors.append(f'status error: got {data_dict['status']}, expected \'extracted\'')
    
    if not data_dict['usage'] == {
        'model_name': 'test-claude',
        'input_tokens': 100,
        'output_tokens': 100,
        'cost': '0.0068',
        'latency': 4000.01
    }:
        errors.append(f'usage error')
    
    if not response.status == '200 OK':
        errors.append(f'response.status error: got {response.status}, expected \'200 OK\'')

    try:
        Invoice.model_validate(data_dict['data'])
    except pydantic.ValidationError:
        errors.append(f'JSON invoice data failed validation')
    
    
    
    assert not errors, errors


def test_api_missing(client):
    response = client.get('api/documents/1')
    
    errors = []
    if not response.status == '404 NOT FOUND':
        errors.append(f'response.status error, got {response.status}, expected \'404 NOT FOUND\'')
    
    if not json.loads(response.get_data(as_text=True))['error'] == 'Not Found':
        errors.append(f'JSON response error')
    
    assert not errors, errors