from flask import Blueprint, redirect, url_for, session, flash, request, render_template, make_response
from app import oauth
from app.models import GrupoUsuario
import os

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login')
def login():
    redirect_uri = url_for('auth.auth_callback', _external=True)
    session['nonce'] = os.urandom(16).hex()
    session['state'] = os.urandom(16).hex()
    return oauth.google.authorize_redirect(redirect_uri, nonce=session['nonce'], state=session['state'])

@auth_bp.route('/auth/callback')
def auth_callback():
    state_in_request = request.args.get('state')
    if 'state' not in session or session.get('state') != state_in_request:
        session.clear()
        flash("Erro de CSRF: estado não corresponde! Tente novamente.", 'danger')
        return redirect(url_for('auth.login'))
    
    token = oauth.google.authorize_access_token()
    nonce = session.pop('nonce', None)
    
    if not nonce:
        return "Erro: Nonce ausente na sessão!", 400
    
    resp = oauth.google.parse_id_token(token, nonce=nonce)
    email = resp['email']
    
    usuario = GrupoUsuario.query.filter_by(email=email).first()
    if usuario is None:
        session.clear()
        flash('Seu email não está autorizado a acessar este sistema.', 'danger')
        return redirect(url_for('auth.error'))

    session['email'] = email
    session['grupo'] = usuario.grupo

    return redirect(url_for('admin.admin_homepage'))

@auth_bp.route('/error')
def error():
    return render_template('error.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    response = make_response(redirect(url_for('public.homepage')))
    response.set_cookie('session', '', expires=0)
    response.set_cookie('oauth_token', '', expires=0)
    return response
