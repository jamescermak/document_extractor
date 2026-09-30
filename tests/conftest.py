import pytest
from app import create_app
from app.config import TestConfig


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