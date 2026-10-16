from sqlalchemy import select
from app import db
from app.models import Document
from app import routes
from app.schemas import Invoice
import threading
from datetime import datetime

class MockThread():
    def __init__(self, target, args, daemon):
        self.target = target
        self.args = args
    
    def start(self):
        self.target(*self.args)

def test_health_route(client):
    response = client.get('/health')
    assert '200 OK' == response.status
        
def test_upload(monkeypatch, client, app, test_pdf):
    job_list = []
    def mock_job(doc_id, *args, **kwargs):
        job_list.append(doc_id)    
    
    monkeypatch.setattr(threading, 'Thread', MockThread)
    monkeypatch.setattr(routes, 'run_job', mock_job)
    
    data = {
        'file': (test_pdf, 'test_filename.pdf'),
        'doc_type': 'invoice'
    }    
    response = client.post('/upload', data=data, content_type='multipart/form-data', follow_redirects=False)      
    
    with app.app_context():
        doc = db.session.execute(select(Document)).scalar_one()
        errors = []
        if not doc.status == 'uploaded':
            errors.append('doc status error')
        if not doc.id == 1:
            errors.append('doc id error')
        if not response.status_code == 302:
            errors.append(f'status code error, {response.status_code} != 302')
        if not len(job_list) == 1 or job_list[0] != doc.id:
            errors.append('error when calling run_job')
    
        assert not errors, 'errors occured:\n{}'.format('\n'.join(errors))


def test_documents_route(make_db_row, app, client, raw_invoice):
    make_db_row()
    with app.app_context():
        doc = db.session.get(Document, 1)
        doc.status = 'extracted'
        doc.extracted_JSON = Invoice(**raw_invoice).model_dump(mode='json')
        doc.flags_JSON = []
        db.session.commit()

    response = client.get('/documents/1')
    errors = []
    if not response.status == '200 OK':
        errors.append(f'error with response.status: got {response.status}, expected 200 OK')
    
    if not b'Costco' in response.data:
        errors.append(f'error rendering HTML, expected vendor name but None found')
    
    assert not errors, errors


def test_approve_route(make_db_row, app, client, raw_invoice):
    make_db_row()
    with app.app_context():
        doc = db.session.get(Document, 1)
        doc.status = 'extracted'
        doc.extracted_JSON = Invoice(**raw_invoice).model_dump(mode='json')
        doc.flags_JSON = []
        db.session.commit()
    
    data = {
        'new_vendor': 'Safeway',
        'new_date': datetime.now().date().isoformat(),
        'new_subtotal': '21.01',
        'new_tax': '8.00',
        'new_total': '29.00',
    }
    
    response = client.post('/documents/1/approve', data=data, follow_redirects=True)
    
    errors = []
    if not response.status == '200 OK':
        errors.append(f'response status error: got {response.status} expected \'200 OK\'')
    
    with app.app_context():
        doc = db.session.get(Document, 1)
        if not doc.status == 'approved':
            errors.append(f'doc status error: got {doc.status}, expected \'approved\'')

        if not ('vendor', 'Safeway') in doc.corrected_JSON.items():
            errors.append(f'corrected_JSON error: got (\'vendor\', {doc.corrected_JSON['vendor']}), expected (\'vendor\', \'Safeway\')')
        
    assert not errors

    
    

