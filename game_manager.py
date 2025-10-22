"""
Game Manager - Complete Implementation
"""

import random
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from player_manager import PlayerManager
from missions import MissionManager
from roles import RoleManager
from enhanced_features import replay_system # This is correct
from config import GAME_SETTINGS, RANDOM_EVENTS

# --- FIX: Import utils functions specifically ---
# We CANNOT import utils.* because utils imports this file.
# We must import only what this file needs at the function level
# or pass them in from mafia_bot_main.py.

# For now, we will rely on mafia_bot_main.py to send messages
# and this file to handle logic.

player_manager = PlayerManager()
mission_manager = MissionManager()
role_manager = RoleManager()


class GameManager:
    def __init__(self):
        self.games: Dict[str, dict] = {}
        self.game_counter = 0
        self.pending_actions: Dict[str, dict] = {}
    
    def check_game_end_condition(self, game: dict) -> tuple:
        """Check if game should end and return winner"""
        alive_players = [p for p in game['players'] if p['alive']]
        mafia_alive = sum(1 for p in alive_players if role_manager.get_role_team(p['role']) == 'mafia')
        villagers_alive = sum(1 for p in alive_players if role_manager.get_role_team(p['role']) == 'villagers')
        if mafia_alive == 0: return True, 'villagers'
        if mafia_alive >= villagers_alive: return True, 'mafia'
        return False, None

    def create_game(self, mode: str, creator_id: int, chat_id: int) -> str:
        """Create a new game lobby"""
        self.game_counter += 1
        # game_id = generate_game_id() # This function is in utils
        # Simple game ID for now
        game_id = f"G-{random.randint(100, 999)}-{self.game_counter}"

        creator = player_manager.get_player(creator_id)
        self.games[game_id] = {
            'id': game_id, 'mode': mode, 'creator_id': creator_id, 'chat_id': chat_id,
            'players': [{
                'user_id': creator_id, 'username': creator['username'], 'role': None,
                'alive': True, 'votes': 0, 'protected': False, 'investigated': False,
                'items_used': [], 'last_protected': None
            }],
            'status': 'waiting', 'phase': 'day', 'round': 0, 'started_at': None,
            'winner': None, 'missions': [], 'events': [], 'night_actions': {},
            'day_votes': {}, 'active_event': None
        }
        self.pending_actions[game_id] = {}
        return game_id
    
    def get_game(self, game_id: str) -> Optional[dict]:
        return self.games.get(game_id)
    
    def get_required_players(self, mode: str) -> int:
        return GAME_SETTINGS.get(mode, {}).get('min_players', 2)
    
    def join_game(self, game_id: str, user_id: int, username: str) -> Tuple[bool, str]:
        game = self.get_game(game_id)
        if not game: return False, "Game not found!"
        if game['status'] != 'waiting': return False, "Game already started!"
        if any(p['user_id'] == user_id for p in game['players']):
            return False, "You're already in this game!"
        
        max_players = GAME_SETTINGS.get(game['mode'], {}).get('max_players', 10)
        if len(game['players']) >= max_players: return False, "Game lobby is full!"
        
        game['players'].append({
            'user_id': user_id, 'username': username, 'role': None, 'alive': True,
            'votes': 0, 'protected': False, 'investigated': False,
            'items_used': [], 'last_protected': None
        })
        player_manager.register_player(user_id, username)
        return True, f"{username} joined!"
    
    def start_game(self, game_id: str, user_id: int) -> Tuple[bool, str]:
        game = self.get_game(game_id)
        if not game: return False, "Game not found!"
        if game['creator_id'] != user_id: return False, "Only creator can start!"
        if game['status'] != 'waiting': return False, "Game already started!"
        required = self.get_required_players(game['mode'])
        if len(game['players']) < required: return False, f"Need {required} players!"
        max_players = GAME_SETTINGS.get(game['mode'], {}).get('max_players', 10)
        if len(game['players']) > max_players: return False, f"Too many players! Max is {max_players}."

        self._assign_roles(game)
        game['missions'] = mission_manager.generate_missions(game['mode'])
        game['status'] = 'in_progress'; game['started_at'] = datetime.now()
        game['round'] = 1; game['phase'] = 'night'
        return True, "Game started!"
    
    def _assign_roles(self, game: dict):
        mode = game['mode']
        roles = role_manager.assign_roles(len(game['players']), mode)
        players_to_assign = game['players'][:len(roles)]
        for player, role in zip(players_to_assign, roles):
            player['role'] = role
            player['abilities'] = role_manager.get_role_abilities(role)
            player_manager.record_role_played(player['user_id'], role)
    
    def get_role_description(self, role: str) -> str:
        return role_manager.format_role_card(role)
    
    async def start_round(self, game_id: str, message, context):
        """ message and context are passed from mafia_bot_main.py """
        game = self.get_game(game_id)
        if not game: return
        self._trigger_random_event(game)
        if game['phase'] == 'night':
            await self._night_phase(game_id, message, context)
        elif game['phase'] == 'day':
            await self._day_phase(game_id, message, context)
    
    def _trigger_random_event(self, game: dict):
        if random.random() < 0.15:
            event = random.choice(RANDOM_EVENTS); game['active_event'] = event
            game['events'].append(event)
    
    async def _night_phase(self, game_id: str, message, context):
        game = self.get_game(game_id)
        night_duration = GAME_SETTINGS[game['mode']]['night_duration']
        text = f"🌙 <b>NIGHT {game['round']}</b> 🌙\nTown sleeps..."
        if game.get('active_event'): text += f"\n{game['active_event']['name']}\n{game['active_event']['description']}"
        text += f"\nRoles act!\n⏰ {night_duration}s"
        
        # We must import utils here to avoid circular import at top level
        from utils import send_phase_transition, create_player_action_keyboard
        await send_phase_transition(message, 'night')
        await message.reply_text(text, parse_mode='HTML')
        
        for player in game['players']:
            if not player['alive']: continue
            if player['role'] in ['mafia', 'godfather']:
                await self._send_mafia_action(game_id, player, context)
            elif player['role'] == 'detective':
                await self._send_detective_action(game_id, player, context)
            elif player['role'] == 'doctor':
                await self._send_doctor_action(game_id, player, context)
        
        await asyncio.sleep(night_duration)
        await self._process_night_actions(game_id, message, context)
    
    async def _send_mafia_action(self, game_id: str, player: dict, context):
        from utils import create_player_action_keyboard # Local import
        game = self.get_game(game_id)
        targets = [p for p in game['players'] if p['alive'] and role_manager.get_role_team(p['role']) != 'mafia']
        if not targets: return
        keyboard = create_player_action_keyboard('kill', targets)
        try: await context.bot.send_message(player['user_id'], "🔪 <b>Choose target:</b>", parse_mode='HTML', reply_markup=keyboard)
        except Exception as e: print(f"Error sending mafia action: {e}")
    
    async def _send_detective_action(self, game_id: str, player: dict, context):
        from utils import create_player_action_keyboard # Local import
        game = self.get_game(game_id)
        targets = [p for p in game['players'] if p['alive'] and p['user_id'] != player['user_id']]
        if not targets: return
        keyboard = create_player_action_keyboard('investigate', targets)
        try: await context.bot.send_message(player['user_id'], "🔍 <b>Investigate who?</b>", parse_mode='HTML', reply_markup=keyboard)
        except Exception as e: print(f"Error sending detective action: {e}")
    
    async def _send_doctor_action(self, game_id: str, player: dict, context):
        from utils import create_player_action_keyboard # Local import
        game = self.get_game(game_id)
        targets = [p for p in game['players'] if p['alive']]
        if not targets: return
        keyboard = create_player_action_keyboard('protect', targets)
        try: await context.bot.send_message(player['user_id'], "💉 <b>Protect who?</b>", parse_mode='HTML', reply_markup=keyboard)
        except Exception as e: print(f"Error sending doctor action: {e}")
    
    async def _process_night_actions(self, game_id: str, message, context):
        from utils import send_animated_message, send_elimination_animation, format_night_summary # Local import
        game = self.get_game(game_id)
        actions = self.pending_actions.get(game_id, {})
        await send_animated_message(message, ["⚡ Processing...", "🌙 Night reveals..."], delay=1.5)
        
        kill_target, protect_target, investigate_target = actions.get('kill'), actions.get('protect'), actions.get('investigate')
        eliminated_player, protected, investigation_result = None, False, None
        
        for player in game['players']: player['protected'] = False
        if protect_target:
            for player in game['players']:
                if player['user_id'] == protect_target: player['protected'] = True; protected = True; break
        if kill_target:
            for player in game['players']:
                if player['user_id'] == kill_target:
                    if player.get('protected', False): protected = True
                    else: player['alive'] = False; eliminated_player = player
                    break
        if investigate_target:
            for player in game['players']:
                if player['user_id'] == investigate_target:
                    if player['role'] == 'godfather': investigation_result = {'player': player, 'result': 'innocent'}
                    else: investigation_result = {'player': player, 'result': 'mafia' if role_manager.get_role_team(player['role']) == 'mafia' else 'innocent'}
                    break
        
        if investigation_result:
            detective = next((p for p in game['players'] if p['role'] == 'detective' and p['alive']), None)
            if detective:
                try: await context.bot.send_message(detective['user_id'], f"🔍 Result for <b>{investigation_result['player']['username']}</b>: <b>{investigation_result['result'].upper()}</b>", parse_mode='HTML')
                except: pass
        
        if eliminated_player:
            await send_elimination_animation(message, eliminated_player['username'], eliminated_player['role'])
        else:
            summary = format_night_summary(eliminated_player, {'protected': protected})
            await message.reply_text(summary, parse_mode='HTML')
        
        self.pending_actions[game_id] = {}
        game_ended, winner = self.check_game_end_condition(game) # Use self method
        if game_ended: await self._end_game(game_id, winner, message, context); return
        game['phase'] = 'day'; await asyncio.sleep(2)
        await self._day_phase(game_id, message, context)
    
    async def _day_phase(self, game_id: str, message, context):
        from utils import send_phase_transition, create_voting_keyboard # Local import
        game = self.get_game(game_id)
        await send_phase_transition(message, 'day')
        day_duration = GAME_SETTINGS[game['mode']]['day_duration']
        alive_players = [p for p in game['players'] if p['alive']]
        text = f"☀️ <b>DAY {game['round']}</b> ☀️\nTown gathers to vote!\n<b>Alive ({len(alive_players)}):</b>\n"
        text += "\n".join(f"• {p['username']}" for p in alive_players)
        text += f"\n⏰ {day_duration}s to vote!"
        keyboard = create_voting_keyboard(alive_players)
        await message.reply_text(text, parse_mode='HTML', reply_markup=keyboard)
        await asyncio.sleep(day_duration)
        await self._process_day_votes(game_id, message, context)
    
    async def _process_day_votes(self, game_id: str, message, context):
        from utils import format_vote_results, format_day_summary # Local import
        game = self.get_game(game_id); votes = game.get('day_votes', {}); eliminated_player = None
        if not votes:
            await message.reply_text("🤷 <b>No votes cast!</b> Moving on...", parse_mode='HTML')
        else:
            vote_counts = {}
            for target_id in votes.values():
                if target_id == 'skip': continue
                target_id = int(target_id); vote_counts[target_id] = vote_counts.get(target_id, 0) + 1
            results_text = format_vote_results(game, vote_counts)
            await message.reply_text(results_text, parse_mode='HTML')
            if vote_counts:
                sorted_votes = sorted(vote_counts.items(), key=lambda x: x[1], reverse=True)
                if len(sorted_votes) > 1 and sorted_votes[0][1] == sorted_votes[1][1]:
                    await message.reply_text("⚖️ <b>A tie!</b> No one is eliminated.", parse_mode='HTML')
                else:
                    eliminated_id = sorted_votes[0][0]
                    for player in game['players']:
                        if player['user_id'] == eliminated_id:
                            player['alive'] = False; eliminated_player = player; break
                    if eliminated_player:
                        summary = format_day_summary(eliminated_player, vote_counts[eliminated_id])
                        await message.reply_text(summary, parse_mode='HTML')
            else: await message.reply_text("🤷 <b>Only skip votes!</b> Moving on...", parse_mode='HTML')
        
        game['day_votes'] = {}
        game_ended, winner = self.check_game_end_condition(game) # Use self method
        if game_ended: await self._end_game(game_id, winner, message, context); return
        game['round'] += 1; game['phase'] = 'night'; await asyncio.sleep(3)
        await self._night_phase(game_id, message, context)
    
    async def handle_action(self, update, context):
        from telegram import ReplyKeyboardRemove # Local import
        message, text, user_id = update.message, message.text, update.effective_user.id
        game_id, action_type = None, None
        for gid, game in self.games.items():
            if game['status'] == 'in_progress' and game['phase'] == 'night':
                for player in game['players']:
                    if player['user_id'] == user_id and player['alive']:
                        game_id, action_type = gid, self._detect_action_type(text, player['role']); break
                if game_id: break
        if not game_id or not action_type: return
        target_username = text.split(maxsplit=1)[1] if len(text.split()) > 1 else None
        if target_username:
            game = self.get_game(game_id)
            target_player = next((p for p in game['players'] if p['username'] == target_username and p['alive']), None)
            if target_player:
                self.pending_actions.setdefault(game_id, {})[action_type] = target_player['user_id']
                await message.reply_text(f"✅ Action recorded: {target_username}", parse_mode='HTML', reply_markup=ReplyKeyboardRemove())
    
    def _detect_action_type(self, text: str, role: str) -> Optional[str]:
        if '🔪' in text and role in ['mafia', 'godfather']: return 'kill'
        if '🔍' in text and role == 'detective': return 'investigate'
        if '💉' in text and role == 'doctor': return 'protect'
        return None
    
    async def handle_vote(self, update, context):
        from telegram import ReplyKeyboardRemove # Local import
        message, text, user_id = update.message, message.text, update.effective_user.id
        game_id = None
        for gid, game in self.games.items():
            if game['status'] == 'in_progress' and game['phase'] == 'day':
                if any(p['user_id'] == user_id and p['alive'] for p in game['players']): game_id = gid; break
        if not game_id: return
        game = self.get_game(game_id)
        if '⏭️' in text or 'Skip' in text:
            game['day_votes'][user_id] = 'skip'
            await message.reply_text("✅ Vote skipped!", parse_mode='HTML', reply_markup=ReplyKeyboardRemove())
            return
        if '🗳️' in text or 'Vote:' in text:
            target_username = text.split(':')[-1].strip() if ':' in text else text.split()[-1]
            target_player = next((p for p in game['players'] if p['username'] == target_username and p['alive']), None)
            if target_player:
                game['day_votes'][user_id] = target_player['user_id']
                await message.reply_text(f"✅ Vote recorded for: {target_username}", parse_mode='HTML', reply_markup=ReplyKeyboardRemove())
    
    async def _end_game(self, game_id: str, winner: str, message, context):
        from utils import send_victory_animation, create_main_menu_keyboard # Local import
        game = self.get_game(game_id)
        if game['status'] == 'finished': return
        game['status'], game['winner'] = 'finished', winner
        winners, losers = [], []
        for player in game['players']:
            is_evil = role_manager.is_evil_role(player['role'])
            if (winner == 'villagers' and not is_evil) or (winner == 'mafia' and is_evil): winners.append(player)
            else: losers.append(player)
        
        await send_victory_animation(message, winner, winners)
        for player in winners:
            player_manager.add_win(player['user_id']); rewards = self._calculate_rewards(game, player, True)
            player_manager.add_xp(player['user_id'], rewards['xp']); player_manager.add_coins(player['user_id'], rewards['coins'])
        for player in losers:
            player_manager.add_loss(player['user_id']); rewards = self._calculate_rewards(game, player, False)
            player_manager.add_xp(player['user_id'], rewards['xp']); player_manager.add_coins(player['user_id'], rewards['coins'])
        
        stats_text = self._format_game_stats(game, winners)
        keyboard = create_main_menu_keyboard() # This is a ReplyKeyboardMarkup
        await message.reply_text(stats_text, parse_mode='HTML', reply_markup=keyboard)
        
        replay_system.save_replay(game_id, game)
        if game_id in self.pending_actions: del self.pending_actions[game_id]
    
    def _calculate_rewards(self, game: dict, player: dict, won: bool) -> dict:
        base_xp = GAME_SETTINGS[game['mode']]['base_xp_reward']
        base_coins = 50; rewards = {'xp': base_xp, 'coins': base_coins}
        if won: rewards['xp'] += 100; rewards['coins'] += 50
        if player['alive']: rewards['xp'] += 50; rewards['coins'] += 25
        return rewards
    
    def _format_game_stats(self, game: dict, winners: list) -> str:
        text = (f"📊 <b>GAME STATS</b> 📊\n🆔: {game['id']}\n🎯: {game['mode'].upper()}\n"
                f"🔄: {game['round']}\n🏆: {game['winner'].upper()}\n\n<b>Roles:</b>\n")
        text += "\n".join(f"{'✅' if p['alive'] else '💀'} {p['username']} - {p['role'].upper()}" for p in game['players'])
        return text
    
    def cancel_game(self, game_id: str, user_id: int) -> Tuple[bool, str]:
        game = self.get_game(game_id)
        if not game: return False, "Game not found!"
        if game['creator_id'] != user_id: return False, "Only creator can cancel!"
        if game['status'] != 'waiting': return False, "Game in progress!"
        del self.games[game_id]
        if game_id in self.pending_actions: del self.pending_actions[game_id]
        return True, "Game cancelled!"

# This global instance is used by utils.py
game_manager = GameManager()
