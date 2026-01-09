"""
Pokémon Knower - AI-Powered Pokédex
Flask Application with SQLite Database
"""

import os
import json
import numpy as np
import cv2
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify, redirect, url_for, send_from_directory, session
from flask_cors import CORS
from models import db, Pokemon, PokemonImage, PokemonType, User, Donation, Favorite, Team, TeamMember, QuizScore, Move, Ability, Badge, UserBadge
from battle_engine import BattleEngine
from ai_engine import PokemonIdentifier

load_dotenv()
load_dotenv('.env.example', override=False)

app = Flask(__name__)
CORS(app)

# Configuration
DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL:
    if DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pokemon.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'pokemon-knower-dev-secret-key')

MODEL_PATH = 'pokemon_classifier_model_V3.h5'
CLASS_INDICES_PATH = 'class_indices.json'
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

# Cache for evolution chains to avoid repeated external API calls
evolution_cache = {}

def get_evolution_chain_from_pokeapi(pokemon_id):
    """Fetch and parse evolution chain from PokeAPI"""
    try:
        import requests
        # 1. Get species data to find evolution chain URL
        species_res = requests.get(f'https://pokeapi.co/api/v2/pokemon-species/{pokemon_id}')
        if not species_res.ok:
            return None
            
        species_data = species_res.json()
        evolution_chain_url = species_data['evolution_chain']['url']
        
        # Check cache
        if evolution_chain_url in evolution_cache:
            return evolution_cache[evolution_chain_url]
            
        # 2. Get evolution chain data
        evo_res = requests.get(evolution_chain_url)
        if not evo_res.ok:
            return None
            
        evo_data = evo_res.json()
        chain = evo_data['chain']
        
        # 3. Parse into a flat list of connections for Mermaid
        # Structure: start -> end [label]
        connections = []
        
        def traverse_chain(node):
            current_name = node['species']['name'].capitalize()
            # Try to get ID from URL to match with local DB if needed, or just use name
            # url format: .../pokemon-species/1/
            current_id = int(node['species']['url'].split('/')[-2])
            
            for evolution in node['evolves_to']:
                target_name = evolution['species']['name'].capitalize()
                target_id = int(evolution['species']['url'].split('/')[-2])
                
                # Determine evolution method details
                details = evolution['evolution_details'][0] if evolution['evolution_details'] else {}
                trigger = details.get('trigger', {}).get('name', '')
                
                method_label = ""
                if trigger == 'level-up' and details.get('min_level'):
                    method_label = f"Lvl {details['min_level']}"
                elif trigger == 'use-item' and details.get('item'):
                    method_label = details['item']['name'].replace('-', ' ').title()
                elif trigger == 'trade':
                    method_label = "Trade"
                elif details.get('happiness'):
                    method_label = "High Friendship"
                else:
                    method_label = trigger.replace('-', ' ').title()
                    
                connections.append({
                    'source': current_name,
                    'source_id': current_id,
                    'target': target_name,
                    'target_id': target_id,
                    'label': method_label
                })
                
                traverse_chain(evolution)
                
        traverse_chain(chain)
        
        result = {'connections': connections}
        evolution_cache[evolution_chain_url] = result
        return result
        
    except Exception as e:
        print(f"Error fetching evolution: {e}")
        return None

@app.route('/api/pokemon/<int:pokemon_id>/evolution')
def get_pokemon_evolution(pokemon_id):
    """Get evolution chain for a Pokemon"""
    local_pokemon = Pokemon.query.get(pokemon_id)
    # If we have a huge local DB, we could try to infer, but PokeAPI is safer for structure
    # Use the 'number' from local DB which corresponds to PokeAPI ID usually
    if not local_pokemon:
        return jsonify({'error': 'Pokemon not found'}), 404
        
    # Use the Pokemon's number (dex ID) for PokeAPI
    data = get_evolution_chain_from_pokeapi(local_pokemon.number)
    
    if data:
        return jsonify(data)
    else:
        return jsonify({'error': 'Evolution data not available'}), 404

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

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Initialize database
db.init_app(app)

# Register blueprints
from auth import auth_bp, get_current_user
from donations import donations_bp
from admin import admin_bp

app.register_blueprint(auth_bp)
app.register_blueprint(donations_bp)
app.register_blueprint(admin_bp)

try:
    from chat import chat_bp
    app.register_blueprint(chat_bp)
except ImportError as e:
    print(f"Warning: Could not import chat module. Chat features will be disabled. Error: {e}")

# Context processor to make current_user available in all templates
@app.context_processor
def inject_user():
    return dict(current_user=get_current_user())

@app.route('/profile')
def profile():
    """User profile page with gamification stats"""
    user = get_current_user()
    if not user:
        return redirect(url_for('auth.login', next=request.url))
        
    teams = Team.query.filter_by(user_id=user.id).order_by(Team.updated_at.desc()).limit(5).all()
    favorites_count = Favorite.query.filter_by(user_id=user.id).count()
    
    
    return render_template('profile.html', user=user, teams=teams, favorites_count=favorites_count)

@app.route('/leaderboard')
def leaderboard_page():
    """Global XP leaderboard page"""
    # Get top 50 users by XP
    users = User.query.order_by(User.exp.desc()).limit(50).all()
    return render_template('leaderboard.html', users=users)

# Global variables
target_size = (224, 224)
model = None
class_labels = {}
tf_loaded = None

def ensure_tf_loaded():
    """Lazy load TensorFlow on first use"""
    global model, tf_loaded, target_size
    if tf_loaded is not None:
        return tf_loaded
    
    try:
        import tensorflow
        from tensorflow.keras.models import load_model as keras_load
        
        if os.path.exists(MODEL_PATH):
            print("Loading ML model...")
            try:
                import tensorflow as tf
                with tf.keras.utils.custom_object_scope({}):
                    model = keras_load(MODEL_PATH, compile=False)
            except Exception as e1:
                print(f"Model load failed: {e1}")
                tf_loaded = False
                return False
            
            input_shape = model.input_shape
            if input_shape and len(input_shape) == 4:
                target_size = (input_shape[1], input_shape[2])
            print(f"Model loaded successfully. Input size: {target_size}")
            tf_loaded = True
            return True
    except Exception as e:
        print(f"TensorFlow initialization error: {e}")
        tf_loaded = False
        return False

def load_class_labels():
    """Load class indices"""
    global class_labels
    if class_labels:
        return
    
    if os.path.exists(CLASS_INDICES_PATH):
        with open(CLASS_INDICES_PATH, 'r') as f:
            indices = json.load(f)
            class_labels = {v: k for k, v in indices.items()}
        print(f"Loaded {len(class_labels)} class labels")

# Load class labels on startup
load_class_labels()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def preprocess_image(image_path):
    """Preprocess image for model prediction"""
    global target_size
    try:
        from tensorflow.keras.preprocessing.image import img_to_array
        img = cv2.imread(image_path)
        if img is None:
            return None
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img = cv2.resize(img, target_size)
        img = img.astype("float") / 255.0
        img = img_to_array(img)
        img = np.expand_dims(img, axis=0)
        return img
    except Exception as e:
        print(f"Image preprocessing error: {e}")
        return None

