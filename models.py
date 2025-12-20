"""
Database models for Pokémon Knower
Using SQLAlchemy with SQLite (local) or PostgreSQL (production)
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class User(db.Model):
    """User model for authentication (linked to Stytch)"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    stytch_user_id = db.Column(db.String(255), unique=True, nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=True)
    avatar_url = db.Column(db.String(500), nullable=True)
    role = db.Column(db.String(50), default='user')  # 'user', 'admin'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship to donations
    donations = db.relationship('Donation', backref='user', lazy=True)
    
    @property
    def is_admin(self):
        return self.role == 'admin'
    
    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'avatar_url': self.avatar_url,
            'role': self.role,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class Donation(db.Model):
    """Track donations made via Stripe"""
    __tablename__ = 'donations'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    stripe_session_id = db.Column(db.String(255), unique=True, nullable=False)
    stripe_payment_intent_id = db.Column(db.String(255), nullable=True)
    amount = db.Column(db.Integer, nullable=False)  # Amount in cents
    currency = db.Column(db.String(10), default='usd')
    status = db.Column(db.String(50), default='pending')  # pending, succeeded, failed
    donor_email = db.Column(db.String(255), nullable=True)
    donor_name = db.Column(db.String(255), nullable=True)
    message = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'amount': self.amount / 100,  # Convert cents to dollars
            'currency': self.currency,
            'status': self.status,
            'donor_name': self.donor_name,
            'message': self.message,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

class Pokemon(db.Model):
    """Main Pokémon table with all stats and info"""
    __tablename__ = 'pokemon'
    
    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.Integer, unique=True, nullable=False)
    name = db.Column(db.String(100), unique=True, nullable=False)
    
    # Types
    main_type = db.Column(db.String(50), nullable=False)
    secondary_type = db.Column(db.String(50), nullable=True)
    
    # Basic Info
    region = db.Column(db.String(50), default='Kanto')
    category = db.Column(db.String(100))
    height = db.Column(db.String(20))  # e.g., "0.7 m"
    weight = db.Column(db.String(20))  # e.g., "6.9 kg"
    pokemon_family = db.Column(db.String(100))
    
    # Combat Stats (from Pokemon GO data)
    attack = db.Column(db.Integer, default=0)
    defense = db.Column(db.Integer, default=0)
    stamina = db.Column(db.Integer, default=0)
    
    # Game Info
    cp_range = db.Column(db.String(50))
    hp_range = db.Column(db.String(50))
    capture_rate = db.Column(db.String(10))
    flee_rate = db.Column(db.String(10))
    
    # Gender
    male_perc = db.Column(db.String(10))
    female_perc = db.Column(db.String(10))
    
    # Type effectiveness (stored as JSON strings)
    resistance = db.Column(db.Text)
    weakness = db.Column(db.Text)
    
    # Availability
    wild_avail = db.Column(db.String(100))
    egg_avail = db.Column(db.String(100))
    raid_avail = db.Column(db.String(100))
    research_avail = db.Column(db.String(100))
    shiny = db.Column(db.String(10))
    shadow = db.Column(db.String(10))
    
    # Description & Moves
    pokedex_desc = db.Column(db.Text)
    possible_attacks = db.Column(db.Text)
    
    # External image URL (from original CSV)
    pic_url = db.Column(db.String(500))
    
    # Relationship to images
    images = db.relationship('PokemonImage', backref='pokemon', lazy=True)
    
    def to_dict(self):
        """Convert to dictionary for JSON responses"""
        return {
            'id': self.id,
            'number': self.number,
            'name': self.name,
            'main_type': self.main_type,
            'secondary_type': self.secondary_type,
            'region': self.region,
            'category': self.category,
            'height': self.height,
            'weight': self.weight,
            'pokemon_family': self.pokemon_family,
            'attack': self.attack,
            'defense': self.defense,
            'stamina': self.stamina,
            'hp': self.stamina,  # Alias for compatibility
            'cp_range': self.cp_range,
            'hp_range': self.hp_range,
            'capture_rate': self.capture_rate,
            'flee_rate': self.flee_rate,
            'male_perc': self.male_perc,
            'female_perc': self.female_perc,
            'resistance': self.resistance,
            'weakness': self.weakness,
            'pokedex_desc': self.pokedex_desc,
            'possible_attacks': self.possible_attacks,
            'pic_url': self.pic_url,
            'images': [img.to_dict() for img in self.images]
        }


