"""
Player Manager - Handles player data, progression, and statistics
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional


class PlayerManager:
    def __init__(self, data_file: str = 'players.json'):
        self.data_file = data_file
        self.players: Dict[int, dict] = {}
        self.load_data()
    
    def load_data(self):
        """Load player data from file"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    self.players = {int(k): v for k, v in data.items()}
            except Exception as e:
                print(f"Error loading player data: {e}")
                self.players = {}
        else:
            self.players = {}
    
    def save_data(self):
        """Save player data to file"""
        try:
            with open(self.data_file, 'w') as f:
                json.dump(self.players, f, indent=2, default=str)
        except Exception as e:
            print(f"Error saving player data: {e}")
    
    def register_player(self, user_id: int, username: str) -> dict:
        """Register a new player or return existing"""
        if user_id not in self.players:
            self.players[user_id] = {
                'user_id': user_id, 'username': username, 'level': 1, 'xp': 0, 'coins': 100,
                'wins': 0, 'losses': 0, 'games_played': 0, 'roles_played': {},
                'achievements': [], 'items': [], 'created_at': datetime.now().isoformat(),
                'last_daily_claim': None, 'streak': 0, 'total_playtime': 0,
                'favorite_role': None, 'mvp_count': 0
            }
            self.save_data()
        elif self.players[user_id]['username'] != username:
            self.players[user_id]['username'] = username
            self.save_data()
        return self.players[user_id]
    
    def get_player(self, user_id: int) -> Optional[dict]:
        return self.players.get(user_id)
    
    def get_player_by_username(self, username: str) -> Optional[dict]:
        """Find player by username (case-insensitive)"""
        username_lower = username.lower()
        for player in self.players.values():
            if player['username'].lower() == username_lower:
                return player
        return None

    def add_xp(self, user_id: int, amount: int) -> dict:
        """Add XP to player and handle level ups"""
        player = self.get_player(user_id)
        if not player: return None
        
        player['xp'] += amount
        xp_for_next_level = self._calculate_xp_for_level(player['level'] + 1)
        
        leveled_up = False
        while xp_for_next_level > 0 and player['xp'] >= xp_for_next_level:
            player['level'] += 1
            player['xp'] -= xp_for_next_level
            player['coins'] += 50 * player['level']
            leveled_up = True
            xp_for_next_level = self._calculate_xp_for_level(player['level'] + 1)
        
        if leveled_up: self._check_level_achievements(user_id)
        self.save_data()
        return player
    
    def _calculate_xp_for_level(self, level: int) -> int:
        if level <= 1: return 100
        return int(100 * (level ** 1.5))
    
    def add_coins(self, user_id: int, amount: int):
        player = self.get_player(user_id)
        if player: player['coins'] += amount; self.save_data()
    
    def spend_coins(self, user_id: int, amount: int) -> bool:
        player = self.get_player(user_id)
        if player and player['coins'] >= amount:
            player['coins'] -= amount; self.save_data(); return True
        return False
    
    def add_win(self, user_id: int):
        player = self.get_player(user_id)
        if player:
            player['wins'] += 1; player['games_played'] += 1
            self._check_win_achievements(user_id); self.save_data()
    
    def add_loss(self, user_id: int):
        player = self.get_player(user_id)
        if player: player['losses'] += 1; player['games_played'] += 1; self.save_data()
    
    def record_role_played(self, user_id: int, role: str):
        player = self.get_player(user_id)
        if player:
            player['roles_played'][role] = player['roles_played'].get(role, 0) + 1
            if player['roles_played']:
                player['favorite_role'] = max(player['roles_played'].items(), key=lambda x: x[1])[0]
            self.save_data()
    
    def add_achievement(self, user_id: int, achievement: dict):
        player = self.get_player(user_id)
        if player and not any(a['id'] == achievement['id'] for a in player['achievements']):
            achievement['earned_at'] = datetime.now().isoformat()
            player['achievements'].append(achievement)
            player['coins'] += achievement.get('reward', 50)
            self.save_data(); return True
        return False
    
    def _check_level_achievements(self, user_id: int):
        player = self.get_player(user_id);
        if not player: return; level = player['level']
        achievements = [
            {'id': 'level_5', 'name': 'Rising Star', 'level': 5, 'reward': 100, 'icon': '⭐'},
            {'id': 'level_10', 'name': 'Veteran', 'level': 10, 'reward': 200, 'icon': '🎖️'},
        ]
        for ach in achievements:
            if level >= ach['level']: self.add_achievement(user_id, ach)
    
    def _check_win_achievements(self, user_id: int):
        player = self.get_player(user_id);
        if not player: return; wins = player['wins']
        achievements = [
            {'id': 'first_win', 'name': 'First Blood', 'wins': 1, 'reward': 50, 'icon': '🏆'},
            {'id': 'win_10', 'name': 'Skilled', 'wins': 10, 'reward': 150, 'icon': '🎯'},
        ]
        for ach in achievements:
            if wins >= ach['wins']: self.add_achievement(user_id, ach)
    
    def claim_daily_reward(self, user_id: int) -> tuple:
        player = self.get_player(user_id);
        if not player: return False, None
        now = datetime.now(); last_claim_iso = player.get('last_daily_claim'); can_claim = False
        if last_claim_iso:
            last_claim_date = datetime.fromisoformat(last_claim_iso)
            if now.date() > last_claim_date.date():
                can_claim = True
                if now.date() - last_claim_date.date() == timedelta(days=1): player['streak'] = player.get('streak', 0) + 1
                else: player['streak'] = 1
        else: can_claim = True; player['streak'] = 1
        if not can_claim: return False, None
        streak_multiplier = min(player.get('streak', 1), 7)
        xp_reward, coin_reward = 50 * streak_multiplier, 25 * streak_multiplier
        player['last_daily_claim'] = now.isoformat()
        self.add_xp(user_id, xp_reward); self.add_coins(user_id, coin_reward)
        self.save_data()
        return True, {'xp': xp_reward, 'coins': coin_reward, 'streak': player.get('streak', 1)}
    
    def get_leaderboard(self, limit: int = 10) -> List[dict]:
        sorted_players = sorted(self.players.values(), key=lambda p: (p['level'], p['xp']), reverse=True)
        return sorted_players[:limit]
    
    def add_item(self, user_id: int, item: dict):
        player = self.get_player(user_id)
        if player:
            item_entry = {'id': item['id'], 'acquired_at': datetime.now().isoformat()}
            player['items'].append(item_entry)
            self.save_data()
            
    def remove_item(self, user_id: int, item_id: str) -> bool:
        """Remove an item from player inventory by ID"""
        player = self.get_player(user_id)
        if not player: return False
        
        item_to_remove = next((item for item in player['items'] if item['id'] == item_id), None)
        
        if item_to_remove:
            player['items'].remove(item_to_remove)
            self.save_data()
            return True # Item was found and removed
        return False # Item was not found

    def has_item(self, user_id: int, item_id: str) -> bool:
        player = self.get_player(user_id)
        return player and any(item['id'] == item_id for item in player.get('items', []))
