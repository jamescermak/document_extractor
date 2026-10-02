import pytest
from sqlalchemy import select
from app import db
from app.models import Document

def test_health_route(client):
    response = client.get('/health')
    assert '200 OK' == response.status
    

def test_upload(client, app, test_pdf):
    data = {
        'file': (test_pdf, 'test_filename.pdf'),
        'doc_type': 'invoice'
    }
    
    client.post('/upload', data=data, content_type='multipart/form-data', follow_redirects=True)  
    
    with app.app_context():
        doc = db.session.execute(select(Document)).scalar_one()
        assert doc.status == 'uploaded' and doc.original_filename == 'test_filename.pdf'