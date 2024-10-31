from flask import Blueprint, render_template

public_bp = Blueprint('public', __name__)

# Rota para a página inicial pública
@public_bp.route('/')
def homepage():
    return render_template('homepage.html')
