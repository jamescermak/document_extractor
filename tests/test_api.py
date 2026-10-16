from app.schemas import Invoice
from app.db import db
from app.models import Document
import json

def test_api_success(make_db_row, raw_invoice, app, client):
    make_db_row()
    with app.app_context():
        doc = db.session.get(Document, 1)
        doc.extracted_JSON = Invoice(**raw_invoice).model_dump(mode='json')
        doc.flags_JSON = []
        db.session.commit()
    response = client.get('api/documents/1')
    data_dict = json.loads(response.get_data(as_text=True))

    errors = []
    if not data_dict['status'] == 'uploaded':
        errors.append(f'status error: got {data_dict['status']}, expected \'uploaded\'')
    
    if not response.status == '200 OK':
        errors.append(f'response.status error: got {response.status}, expected \'200 OK\'')
    
    assert not errors, errors


def test_api_missing(client):
    response = client.get('api/documents/1')
    assert response.status == '404 NOT FOUND'