"""
Flask application initialization.
"""
from flask import Flask
from app.routes import register_routes
from app.models import db


def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'dev-secret-key-change-in-production'
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
    
    # Database configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///attendance.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize database
    db.init_app(app)
    
    # Create tables
    with app.app_context():
        db.create_all()
    
    # Register routes
    register_routes(app)
    
    return app
