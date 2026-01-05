import requests
import time
import random
from app import app, db
from models import Move, Ability

def fetch_with_retries(url, max_retries=5):
    """Fetch URL with exponential backoff retries"""
    for i in range(max_retries):
        try:
            res = requests.get(url, timeout=10)
            if res.status_code == 200:
                return res
            if res.status_code == 429: # Rate limited
                wait = (2 ** i) + random.random()
                print(f"Rate limited. Waiting {wait:.2f}s...")
                time.sleep(wait)
                continue
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
            wait = (2 ** i) + random.random()
            print(f"Connection error: {e}. Retry {i+1}/{max_retries} in {wait:.2f}s...")
            time.sleep(wait)
    return None

def seed_dex():
    """Seed Moves and Abilities from PokeAPI with robustness"""
    print("Starting Dex seeding (Robust Mode)...")
    
    with app.app_context():
        # Ensure tables exist
        db.create_all()
        
        # --- SEED MOVES ---
        target_moves = 100
        current_moves = Move.query.count()
        if current_moves < target_moves:
            print(f"Current moves: {current_moves}. Fetching up to {target_moves}...")
            try:
                # Fetch list of moves
                res = fetch_with_retries(f'https://pokeapi.co/api/v2/move?limit={target_moves}') 
                if res:
                    results = res.json()['results']
                    count = 0
                    
                    for item in results:
                        name = item['name'].replace('-', ' ').title()
                        if Move.query.filter_by(name=name).first():
                            continue
                            
                        # Detail fetch
                        m_res = fetch_with_retries(item['url'])
                        if not m_res:
                            print(f"Skipping {name} due to repeated failures.")
                            continue
                        
                        m_data = m_res.json()
                        
                        # English Description
                        desc = "No description available."
                        # Usually flavor_text_entries is more descriptive
                        if m_data.get('flavor_text_entries'):
                            for entry in m_data['flavor_text_entries']:
                                if entry['language']['name'] == 'en':
                                    desc = entry['flavor_text'].replace('\n', ' ')
                                    break
                        elif m_data.get('effect_entries'):
                             for entry in m_data['effect_entries']:
                                if entry['language']['name'] == 'en':
                                    desc = entry['short_effect'].replace('\n', ' ')
                                    break
                        
                        move = Move(
                            name=name,
                            type=m_data['type']['name'],
                            category=m_data['damage_class']['name'],
                            power=m_data.get('power'),
                            accuracy=m_data.get('accuracy'),
                            pp=m_data.get('pp'),
                            effect_chance=m_data.get('effect_chance'),
                            description=desc
                        )
                        db.session.add(move)
                        count += 1
                        
                        # Commit in batches
                        if count % 10 == 0:
                            db.session.commit()
                            print(f"Added {count} moves...")
                        
                        # Avoid hammering API
                        time.sleep(0.1)
                        
                    db.session.commit()
                    print(f"Successfully seeded {count} moves.")
            except Exception as e:
                print(f"Unexpected error seeding moves: {e}")

        # --- SEED ABILITIES ---
        target_abilities = 100
        current_abilities = Ability.query.count()
        if current_abilities < target_abilities:
            print(f"Current abilities: {current_abilities}. Fetching up to {target_abilities}...")
            try:
                res = fetch_with_retries(f'https://pokeapi.co/api/v2/ability?limit={target_abilities}')
                if res:
                    results = res.json()['results']
                    count = 0
                    
                    for item in results:
                        name = item['name'].replace('-', ' ').title()
                        if Ability.query.filter_by(name=name).first():
                            continue
                            
                        a_res = fetch_with_retries(item['url'])
                        if not a_res:
                            print(f"Skipping {name} due to repeated failures.")
                            continue
                            
                        a_data = a_res.json()
                        
                        desc = "No description available."
                        if a_data.get('flavor_text_entries'):
                            for entry in a_data['flavor_text_entries']:
                                if entry['language']['name'] == 'en':
                                    desc = entry['flavor_text'].replace('\n', ' ')
                                    break
                        elif a_data.get('effect_entries'):
                             for entry in a_data['effect_entries']:
                                if entry['language']['name'] == 'en':
                                    desc = entry['short_effect'].replace('\n', ' ')
                                    break
                                    
                        ability = Ability(
                            name=name,
                            description=desc
                        )
                        db.session.add(ability)
                        count += 1
                        
                        if count % 10 == 0:
                            db.session.commit()
                            print(f"Added {count} abilities...")
                        
                        time.sleep(0.1)
                        
                    db.session.commit()
                    print(f"Successfully seeded {count} abilities.")
            except Exception as e:
                print(f"Unexpected error seeding abilities: {e}")

if __name__ == '__main__':
    seed_dex()
