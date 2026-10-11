from flask import jsonify, render_template, request, redirect, url_for
import os
from werkzeug.utils import secure_filename
from .models import Document
from .db import db
from werkzeug.exceptions import abort
import uuid
from .schemas import DOC_TO_SCHEMA, get_schema_from_doc
from .extraction import extract_from_file, MEDIA_TYPES
from .checks import validate_invoice

ALLOWED_EXTENSIONS = list(MEDIA_TYPES.keys())
ALLOWED_DOC_TYPES = list(DOC_TO_SCHEMA.keys())

def update_document(document, *, response):
        document.status=response['status']
        document.extracted_JSON=response['parsed_model'].model_dump(mode='json') if response['parsed_model'] else None
        document.flags_JSON=response['raw_errors']
        document.model_name=response['usage_record']['model']
        document.input_tokens=response['usage_record']['input_tokens']
        document.output_tokens=response['usage_record']['output_tokens']
        document.cost=response['usage_record']['cost_usd']
        document.latency_ms=response['usage_record']['latency_ms']

def register_routes(app):
    @app.route('/')
    def home():
        return render_template('upload.html')
    
    @app.route('/health', methods=['GET'])
    def check_health():
        return jsonify({'status code': '200'})
    
    @app.route('/upload', methods=['POST'])
    def upload():
        if 'file' not in request.files:
            abort(400, 'error uploading file')
        
        doc_type = request.form.get('doc_type')
        if doc_type not in ALLOWED_DOC_TYPES:
            abort(400, 'invalid doc type')
        
        file = request.files['file'] 
        original_filename = file.filename
        extension = os.path.splitext(original_filename)[1]
        if extension.lower() not in ALLOWED_EXTENSIONS:
            abort(400, 'invalid file type')
        
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        filename = f'{uuid.uuid4().hex}_{secure_filename(file.filename)}'
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        file.save(file_path)
        document = Document(
            original_filename=original_filename,
            file_path=file_path,
            doc_type=doc_type,
            status='uploaded'
        )
        
        response = extract_from_file(file_path=file_path, schema=get_schema_from_doc(doc_type))
        invoice = response['parsed_model']
        
        if invoice:
            errors = validate_invoice(response['parsed_model'])
            if errors:
                response['status'] = 'needs_review'
                for e in errors:
                    response['raw_errors'].append(e)
          
        update_document(document, response=response)
        
        db.session.add(document)
        db.session.commit()  

        return redirect(url_for('review', id=document.id))            
    
    @app.route('/review/<int:id>')
    def review(id):
        document = db.get_or_404(Document, id)
        return jsonify(document.id)