class PokemonImage(db.Model):
    """Store references to local Pokémon images for carousel"""
    __tablename__ = 'pokemon_images'
    
    id = db.Column(db.Integer, primary_key=True)
    pokemon_id = db.Column(db.Integer, db.ForeignKey('pokemon.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    path = db.Column(db.String(500), nullable=False)  # Relative path from static
    is_primary = db.Column(db.Boolean, default=False)
    order = db.Column(db.Integer, default=0)
    
    def to_dict(self):
        return {
            'id': self.id,
            'filename': self.filename,
            'path': self.path,
            'is_primary': self.is_primary,
            'order': self.order
        }


class Favorite(db.Model):
    """User's favorite Pokémon"""
    __tablename__ = 'favorites'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    pokemon_id = db.Column(db.Integer, db.ForeignKey('pokemon.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text, nullable=True)
    
    user = db.relationship('User', backref=db.backref('favorites', lazy=True))
    pokemon = db.relationship('Pokemon', backref=db.backref('favorited_by', lazy=True))
    
    __table_args__ = (db.UniqueConstraint('user_id', 'pokemon_id', name='unique_user_pokemon'),)
    
    def to_dict(self):
        return {
            'id': self.id,
            'pokemon_id': self.pokemon_id,
            'pokemon': self.pokemon.to_dict() if self.pokemon else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'notes': self.notes
        }


class Team(db.Model):
    """User's Pokémon teams"""
    __tablename__ = 'teams'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False, default='My Team')
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('teams', lazy=True))
    members = db.relationship('TeamMember', backref='team', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'members': [m.to_dict() for m in self.members],
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class TeamMember(db.Model):
    """Pokémon in a team (max 6)"""
    __tablename__ = 'team_members'
    
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'), nullable=False)
    pokemon_id = db.Column(db.Integer, db.ForeignKey('pokemon.id'), nullable=False)
    slot = db.Column(db.Integer, nullable=False)  # 1-6
    nickname = db.Column(db.String(50), nullable=True)
    
    pokemon = db.relationship('Pokemon')
    
    __table_args__ = (
        db.UniqueConstraint('team_id', 'slot', name='unique_team_slot'),
        db.CheckConstraint('slot >= 1 AND slot <= 6', name='valid_slot')
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'slot': self.slot,
            'nickname': self.nickname,
            'pokemon': self.pokemon.to_dict() if self.pokemon else None
        }


class QuizScore(db.Model):
    """Track quiz scores for leaderboard"""
    __tablename__ = 'quiz_scores'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    score = db.Column(db.Integer, nullable=False)
    total_questions = db.Column(db.Integer, nullable=False, default=10)
    quiz_type = db.Column(db.String(50), default='whos_that_pokemon')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('quiz_scores', lazy=True))
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_name': self.user.name if self.user else 'Anonymous',
            'score': self.score,
            'total_questions': self.total_questions,
            'percentage': round((self.score / self.total_questions) * 100, 1),
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class SiteStats(db.Model):
    """Track site usage statistics"""
    __tablename__ = 'site_stats'
    
    id = db.Column(db.Integer, primary_key=True)
    stat_date = db.Column(db.Date, nullable=False, unique=True)
    page_views = db.Column(db.Integer, default=0)
    unique_visitors = db.Column(db.Integer, default=0)
    scans_performed = db.Column(db.Integer, default=0)
    searches_performed = db.Column(db.Integer, default=0)
    new_users = db.Column(db.Integer, default=0)


class PokemonType(db.Model):
    """Reference table for Pokémon types with colors"""
    __tablename__ = 'pokemon_types'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    color = db.Column(db.String(7), nullable=False)  # Hex color
    icon = db.Column(db.String(50))  # Font Awesome icon class
    
    @staticmethod
    def get_type_data():
        """Return type data with colors"""
        return {
            'normal': {'color': '#A8A878', 'icon': 'fa-circle'},
            'fire': {'color': '#F08030', 'icon': 'fa-fire'},
            'water': {'color': '#6890F0', 'icon': 'fa-droplet'},
            'electric': {'color': '#F8D030', 'icon': 'fa-bolt'},
            'grass': {'color': '#78C850', 'icon': 'fa-leaf'},
            'ice': {'color': '#98D8D8', 'icon': 'fa-snowflake'},
            'fighting': {'color': '#C03028', 'icon': 'fa-hand-fist'},
            'poison': {'color': '#A040A0', 'icon': 'fa-skull-crossbones'},
            'ground': {'color': '#E0C068', 'icon': 'fa-mountain'},
            'flying': {'color': '#A890F0', 'icon': 'fa-feather'},
            'psychic': {'color': '#F85888', 'icon': 'fa-brain'},
            'bug': {'color': '#A8B820', 'icon': 'fa-bug'},
            'rock': {'color': '#B8A038', 'icon': 'fa-gem'},
            'ghost': {'color': '#705898', 'icon': 'fa-ghost'},
            'dragon': {'color': '#7038F8', 'icon': 'fa-dragon'},
            'dark': {'color': '#705848', 'icon': 'fa-moon'},
            'steel': {'color': '#B8B8D0', 'icon': 'fa-shield'},
            'fairy': {'color': '#EE99AC', 'icon': 'fa-star'}
        }
