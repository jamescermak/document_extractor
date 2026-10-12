from sqlalchemy import select
from app import db
from app.models import Document
from app import routes
import time
import threading

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

