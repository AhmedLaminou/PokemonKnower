"""
Database models for Pokémon Knower
Using SQLAlchemy with SQLite
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

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
