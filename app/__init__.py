from flask import Flask
import os

def create_app():
    app = Flask(__name__)

    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'my_flask_app_secret_key')

    from app.routes import main as routes_blueprint
    app.register_blueprint(routes_blueprint)
    
    return app

