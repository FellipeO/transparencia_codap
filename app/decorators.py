from functools import wraps
from flask import session, redirect, url_for

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Verifica se o usuário está logado (se a sessão contém o perfil do Google)
        if 'profile' not in session:
            return redirect(url_for('auth.login'))  # Redireciona para a página de login se não estiver autenticado
        return f(*args, **kwargs)
    return decorated_function