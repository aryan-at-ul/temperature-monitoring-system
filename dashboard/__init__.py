# dashboard/__init__.py
# This file makes the dashboard directory a Python package

from flask import Flask

def create_app(config_name='default'):
    """Create and configure the Flask application"""
    from config import config
    
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Import and register blueprints
    from routes.common import common_bp
    from routes.customer import customer_bp
    from routes.admin import admin_bp
    
    app.register_blueprint(common_bp)
    app.register_blueprint(customer_bp, url_prefix='/customer')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    
    return app