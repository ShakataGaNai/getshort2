import os
from flask import Blueprint, redirect, url_for, request, session, current_app, flash
from flask_login import login_user, logout_user, current_user
import requests
from app import db
from app.models import User

auth_bp = Blueprint('auth', __name__)

# GitHub OAuth Configuration
GITHUB_CLIENT_ID = os.environ.get('GITHUB_CLIENT_ID')
GITHUB_CLIENT_SECRET = os.environ.get('GITHUB_CLIENT_SECRET')
GITHUB_AUTH_URL = 'https://github.com/login/oauth/authorize'
GITHUB_TOKEN_URL = 'https://github.com/login/oauth/access_token'
GITHUB_API_URL = 'https://api.github.com'

@auth_bp.route('/github')
def github_login():
    """Initiate GitHub OAuth flow"""
    if current_user.is_authenticated:
        return redirect(url_for('admin.dashboard'))
    
    github_auth_params = {
        'client_id': GITHUB_CLIENT_ID,
        'redirect_uri': url_for('auth.github_callback', _external=True),
        'scope': 'read:user user:email',
    }
    
    auth_url = f"{GITHUB_AUTH_URL}?client_id={github_auth_params['client_id']}&redirect_uri={github_auth_params['redirect_uri']}&scope={github_auth_params['scope']}"
    return redirect(auth_url)

@auth_bp.route('/github/callback')
def github_callback():
    """Handle GitHub OAuth callback"""
    code = request.args.get('code')
    
    # Exchange code for access token
    token_params = {
        'client_id': GITHUB_CLIENT_ID,
        'client_secret': GITHUB_CLIENT_SECRET,
        'code': code,
        'redirect_uri': url_for('auth.github_callback', _external=True)
    }
    
    token_response = requests.post(
        GITHUB_TOKEN_URL, 
        data=token_params,
        headers={'Accept': 'application/json'}
    )
    
    if token_response.status_code != 200:
        flash('Authentication failed', 'error')
        return redirect(url_for('main.index'))
    
    token_data = token_response.json()
    access_token = token_data.get('access_token')
    
    # Get user info from GitHub API
    headers = {
        'Authorization': f'token {access_token}',
        'Accept': 'application/json'
    }
    
    # Get user profile
    user_response = requests.get(f"{GITHUB_API_URL}/user", headers=headers)
    user_data = user_response.json()
    
    # Get user email
    email_response = requests.get(f"{GITHUB_API_URL}/user/emails", headers=headers)
    email_data = email_response.json()
    
    # Find primary email
    primary_email = None
    for email in email_data:
        if email.get('primary'):
            primary_email = email.get('email')
            break
    
    if not primary_email:
        flash('Could not retrieve email from GitHub', 'error')
        return redirect(url_for('main.index'))
    
    # Check if user exists, create if not
    user = db.session.execute(
        db.select(User).filter_by(github_id=user_data.get('id'))
    ).scalar_one_or_none()
    
    if not user:
        # Check if new user signups are allowed
        allow_signups = os.environ.get('ALLOW_SIGNUPS', 'true').lower() == 'true'
        
        if not allow_signups:
            flash('New user registration is currently disabled.', 'error')
            return redirect(url_for('main.index'))
            
        user = User(
            username=user_data.get('login'),
            email=primary_email,
            github_id=user_data.get('id'),
            avatar_url=user_data.get('avatar_url')
        )
        db.session.add(user)
        db.session.commit()
    
    # Log the user in
    login_user(user)
    
    # Redirect to admin dashboard
    return redirect(url_for('admin.dashboard'))

@auth_bp.route('/logout')
def logout():
    """Log the user out"""
    logout_user()
    return redirect(url_for('main.index'))