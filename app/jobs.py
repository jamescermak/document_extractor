from .db import db
from .models import Document
from .extraction import extract_from_file
from .schemas import get_schema_from_doc
from .checks import validate_invoice
from sqlalchemy.exc import SQLAlchemyError
import logging

logger = logging.getLogger(__name__)

def update_document(document, *, response):
        document.status=response['status']
        document.extracted_JSON=response['parsed_model'].model_dump(mode='json') if response['parsed_model'] else None
        document.flags_JSON=response['raw_errors']
        document.model_name=response['usage_record']['model']
        document.input_tokens=response['usage_record']['input_tokens']
        document.output_tokens=response['usage_record']['output_tokens']
        document.cost=response['usage_record']['cost_usd']
        document.latency_ms=response['usage_record']['latency_ms']

def run_job(id, app):
    with app.app_context():
        document = db.session.get(Document, id)
        if not document:
            logger.warning(f'no record for document with id: {id}')
            return 
        try:
            document.status = 'processing'
            db.session.commit()
            
            file_path = document.file_path
            doc_type = document.doc_type
            
            response = extract_from_file(file_path=file_path, schema=get_schema_from_doc(doc_type))
            invoice = response['parsed_model']

            if invoice:
                errors = validate_invoice(response['parsed_model'])
                if errors:
                    response['status'] = 'needs_review'
                    for e in errors:
                        response['raw_errors'].append(e)
        
            update_document(document, response=response)
            db.session.commit()
        
        except Exception as e:
            logger.exception(str(e))
            db.session.rollback()
            document.status = 'failed'
            document.flags_JSON = [f'{e.__class__.__name__}: {e}']
            db.session.commit()
        
        

        
        
        