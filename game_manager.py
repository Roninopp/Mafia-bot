"""
Game Manager - Handles all game logic and state management
"""

import random
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from player_manager import PlayerManager
from missions import MissionManager
from roles import RoleManager

player_manager = PlayerManager()
mission_manager = MissionManager()
role_manager = RoleManager()


class GameManager:
    def __init__(self):
        self.games: Dict[str, dict] = {}
        self.game_counter = 0
    
    def create_game(self, mode: str, creator_id: int, chat_id: int) -> str:
        """Create a new game lobby"""
        self.game_counter += 1
        game_id = f"game_{self.game_counter}_{int(datetime.now().timestamp())}"
        
        creator = player_manager.get_player(creator_id)
        
        self.games[game_id] = {
            'id': game_id,
            'mode': mode,
            'creator_id': creator_id,
            'chat_id': chat_id,
            'players': [{
                'user_id': creator_id,
                'username': creator['username'],
                'role': None,
                'alive': True,
                'votes': 0,
                'protected': False,
                'investigated': False
            }],
            'status': 'waiting',  # waiting, in_progress, finished
            'phase': 'day',  # day, night, voting
            'round': 0,
            'started_at': None,
            'winner': None,
            'missions': [],
            'events': []
        }
        
        return game_id
    
    def get_game(self, game_id: str) -> Optional[dict]:
        """Get game by ID"""
        return self.games.get(game_id)
    
    def get_required_players(self, mode: str) -> int:
        """Get required number of players for mode"""
        requirements = {
            '5v5': 10,
            '1v1': 2,
            '1vboss': 5
        }
        return requirements.get(mode, 2)
    
    def join_game(self, game_id: str, user_id: int, username: str) -> Tuple[bool, str]:
        """Join a game lobby"""
        game = self.get_game(game_id)
        
        if not game:
            return False, "Game not found!"
        
        if game['status'] != 'waiting':
            return False, "Game already started!"
        
        # Check if already joined
        if any(p['user_id'] == user_id for p in game['players']):
            return False, "You're already in this game!"
        
        # Check if lobby is full
        max_players = self.get_required_players(game['mode'])
        if len(game['players']) >= max_players:
            return False, "Game lobby is full!"
        
        # Add player
        game['players'].append({
            'user_id': user_id,
            'username': username,
            'role': None,
            'alive': True,
            'votes': 0,
            'protected': False,
            'investigated': False
        })
        
        return True, f"{username} joined the game!"
    
    def start_game(self, game_id: str, user_id: int) -> Tuple[bool, str]:
        """Start a game"""
        game = self.get_game(game_id)
        
        if not game:
            return False, "Game not found!"
        
        if game['creator_id'] != user_id:
            return False, "Only the creator can start the game!"
        
        if game['status'] != 'waiting':
            return False, "Game already started!"
        
        required = self.get_required_players(game['mode'])
        if len(game['players']) < required:
            return False, f"Need {required} players to start!"
        
        # Assign roles
        self._assign_roles(game)
        
        # Initialize missions
        game['missions'] = mission_manager.generate_missions(game['mode'])
        
        # Update game state
        game['status'] = 'in_progress'
        game['started_at'] = datetime.now()
        game['round'] = 1
        game['phase'] = 'night'
        
        return True, "Game started!"
    
    def _assign_roles(self, game: dict):
        """Assign roles to players based on game mode"""
        mode = game['mode']
        players = game['players']
        
        if mode == '5v5':
            roles = ['mafia'] * 3 + ['detective'] * 1 + ['doctor'] * 1 + ['villager'] * 5
        elif mode == '1v1':
            roles = ['mafia', 'detective']
        elif mode == '1vboss':
            roles = ['boss'] + ['villager'] * (len(players) - 1)
        else:
            roles = ['villager'] * len(players)
        
        random.shuffle(roles)
        
        for player, role in zip(players, roles):
            player['role'] = role
            player['abilities'] = role_manager.get_role_abilities(role)
    
    def get_role_description(self, role: str) -> str:
        """Get role description"""
        descriptions = {
            'mafia': (
                "🔪 <b>MAFIA</b>\n"
                "You are part of the Mafia! Your goal is to eliminate all villagers.\n"
                "• Eliminate one player each night\n"
                "• Blend in during the day\n"
                "• Coordinate with other Mafia members"
            ),
            'detective': (
                "🔍 <b>DETECTIVE</b>\n"
                "You can investigate players to discover their role.\n"
                "• Investigate one player each night\n"
                "• Share information carefully\n"
                "• Lead the villagers to victory"
            ),
            'doctor': (
                "💉 <b>DOCTOR</b>\n"
                "You can protect one player from elimination each night.\n"
                "• Choose wisely\n"
                "• You cannot protect the same player twice in a row\n"
                "• Save the innocent!"
            ),
            'villager': (
                "👥 <b>VILLAGER</b>\n"
                "You are an innocent villager. Work with others to find the Mafia.\n"
                "• Vote during the day\n"
                "• Discuss and deduce\n"
                "• Trust carefully"
            ),
            'boss': (
                "👑 <b>BOSS</b>\n"
                "You are the powerful Mafia Boss! Survive the hunters.\n"
                "• Special abilities\n"
                "• Extra protection\n"
                "• Defeat them all!"
            )
        }
        return descriptions.get(role, "Unknown role")
    
    async def start_round(self, game_id: str, message, context):
        """Start a new round"""
        game = self.get_game(game_id)
        
        if game['phase'] == 'night':
            await self._night_phase(game_id, message, context)
        elif game['phase'] == 'day':
            await self._day_phase(game_id, message, context)
    
    async def _night_phase(self, game_id: str, message, context):
        """Handle night phase"""
        game = self.get_game(game_id)
        
        text = (
            f"🌙 <b>NIGHT {game['round']}</b> 🌙\n\n"
            "The town sleeps... but evil lurks in the shadows.\n\n"
            "🔪 Mafia, choose your target\n"
            "🔍 Detective, investigate someone\n"
            "💉 Doctor, protect someone\n\n"
            "⏰ You have 60 seconds!"
        )
        
        await message.reply_text(text, parse_mode='HTML')
        
        # Send action prompts to role players
        for player in game['players']:
            if not player['alive']:
                continue
            
            if player['role'] == 'mafia':
                await self._send_mafia_action(game_id, player, context)
            elif player['role'] == 'detective':
                await self._send_detective_action(game_id, player, context)
            elif player['role'] == 'doctor':
                await self._send_doctor_action(game_id, player, context)
        
        # Wait for actions (60 seconds)
        await asyncio.sleep(60)
        
        # Process night actions
        await self._process_night_actions(game_id, message, context)
    
    async def _send_mafia_action(self, game_id: str, player: dict, context):
        """Send mafia action choice"""
        game = self.get_game(game_id)
        
        keyboard = []
        for p in game['players']:
            if p['alive'] and p['role'] != 'mafia':
                keyboard.append([
                    InlineKeyboardButton(
                        f"🔪 Eliminate {p['username']}",
                        callback_data=f"action_kill_{game_id}_{p['user_id']}"
                    )
                ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        try:
            await context.bot.send_message(
                chat_id=player['user_id'],
                text="🔪 <b>Choose your target:</b>",
                parse_mode='HTML',
                reply_markup=reply_markup
            )
        except:
            pass
    
    async def _send_detective_action(self, game_id: str, player: dict, context):
        """Send detective action choice"""
        game = self.get_game(game_id)
        
        keyboard = []
        for p in game['players']:
            if p['alive'] and p['user_id'] != player['user_id']:
                keyboard.append([
                    InlineKeyboardButton(
                        f"🔍 Investigate {p['username']}",
                        callback_data=f"action_investigate_{game_id}_{p['user_id']}"
                    )
                ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        try:
            await context.bot.send_message(
                chat_id=player['user_id'],
                text="🔍 <b>Who do you want to investigate?</b>",
                parse_mode='HTML',
                reply_markup=reply_markup
            )
        except:
            pass
    
    async def _send_doctor_action(self, game_id: str, player: dict, context):
        """Send doctor action choice"""
        game = self.get_game(game_id)
        
        keyboard = []
        for p in game['players']:
            if p['alive']:
                keyboard.append([
                    InlineKeyboardButton(
                        f"💉 Protect {p['username']}",
                        callback_data=f"action_protect_{game_id}_{p['user_id']}"
                    )
                ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        try:
            await context.bot.send_message(
                chat_id=player['user_id'],
                text="💉 <b>Who do you want to protect?</b>",
                parse_mode='HTML',
                reply_markup=reply_markup
            )
        except:
            pass
    
    async def _process_night_actions(self, game_id: str, message, context):
        """Process all night actions"""
        game = self.get_game(game_id)
        
        # Animation
        await asyncio.sleep(2)
        await message.reply_text("⚡ Processing night actions...")
        await asyncio.sleep(2)
        
        # Check for eliminations and protections
        eliminate