def get_pokemon_by_name(name):
    """Get Pokémon from database by name (case-insensitive)"""
    return Pokemon.query.filter(Pokemon.name.ilike(name)).first()

def get_pokemon_by_number(number):
    """Get Pokémon from database by number"""
    return Pokemon.query.filter_by(number=number).first()

# ==================== ROUTES ====================

@app.route('/pokedata/<path:filename>')
def pokedata_file(filename):
    """Serve Pokémon images stored outside /static (e.g., PokemonData/<PokemonName>/...)"""
    return send_from_directory(POKEMON_DATA_DIR, filename)


def image_url(path: str) -> str:
    """Convert a stored image path into a URL usable in templates."""
    if not path:
        return ''
    if path.startswith('pokedata/'):
        return url_for('pokedata_file', filename=path[len('pokedata/'):])
    return url_for('static', filename=path)


@app.context_processor
def utility_processor():
    return {'image_url': image_url}

@app.route('/')
def index():
    """Netflix-style home page with hero carousel and browse rows"""
    from sqlalchemy.sql.expression import func
    
    # Get user streak for display
    user = get_current_user()
    user_streak = 0
    if user:
        from datetime import datetime, timedelta
        recent_scores = QuizScore.query.filter_by(user_id=user.id).order_by(QuizScore.created_at.desc()).limit(30).all()
        if recent_scores:
            streak = 0
            today = datetime.utcnow().date()
            for score in recent_scores:
                score_date = score.created_at.date()
                if score_date == today - timedelta(days=streak):
                    streak += 1
                else:
                    break
            user_streak = streak
    
    # Trending: Random selection of popular Pokemon (could be based on views/favorites later)
    trending_pokemon = Pokemon.query.order_by(func.random()).limit(12).all()
    
    # Legendary Pokemon (high stats, typically = legendary-like)
    legendary_pokemon = Pokemon.query.filter(
        (Pokemon.attack >= 120) | (Pokemon.sp_attack >= 120)
    ).order_by(Pokemon.attack.desc()).limit(12).all()
    
    # Electric Types
    electric_pokemon = Pokemon.query.filter(
        (Pokemon.main_type.ilike('electric')) | (Pokemon.secondary_type.ilike('electric'))
    ).order_by(func.random()).limit(12).all()
    
    # Fire Types
    fire_pokemon = Pokemon.query.filter(
        (Pokemon.main_type.ilike('fire')) | (Pokemon.secondary_type.ilike('fire'))
    ).order_by(func.random()).limit(12).all()
    
    return render_template('home.html',
                         user_streak=user_streak,
                         trending_pokemon=trending_pokemon,
                         legendary_pokemon=legendary_pokemon,
                         electric_pokemon=electric_pokemon,
                         fire_pokemon=fire_pokemon)


@app.route('/home-classic')
def index_classic():
    """Classic home page with search and scanner (legacy)"""
    return render_template('index.html')

@app.route('/about')
def about():
    """About page"""
    return render_template('about.html')


# Route aliases for navbar links
@app.route('/donate')
def donate():
    """Redirect to donations blueprint"""
    return redirect(url_for('donations.donate_page'))


@app.route('/admin-dashboard')
def admin_dashboard():
    """Redirect to admin blueprint"""
    return redirect(url_for('admin.dashboard'))

@app.route('/pokedex')
def pokedex():
    """Full Pokédex listing page"""
    page = request.args.get('page', 1, type=int)
    per_page = 24
    
    pokemon_list = Pokemon.query.order_by(Pokemon.number).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('pokedex.html', 
                         pokemon_list=pokemon_list.items,
                         pagination=pokemon_list,
                         types=PokemonType.get_type_data())

@app.route('/pokemon/')
def pokemon_list_redirect():
    """Redirect /pokemon/ to pokedex"""
    return redirect(url_for('pokedex'))

@app.route('/pokemon/<identifier>')
def pokemon_detail(identifier):
    """Detailed Pokémon page with card design and image carousel"""
    # Try to find by name first, then by number
    pokemon = get_pokemon_by_name(identifier)
    
    if not pokemon:
        try:
            number = int(identifier)
            pokemon = get_pokemon_by_number(number)
        except ValueError:
            pass
    
    if not pokemon:
        return render_template('404.html', message=f"Pokémon '{identifier}' not found"), 404
    
    # Get adjacent Pokémon for navigation
    prev_pokemon = Pokemon.query.filter(Pokemon.number < pokemon.number).order_by(Pokemon.number.desc()).first()
    next_pokemon = Pokemon.query.filter(Pokemon.number > pokemon.number).order_by(Pokemon.number.asc()).first()
    
    # Get local images for carousel
    images = PokemonImage.query.filter_by(pokemon_id=pokemon.id).order_by(PokemonImage.order).all()
    
    return render_template('pokemon_detail.html',
                         pokemon=pokemon,
                         images=images,
                         prev_pokemon=prev_pokemon,
                         next_pokemon=next_pokemon,
                         types=PokemonType.get_type_data())

@app.route('/api/pokemon/<identifier>')
def api_pokemon(identifier):
    """API endpoint to get Pokémon data as JSON"""
    pokemon = get_pokemon_by_name(identifier)
    
    if not pokemon:
        try:
            number = int(identifier)
            pokemon = get_pokemon_by_number(number)
        except ValueError:
            pass
    
    if not pokemon:
        return jsonify({'error': 'Pokémon not found'}), 404
    
    return jsonify(pokemon.to_dict())

@app.route('/api/pokemon/<int:pokemon_id>/images')
def api_pokemon_images(pokemon_id):
    """Get images for a specific Pokémon"""
    images = PokemonImage.query.filter_by(pokemon_id=pokemon_id).order_by(PokemonImage.order).all()
    return jsonify([img.to_dict() for img in images])

@app.route('/scan')
def scanner():
    """Real-time AR Scanner page"""
    return render_template('scanner.html')

@app.route('/search')
def search():
    """Search Pokémon with filters"""
    query = request.args.get('q', '').strip().lower()
    pokemon_type = request.args.get('type', '').strip().lower()
    min_attack = request.args.get('minAttack', type=int)
    min_defense = request.args.get('minDefense', type=int)
    min_stamina = request.args.get('minStamina', type=int)
    page = request.args.get('page', 1, type=int)
    per_page = 24
    
    # Build query
    filters = []
    
    if query:
        filters.append(Pokemon.name.ilike(f'%{query}%'))
    
    if pokemon_type:
        filters.append(
            (Pokemon.main_type.ilike(pokemon_type)) | 
            (Pokemon.secondary_type.ilike(pokemon_type))
        )
    
    if min_attack:
        filters.append(Pokemon.attack >= min_attack)
    
    if min_defense:
        filters.append(Pokemon.defense >= min_defense)
    
    if min_stamina:
        filters.append(Pokemon.hp >= min_stamina)
    
    # Execute query
    base_query = Pokemon.query
    if filters:
        from sqlalchemy import and_
        base_query = base_query.filter(and_(*filters))
    
    results = base_query.order_by(Pokemon.number).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'results': [p.to_dict() for p in results.items],
        'pagination': {
            'page': results.page,
            'total_pages': results.pages,
            'total': results.total,
            'has_next': results.has_next,
            'has_prev': results.has_prev
        }
    })

