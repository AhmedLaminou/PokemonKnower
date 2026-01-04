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
import json
from dotenv import load_dotenv

# Add the project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from models import db, Pokemon, PokemonImage, PokemonType

# Configuration
MAIN_CSV_PATH = os.path.join('Data', 'pokémon_with_stats', 'All_Pokemon.csv')
DESC_CSV_PATH = os.path.join('Data', '1025Pokémons', 'pokedex.csv')
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
        # Handle float strings like "53.0" by converting to float first
        return int(float(value)) if value else default
    except (ValueError, TypeError):
        return default

def parse_float(value, default=0.0):
    """Safely parse float from string"""
    try:
        return float(value) if value else default
    except (ValueError, TypeError):
        return default

def load_descriptions():
    """Load descriptions from pokedex.csv keyed by number"""
    descriptions = {}
    if not os.path.exists(DESC_CSV_PATH):
        print(f"Warning: {DESC_CSV_PATH} not found. Descriptions will be empty.")
        return descriptions
        
    try:
        with open(DESC_CSV_PATH, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # "id","name","height","weight","hp","attack","defense","s_attack","s_defense","speed","type","evo_set","info"
                # Some CSVs might handle numeric columns differently, handle strictly
                try:
                    num = parse_int(row.get('id') or row.get('number'))
                    desc = row.get('info') or row.get('description') or ''
                    if num > 0:
                        descriptions[num] = desc
                except Exception:
                    continue
    except Exception as e:
        print(f"Error reading description CSV: {e}")
        
    return descriptions

def clean_name(name):
    """Clean Pokémon name (e.g., remove special chars if needed)"""
    return (name or '').strip()

def migrate_csv_data(app):
    """Import Pokémon data from CSV to database (idempotent upsert)"""
    print("Starting CSV migration...")
    
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Load descriptions
        descriptions_map = load_descriptions()
        
        # Read Main CSV and import
        if not os.path.exists(MAIN_CSV_PATH):
            print(f"Error: {MAIN_CSV_PATH} not found!")
            return False
        
        with open(MAIN_CSV_PATH, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            count = 0
            
            for row in reader:
                # Number,Name,Type 1,Type 2,Abilities,HP,Att,Def,Spa,Spd,Spe,BST,...
                number = parse_int(row.get('Number', 0))
                if number <= 0:
                    continue

                if MAX_POKEDEX_NUMBER and number > MAX_POKEDEX_NUMBER:
                    continue

                name = clean_name(row.get('Name'))
                if not name:
                    continue

                # Parse Flags
                is_legendary = parse_float(row.get('Legendary', 0)) > 0
                is_mega = parse_float(row.get('Mega Evolution', 0)) > 0
                is_alolan = parse_float(row.get('Alolan Form', 0)) > 0
                is_galarian = parse_float(row.get('Galarian Form', 0)) > 0
                
                # Parse Stats
                hp = parse_int(row.get('HP', 0))
                att = parse_int(row.get('Att', 0))
                defense = parse_int(row.get('Def', 0))
                spa = parse_int(row.get('Spa', 0))
                spd = parse_int(row.get('Spd', 0))
                speed = parse_int(row.get('Spe', 0))
                bst = parse_int(row.get('BST', 0))
                
                height = str(row.get('Height', ''))
                weight = str(row.get('Weight', ''))
                
                # Abilities (clean string representation)
                abilities = row.get('Abilities', '')
                
                # Collect Type Effectiveness
                # Columns like "Against Normal", "Against Fire", etc.
                against = {}
                for key, val in row.items():
                    if key.startswith('Against '):
                        type_name = key.replace('Against ', '')
                        try:
                            multiplier = float(val)
                            if multiplier != 1.0: # Only save non-neutral
                                against[type_name] = multiplier
                        except:
                            pass
                            
                # Upsert: update if name matches (unique constraint is on name conceptually for us, though DB allows duplicates now)
                # We search by name to update specific forms
                existing = Pokemon.query.filter_by(name=name).first()
                if not existing:
                    # Fallback: maybe name changed? Unlikely for automated sync.
                    # Just create new
                    pokemon = Pokemon()
                else:
                    pokemon = existing

                # Set/Update fields
                pokemon.number = number
                pokemon.name = name
                pokemon.main_type = row.get('Type 1', 'Normal')
                pokemon.secondary_type = row.get('Type 2', '') or None
                pokemon.hp = hp
                pokemon.attack = att
                pokemon.defense = defense
                pokemon.sp_attack = spa
                pokemon.sp_defense = spd
                pokemon.speed = speed
                pokemon.bst = bst
                pokemon.height = height
                pokemon.weight = weight
                
                pokemon.generation = parse_float(row.get('Generation', 1))
                pokemon.catch_rate = parse_int(row.get('Catch Rate', 0))
                
                pokemon.is_legendary = is_legendary
                pokemon.is_mega = is_mega
                pokemon.is_alolan = is_alolan
                pokemon.is_galarian = is_galarian
                pokemon.abilities = abilities
                pokemon.against_types = json.dumps(against)
                
                # Description mapping (using Number)
                pokemon.pokedex_desc = descriptions_map.get(number, '')
                
                if not existing:
                    db.session.add(pokemon)
                
                count += 1
            
            db.session.commit()
            print(f"Imported {count} Pokémon/Forms from CSV")
        
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

        # Track per-Pokémon ordering 
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

        # 1) Support flat numeric files directly in static/images
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

            # Fallback for numeric files: prioritize "base" forms if possible
            # But here `pokemon_by_number` might point to Mega form if that was last in DB
            # We will just accept it for now as "good enough" for migration
            pokemon = pokemon_by_number.get(number)
            if not pokemon:
                continue

            img_path = f"images/{filename}"
            add_image(pokemon, filename=filename, path=img_path)
        
        # Scan folders matching names
        def scan_folder_tree(root_dir: str, path_prefix: str):
            nonlocal image_count

            if not os.path.exists(root_dir):
                return

            for folder_name in os.listdir(root_dir):
                folder_path = os.path.join(root_dir, folder_name)
                
                if not os.path.isdir(folder_path):
                    continue
                
                pokemon_name = normalize_folder_name(folder_name)
                pokemon = pokemon_by_norm_name.get(pokemon_name)
                
                if not pokemon:
                    pokemon = pokemon_by_name.get((folder_name or '').lower())
                
                if not pokemon:
                    continue
                
                images = []
                for filename in os.listdir(folder_path):
                    ext = os.path.splitext(filename)[1].lower()
                    if ext in valid_extensions:
                        images.append(filename)
                
                images.sort()
                
                for idx, filename in enumerate(images[:12]):
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
