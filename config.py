import os
from dotenv import load_dotenv

# Carrega as variáveis do arquivo .env
load_dotenv()

class Config:
    # Pastas para upload dos arquivos
    UPLOAD_FOLDER_ESTATUTO = os.getenv("UPLOAD_FOLDER_ESTATUTO") 
    UPLOAD_FOLDER_AQUISICOES = os.getenv("UPLOAD_FOLDER_AQUISICOES")
    UPLOAD_FOLDER_OPORTUNIDADES = os.getenv("UPLOAD_FOLDER_OPORTUNIDADES")

    # Configurações do banco de dados
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
        # Chave secreta da aplicação
    SECRET_KEY = os.getenv('SECRET_KEY')
    
    # Configurações de sessão
    SESSION_TYPE = 'filesystem'
    SESSION_PERMANENT = False

    # Variáveis de ambiente do OAuth Google
    GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')

    # Armazenando a instância do cliente OAuth
    OAUTH_CLIENT = None