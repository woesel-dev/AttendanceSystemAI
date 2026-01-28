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
    import os
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///attendance.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize database
    db.init_app(app)
    
    # Create tables
    with app.app_context():
        db.create_all()
        
        # Auto-Seed Logic
        from app.models import User
        try:
            if User.query.first() is None:
                print("Database empty, seeding automatically...")
                # Import here to avoid circular dependency
                from seed_db import seed_database
                # Pass the current app instance to avoid creating valid context inside
                seed_database(app)
                print("Database seeded automatically!")
        except Exception as e:
            print(f"Error during auto-seeding: {e}")
    
    # Register routes
    register_routes(app)
    
    return app