@app.route('/api/types')
def api_types():
    """Get all Pokémon types with colors"""
    return jsonify(PokemonType.get_type_data())

@app.route('/predict', methods=['POST'])
def predict():
    """Predict Pokémon from uploaded image"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type'}), 400
    
    filepath = None
    try:
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        filepath = os.path.join(UPLOAD_FOLDER, 'temp_upload.png')
        file.save(filepath)
        
        model_loaded = ensure_tf_loaded()
        
        if model_loaded and model is not None:

            print("Using ML model for prediction...")
            img = preprocess_image(filepath)
            
            # Local Prediction
            try:
                predictions = model.predict(img, verbose=0)
                predicted_idx = np.argmax(predictions[0])
                confidence = float(np.max(predictions[0])) * 100
                pokemon_name = class_labels.get(predicted_idx, 'Unknown')
                
                # Top 3 from local
                top_3_indices = np.argsort(predictions[0])[-3:][::-1]
                top_3 = []
                for idx in top_3_indices:
                    if idx in class_labels:
                        top_3.append({
                            'name': class_labels[idx],
                            'confidence': float(predictions[0][idx]) * 100
                        })
            except Exception as e:
                print(f"Local model error: {e}, forcing VLM fallback.")
                confidence = 0 # Force fallback
                
            is_shiny = False # Default for local model

                
            # HYBRID DECISION: If confidence is low (< 85%) or Unknown, use VLM
            if confidence < 85.0 or pokemon_name == 'Unknown':
                print(f"Low confidence ({confidence:.2f}%), switching to AI Vision...")
                identifier = PokemonIdentifier()
                vlm_result = identifier.identify_pokemon(filepath)
                
                if vlm_result and vlm_result.get('is_pokemon'):
                    print(f"VLM ID: {vlm_result['name']} ({vlm_result['confidence']}%)")
                    pokemon_name = vlm_result['name']
                    confidence = vlm_result['confidence']
                    is_shiny = vlm_result.get('is_shiny', False)
                    # Overwrite top_3 with VLM result as primary
                    top_3 = [{'name': pokemon_name, 'confidence': confidence}]
                else:
                    print("VLM could not identify or not a Pokemon.")
                    is_shiny = False
        else:
            # Model not loaded, go straight to VLM
            print("Local model not loaded, using AI Vision...")
            identifier = PokemonIdentifier()
            vlm_result = identifier.identify_pokemon(filepath)
            
            if vlm_result and vlm_result.get('is_pokemon'):
                pokemon_name = vlm_result['name']
                confidence = vlm_result['confidence']
                is_shiny = vlm_result.get('is_shiny', False)
                top_3 = [{'name': pokemon_name, 'confidence': confidence}]
            else:
                pokemon_name = 'Unknown'
                confidence = 0.0
                is_shiny = False
                top_3 = []
        
        # Get Pokémon data from database
        pokemon = get_pokemon_by_name(pokemon_name)
        pokemon_data = pokemon.to_dict() if pokemon else None
        
        # Gamification: Award XP for successful scan
        xp_data = {}
        user = get_current_user()
        if user and confidence > 70:
            xp_amount = 50
            # Bonus for finding shiny
            if is_shiny:
                xp_amount += 100
                
            xp_result = award_xp(user, xp_amount, " Pokémon Scan")
            new_badges = check_achievements(user)
            
            xp_data = {
                'xp_earned': xp_amount,
                'leveled_up': xp_result['leveled_up'],
                'new_level': xp_result['new_level'],
                'new_badges': new_badges
            }
        
        return jsonify({
            'name': pokemon_name,
            'confidence': round(confidence, 2),
            'is_shiny': is_shiny,
            'top_3': top_3,
            'pokemon': pokemon_data,
            'gamification': xp_data
        })
        
    except Exception as e:
        print(f"Prediction error: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        if filepath and os.path.exists(filepath):
            os.remove(filepath)

@app.route('/api/leaderboard/xp')
def api_xp_leaderboard():
    """Get global XP leaderboard"""
    users = User.query.order_by(User.exp.desc()).limit(20).all()
    return jsonify([{
        'name': u.name or u.email.split('@')[0],
        'avatar_url': u.avatar_url,
        'level': u.level,
        'exp': u.exp,
        'badges_count': len(u.earned_badges)
    } for u in users])

@app.route('/api/random')
def random_pokemon():
    """Get a random Pokémon"""
    from sqlalchemy.sql.expression import func
    pokemon = Pokemon.query.order_by(func.random()).first()
    if pokemon:
        return jsonify(pokemon.to_dict())
    return jsonify({'error': 'No Pokémon found'}), 404

@app.route('/api/stats')
def api_stats():
    """Get database statistics"""
    total_pokemon = Pokemon.query.count()
    total_images = PokemonImage.query.count()
    types = db.session.query(Pokemon.main_type, db.func.count(Pokemon.id)).group_by(Pokemon.main_type).all()
    
    return jsonify({
        'total_pokemon': total_pokemon,
        'total_images': total_images,
        'types_distribution': {t: c for t, c in types}
    })

# ==================== FAVORITES ====================

@app.route('/favorites')
def favorites_page():
    """User's favorites page"""
    user = get_current_user()
    if not user:
        return redirect(url_for('auth.login', next=request.url))
    
    favorites = Favorite.query.filter_by(user_id=user.id).order_by(Favorite.created_at.desc()).all()
    return render_template('favorites.html', favorites=favorites)

@app.route('/api/favorites', methods=['GET'])
def api_get_favorites():
    """Get user's favorites"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Login required'}), 401
    
    favorites = Favorite.query.filter_by(user_id=user.id).all()
    return jsonify([f.to_dict() for f in favorites])

@app.route('/api/favorites/<int:pokemon_id>', methods=['POST'])
def api_add_favorite(pokemon_id):
    """Add a Pokemon to favorites"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Login required'}), 401
    
    pokemon = Pokemon.query.get(pokemon_id)
    if not pokemon:
        return jsonify({'error': 'Pokemon not found'}), 404
    
    existing = Favorite.query.filter_by(user_id=user.id, pokemon_id=pokemon_id).first()
    if existing:
        return jsonify({'error': 'Already in favorites'}), 400
    
    favorite = Favorite(user_id=user.id, pokemon_id=pokemon_id)
    db.session.add(favorite)
    
    # Gamification: Award XP
    xp_result = award_xp(user, 10, "Added Favorite")
    new_badges = check_achievements(user)
    
    db.session.commit()
    
    response = {
        'success': True, 
        'favorite': favorite.to_dict(),
        'xp_earned': 10,
        'leveled_up': xp_result['leveled_up'],
        'new_badges': new_badges
    }
    
    return jsonify(response)

