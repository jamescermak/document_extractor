from flask import Flask
from .routes import register_routes
from .db import db
from .models import Document
from .config import DevConfig

def create_app(Config=DevConfig):
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    
    with app.app_context():
        db.create_all()
    
    register_routes(app)
    return app
