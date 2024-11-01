from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from authlib.integrations.flask_client import OAuth
from config import Config
import os

# Inicializa o banco de dados
db = SQLAlchemy()

# Inicializa o OAuth para o Google SSO
oauth = OAuth()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Carregar o diretório de uploads diretamente do .env
    app.config['UPLOAD_FOLDER_ESTATUTO'] = os.getenv('UPLOAD_FOLDER_ESTATUTO')

    # Inicializa as extensões
    db.init_app(app)
    oauth.init_app(app)

    # Registra o cliente OAuth do Google
    google = oauth.register(
        name='google',
        client_id=app.config['GOOGLE_CLIENT_ID'],
        client_secret=app.config['GOOGLE_CLIENT_SECRET'],
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={'scope': 'openid profile email'}
    )

    # Registrar blueprints
    from app.auth import auth_bp
    from app.routes import admin_bp
    from app.public import public_bp

    # Registra os blueprints com os caminhos específicos
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')  # Rotas de admin protegidas
    app.register_blueprint(public_bp)  # Rotas públicas para a homepage

    return app
