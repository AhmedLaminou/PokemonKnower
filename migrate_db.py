"""
Migration script to import Pokémon data from CSV into database.
Supports both SQLite (local dev) and PostgreSQL (production via DATABASE_URL).
Idempotent: safe to run multiple times (uses upsert logic).
Also scans for local images in static/images/ and PokemonData/ folders.
"""

import os
import csv
import sys
import re
from dotenv import load_dotenv

# Add the project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from models import db, Pokemon, PokemonImage, PokemonType

# Configuration
CSV_PATH = 'pokemon.csv'
IMAGES_DIR = 'static/images'
load_dotenv()
load_dotenv('.env.example', override=False)

def resolve_pokemon_data_dir() -> str:
    configured = (os.environ.get('POKEMON_DATA_DIR') or '').strip()
    if configured and os.path.isdir(configured):
        return configured
    if os.path.isdir('PokemonData'):
        return 'PokemonData'
    if os.path.isdir(os.path.join('static', 'images', 'PokemonData')):
        return os.path.join('static', 'images', 'PokemonData')
    return 'PokemonData'

POKEMON_DATA_DIR = resolve_pokemon_data_dir()
MAX_POKEDEX_NUMBER_RAW = (os.environ.get('MAX_POKEDEX_NUMBER', '') or '').strip()
MAX_POKEDEX_NUMBER = int(MAX_POKEDEX_NUMBER_RAW) if MAX_POKEDEX_NUMBER_RAW else None

def get_database_uri():
    """Get database URI from environment or default to SQLite"""
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
        return database_url
    return 'sqlite:///pokemon.db'

def create_app():
    """Create Flask app for database context"""
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = get_database_uri()
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    return app

def parse_int(value, default=0):
    """Safely parse integer from string"""
    try:
        return int(value) if value else default
    except (ValueError, TypeError):
        return default

