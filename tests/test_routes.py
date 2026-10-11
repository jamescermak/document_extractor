import pytest
from sqlalchemy import select
from app import db
from app.models import Document
from app import routes
from app.schemas import Invoice
import copy

def test_health_route(client):
    response = client.get('/health')
    assert '200 OK' == response.status
    

def test_upload(monkeypatch, client, app, test_pdf, raw_invoice):
    def mock_extract(*args, **kwargs):
        return {
            'parsed_model': Invoice(**raw_invoice),
            'attempt_count': 1,
            'raw_errors': [],
            'status': 'extracted',
            'usage_record': {
                'model': 'sample-claude-model',
                'input_tokens': 1000,
                'output_tokens': 1000,
                'cost_usd': 0.0004,
                'latency_ms': 3000
            }
        }
    
    monkeypatch.setattr(routes, 'extract_from_file', mock_extract)
    
    data = {
        'file': (test_pdf, 'test_filename.pdf'),
        'doc_type': 'invoice'
    }
    
    client.post('/upload', data=data, content_type='multipart/form-data', follow_redirects=True)  
    with app.app_context():
        errors = []
        doc = db.session.execute(select(Document)).scalar_one()
        
        if not doc.status == 'extracted':
            errors.append('doc status error')
        
        if not doc.original_filename == 'test_filename.pdf':
            errors.append('file name error')
        
        if not doc.model_name == 'sample-claude-model':
            errors.append('model name error') 
        
        assert not errors, 'errors occured:\n{}'.format('\n'.join(errors))


def test_bad_invoice(monkeypatch, client, app, test_pdf, raw_invoice):
    def mock_extract(*args, **kwargs):
        bad_invoice = copy.deepcopy(raw_invoice)
        bad_invoice['total'] = '5.00'
        return {
            'parsed_model': Invoice(**bad_invoice),
            'attempt_count': 1,
            'raw_errors': [],
            'status': 'extracted',
            'usage_record': {
                'model': 'sample-claude-model',
                'input_tokens': 1000,
                'output_tokens': 1000,
                'cost_usd': 0.0004,
                'latency_ms': 3000
            }
        }
    
    monkeypatch.setattr(routes, 'extract_from_file', mock_extract)
    
    data = {
        'file': (test_pdf, 'test_filename.pdf'),
        'doc_type': 'invoice'
    }
    
    client.post('/upload', data=data, content_type='multipart/form-data', follow_redirects=True)  
    with app.app_context():
        errors = []
        doc = db.session.execute(select(Document)).scalar_one()
        
        if not doc.status == 'needs_review':
            errors.append('doc status error')
        
        if not doc.original_filename == 'test_filename.pdf':
            errors.append('file name error')
        
        if not doc.model_name == 'sample-claude-model':
            errors.append('model name error') 
        
        if not ('error when computing total, expected_total=Decimal(\'29.00\'), actual_total=Decimal(\'5.00\')' in doc.flags_JSON): 
            errors.append('flags_JSON error')
        
        assert not errors, 'errors occured:\n{}'.format('\n'.join(errors))