@app.route('/api/favorites/<int:pokemon_id>', methods=['DELETE'])
def api_remove_favorite(pokemon_id):
    """Remove a Pokemon from favorites"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Login required'}), 401
    
    favorite = Favorite.query.filter_by(user_id=user.id, pokemon_id=pokemon_id).first()
    if not favorite:
        return jsonify({'error': 'Not in favorites'}), 404
    
    db.session.delete(favorite)
    db.session.commit()
    
    return jsonify({'success': True})

@app.route('/api/favorites/check/<int:pokemon_id>')
def api_check_favorite(pokemon_id):
    """Check if Pokemon is in favorites"""
    user = get_current_user()
    if not user:
        return jsonify({'is_favorite': False})
    
    is_fav = Favorite.query.filter_by(user_id=user.id, pokemon_id=pokemon_id).first() is not None
    return jsonify({'is_favorite': is_fav})

# ==================== TEAM BUILDER ====================

@app.route('/team-builder')
def team_builder():
    """Team builder page"""
    user = get_current_user()
    teams = []
    if user:
        teams = Team.query.filter_by(user_id=user.id).order_by(Team.updated_at.desc()).all()
    
    pokemon_list = Pokemon.query.order_by(Pokemon.number).all()
    return render_template('team_builder.html', teams=teams, pokemon_list=pokemon_list, types=PokemonType.get_type_data())

@app.route('/api/teams', methods=['GET'])
def api_get_teams():
    """Get user's teams"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Login required'}), 401
    
    teams = Team.query.filter_by(user_id=user.id).all()
    return jsonify([t.to_dict() for t in teams])

@app.route('/api/teams', methods=['POST'])
def api_create_team():
    """Create a new team"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Login required'}), 401
    
    data = request.get_json()
    team = Team(
        user_id=user.id,
        name=data.get('name', 'My Team'),
        description=data.get('description', '')
    )
    db.session.add(team)
    db.session.commit()
    
    return jsonify({'success': True, 'team': team.to_dict()})

@app.route('/api/teams/<int:team_id>', methods=['PUT'])
def api_update_team(team_id):
    """Update team details or members"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Login required'}), 401
    
    team = Team.query.filter_by(id=team_id, user_id=user.id).first()
    if not team:
        return jsonify({'error': 'Team not found'}), 404
    
    data = request.get_json()
    
    if 'name' in data:
        team.name = data['name']
    if 'description' in data:
        team.description = data['description']
    
    if 'members' in data:
        TeamMember.query.filter_by(team_id=team.id).delete()
        for member_data in data['members']:
            if member_data.get('pokemon_id'):
                member = TeamMember(
                    team_id=team.id,
                    pokemon_id=member_data['pokemon_id'],
                    slot=member_data['slot'],
                    nickname=member_data.get('nickname')
                )
                db.session.add(member)
    
    db.session.commit()
    return jsonify({'success': True, 'team': team.to_dict()})

@app.route('/api/teams/<int:team_id>', methods=['DELETE'])
def api_delete_team(team_id):
    """Delete a team"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Login required'}), 401
    
    team = Team.query.filter_by(id=team_id, user_id=user.id).first()
    if not team:
        return jsonify({'error': 'Team not found'}), 404
    
    db.session.delete(team)
    db.session.commit()
    
    return jsonify({'success': True})

@app.route('/api/team-analysis', methods=['POST'])
def api_team_analysis():
    """Analyze team type coverage"""
    data = request.get_json()
    pokemon_ids = data.get('pokemon_ids', [])
    
    if not pokemon_ids:
        return jsonify({'error': 'No Pokemon provided'}), 400
    
    pokemon_list = Pokemon.query.filter(Pokemon.id.in_(pokemon_ids)).all()
    
    type_coverage = {}
    weaknesses = {}
    resistances = {}
    
    all_types = list(PokemonType.get_type_data().keys())
    
    for t in all_types:
        type_coverage[t] = 0
        weaknesses[t] = 0
        resistances[t] = 0
    
    for p in pokemon_list:
        if p.main_type:
            type_coverage[p.main_type.lower()] = type_coverage.get(p.main_type.lower(), 0) + 1
        if p.secondary_type:
            type_coverage[p.secondary_type.lower()] = type_coverage.get(p.secondary_type.lower(), 0) + 1
    
    return jsonify({
        'type_coverage': type_coverage,
        'team_size': len(pokemon_list),
        'pokemon': [p.to_dict() for p in pokemon_list]
    })

# ==================== TYPE CHART ====================

@app.route('/type-chart')
def type_chart():
    """Interactive type effectiveness chart"""
    return render_template('type_chart.html', types=PokemonType.get_type_data())

# ==================== QUIZ ====================

@app.route('/quiz')
def quiz_page():
    """Who's That Pokemon quiz"""
    return render_template('quiz.html')

@app.route('/api/quiz/question')
def api_quiz_question():
    """Get a random quiz question"""
    from sqlalchemy.sql.expression import func
    
    correct = Pokemon.query.order_by(func.random()).first()
    if not correct:
        return jsonify({'error': 'No Pokemon available'}), 404
    
    wrong = Pokemon.query.filter(Pokemon.id != correct.id).order_by(func.random()).limit(3).all()
    
    options = [correct] + wrong
    import random
    random.shuffle(options)
    
    return jsonify({
        'pokemon_id': correct.id,
        'pokemon_number': correct.number,
        'options': [{'id': p.id, 'name': p.name} for p in options]
    })

@app.route('/api/quiz/submit', methods=['POST'])
def api_quiz_submit():
    """Submit quiz score and award XP"""
    user = get_current_user()
    data = request.get_json()
    
    start_score = data.get('score', 0)
    total = data.get('total', 10)
    
    score = QuizScore(
        user_id=user.id if user else None,
        score=start_score,
        total_questions=total
    )
    db.session.add(score)
    
    response = {'success': True, 'score': score.to_dict()}
    
    # Award XP and check badges if logged in
    if user:
        # Base XP = score * 10
        xp_amount = start_score * 10
        xp_result = award_xp(user, xp_amount, "Quiz Completion")
        
        # Check for new badges
        new_badges = check_achievements(user)
        
        response.update({
            'xp_earned': xp_amount,
            'leveled_up': xp_result['leveled_up'],
            'new_level': xp_result['new_level'],
            'new_badges': new_badges
        })
        
        # Update streak if perfect score
        if start_score == total:
             # Logic handled in streak calculation usually, but could grant bonus here
             pass
    
    db.session.commit()
    return jsonify(response)

@app.route('/api/quiz/leaderboard')
def api_quiz_leaderboard():
    """Get quiz leaderboard"""
    scores = QuizScore.query.filter(QuizScore.user_id.isnot(None)).order_by(
        (QuizScore.score * 100 / QuizScore.total_questions).desc(),
        QuizScore.created_at.desc()
    ).limit(20).all()
    
    return jsonify([s.to_dict() for s in scores])