def migrate_csv_data(app):
    """Import Pokémon data from CSV to database (idempotent upsert)"""
    print("Starting CSV migration...")
    
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Read CSV and import
        if not os.path.exists(CSV_PATH):
            print(f"Error: {CSV_PATH} not found!")
            return False
        
        with open(CSV_PATH, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            count = 0
            
            for row in reader:
                number = parse_int(row.get('number', 0))
                if number <= 0:
                    continue

                if MAX_POKEDEX_NUMBER and number > MAX_POKEDEX_NUMBER:
                    continue

                name = (row.get('pokemon_name', '') or '').strip()
                if not name:
                    continue

                # Upsert: update if exists, insert if not
                existing = Pokemon.query.filter_by(number=number).first()
                if existing:
                    existing.name = name
                    existing.main_type = row.get('main_type', 'Normal')
                    existing.secondary_type = row.get('secondary_type', '') or None
                    existing.region = row.get('region', 'Kanto')
                    existing.category = row.get('category', '')
                    existing.height = row.get('height', '')
                    existing.weight = row.get('weight', '')
                    existing.pokemon_family = row.get('pokemon_family', '')
                    existing.attack = parse_int(row.get('attack', 0))
                    existing.defense = parse_int(row.get('defense', 0))
                    existing.stamina = parse_int(row.get('stamina', 0))
                    existing.cp_range = row.get('cp_range', '')
                    existing.hp_range = row.get('hp_range', '')
                    existing.capture_rate = row.get('capture_rate', '')
                    existing.flee_rate = row.get('flee_rate', '')
                    existing.male_perc = row.get('male_perc', '')
                    existing.female_perc = row.get('female_perc', '')
                    existing.resistance = row.get('resistance', '')
                    existing.weakness = row.get('weakness', '')
                    existing.wild_avail = row.get('wild_avail', '')
                    existing.egg_avail = row.get('egg_avail', '')
                    existing.raid_avail = row.get('raid_avail', '')
                    existing.research_avail = row.get('research_avail', '')
                    existing.shiny = row.get('shiny', '')
                    existing.shadow = row.get('shadow', '')
                    existing.pokedex_desc = row.get('pkedex_desc', '')
                    existing.possible_attacks = row.get('poss_attacks', '')
                    existing.pic_url = row.get('pic_url', '')
                else:
                    pokemon = Pokemon(
                        number=number,
                        name=name,
                        main_type=row.get('main_type', 'Normal'),
                        secondary_type=row.get('secondary_type', '') or None,
                        region=row.get('region', 'Kanto'),
                        category=row.get('category', ''),
                        height=row.get('height', ''),
                        weight=row.get('weight', ''),
                        pokemon_family=row.get('pokemon_family', ''),
                        attack=parse_int(row.get('attack', 0)),
                        defense=parse_int(row.get('defense', 0)),
                        stamina=parse_int(row.get('stamina', 0)),
                        cp_range=row.get('cp_range', ''),
                        hp_range=row.get('hp_range', ''),
                        capture_rate=row.get('capture_rate', ''),
                        flee_rate=row.get('flee_rate', ''),
                        male_perc=row.get('male_perc', ''),
                        female_perc=row.get('female_perc', ''),
                        resistance=row.get('resistance', ''),
                        weakness=row.get('weakness', ''),
                        wild_avail=row.get('wild_avail', ''),
                        egg_avail=row.get('egg_avail', ''),
                        raid_avail=row.get('raid_avail', ''),
                        research_avail=row.get('research_avail', ''),
                        shiny=row.get('shiny', ''),
                        shadow=row.get('shadow', ''),
                        pokedex_desc=row.get('pkedex_desc', ''),
                        possible_attacks=row.get('poss_attacks', ''),
                        pic_url=row.get('pic_url', '')
                    )
                    db.session.add(pokemon)
                count += 1
            
            db.session.commit()
            print(f"Imported {count} Pokémon from CSV")
        
        return True

def normalize_folder_name(name: str) -> str:
    name = (name or '').strip().lower()
    name = name.replace('_', ' ').replace('-', ' ')
    name = re.sub(r"[^a-z0-9\s]", " ", name)
    name = ' '.join(name.split())
    return name

def scan_local_images(app):
    """Scan static/images/ for Pokémon image folders and add to database (idempotent)"""
    print("Scanning for local Pokémon images...")
    
    with app.app_context():
        if not os.path.exists(IMAGES_DIR):
            os.makedirs(IMAGES_DIR, exist_ok=True)
        
        # Clear existing images (will be re-scanned)
        PokemonImage.query.delete()
        db.session.commit()
        
        # Get all Pokémon from database
        pokemon_list = Pokemon.query.all()
        pokemon_by_name = {p.name.lower(): p for p in pokemon_list}
        pokemon_by_norm_name = {normalize_folder_name(p.name): p for p in pokemon_list}
        pokemon_by_number = {p.number: p for p in pokemon_list}
        
        image_count = 0

        # Track per-Pokémon ordering to avoid duplicate primaries when combining sources
        next_order_by_pokemon_id = {}

        def add_image(pokemon, filename: str, path: str):
            nonlocal image_count
            current_order = next_order_by_pokemon_id.get(pokemon.id, 0)
            pokemon_image = PokemonImage(
                pokemon_id=pokemon.id,
                filename=filename,
                path=path,
                is_primary=(current_order == 0),
                order=current_order,
            )
            db.session.add(pokemon_image)
            next_order_by_pokemon_id[pokemon.id] = current_order + 1
            image_count += 1

        # 1) Support flat numeric files directly in static/images (e.g. 1.jpeg -> Bulbasaur)
        valid_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.webp'}
        flat_files = [
            fn for fn in os.listdir(IMAGES_DIR)
            if os.path.isfile(os.path.join(IMAGES_DIR, fn))
        ]

        for filename in sorted(flat_files):
            ext = os.path.splitext(filename)[1].lower()
            if ext not in valid_extensions:
                continue

            stem = os.path.splitext(filename)[0]
            try:
                number = int(stem)
            except ValueError:
                continue

            pokemon = pokemon_by_number.get(number)
            if not pokemon:
                continue

            img_path = f"images/{filename}"
            add_image(pokemon, filename=filename, path=img_path)
        
        def scan_folder_tree(root_dir: str, path_prefix: str):
            nonlocal image_count

            if not os.path.exists(root_dir):
                return

            for folder_name in os.listdir(root_dir):
                folder_path = os.path.join(root_dir, folder_name)
                
                # Skip if not a directory
                if not os.path.isdir(folder_path):
                    continue
                
                # Try to match folder name to Pokémon
                pokemon_name = normalize_folder_name(folder_name)
                pokemon = pokemon_by_norm_name.get(pokemon_name)
                
                # Also try exact match
                if not pokemon:
                    pokemon = pokemon_by_name.get((folder_name or '').lower())
                
                if not pokemon:
                    continue
                
                # Scan images in the folder
                images = []
                
                for filename in os.listdir(folder_path):
                    ext = os.path.splitext(filename)[1].lower()
                    if ext in valid_extensions:
                        images.append(filename)
                
                # Sort images and add to database
                images.sort()
                
                for idx, filename in enumerate(images[:12]):  # Limit to 12 images per Pokémon
                    img_path = f"{path_prefix}/{folder_name}/{filename}"

                    add_image(pokemon, filename=filename, path=img_path)

        scan_folder_tree(IMAGES_DIR, 'images')
        scan_folder_tree(POKEMON_DATA_DIR, 'pokedata')
        
        db.session.commit()
        print(f"Added {image_count} local images to database")

def seed_type_data(app):
    """Seed the Pokémon types table (idempotent upsert)"""
    print("Seeding type data...")
    
    with app.app_context():
        type_data = PokemonType.get_type_data()
        count = 0
        
        for name, data in type_data.items():
            existing = PokemonType.query.filter_by(name=name.capitalize()).first()
            if existing:
                existing.color = data['color']
                existing.icon = data['icon']
            else:
                ptype = PokemonType(
                    name=name.capitalize(),
                    color=data['color'],
                    icon=data['icon']
                )
                db.session.add(ptype)
            count += 1
        
        db.session.commit()
        print(f"Synced {count} Pokémon types")

def main():
    """Run the full migration"""
    print("=" * 50)
    print("Pokémon Knower Database Migration")
    print("=" * 50)
    
    app = create_app()
    
    # Step 1: Migrate CSV data
    if not migrate_csv_data(app):
        print("Migration failed!")
        return False
    
    # Step 2: Seed type data
    seed_type_data(app)
    
    # Step 3: Scan for local images
    scan_local_images(app)
    
    print("=" * 50)
    print("Migration completed successfully!")
    print(f"Database URI: {get_database_uri()[:50]}...")
    print("=" * 50)
    
    return True

if __name__ == '__main__':
    main()
