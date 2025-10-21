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
                    # Convert string keys back to integers
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
                json.dump(self.players, f, indent=2)
        except Exception as e:
            print(f"Error saving player data: {e}")
    
    def register_player(self, user_id: int, username: str) -> dict:
        """Register a new player or return existing"""
        if user_id not in self.players:
            self.players[user_id] = {
                'user_id': user_id,
                'username': username,
                'level': 1,
                'xp': 0,
                'coins': 100,
                'wins': 0,
                'losses': 0,
                'games_played': 0,
                'roles_played': {},
                'achievements': [],
                'items': [],
                'created_at': datetime.now().isoformat(),
                'last_daily_claim': None,
                'streak': 0,
                'total_playtime': 0,
                'favorite_role': None,
                'mvp_count': 0
            }
            self.save_data()
        else:
            # Update username if changed
            self.players[user_id]['username'] = username
            self.save_data()
        
        return self.players[user_id]
    
    def get_player(self, user_id: int) -> Optional[dict]:
        """Get player data"""
        return self.players.get(user_id)
    
    def add_xp(self, user_id: int, amount: int) -> dict:
        """Add XP to player and handle level ups"""
        player = self.get_player(user_id)
        if not player:
            return None
        
        player['xp'] += amount
        
        # Check for level up
        xp_for_next_level = self._calculate_xp_for_level(player['level'] + 1)
        
        while player['xp'] >= xp_for_next_level:
            player['level'] += 1
            player['xp'] -= xp_for_next_level
            player['coins'] += 50 * player['level']  # Bonus coins on level up
            
            # Check for new achievements
            self._check_level_achievements(user_id)
            
            xp_for_next_level = self._calculate_xp_for_level(player['level'] + 1)
        
        self.save_data()
        return player
    
    def _calculate_xp_for_level(self, level: int) -> int:
        """Calculate XP required for a level"""
        return int(100 * (level ** 1.5))
    
    def add_coins(self, user_id: int, amount: int):
        """Add coins to player"""
        player = self.get_player(user_id)
        if player:
            player['coins'] += amount
            self.save_data()
    
    def spend_coins(self, user_id: int, amount: int) -> bool:
        """Spend coins"""
        player = self.get_player(user_id)
        if player and player['coins'] >= amount:
            player['coins'] -= amount
            self.save_data()
            return True
        return False
    
    def add_win(self, user_id: int):
        """Record a win"""
        player = self.get_player(user_id)
        if player:
            player['wins'] += 1
            player['games_played'] += 1
            self._check_win_achievements(user_id)
            self.save_data()
    
    def add_loss(self, user_id: int):
        """Record a loss"""
        player = self.get_player(user_id)
        if player:
            player['losses'] += 1
            player['games_played'] += 1
            self.save_data()
    
    def record_role_played(self, user_id: int, role: str):
        """Record role played"""
        player = self.get_player(user_id)
        if player:
            if role not in player['roles_played']:
                player['roles_played'][role] = 0
            player['roles_played'][role] += 1
            
            # Update favorite role
            if player['roles_played']:
                favorite = max(player['roles_played'].items(), key=lambda x: x[1])
                player['favorite_role'] = favorite[0]
            
            self.save_data()
    
    def add_achievement(self, user_id: int, achievement: dict):
        """Add achievement to player"""
        player = self.get_player(user_id)
        if player:
            # Check if already has achievement
            if not any(a['id'] == achievement['id'] for a in player['achievements']):
                achievement['earned_at'] = datetime.now().isoformat()
                player['achievements'].append(achievement)
                player['coins'] += achievement.get('reward', 50)
                self.save_data()
                return True
        return False
    
    def _check_level_achievements(self, user_id: int):
        """Check for level-based achievements"""
        player = self.get_player(user_id)
        level = player['level']
        
        achievements = [
            {'id': 'level_5', 'name': 'Rising Star', 'description': 'Reach level 5', 'level': 5, 'reward': 100, 'icon': '⭐'},
            {'id': 'level_10', 'name': 'Veteran', 'description': 'Reach level 10', 'level': 10, 'reward': 200, 'icon': '🎖️'},
            {'id': 'level_25', 'name': 'Master', 'description': 'Reach level 25', 'level': 25, 'reward': 500, 'icon': '💎'},
            {'id': 'level_50', 'name': 'Legend', 'description': 'Reach level 50', 'level': 50, 'reward': 1000, 'icon': '🏆'},
        ]
        
        for achievement in achievements:
            if level >= achievement['level']:
                self.add_achievement(user_id, achievement)
    
    def _check_win_achievements(self, user_id: int):
        """Check for win-based achievements"""
        player = self.get_player(user_id)
        wins = player['wins']
        
        achievements = [
            {'id': 'first_win', 'name': 'First Blood', 'description': 'Win your first game', 'wins': 1, 'reward': 50, 'icon': '🏆'},
            {'id': 'win_10', 'name': 'Skilled', 'description': 'Win 10 games', 'wins': 10, 'reward': 150, 'icon': '🎯'},
            {'id': 'win_50', 'name': 'Expert', 'description': 'Win 50 games', 'wins': 50, 'reward': 500, 'icon': '💪'},
            {'id': 'win_100', 'name': 'Champion', 'description': 'Win 100 games', 'wins': 100, 'reward': 1000, 'icon': '👑'},
        ]
        
        for achievement in achievements:
            if wins >= achievement['wins']:
                self.add_achievement(user_id, achievement)
    
    def claim_daily_reward(self, user_id: int) -> tuple:
        """Claim daily reward"""
        player = self.get_player(user_id)
        if not player:
            return False, None
        
        now = datetime.now()
        last_claim = player.get('last_daily_claim')
        
        if last_claim:
            last_claim_date = datetime.fromisoformat(last_claim)
            if now.date() == last_claim_date.date():
                return False, None
            
            # Check streak
            if now.date() - last_claim_date.date() == timedelta(days=1):
                player['streak'] += 1
            else:
                player['streak'] = 1
        else:
            player['streak'] = 1
        
        # Calculate reward based on streak
        base_xp = 50
        base_coins = 25
        
        streak_multiplier = min(player['streak'], 7)  # Max 7 day streak bonus
        
        xp_reward = base_xp * streak_multiplier
        coin_reward = base_coins * streak_multiplier
        
        player['last_daily_claim'] = now.isoformat()
        self.add_xp(user_id, xp_reward)
        self.add_coins(user_id, coin_reward)
        
        self.save_data()
        
        return True, {
            'xp': xp_reward,
            'coins': coin_reward,
            'streak': player['streak']
        }
    
    def get_leaderboard(self, limit: int = 10) -> List[dict]:
        """Get top players by level and XP"""
        sorted_players = sorted(
            self.players.values(),
            key=lambda p: (p['level'], p['xp']),
            reverse=True
        )
        return sorted_players[:limit]
    
    def get_win_rate(self, user_id: int) -> float:
        """Calculate win rate"""
        player = self.get_player(user_id)
        if not player or player['games_played'] == 0:
            return 0.0
        
        return (player['wins'] / player['games_played']) * 100
    
    def add_item(self, user_id: int, item: dict):
        """Add item to player inventory"""
        player = self.get_player(user_id)
        if player:
            item['acquired_at'] = datetime.now().isoformat()
            player['items'].append(item)
            self.save_data()
    
    def has_item(self, user_id: int, item_id: str) -> bool:
        """Check if player has an item"""
        player = self.get_player(user_id)
        if player:
            return any(item['id'] == item_id for item in player['items'])
        return False
    
    def get_rank(self, user_id: int) -> str:
        """Get player rank based on level"""
        player = self.get_player(user_id)
        if not player:
            return "Rookie"
        
        level = player['level']
        
        if level < 5:
            return "🌱 Rookie"
        elif level < 10:
            return "⚔️ Soldier"
        elif level < 20:
            return "🎖️ Warrior"
        elif level < 30:
            return "👑 Elite"
        elif level < 50:
            return "💎 Master"
        else:
            return "🏆 Legend"
