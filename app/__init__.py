from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from authlib.integrations.flask_client import OAuth
from config import Config

# Inicializa o banco de dados
db = SQLAlchemy()

# Inicializa o OAuth para o Google SSO
oauth = OAuth()

def create_app():
    app = Flask(__name__)
    
    # Carrega as configurações do arquivo config.py
    app.config.from_object(Config)

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
    from app.auth import auth_bp  # Blueprint para autenticação (login/logout)
    from app.routes import main_bp  # Blueprint para rotas principais (exibição dos lançamentos)
    
    app.register_blueprint(auth_bp)  # Rotas de autenticação
    app.register_blueprint(main_bp)  # Rotas principais

    return app