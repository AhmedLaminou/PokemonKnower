"""
Admin dashboard module
"""

from functools import wraps
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, session
from models import db, User, Donation, Pokemon, Favorite, Team, QuizScore, PokemonImage

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


def admin_required(f):
    """Decorator to require admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login', next=request.url))
        
        user = User.query.get(session['user_id'])
        if not user or not user.is_admin:
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function


@admin_bp.route('/')
@admin_required
def dashboard():
    """Admin dashboard home"""
    from datetime import datetime, timedelta
    from sqlalchemy import func
    
    # Basic stats
    total_users = User.query.count()
    total_donations = Donation.query.filter_by(status='succeeded').count()
    total_revenue = db.session.query(db.func.sum(Donation.amount)).filter_by(status='succeeded').scalar() or 0
    total_pokemon = Pokemon.query.count()
    total_images = PokemonImage.query.count()
    
    # User engagement stats
    total_favorites = Favorite.query.count()
    total_teams = Team.query.count()
    total_quiz_plays = QuizScore.query.count()
    
    # Users in last 7 days
    week_ago = datetime.utcnow() - timedelta(days=7)
    new_users_week = User.query.filter(User.created_at >= week_ago).count()
    active_users_week = User.query.filter(User.last_login >= week_ago).count()
    
    # Donations in last 30 days
    month_ago = datetime.utcnow() - timedelta(days=30)
    monthly_revenue = db.session.query(db.func.sum(Donation.amount)).filter(
        Donation.status == 'succeeded',
        Donation.created_at >= month_ago
    ).scalar() or 0
    
    # Average donation amount
    avg_donation = db.session.query(db.func.avg(Donation.amount)).filter_by(status='succeeded').scalar() or 0
    
    # Top favorited Pokemon
    top_favorited = db.session.query(
        Pokemon.name,
        Pokemon.number,
        func.count(Favorite.id).label('fav_count')
    ).join(Favorite).group_by(Pokemon.id).order_by(func.count(Favorite.id).desc()).limit(5).all()
    
    # Type distribution
    type_distribution = db.session.query(
        Pokemon.main_type,
        func.count(Pokemon.id).label('count')
    ).group_by(Pokemon.main_type).order_by(func.count(Pokemon.id).desc()).all()
    
    # Quiz stats
    avg_quiz_score = db.session.query(
        func.avg(QuizScore.score * 100.0 / QuizScore.total_questions)
    ).scalar() or 0
    
    # Recent donations
    recent_donations = Donation.query.filter_by(status='succeeded').order_by(Donation.created_at.desc()).limit(10).all()
    
    # Recent users
    recent_users = User.query.order_by(User.created_at.desc()).limit(10).all()
    
    # Admin users count
    admin_count = User.query.filter_by(role='admin').count()
    
    return render_template('admin/dashboard.html',
        total_users=total_users,
        total_donations=total_donations,
        total_revenue=total_revenue / 100,
        total_pokemon=total_pokemon,
        total_images=total_images,
        total_favorites=total_favorites,
        total_teams=total_teams,
        total_quiz_plays=total_quiz_plays,
        new_users_week=new_users_week,
        active_users_week=active_users_week,
        monthly_revenue=monthly_revenue / 100,
        avg_donation=avg_donation / 100,
        top_favorited=top_favorited,
        type_distribution=type_distribution,
        avg_quiz_score=avg_quiz_score,
        recent_donations=recent_donations,
        recent_users=recent_users,
        admin_count=admin_count
    )


@admin_bp.route('/users')
@admin_required
def users():
    """User management page"""
    page = request.args.get('page', 1, type=int)
    users = User.query.order_by(User.created_at.desc()).paginate(page=page, per_page=20)
    return render_template('admin/users.html', users=users)


@admin_bp.route('/users/<int:user_id>/toggle-admin', methods=['POST'])
@admin_required
def toggle_admin(user_id):
    """Toggle admin status for a user"""
    user = User.query.get_or_404(user_id)
    
    # Prevent removing own admin status
    if user.id == session['user_id']:
        return jsonify({'error': 'Cannot modify your own admin status'}), 400
    
    user.role = 'user' if user.role == 'admin' else 'admin'
    db.session.commit()
    
    return jsonify({'success': True, 'new_role': user.role})


@admin_bp.route('/donations')
@admin_required
def donations():
    """Donations management page"""
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '')
    
    query = Donation.query
    if status:
        query = query.filter_by(status=status)
    
    donations = query.order_by(Donation.created_at.desc()).paginate(page=page, per_page=20)
    return render_template('admin/donations.html', donations=donations, status_filter=status)
