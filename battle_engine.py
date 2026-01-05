import random
import math

class BattleEngine:
    """
    Simple turn-based battle engine for 1v1 Pokemon battles.
    Handles damage calculation, turn order, and win conditions.
    """
    
    def __init__(self, player_pokemon, enemy_pokemon):
        self.player = self._init_state(player_pokemon, is_player=True)
        self.enemy = self._init_state(enemy_pokemon, is_player=False)
        self.turn = 1
        self.log = []
        self.winner = None
        
    def _init_state(self, pokemon, is_player):
        return {
            'name': pokemon.name,
            'id': pokemon.id,
            'image': self._get_image(pokemon),
            'hp': pokemon.stamina,
            'max_hp': pokemon.stamina,
            'stats': {
                'attack': pokemon.attack,
                'defense': pokemon.defense,
                'sp_attack': pokemon.sp_attack,
                'sp_defense': pokemon.sp_defense,
                'speed': pokemon.speed
            },
            'types': [t for t in [pokemon.main_type, pokemon.secondary_type] if t],
            'moves': self._generate_moves(pokemon),
            'is_player': is_player
        }

    def _get_image(self, pokemon):
        # Fallback logic for image
        return f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/{pokemon.number}.png"

    def _generate_moves(self, pokemon):
        # In a real app, we'd pull from a Move table. 
        # For this prototype, we generate generic moves based on stats/types.
        moves = []
        
        # 1. Main STAB Move
        moves.append({
            'name': f"{pokemon.main_type} Strike",
            'type': pokemon.main_type.lower(),
            'power': 80,
            'category': 'physical' if pokemon.attack > pokemon.sp_attack else 'special',
            'accuracy': 100
        })
        
        # 2. Secondary/Coverage
        if pokemon.secondary_type:
            moves.append({
                'name': f"{pokemon.secondary_type} Blast",
                'type': pokemon.secondary_type.lower(),
                'power': 75,
                'category': 'special',
                'accuracy': 95
            })
        else:
            moves.append({
                'name': "Quick Attack",
                'type': "normal",
                'power': 40,
                'category': 'physical',
                'accuracy': 100,
                'priority': 1
            })
            
        # 3. Heavy Hitter
        moves.append({
            'name': "Hyper Beam",
            'type': "normal",
            'power': 120,
            'category': 'special',
            'accuracy': 75
        })
        
        # 4. Status/Heal
        moves.append({
            'name': "Recover",
            'type': "normal",
            'power': 0,
            'category': 'status',
            'accuracy': 100
        })
        
        return moves

    def execute_turn(self, player_move_index, enemy_move_index=None):
        if self.winner:
            return self.get_state()
            
        player_move = self.player['moves'][player_move_index]
        
        # AI Logic if no specific enemy move
        if enemy_move_index is None:
            enemy_move_index = random.randint(0, len(self.enemy['moves']) - 1)
        enemy_move = self.enemy['moves'][enemy_move_index]
        
        # Determine Order
        player_speed = self.player['stats']['speed']
        enemy_speed = self.enemy['stats']['speed']
        
        # Simple priority check (Quick Attack)
        p_prio = player_move.get('priority', 0)
        e_prio = enemy_move.get('priority', 0)
        
        first = 'player'
        if p_prio > e_prio:
            first = 'player'
        elif e_prio > p_prio:
            first = 'enemy'
        elif player_speed >= enemy_speed:
            first = 'player'
        else:
            first = 'enemy'
            
        turn_logs = []
        
        if first == 'player':
            turn_logs.extend(self._attack(self.player, self.enemy, player_move))
            if self.enemy['hp'] > 0:
                turn_logs.extend(self._attack(self.enemy, self.player, enemy_move))
        else:
            turn_logs.extend(self._attack(self.enemy, self.player, enemy_move))
            if self.player['hp'] > 0:
                turn_logs.extend(self._attack(self.player, self.enemy, player_move))
                
        self.log.extend(turn_logs)
        self.turn += 1
        
        self._check_winner()
        return self.get_state(latest_logs=turn_logs)

    def _attack(self, attacker, defender, move):
        logs = []
        logs.append(f"{attacker['name']} used {move['name']}!")
        
        if move['category'] == 'status':
            heal = int(attacker['max_hp'] * 0.5)
            attacker['hp'] = min(attacker['max_hp'], attacker['hp'] + heal)
            logs.append(f"{attacker['name']} recovered HP!")
            return logs
            
        # Hit Check
        if random.randint(1, 100) > move['accuracy']:
            logs.append("But it missed!")
            return logs
            
        # Damage Calc
        # ((2 * Level / 5 + 2) * Power * A / D) / 50 + 2 * Modifier
        # Simplified: Level = 50
        level = 50
        a = attacker['stats']['attack'] if move['category'] == 'physical' else attacker['stats']['sp_attack']
        d = defender['stats']['defense'] if move['category'] == 'physical' else defender['stats']['sp_defense']
        power = move['power']
        
        damage = (((2 * level / 5 + 2) * power * a / d) / 50) + 2
        
        # Modifiers (STAB, Type Effectiveness)
        modifier = 1.0
        
        # STAB
        if move['type'] in attacker['types']:
            modifier *= 1.5
            
        # Random
        modifier *= random.uniform(0.85, 1.0)
        
        final_damage = int(damage * modifier)
        defender['hp'] = max(0, defender['hp'] - final_damage)
        
        logs.append(f"It dealt {final_damage} damage!")
        
        if defender['hp'] == 0:
            logs.append(f"{defender['name']} fainted!")
            
        return logs

    def _check_winner(self):
        if self.player['hp'] <= 0:
            self.winner = 'enemy'
        elif self.enemy['hp'] <= 0:
            self.winner = 'player'

    def get_state(self, latest_logs=None):
        return {
            'player': self.player,
            'enemy': self.enemy,
            'turn': self.turn,
            'winner': self.winner,
            'logs': latest_logs if latest_logs is not None else self.log[-5:]
        }