@app.route('/api/user/streak')
def api_user_streak():
    """Calculate user's daily play streak"""
    user = get_current_user()
    if not user:
        return jsonify({'streak': 0, 'played_today': False})
    
    from sqlalchemy import func, cast, Date
    from datetime import date, timedelta
    
    # Get all unique dates the user played a quiz
    # SQLite vs Postgres date extraction difference handled roughly here or via ORM
    # For SQLite cast to Date works if stored accurately, otherwise might need string manip
    # But let's try a simpler approach retrieving dates and processing in python for reliability across DBs
    
    scores = QuizScore.query.filter_by(user_id=user.id).order_by(QuizScore.created_at.desc()).all()
    
    if not scores:
        return jsonify({'streak': 0, 'played_today': False})
    
    played_dates = sorted(list(set(s.created_at.date() for s in scores)), reverse=True)
    
    if not played_dates:
        return jsonify({'streak': 0, 'played_today': False})
        
    today = date.today()
    played_today = played_dates[0] == today
    
    current_streak = 0
    check_date = today 
    
    # If they haven't played today, we check if they played yesterday to keep the streak alive
    # If they played today, we start counting from today
    # If they missed yesterday (and today), streak is 0 (unless we are generous and day didn't end)
    
    # Logic:
    # 1. Check if today is present. If yes, streak += 1, check yesterday.
    # 2. If today not present, check yesterday. If yes, streak relates to previous run?
    # Actually simpler: Look for consecutive days starting from today OR yesterday.
    
    if played_today:
        check_date = today
    elif played_dates[0] == today - timedelta(days=1):
        check_date = today - timedelta(days=1)
    else:
        # Last play was before yesterday -> Streak broken
        return jsonify({'streak': 0, 'played_today': False})
        
    for d in played_dates:
        if d == check_date:
            current_streak += 1
            check_date -= timedelta(days=1)
        elif d > check_date:
            continue # Should not happen if sorted desc unique
        else:
            break # Gap found
            
    return jsonify({
        'streak': current_streak,
        'played_today': played_today,
        'last_played': played_dates[0].isoformat()
    })

# ==================== COMPARISON TOOL ====================

@app.route('/api/team/analyze', methods=['POST'])
def api_analyze_custom():
    """Analyze an ad-hoc team list"""
    data = request.json
    member_ids = data.get('members', [])
    
    if not member_ids:
        return jsonify({'error': 'No members provided'}), 400
        
    members = Pokemon.query.filter(Pokemon.id.in_(member_ids)).all()
    
    return analyze_pokemon_list(members)

