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
                # Ensure file is not empty before loading
                if os.path.getsize(self.data_file) > 0:
                    with open(self.data_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        # Ensure data is a dictionary
                        if isinstance(data, dict):
                             self.players = {int(k): v for k, v in data.items()}
                        else:
                             print("Warning: players.json does not contain a valid dictionary. Initializing empty.")
                             self.players = {}
                else:
                    print("Warning: players.json is empty. Initializing empty.")
                    self.players = {}
            except json.JSONDecodeError as e:
                print(f"Error decoding player data from {self.data_file}: {e}. Initializing empty.")
                self.players = {}
            except Exception as e:
                print(f"Error loading player data: {e}. Initializing empty.")
                self.players = {}
        else:
            self.players = {} # Initialize empty if file doesn't exist

    def save_data(self):
        """Save player data to file"""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.players, f, indent=2, default=str, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving player data: {e}")

    def register_player(self, user_id: int, username: str) -> dict:
        """Register a new player or return/update existing"""
        player = self.players.get(user_id)
        if not player:
            player = {
                'user_id': user_id, 'username': username, 'level': 1, 'xp': 0, 'coins': 100,
                'wins': 0, 'losses': 0, 'games_played': 0, 'roles_played': {},
                'achievements': [], 'items': [], 'created_at': datetime.now().isoformat(),
                'last_daily_claim': None, 'streak': 0, 'total_playtime': 0,
                'favorite_role': None, 'mvp_count': 0
            }
            self.players[user_id] = player
            self.save_data()
            print(f"Registered new player: {username} ({user_id})")
        # Update username if it has changed
        elif player.get('username') != username:
            player['username'] = username
            self.save_data()
            print(f"Updated username for player: {username} ({user_id})")

        # Ensure essential keys exist (migration for older data)
        player.setdefault('items', [])
        player.setdefault('coins', 0)
        player.setdefault('level', 1)
        player.setdefault('xp', 0)
        player.setdefault('wins', 0)
        player.setdefault('losses', 0)
        player.setdefault('games_played', 0)

        return player

    def get_player(self, user_id: int) -> Optional[dict]:
        """Get player data"""
        return self.players.get(user_id)

    def get_player_by_username(self, username: str) -> Optional[dict]:
        """Find player by username (case-insensitive)"""
        if not username: return None
        username_lower = username.lower()
        for player in self.players.values():
            if player.get('username','').lower() == username_lower:
                return player
        return None

    def add_xp(self, user_id: int, amount: int):
        """Add XP to player and handle level ups"""
        player = self.get_player(user_id)
        if not player: return

        player['xp'] = player.get('xp', 0) + amount
        leveled_up = False

        while True:
            current_level = player.get('level', 1)
            xp_needed = self._calculate_xp_for_level(current_level + 1)

            if xp_needed <= 0: # Avoid infinite loop if calc is wrong
                 print(f"Warning: Calculated 0 XP needed for level {current_level + 1}")
                 break

            if player['xp'] >= xp_needed:
                player['level'] = current_level + 1
                player['xp'] -= xp_needed
                self.add_coins(user_id, 100 * player['level']) # Bonus coins
                leveled_up = True
                print(f"Player {user_id} leveled up to {player['level']}!")
            else:
                break # Not enough XP for next level

        if leveled_up:
            self._check_level_achievements(user_id)
        self.save_data()

    def _calculate_xp_for_level(self, level: int) -> int:
        """Calculate XP required FOR the next level (e.g., level 2 needs XP for level 2)"""
        if level <= 1: return 100 # Base XP for level 2
        # Formula: 100 * (level ^ 1.5) - adjusted slightly
        return int(100 * ((level-1) ** 1.5) + 100)

    def add_coins(self, user_id: int, amount: int):
        player = self.get_player(user_id)
        if player:
            player['coins'] = player.get('coins', 0) + amount
            self.save_data()

    def spend_coins(self, user_id: int, amount: int) -> bool:
        player = self.get_player(user_id)
        if player and player.get('coins', 0) >= amount:
            player['coins'] -= amount
            self.save_data()
            return True
        return False

    def add_win(self, user_id: int):
        player = self.get_player(user_id)
        if player:
            player['wins'] = player.get('wins', 0) + 1
            player['games_played'] = player.get('games_played', 0) + 1
            self._check_win_achievements(user_id)
            self.save_data()

    def add_loss(self, user_id: int):
        player = self.get_player(user_id)
        if player:
            player['losses'] = player.get('losses', 0) + 1
            player['games_played'] = player.get('games_played', 0) + 1
            self.save_data()

    def record_role_played(self, user_id: int, role: str):
        player = self.get_player(user_id)
        if player:
            player.setdefault('roles_played', {})
            player['roles_played'][role] = player['roles_played'].get(role, 0) + 1
            # Update favorite role
            if player['roles_played']:
                player['favorite_role'] = max(player['roles_played'].items(), key=lambda item: item[1])[0]
            self.save_data()

    def add_achievement(self, user_id: int, achievement: dict):
        player = self.get_player(user_id)
        if player:
            player.setdefault('achievements', [])
            # Check if achievement (by ID) already exists
            if not any(ach.get('id') == achievement.get('id') for ach in player['achievements']):
                new_achievement = achievement.copy() # Avoid modifying original dict
                new_achievement['earned_at'] = datetime.now().isoformat()
                player['achievements'].append(new_achievement)
                player['coins'] = player.get('coins', 0) + new_achievement.get('reward', 50)
                self.save_data()
                print(f"Player {user_id} earned achievement: {achievement.get('name')}")
                return True
        return False

    # Example Achievement Checks (Can be moved to a separate AchievementManager)
    def _check_level_achievements(self, user_id: int):
        player = self.get_player(user_id);
        if not player: return; level = player.get('level', 1)
        achievements_to_check = [
            {'id': 'level_5', 'name': 'Rising Star', 'description':'Reach Lv 5', 'level': 5, 'reward': 100, 'icon': '⭐'},
            {'id': 'level_10', 'name': 'Veteran', 'description':'Reach Lv 10', 'level': 10, 'reward': 200, 'icon': '🎖️'},
        ]
        for ach in achievements_to_check:
            if level >= ach.get('level', 999): # Use get with high default
                self.add_achievement(user_id, ach)

    def _check_win_achievements(self, user_id: int):
        player = self.get_player(user_id);
        if not player: return; wins = player.get('wins', 0)
        achievements_to_check = [
            {'id': 'first_win', 'name': 'First Blood','description':'Win 1st game', 'wins': 1, 'reward': 50, 'icon': '🏆'},
            {'id': 'win_10', 'name': 'Skilled', 'description':'Win 10 games','wins': 10, 'reward': 150, 'icon': '🎯'},
        ]
        for ach in achievements_to_check:
             if wins >= ach.get('wins', 999999): # Use get with high default
                self.add_achievement(user_id, ach)

    def claim_daily_reward(self, user_id: int) -> tuple[bool, Optional[dict]]:
        player = self.get_player(user_id)
        if not player: return False, None

        now = datetime.now()
        last_claim_iso = player.get('last_daily_claim')
        can_claim = False

        if last_claim_iso:
            try:
                last_claim_date = datetime.fromisoformat(last_claim_iso)
                if now.date() > last_claim_date.date():
                    can_claim = True
                    # Check streak
                    if now.date() - last_claim_date.date() == timedelta(days=1):
                        player['streak'] = player.get('streak', 0) + 1
                    else:
                        player['streak'] = 1 # Reset streak
            except ValueError:
                 print(f"Warning: Invalid date format for last_daily_claim for user {user_id}. Resetting.")
                 can_claim = True
                 player['streak'] = 1
        else:
            # First time claiming
            can_claim = True
            player['streak'] = 1

        if not can_claim:
            return False, None # Already claimed today

        # Calculate reward
        streak = player.get('streak', 1)
        streak_multiplier = min(streak, 7) # Max 7 day streak bonus
        base_xp = 50
        base_coins = 25
        xp_reward = base_xp * streak_multiplier
        coin_reward = base_coins * streak_multiplier

        # Update player data
        player['last_daily_claim'] = now.isoformat()
        self.add_xp(user_id, xp_reward)
        self.add_coins(user_id, coin_reward)
        self.save_data()

        print(f"Player {user_id} claimed daily reward. Streak: {streak}")
        return True, {'xp': xp_reward, 'coins': coin_reward, 'streak': streak}

    def get_leaderboard(self, limit: int = 10) -> List[dict]:
        """Get top players by level and XP"""
        # Ensure players have level and xp before sorting
        valid_players = [p for p in self.players.values() if 'level' in p and 'xp' in p]
        sorted_players = sorted(
            valid_players,
            key=lambda p: (p.get('level', 0), p.get('xp', 0)),
            reverse=True
        )
        return sorted_players[:limit]

    def add_item(self, user_id: int, item_details: dict):
        """Add item to player inventory using item details from config"""
        player = self.get_player(user_id)
        if player and item_details:
            item_entry = {'id': item_details['id'], 'acquired_at': datetime.now().isoformat()}
            player.setdefault('items', [])
            # Avoid adding duplicates if needed, depending on item type
            if not any(i.get('id') == item_details['id'] for i in player['items']):
                 player['items'].append(item_entry)
                 self.save_data()
                 print(f"Added item {item_details['id']} to player {user_id}")

    def remove_item(self, user_id: int, item_id: str) -> bool:
        """Remove an item from player inventory by ID. Returns True if removed."""
        player = self.get_player(user_id)
        if not player or 'items' not in player: return False

        initial_length = len(player['items'])
        player['items'] = [item for item in player['items'] if item.get('id') != item_id]

        if len(player['items']) < initial_length:
            self.save_data()
            print(f"Removed item {item_id} from player {user_id}")
            return True # Item was found and removed
        return False # Item was not found

    def has_item(self, user_id: int, item_id: str) -> bool:
        """Check if player has an item"""
        player = self.get_player(user_id)
        # Use .get with default empty list for safety
        return player and any(item.get('id') == item_id for item in player.get('items', []))
