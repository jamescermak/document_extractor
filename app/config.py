import os

class Config:
    pass

class DevConfig(Config):
    DB_URL = os.getenv('DATABASE_URL', 'sqlite:///project.db')
    SQLALCHEMY_DATABASE_URI = DB_URL
    UPLOAD_FOLDER = 'uploads'
    
class TestConfig(Config):
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    TESTING = True