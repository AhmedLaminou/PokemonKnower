"""
Authentication module using Stytch
Supports: Magic Link + Google OAuth
"""

import os
from functools import wraps
from datetime import datetime
from flask import Blueprint, request, redirect, url_for, session, jsonify, render_template, current_app
import stytch

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# Stytch configuration (from environment variables)
STYTCH_PROJECT_ID = os.environ.get('STYTCH_PROJECT_ID', '')
STYTCH_SECRET = os.environ.get('STYTCH_SECRET', '')
STYTCH_ENV = os.environ.get('STYTCH_ENV', 'test')  # 'test' or 'live'

# Initialize Stytch client
stytch_client = None

def get_stytch_client():
    """Lazy initialization of Stytch client"""
    global stytch_client
    if stytch_client is None and STYTCH_PROJECT_ID and STYTCH_SECRET:
        # Stytch v9.x uses environment parameter as string: 'test' or 'live'
        stytch_client = stytch.Client(
            project_id=STYTCH_PROJECT_ID,
            secret=STYTCH_SECRET,
            environment=STYTCH_ENV  # 'test' or 'live'
        )
    return stytch_client


def get_base_url():
    """Get the base URL for callbacks"""
    return os.environ.get('BASE_URL', 'http://127.0.0.1:5000')


def login_required(f):
    """Decorator to require login for a route"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """Decorator to require admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login', next=request.url))
        
        from models import User
        user = User.query.get(session['user_id'])
        if not user or not user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated_function


def get_current_user():
    """Get the current logged-in user"""
    if 'user_id' not in session:
        return None
    from models import User
    return User.query.get(session['user_id'])


@auth_bp.route('/login')
def login():
    """Login page with magic link and Google OAuth options"""
    next_url = request.args.get('next', url_for('index'))
    return render_template('auth/login.html', next_url=next_url)


