import os
from dotenv import load_dotenv

# Carrega as variáveis do arquivo .env
load_dotenv()

class Config:
    # Pasta para upload dos arquivos
    UPLOAD_FOLDER_ESTATUTO = os.getenv("UPLOAD_FOLDER_ESTATUTO")

    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.getenv('SECRET_KEY')
    
    # Configurações de sessão
    SESSION_TYPE = 'filesystem'  # Use 'filesystem' para manter as sessões persistentes
    SESSION_PERMANENT = False

    # Variáveis de ambiente do OAuth Google
    GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')

    # Armazenando a instância do cliente OAuth
    OAUTH_CLIENT = None