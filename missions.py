"""
Mission Manager - Handles mission generation and tracking
"""

import random
from typing import List, Dict
from config import MISSION_TEMPLATES


class MissionManager:
    def __init__(self):
        self.active_missions: Dict[str, List[dict]] = {}
    
    def generate_missions(self, game_mode: str, count: int = 3) -> List[dict]:
        """Generate random missions for a game mode"""
        templates = MISSION_TEMPLATES.get(game_mode, [])
        
        if not templates:
            return []
        
        # Select random missions
        selected = random.sample(templates, min(count, len(templates)))
        
        missions = []
        for template in selected:
            mission = {
                'id': template['id'],
                'name': template['name'],
                'description': template['description'],
                'reward_xp': template['reward_xp'],
                'reward_coins': template['reward_coins'],
                'completed': False,
                'progress': 0,
                'target': 1,
                'type': self._get_mission_type(template['id'])
            }
            missions.append(mission)
        
        return missions
    
    def _get_mission_type(self, mission_id: str) -> str:
        """Get mission type from ID"""
        if 'identify' in mission_id or 'find' in mission_id:
            return 'investigation'
        elif 'survive' in mission_id:
            return 'survival'
        elif 'win' in mission_id or 'defeat' in mission_id:
            return 'victory'
        elif 'protect' in mission_id:
            return 'support'
        else:
            return 'general'
    
    def check_mission_progress(self, game_id: str, player_id: int, action: str, result: dict):
        """Check and update mission progress"""
        if game_id not in self.active_missions:
            return []
        
        completed_missions = []
        
        for mission in self.active_missions[game_id]:
            if mission['completed']:
                continue
            
            if self._check_mission_condition(mission, action, result):
                mission['progress'] += 1
                
                if mission['progress'] >= mission['target']:
                    mission['completed'] = True
                    completed_missions.append(mission)
        
        return completed_missions
    
    def _check_mission_condition(self, mission: dict, action: str, result: dict) -> bool:
        """Check if action satisfies mission condition"""
        mission_id = mission['id']
        
        # Investigation missions
        if mission_id == 'identify_mafia' and action == 'investigate':
            return result.get('role') == 'mafia'
        
        # Survival missions
        if mission_id == 'survive_night' and action == 'survive_night':
            return True
        
        # Victory missions
        if 'win' in mission_id and action == 'game_end':
            return result.get('won', False)
        
        if mission_id == 'defeat_boss' and action == 'game_end':
            return result.get('won', False) and result.get('mode') == '1vboss'
        
        # Speed missions
        if mission_id == 'quick_win' and action == 'game_end':
            duration = result.get('duration', float('inf'))
            return result.get('won', False) and duration < 120
        
        return False
    
    def get_available_missions(self, player_level: int) -> List[dict]:
        """Get missions available for player level"""
        all_missions = []
        
        for mode, templates in MISSION_TEMPLATES.items():
            for template in templates:
                mission = template.copy()
                mission['mode'] = mode
                mission['level_required'] = self._get_mission_level_requirement(template['id'])
                
                if player_level >= mission['level_required']:
                    all_missions.append(mission)
        
        return all_missions
    
    def _get_mission_level_requirement(self, mission_id: str) -> int:
        """Get level requirement for mission"""
        level_requirements = {
            'identify_mafia': 1,
            'survive_night': 3,
            'quick_win': 5,
            'defeat_boss': 10,
            'perfect_game': 15
        }
        
        return level_requirements.get(mission_id, 1)
    
    def create_daily_missions(self, player_level: int) -> List[dict]:
        """Create daily missions for a player"""
        available = self.get_available_missions(player_level)
        
        if not available:
            return []
        
        # Select 3 random missions of different types
        missions = []
        types_used = set()
        
        random.shuffle(available)
        
        for mission in available:
            if len(missions) >= 3:
                break
            
            mission_type = self._get_mission_type(mission['id'])
            if mission_type not in types_used:
                missions.append(mission)
                types_used.add(mission_type)
        
        return missions
    
    def track_mission(self, game_id: str, missions: List[dict]):
        """Start tracking missions for a game"""
        self.active_missions[game_id] = missions
    
    def get_mission_rewards(self, mission: dict) -> dict:
        """Get rewards for completing a mission"""
        return {
            'xp': mission['reward_xp'],
            'coins': mission['reward_coins']
        }
    
    def format_mission_progress(self, mission: dict) -> str:
        """Format mission progress for display"""
        status = "✅" if mission['completed'] else "⏳"
        progress = f"{mission['progress']}/{mission['target']}"
        
        text = (
            f"{status} <b>{mission['name']}</b>\n"
            f"   {mission['description']}\n"
            f"   Progress: {progress}\n"
            f"   💎 {mission['reward_xp']} XP • 🪙 {mission['reward_coins']} Coins\n"
        )
        
        return text
    
    def get_mission_hint(self, mission_id: str) -> str:
        """Get hint for completing a mission"""
        hints = {
            'identify_mafia': "💡 Use your investigation wisely and look for suspicious behavior!",
            'survive_night': "💡 Stay alert and trust the Doctor's protection!",
            'quick_win': "💡 Be decisive and act fast to claim victory!",
            'defeat_boss': "💡 Teamwork makes the dream work! Coordinate with others!",
            'perfect_game': "💡 Play strategically and avoid any mistakes!"
        }
        
        return hints.get(mission_id, "💡 Good luck!")
    
    def cleanup_game_missions(self, game_id: str):
        """Remove missions after game ends"""
        if game_id in self.active_missions:
            del self.active_missions[game_id]
