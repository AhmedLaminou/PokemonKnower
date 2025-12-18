"""
Migration script to import Pokémon data from CSV into SQLite database
Also scans for local images in static/images/{pokemon_name}/ folders
"""

import os
import csv
import sys
import re

# Add the project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from models import db, Pokemon, PokemonImage, PokemonType

# Configuration
CSV_PATH = 'pokemon.csv'
IMAGES_DIR = 'static/images'
POKEMON_DATA_DIR = os.environ.get('POKEMON_DATA_DIR', 'PokemonData')
DATABASE_PATH = 'pokemon.db'
MAX_POKEDEX_NUMBER = int(os.environ.get('MAX_POKEDEX_NUMBER', '151'))

def create_app():
    """Create Flask app for database context"""
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DATABASE_PATH}'
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
    """Import Pokémon data from CSV to database"""
    print("Starting CSV migration...")
    
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Clear existing data
        PokemonImage.query.delete()
        Pokemon.query.delete()
        db.session.commit()
        
        # Read CSV and import
        if not os.path.exists(CSV_PATH):
            print(f"Error: {CSV_PATH} not found!")
            return False
        
        with open(CSV_PATH, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            count = 0
            
            for row in reader:
                number = parse_int(row.get('number', 0))
                if number <= 0 or number > MAX_POKEDEX_NUMBER:
                    continue

                name = (row.get('pokemon_name', '') or '').strip()
                if not name:
                    continue

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
    """Scan static/images/ for Pokémon image folders and add to database"""
    print("Scanning for local Pokémon images...")
    
    with app.app_context():
        if not os.path.exists(IMAGES_DIR):
            os.makedirs(IMAGES_DIR, exist_ok=True)
        
        # Get all Pokémon from database
        pokemon_list = Pokemon.query.all()
        pokemon_by_name = {p.name.lower(): p for p in pokemon_list}
        pokemon_by_norm_name = {normalize_folder_name(p.name): p for p in pokemon_list}
        pokemon_by_number = {p.number: p for p in pokemon_list}
        
        image_count = 0

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
            pokemon_image = PokemonImage(
                pokemon_id=pokemon.id,
                filename=filename,
                path=img_path,
                is_primary=True,
                order=0
            )
            db.session.add(pokemon_image)
            image_count += 1
        
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
                    
                    pokemon_image = PokemonImage(
                        pokemon_id=pokemon.id,
                        filename=filename,
                        path=img_path,
                        is_primary=(idx == 0),
                        order=idx
                    )
                    db.session.add(pokemon_image)
                    image_count += 1

        scan_folder_tree(IMAGES_DIR, 'images')
        scan_folder_tree(POKEMON_DATA_DIR, 'pokedata')
        
        db.session.commit()
        print(f"Added {image_count} local images to database")

def seed_type_data(app):
    """Seed the Pokémon types table"""
    print("Seeding type data...")
    
    with app.app_context():
        PokemonType.query.delete()
        
        type_data = PokemonType.get_type_data()
        
        for name, data in type_data.items():
            ptype = PokemonType(
                name=name.capitalize(),
                color=data['color'],
                icon=data['icon']
            )
            db.session.add(ptype)
        
        db.session.commit()
        print(f"Added {len(type_data)} Pokémon types")

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
    print(f"Database created at: {DATABASE_PATH}")
    print("=" * 50)
    
    return True

if __name__ == '__main__':
    main()
