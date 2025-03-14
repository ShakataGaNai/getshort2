import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    
    # Load configuration from environment variables
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-please-change-in-production')
    
    # Database configuration
    db_type = os.environ.get('DB_TYPE', 'sqlite')
    if db_type == 'sqlite':
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///getshort.db'
    else:
        # MySQL/MariaDB configuration
        db_user = os.environ.get('DB_USER')
        db_password = os.environ.get('DB_PASSWORD')
        db_host = os.environ.get('DB_HOST')
        db_name = os.environ.get('DB_NAME', 'getshort')
        
        # Use DATABASE_URL if provided, otherwise construct from individual settings
        app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
            'DATABASE_URL', 
            f'mysql+pymysql://{db_user}:{db_password}@{db_host}/{db_name}'
        )
    
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Initialize login manager
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    
    # Register blueprints
    from app.routes.main import main_bp
    from app.routes.admin import admin_bp
    from app.routes.auth import auth_bp
    from app.routes.api import api_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # Create database tables if they don't exist
    with app.app_context():
        db.create_all()
    
    return app