from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)

    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///app.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'my_flask_app_secret_key')

    db.init_app(app)
    with app.app_context():
        from .models import Customer
        db.create_all()
    from app.routes import main as routes_blueprint
    app.register_blueprint(routes_blueprint)

    return app