@auth_bp.route('/magic-link', methods=['POST'])
def send_magic_link():
    """Send magic link email"""
    client = get_stytch_client()
    if not client:
        return jsonify({'error': 'Auth not configured'}), 500
    
    email = request.form.get('email', '').strip().lower()
    if not email:
        return jsonify({'error': 'Email is required'}), 400
    
    next_url = request.form.get('next', url_for('index'))
    
    try:
        response = client.magic_links.email.login_or_create(
            email=email,
            login_magic_link_url=f"{get_base_url()}/auth/authenticate?next={next_url}",
            signup_magic_link_url=f"{get_base_url()}/auth/authenticate?next={next_url}",
        )
        return jsonify({'success': True, 'message': 'Check your email for the magic link!'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/google')
def google_login():
    """Redirect to Google OAuth"""
    client = get_stytch_client()
    if not client:
        return redirect(url_for('auth.login', error='Auth not configured'))
    
    next_url = request.args.get('next', url_for('index'))
    
    # Build the Google OAuth URL
    oauth_url = (
        f"https://{STYTCH_ENV}.stytch.com/v1/public/oauth/google/start"
        f"?public_token={STYTCH_PROJECT_ID}"
        f"&login_redirect_url={get_base_url()}/auth/oauth/callback?next={next_url}"
        f"&signup_redirect_url={get_base_url()}/auth/oauth/callback?next={next_url}"
    )
    
    return redirect(oauth_url)


@auth_bp.route('/authenticate')
def authenticate_magic_link():
    """Handle magic link callback"""
    from models import db, User
    
    client = get_stytch_client()
    if not client:
        return redirect(url_for('auth.login', error='Auth not configured'))
    
    token = request.args.get('token')
    next_url = request.args.get('next', url_for('index'))
    
    if not token:
        return redirect(url_for('auth.login', error='Invalid token'))
    
    try:
        response = client.magic_links.authenticate(token=token)
        stytch_user = response.user
        
        # Find or create user in our database
        user = User.query.filter_by(stytch_user_id=stytch_user.user_id).first()
        
        if not user:
            # Check if email already exists (shouldn't happen, but handle gracefully)
            user = User.query.filter_by(email=stytch_user.emails[0].email).first()
            if user:
                user.stytch_user_id = stytch_user.user_id
            else:
                user = User(
                    stytch_user_id=stytch_user.user_id,
                    email=stytch_user.emails[0].email,
                    name=stytch_user.name.first_name if stytch_user.name else None,
                )
                db.session.add(user)
        
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        # Set session
        session['user_id'] = user.id
        session['stytch_session_token'] = response.session_token
        
        return redirect(next_url)
    
    except Exception as e:
        return redirect(url_for('auth.login', error=str(e)))


@auth_bp.route('/oauth/callback')
def oauth_callback():
    """Handle OAuth callback (Google)"""
    from models import db, User
    
    client = get_stytch_client()
    if not client:
        return redirect(url_for('auth.login', error='Auth not configured'))
    
    token = request.args.get('token')
    next_url = request.args.get('next', url_for('index'))
    
    if not token:
        return redirect(url_for('auth.login', error='Invalid token'))
    
    try:
        response = client.oauth.authenticate(token=token)
        stytch_user = response.user
        
        # Find or create user in our database
        user = User.query.filter_by(stytch_user_id=stytch_user.user_id).first()
        
        email = stytch_user.emails[0].email if stytch_user.emails else None
        name = None
        avatar_url = None
        
        if stytch_user.name:
            name = f"{stytch_user.name.first_name or ''} {stytch_user.name.last_name or ''}".strip()
        
        # Try to get avatar from OAuth provider
        if hasattr(response, 'provider_values') and response.provider_values:
            avatar_url = getattr(response.provider_values, 'profile_picture_url', None)
        
        if not user:
            if email:
                user = User.query.filter_by(email=email).first()
            
            if user:
                user.stytch_user_id = stytch_user.user_id
                if name:
                    user.name = name
                if avatar_url:
                    user.avatar_url = avatar_url
            else:
                user = User(
                    stytch_user_id=stytch_user.user_id,
                    email=email,
                    name=name,
                    avatar_url=avatar_url,
                )
                db.session.add(user)
        else:
            if name:
                user.name = name
            if avatar_url:
                user.avatar_url = avatar_url
        
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        # Set session
        session['user_id'] = user.id
        session['stytch_session_token'] = response.session_token
        
        return redirect(next_url)
    
    except Exception as e:
        return redirect(url_for('auth.login', error=str(e)))


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration page"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password')
        name = request.form.get('name')
        
        # Validate input
        if not email or not password:
            return render_template('auth/register.html', error='Email and password required')
        
        client = get_stytch_client()
        if not client:
            return render_template('auth/register.html', error='Auth not configured')
        
        try:
            # Create user with password
            response = client.passwords.create(
                email=email,
                password=password,
                name=name,
                session_duration_minutes=60*24*7  # 1 week
            )
            
            # Create local user record
            from models import db, User
            user = User(
                stytch_user_id=response.user_id,
                email=email,
                name=name
            )
            db.session.add(user)
            db.session.commit()
            
            # Set session
            session['user_id'] = user.id
            session['stytch_session_token'] = response.session_token
            
            return redirect(url_for('index'))
        
        except Exception as e:
            return render_template('auth/register.html', error=str(e))
    
    return render_template('auth/register.html')


@auth_bp.route('/logout')
def logout():
    """Log out the current user"""
    client = get_stytch_client()
    
    # Revoke Stytch session if we have one
    if client and 'stytch_session_token' in session:
        try:
            client.sessions.revoke(session_token=session['stytch_session_token'])
        except:
            pass  # Ignore errors during logout
    
    session.clear()
    return redirect(url_for('index'))


@auth_bp.route('/me')
@login_required
def me():
    """Get current user info"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Not authenticated'}), 401
    return jsonify(user.to_dict())