@app.route('/api/team/analysis/<int:team_id>')
def api_team_analysis_saved(team_id):
    """Analyze team coverage and stats"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Login required'}), 401
        
    team = Team.query.get_or_404(team_id)
    if team.user_id != user.id:
        return jsonify({'error': 'Unauthorized'}), 403
        
    members = [m.pokemon for m in team.members]
    return analyze_pokemon_list(members)

def analyze_pokemon_list(pokemon_list):
    """Helper to analyze a list of Pokemon objects with advanced metrics"""
    types = ['normal', 'fire', 'water', 'electric', 'grass', 'ice', 'fighting', 'poison', 'ground', 
             'flying', 'psychic', 'bug', 'rock', 'ghost', 'dragon', 'dark', 'steel', 'fairy']
    
    # Type effectiveness chart for offensive coverage (attacker type -> defender type -> multiplier)
    type_chart = {
        'normal': {'rock': 0.5, 'ghost': 0, 'steel': 0.5},
        'fire': {'fire': 0.5, 'water': 0.5, 'grass': 2, 'ice': 2, 'bug': 2, 'rock': 0.5, 'dragon': 0.5, 'steel': 2},
        'water': {'fire': 2, 'water': 0.5, 'grass': 0.5, 'ground': 2, 'rock': 2, 'dragon': 0.5},
        'electric': {'water': 2, 'electric': 0.5, 'grass': 0.5, 'ground': 0, 'flying': 2, 'dragon': 0.5},
        'grass': {'fire': 0.5, 'water': 2, 'grass': 0.5, 'poison': 0.5, 'ground': 2, 'flying': 0.5, 'bug': 0.5, 'rock': 2, 'dragon': 0.5, 'steel': 0.5},
        'ice': {'fire': 0.5, 'water': 0.5, 'grass': 2, 'ice': 0.5, 'ground': 2, 'flying': 2, 'dragon': 2, 'steel': 0.5},
        'fighting': {'normal': 2, 'ice': 2, 'poison': 0.5, 'flying': 0.5, 'psychic': 0.5, 'bug': 0.5, 'rock': 2, 'ghost': 0, 'dark': 2, 'steel': 2, 'fairy': 0.5},
        'poison': {'grass': 2, 'poison': 0.5, 'ground': 0.5, 'rock': 0.5, 'ghost': 0.5, 'steel': 0, 'fairy': 2},
        'ground': {'fire': 2, 'electric': 2, 'grass': 0.5, 'poison': 2, 'flying': 0, 'bug': 0.5, 'rock': 2, 'steel': 2},
        'flying': {'electric': 0.5, 'grass': 2, 'fighting': 2, 'bug': 2, 'rock': 0.5, 'steel': 0.5},
        'psychic': {'fighting': 2, 'poison': 2, 'psychic': 0.5, 'dark': 0, 'steel': 0.5},
        'bug': {'fire': 0.5, 'grass': 2, 'fighting': 0.5, 'poison': 0.5, 'flying': 0.5, 'psychic': 2, 'ghost': 0.5, 'dark': 2, 'steel': 0.5, 'fairy': 0.5},
        'rock': {'fire': 2, 'ice': 2, 'fighting': 0.5, 'ground': 0.5, 'flying': 2, 'bug': 2, 'steel': 0.5},
        'ghost': {'normal': 0, 'psychic': 2, 'ghost': 2, 'dark': 0.5},
        'dragon': {'dragon': 2, 'steel': 0.5, 'fairy': 0},
        'dark': {'fighting': 0.5, 'psychic': 2, 'ghost': 2, 'dark': 0.5, 'fairy': 0.5},
        'steel': {'fire': 0.5, 'water': 0.5, 'electric': 0.5, 'ice': 2, 'rock': 2, 'steel': 0.5, 'fairy': 2},
        'fairy': {'fire': 0.5, 'fighting': 2, 'poison': 0.5, 'dragon': 2, 'dark': 2, 'steel': 0.5}
    }
    
    # Meta standard stats (approx competitive averages)
    meta_standards = {'hp': 80, 'attack': 90, 'defense': 80, 'sp_attack': 85, 'sp_defense': 80, 'speed': 85}
             
    defensive_coverage = {t: {'weak': 0, 'resist': 0, 'immune': 0} for t in types}
    offensive_coverage = {t: False for t in types}  # Can we hit this type super-effectively?
    
    stats_total = {'hp': 0, 'attack': 0, 'defense': 0, 'sp_attack': 0, 'sp_defense': 0, 'speed': 0}
    member_count = len(pokemon_list)
    team_types = set()
    
    if member_count == 0:
        return jsonify({'error': 'Team is empty'}), 400
        
    import json
    
    for p in pokemon_list:
        # Stats
        stats_total['hp'] += p.hp
        stats_total['attack'] += p.attack
        stats_total['defense'] += p.defense
        stats_total['sp_attack'] += p.sp_attack
        stats_total['sp_defense'] += p.sp_defense
        stats_total['speed'] += p.speed
        
        # Collect team types for offensive coverage
        if p.main_type:
            team_types.add(p.main_type.lower())
        if p.secondary_type:
            team_types.add(p.secondary_type.lower())
        
        # Defensive Coverage (using against_types JSON)
        if p.against_types:
            try:
                matchups = json.loads(p.against_types)
                for t, multiplier in matchups.items():
                    t_lower = t.lower()
                    if t_lower in defensive_coverage:
                        if multiplier > 1:
                            defensive_coverage[t_lower]['weak'] += 1
                        elif multiplier < 1 and multiplier > 0:
                            defensive_coverage[t_lower]['resist'] += 1
                        elif multiplier == 0:
                            defensive_coverage[t_lower]['immune'] += 1
            except:
                pass
    
    # Calculate Offensive Coverage (what types can team hit super-effectively)
    for attacker_type in team_types:
        if attacker_type in type_chart:
            for defender_type, multiplier in type_chart[attacker_type].items():
                if multiplier >= 2:
                    offensive_coverage[defender_type] = True
                
    # Calculate averages
    stats_avg = {k: round(v / member_count) for k, v in stats_total.items()}
    
    # Find weaknesses (types with 2+ team members weak to them)
    critical_weaknesses = [t for t, data in defensive_coverage.items() if data['weak'] >= 2]
    
    # Find offensive gaps (types we can't hit super-effectively)
    offensive_gaps = [t for t, can_hit in offensive_coverage.items() if not can_hit]
    
    # Generate AI coach suggestions
    suggestions = []
    if critical_weaknesses:
        weak_types = ', '.join([t.capitalize() for t in critical_weaknesses[:3]])
        suggestions.append(f"Your team is weak to {weak_types} types. Consider adding Pokémon that resist these.")
    
    if len(offensive_gaps) > 6:
        gap_types = ', '.join([t.capitalize() for t in offensive_gaps[:3]])
        suggestions.append(f"Your team lacks offensive coverage against {gap_types}. Add diverse typings!")
    
    if stats_avg.get('speed', 0) < meta_standards['speed'] - 20:
        suggestions.append("Your team's Speed is below average. Consider faster Pokémon for priority control.")
    
    if not suggestions:
        suggestions.append("Great team balance! Your type coverage and stats look solid.")
    
    return jsonify({
        'coverage': defensive_coverage,
        'offensive_coverage': offensive_coverage,
        'stats_avg': stats_avg,
        'meta_standards': meta_standards,
        'member_count': member_count,
        'team_types': list(team_types),
        'critical_weaknesses': critical_weaknesses,
        'offensive_gaps': offensive_gaps,
        'suggestions': suggestions
    })
@app.route('/compare')
def compare_page():
    """Pokemon comparison tool"""
    pokemon_list = Pokemon.query.order_by(Pokemon.number).all()
    return render_template('compare.html', pokemon_list=pokemon_list)

@app.route('/api/compare', methods=['POST'])
def api_compare():
    """Compare multiple Pokemon"""
    data = request.get_json()
    pokemon_ids = data.get('pokemon_ids', [])
    
    if len(pokemon_ids) < 2:
        return jsonify({'error': 'Select at least 2 Pokemon'}), 400
    if len(pokemon_ids) > 4:
        return jsonify({'error': 'Maximum 4 Pokemon allowed'}), 400
    
    pokemon_list = Pokemon.query.filter(Pokemon.id.in_(pokemon_ids)).all()
    
    return jsonify({
        'pokemon': [p.to_dict() for p in pokemon_list]
    })

# ==================== GALLERY ====================

@app.route('/gallery')
def gallery():
    """Visual gallery of all Pokemon"""
    generation = request.args.get('gen', '')
    pokemon_type = request.args.get('type', '')
    
    query = Pokemon.query
    
    if pokemon_type:
        query = query.filter(
            (Pokemon.main_type.ilike(pokemon_type)) | 
            (Pokemon.secondary_type.ilike(pokemon_type))
        )
    
    if generation:
        gen_ranges = {
            '1': (1, 151), '2': (152, 251), '3': (252, 386),
            '4': (387, 493), '5': (494, 649), '6': (650, 721),
            '7': (722, 809), '8': (810, 905), '9': (906, 1025)
        }
        if generation in gen_ranges:
            start, end = gen_ranges[generation]
            query = query.filter(Pokemon.number >= start, Pokemon.number <= end)
    
    pokemon_list = query.order_by(Pokemon.number).all()
    
    return render_template('gallery.html', 
                          pokemon_list=pokemon_list, 
                          types=PokemonType.get_type_data(),
                          current_type=pokemon_type,
                          current_gen=generation)

# ==================== MOVE & ABILITY DEX ====================

@app.route('/moves')
def move_dex():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    
    query = Move.query
    if search:
        query = query.filter(Move.name.ilike(f'%{search}%'))
        
    moves = query.order_by(Move.name).paginate(page=page, per_page=20)
    return render_template('move_dex.html', moves=moves, search=search)

@app.route('/abilities')
def ability_dex():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    
    query = Ability.query
    if search:
        query = query.filter(Ability.name.ilike(f'%{search}%'))
        
    abilities = query.order_by(Ability.name).paginate(page=page, per_page=20)
    return render_template('ability_dex.html', abilities=abilities, search=search)

# ==================== DOWNLOAD CARD ====================

@app.route('/api/download-card/<int:pokemon_id>')
def download_card(pokemon_id):
    """Generate and download a Pokemon card image"""
    import io
    from flask import Response
    
    pokemon = Pokemon.query.get(pokemon_id)
    if not pokemon:
        return jsonify({'error': 'Pokemon not found'}), 404
    
    card_html = f'''Pokemon Card: {pokemon.name} (#{pokemon.number})
Type: {pokemon.main_type}{' / ' + pokemon.secondary_type if pokemon.secondary_type else ''}
ATK: {pokemon.attack} | DEF: {pokemon.defense} | HP: {pokemon.stamina}
{pokemon.pokedex_desc or ''}
'''
    
    response = Response(card_html, mimetype='text/plain')
    response.headers['Content-Disposition'] = f'attachment; filename={pokemon.name}_card.txt'
    return response

@app.route('/api/pokemon/<int:pokemon_id>/card-data')
def get_card_data(pokemon_id):
    """Get card data for client-side rendering"""
    pokemon = Pokemon.query.get(pokemon_id)
    if not pokemon:
        return jsonify({'error': 'Pokemon not found'}), 404
    
    images = PokemonImage.query.filter_by(pokemon_id=pokemon.id).order_by(PokemonImage.order).all()
    primary_image = images[0].path if images else None
    
    return jsonify({
        'pokemon': pokemon.to_dict(),
        'primary_image': primary_image,
        'image_url': f'https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/{pokemon.number}.png'
    })

# ==================== POKEMON OF THE DAY ====================

@app.route('/api/pokemon-of-the-day')
def pokemon_of_the_day():
    """Get Pokemon of the day (changes daily)"""
    from datetime import date
    import hashlib
    
    today = date.today().isoformat()
    day_hash = int(hashlib.md5(today.encode()).hexdigest(), 16)
    
    total = Pokemon.query.count()
    if total == 0:
        return jsonify({'error': 'No Pokemon available'}), 404
    
    offset = day_hash % total
    pokemon = Pokemon.query.order_by(Pokemon.number).offset(offset).first()
    
    return jsonify(pokemon.to_dict())

# Error handlers
@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500

# ==================== BATTLE SIMULATOR ====================

# In-memory battle session storage
battle_sessions = {}

@app.route('/battle')
def battle_page():
    return render_template('battle.html')

@app.route('/api/battle/start', methods=['POST'])
def start_battle():
    import uuid
    data = request.json or {}
    pokemon_id = data.get('pokemon_id')
    
    # Get Player Pokemon
    if pokemon_id:
        player_poke = Pokemon.query.get(pokemon_id)
    else:
        # Random if not specified
        player_poke = Pokemon.query.order_by(db.func.random()).first()
        
    if not player_poke:
        return jsonify({'error': 'Pokemon not found'}), 404
        
    # Get Enemy Pokemon (Random)
    enemy_poke = Pokemon.query.order_by(db.func.random()).first()
    
    # Init Engine
    engine = BattleEngine(player_poke, enemy_poke)
    
    battle_id = str(uuid.uuid4())
    battle_sessions[battle_id] = engine
    
    return jsonify({
        'battle_id': battle_id,
        'state': engine.get_state()
    })

@app.route('/api/battle/<battle_id>/turn', methods=['POST'])
def battle_turn(battle_id):
    if battle_id not in battle_sessions:
        return jsonify({'error': 'Battle not found'}), 404
        
    engine = battle_sessions[battle_id]
    data = request.json
    move_index = data.get('move_index', 0)
    
    state = engine.execute_turn(move_index)
    
    # Cleanup if over (can fail immediately if deleted, maybe keep for a timeout or rely on restart)
    if state['winner']:
        pass 
    
    return jsonify(state)

# ==================== STORIES / POKETALES ====================

@app.route('/stories')
def stories_page():
    """PokéTales - Stories and lore page"""
    return render_template('stories.html')

# ==================== n8n WEBHOOK ENDPOINTS ====================
# These endpoints allow n8n workflows to interact with the application

@app.route('/api/n8n/featured-pokemon', methods=['GET', 'POST'])
def n8n_featured_pokemon():
    """n8n endpoint: Get or set featured Pokemon for carousel"""
    from sqlalchemy.sql.expression import func
    
    if request.method == 'GET':
        # Return a random high-stat Pokemon suitable for featuring
        featured = Pokemon.query.filter(
            (Pokemon.attack >= 100) | (Pokemon.special_attack >= 100)
        ).order_by(func.random()).first()
        
        if featured:
            return jsonify({
                'status': 'success',
                'pokemon': featured.to_dict(),
                'image_url': f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/{featured.number}.png"
            })
        return jsonify({'status': 'error', 'message': 'No Pokemon found'}), 404
    
    elif request.method == 'POST':
        # n8n can push a specific featured Pokemon
        data = request.get_json()
        # Store in session or cache (could expand to DB table)
        return jsonify({
            'status': 'success',
            'message': 'Featured Pokemon updated',
            'pokemon_id': data.get('pokemon_id')
        })

@app.route('/api/n8n/daily-digest', methods=['POST'])
def n8n_daily_digest():
    """n8n endpoint: Receive data for daily digest email generation"""
    data = request.get_json()
    
    # This would trigger email sending via n8n workflow
    # For now, we return data that n8n can use
    from sqlalchemy.sql.expression import func
    
    # Get stats for digest
    total_pokemon = Pokemon.query.count()
    trending = Pokemon.query.order_by(func.random()).limit(5).all()
    
    return jsonify({
        'status': 'success',
        'digest_data': {
            'total_pokemon': total_pokemon,
            'trending_pokemon': [p.to_dict() for p in trending],
            'quiz_of_the_day': Pokemon.query.order_by(func.random()).first().to_dict() if Pokemon.query.first() else None
        }
    })

@app.route('/api/n8n/generate-story', methods=['POST'])
def n8n_generate_story():
    """n8n endpoint: Trigger AI story generation for a Pokemon"""
    data = request.get_json()
    pokemon_name = data.get('pokemon_name')
    story_type = data.get('story_type', 'origin')  # origin, battle, journey
    
    pokemon = get_pokemon_by_name(pokemon_name) if pokemon_name else None
    
    if not pokemon:
        from sqlalchemy.sql.expression import func
        pokemon = Pokemon.query.order_by(func.random()).first()
    
    if not pokemon:
        return jsonify({'status': 'error', 'message': 'No Pokemon found'}), 404
    
    # Return data for n8n to use with AI (GPT-4, Claude, etc.)
    prompt_data = {
        'pokemon': pokemon.to_dict(),
        'story_type': story_type,
        'prompt_template': f"""Write an engaging {story_type} story about {pokemon.name}. 
        This is a {pokemon.main_type}{(' and ' + pokemon.secondary_type) if pokemon.secondary_type else ''} type Pokémon.
        Stats: HP {pokemon.hp}, Attack {pokemon.attack}, Defense {pokemon.defense}.
        Make it exciting, dramatic, and suitable for Pokémon fans of all ages.
        Keep it under 500 words."""
    }
    
    return jsonify({
        'status': 'success',
        'prompt_data': prompt_data
    })

@app.route('/api/n8n/user-engagement', methods=['POST'])
def n8n_user_engagement():
    """n8n endpoint: Get user engagement data for re-engagement campaigns"""
    # Get users who haven't logged in recently (for n8n to send emails)
    from datetime import datetime, timedelta
    
    inactive_threshold = datetime.utcnow() - timedelta(days=7)
    
    inactive_users = User.query.filter(
        User.last_login < inactive_threshold
    ).limit(50).all()
    
    return jsonify({
        'status': 'success',
        'inactive_users': [{
            'id': u.id,
            'email': u.email,
            'name': u.name,
            'last_login': u.last_login.isoformat() if u.last_login else None
        } for u in inactive_users]
    })

@app.route('/api/n8n/webhook/story-created', methods=['POST'])
def n8n_story_webhook():
    """n8n webhook: Receive generated story from AI workflow"""
    data = request.get_json()
    
    # Here you could save the story to a database
    # For now, we just acknowledge receipt
    story = {
        'title': data.get('title'),
        'content': data.get('content'),
        'pokemon_name': data.get('pokemon_name'),
        'created_at': data.get('created_at')
    }
    
    # TODO: Save to Story model when implemented
    
    return jsonify({
        'status': 'success',
        'message': 'Story received',
        'story_preview': story.get('content', '')[:200] + '...'
    })

# ==================== VOICE API ====================

@app.route('/api/voice/command', methods=['POST'])
def voice_command():
    """Process voice command from the Voice Pokédex"""
    data = request.get_json()
    command = data.get('command', '').lower().strip()
    
    if not command:
        return jsonify({'error': 'No command provided'}), 400
    
    # Parse intent
    response = {
        'understood': True,
        'action': None,
        'data': None,
        'speech': None
    }
    
    # "Tell me about [pokemon]"
    import re
    tell_me_match = re.search(r'(?:tell me about|what is|who is|describe|find)\s+(.+)', command)
    if tell_me_match:
        pokemon_name = tell_me_match.group(1).strip()
        pokemon = get_pokemon_by_name(pokemon_name)
        
        if pokemon:
            response['action'] = 'show_pokemon'
            response['data'] = pokemon.to_dict()
            response['speech'] = f"{pokemon.name} is a {pokemon.main_type}{' and ' + pokemon.secondary_type if pokemon.secondary_type else ''} type Pokémon. It has {pokemon.hp} HP, {pokemon.attack} attack, and {pokemon.defense} defense."
        else:
            response['understood'] = False
            response['speech'] = f"Sorry, I couldn't find a Pokémon called {pokemon_name}"
    
    # "Search for [query]"
    elif 'search' in command:
        search_match = re.search(r'search\s+(?:for\s+)?(.+)', command)
        if search_match:
            query = search_match.group(1).strip()
            response['action'] = 'search'
            response['data'] = {'query': query}
            response['speech'] = f"Searching for {query}"
    
    # Navigation commands
    elif any(word in command for word in ['go to', 'open', 'show']):
        nav_match = re.search(r'(?:go to|open|show)\s+(pokedex|scanner|quiz|gallery|home|favorites|stories)', command)
        if nav_match:
            page = nav_match.group(1)
            routes = {
                'home': '/',
                'pokedex': '/pokedex',
                'scanner': '/scan',
                'quiz': '/quiz',
                'gallery': '/gallery',
                'favorites': '/favorites',
                'stories': '/stories'
            }
            response['action'] = 'navigate'
            response['data'] = {'url': routes.get(page, '/')}
            response['speech'] = f"Opening {page}"
    
    else:
        # Try as Pokemon name directly
        pokemon = get_pokemon_by_name(command)
        if pokemon:
            response['action'] = 'show_pokemon'
            response['data'] = pokemon.to_dict()
            response['speech'] = f"{pokemon.name} is a {pokemon.main_type} type Pokémon with {pokemon.hp} HP."
        else:
            response['understood'] = False
            response['speech'] = "I didn't understand that. Try saying 'Tell me about Pikachu' or 'Open Pokedex'"
    
    return jsonify(response)

    return jsonify(response)

# ==================== GAMIFICATION LOGIC ====================

def award_xp(user, amount, reason="Activity"):
    """Award XP to user and check for level up"""
    if not user:
        return {'leveled_up': False}
        
    leveled_up = user.add_exp(amount)
    db.session.commit()
    
    return {
        'leveled_up': leveled_up,
        'new_level': user.level,
        'xp_earned': amount,
        'reason': reason
    }

def check_achievements(user):
    """Check and award badges based on user stats"""
    if not user:
        return []
        
    new_badges = []
    
    # Define Achievement Logic
    # 1. Quiz Master: Total Score
    total_score = db.session.query(db.func.sum(QuizScore.score)).filter_by(user_id=user.id).scalar() or 0
    if total_score >= 1000:
        award_badge(user, 'Quiz Master', new_badges)
    elif total_score >= 100:
        award_badge(user, 'Novice Trainer', new_badges)
        
    # 2. Collector: Favorites Count
    fav_count = Favorite.query.filter_by(user_id=user.id).count()
    if fav_count >= 50:
        award_badge(user, 'Elite Collector', new_badges)
    elif fav_count >= 10:
        award_badge(user, 'Collector', new_badges)
        
    # 3. Dedicated: Streak
    if user.current_streak >= 7:
        award_badge(user, 'Week Warrior', new_badges)
    if user.current_streak >= 30:
        award_badge(user, 'Monthly Master', new_badges)
        
    return new_badges

def award_badge(user, badge_name, new_list):
    """Helper to grant a badge if not already owned"""
    badge = Badge.query.filter_by(name=badge_name).first()
    if not badge:
        return
        
    # Check if already has it
    if UserBadge.query.filter_by(user_id=user.id, badge_id=badge.id).first():
        return
        
    # Grant badge
    user_badge = UserBadge(user_id=user.id, badge_id=badge.id)
    db.session.add(user_badge)
    
    # Grant XP reward
    user.add_exp(badge.xp_reward)
    
    db.session.commit()
    
    new_list.append({
        'badge': badge.to_dict(),
        'xp_bonus': badge.xp_reward
    })

def seed_badges():
    """Create default badges if they don't exist"""
    badges = [
        {'name': 'Novice Trainer', 'description': 'Score 100+ points in quizzes', 'icon': 'fa-egg', 'category': 'quiz', 'requirement_value': 100, 'xp_reward': 200},
        {'name': 'Quiz Master', 'description': 'Score 1000+ points in quizzes', 'icon': 'fa-brain', 'category': 'quiz', 'requirement_value': 1000, 'xp_reward': 1000},
        {'name': 'Collector', 'description': 'Favorite 10 Pokémon', 'icon': 'fa-star', 'category': 'collection', 'requirement_value': 10, 'xp_reward': 150},
        {'name': 'Elite Collector', 'description': 'Favorite 50 Pokémon', 'icon': 'fa-crown', 'category': 'collection', 'requirement_value': 50, 'xp_reward': 800},
        {'name': 'Week Warrior', 'description': 'Maintain a 7-day streak', 'icon': 'fa-fire', 'category': 'streak', 'requirement_value': 7, 'xp_reward': 500},
        {'name': 'Monthly Master', 'description': 'Maintain a 30-day streak', 'icon': 'fa-calendar-check', 'category': 'streak', 'requirement_value': 30, 'xp_reward': 2500},
    ]
    
    for b_data in badges:
        if not Badge.query.filter_by(name=b_data['name']).first():
            badge = Badge(**b_data)
            db.session.add(badge)
    
    db.session.commit()
    print("Badges seeded.")


@app.route('/api/user/gamification')
def api_user_gamification():
    """Get user level, xp, badges"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Login required'}), 401
    
    badges = [ub.to_dict() for ub in user.earned_badges]
    
    # Calculate progress to next level
    current_level_xp_start = 0 # Simplified, can be better
    # Or just return raw values and let frontend calculate %
    
    return jsonify({
        'level': user.level,
        'exp': user.exp,
        'next_level_exp': user.next_level_exp,
        'badges': badges,
        'streak': user.current_streak
    })

# DB Initialization (Idempotent, runs on startup even under Gunicorn)
with app.app_context():
    try:
        db.create_all()
        seed_badges()
    except Exception as e:
        print(f"Startup DB Error: {e}")

if __name__ == '__main__':
    print("Starting Pokémon Knower...")
    app.run(debug=True, port=5000)
