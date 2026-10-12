from app import jobs
import copy
from app.db import db
from app.models import Document
from app.schemas import Invoice
from pydantic import ValidationError

def test_happy_path(monkeypatch, app, raw_invoice, make_db_row):
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
    
    make_db_row()
    monkeypatch.setattr(jobs, 'extract_from_file', mock_extract)
    jobs.run_job(1, app)
    with app.app_context():
        errors = []
        doc = db.session.get(Document, 1)
        
        if not doc.status == 'extracted':
            errors.append(f'doc status error={doc.status}')
        
        assert not errors, errors

def test_bad_invoice(monkeypatch, app, raw_invoice, make_db_row):
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
    
    make_db_row()
    monkeypatch.setattr(jobs, 'extract_from_file', mock_extract)
    jobs.run_job(1, app)
    with app.app_context():
        errors = []
        doc = db.session.get(Document, 1)
        
        if not doc.status == 'needs_review':
            errors.append(f'doc status error={doc.status}')
        
        if not doc.flags_JSON[0].startswith('error when computing total'):
            errors.append(f'error with {doc.flags_JSON=}')
        
        assert not errors, errors


def test_exception_handling(monkeypatch, app, make_db_row):
    def mock_extract(*args, **kwargs):
        raise FileNotFoundError('file not found')
    
    make_db_row()
    monkeypatch.setattr(jobs, 'extract_from_file', mock_extract)
    jobs.run_job(1, app)
    
    with app.app_context():    
        errors = []
        doc = db.session.get(Document, 1)
        
        if not doc.status == 'failed':
            errors.append(f'doc status error={doc.status}')
        if doc.input_tokens or doc.output_tokens:
            errors.append(f'token error {doc.output_tokens=}, {doc.input_tokens}')
        if doc.model_name:
            errors.append(f'model_name error {doc.model_name=}')
        if doc.cost:
            errors.append(f'cost error {doc.cost=}')
        if not doc.flags_JSON[0] == 'FileNotFoundError: file not found':
            errors.append(f'flags_JSON error {doc.flags_JSON=}')

        assert not errors, errors