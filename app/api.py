from .db import db
from .models import Document
from werkzeug.exceptions import NotFound
from flask import jsonify
import json

def register_api(app):
    @app.route('/api/documents/<int:id>', methods=['GET'])
    def GET_api(id):
        try:
            doc = db.get_or_404(Document, id)
        except NotFound:
            return jsonify({'error': 'Not Found'}), 404
        else:
            data = doc.to_dict()  
            return jsonify(data)