"""
Game Manager - Handles game logic
"""

import random
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from player_manager import PlayerManager
from missions import MissionManager
from roles import RoleManager
from enhanced_features import replay_system # Import the instance
from config import GAME_SETTINGS, RANDOM_EVENTS

# We must import utils locally inside functions to avoid circular import

# Define player_manager, mission_manager, role_manager at module level
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
        alive_players = [p for p in game.get('players', []) if p and p.get('alive')]
        if not alive_players: return True, 'draw' # Or handle appropriately

        mafia_alive = sum(1 for p in alive_players if role_manager.get_role_team(p.get('role','')) == 'mafia')
        villagers_alive = sum(1 for p in alive_players if role_manager.get_role_team(p.get('role','')) == 'villagers')

        if mafia_alive == 0: return True, 'villagers'
        if mafia_alive >= villagers_alive: return True, 'mafia'
        return False, None

    def create_game(self, mode: str, creator_id: int, chat_id: int) -> str:
        """Create a new game lobby"""
        from utils import generate_game_id # Local import
        self.game_counter += 1
        game_id = generate_game_id()

        creator = player_manager.get_player(creator_id)
        creator_username = 'Unknown'
        if creator and isinstance(creator, dict): # Check if creator exists and is dict
             creator_username = creator.get('username', f'User_{creator_id}')
        else:
             print(f"Warning: Creator {creator_id} not found or invalid data.")
             # Register just in case
             creator = player_manager.register_player(creator_id, f'User_{creator_id}')
             creator_username = creator.get('username', f'User_{creator_id}')


        self.games[game_id] = {
            'id': game_id, 'mode': mode, 'creator_id': creator_id, 'chat_id': chat_id,
            'players': [{
                'user_id': creator_id, 'username': creator_username, 'role': None,
                'alive': True, 'votes': 0, 'protected': False, 'investigated': False,
                'items_used': [], 'last_protected': None
            }],
            'status': 'waiting', 'phase': 'day', 'round': 0, 'started_at': None,
            'winner': None, 'missions': [], 'events': [], 'night_actions': {},
            'day_votes': {}, 'active_event': None
        }
        self.pending_actions[game_id] = {}
        print(f"Created game {game_id} in chat {chat_id}")
        return game_id

    def get_game(self, game_id: str) -> Optional[dict]:
        return self.games.get(game_id)

    def get_required_players(self, mode: str) -> int:
        # Use max_players for fixed size modes
        return GAME_SETTINGS.get(mode, {}).get('max_players', 2)

    def join_game(self, game_id: str, user_id: int, username: str) -> Tuple[bool, str]:
        game = self.get_game(game_id)
        if not game: return False, "Game not found!"
        if game.get('status') != 'waiting': return False, "Game already started!"
        if any(p.get('user_id') == user_id for p in game.get('players', [])):
            return False, "You're already in this game!"

        max_players = GAME_SETTINGS.get(game.get('mode'), {}).get('max_players', 10)
        if len(game.get('players', [])) >= max_players: return False, "Game lobby is full!"

        game.setdefault('players', []).append({
            'user_id': user_id, 'username': username, 'role': None, 'alive': True,
            'votes': 0, 'protected': False, 'investigated': False,
            'items_used': [], 'last_protected': None
        })
        player_manager.register_player(user_id, username)
        print(f"Player {username} joined game {game_id}")
        return True, f"{username} joined!"

    def start_game(self, game_id: str, user_id: int) -> Tuple[bool, str]:
        game = self.get_game(game_id)
        if not game: return False, "Game not found!"
        if game.get('creator_id') != user_id: return False, "Only creator can start!"
        if game.get('status') != 'waiting': return False, "Game already started!"
        required = self.get_required_players(game.get('mode',''))
        if len(game.get('players', [])) < required: return False, f"Need {required} players!"

        self._assign_roles(game)
        game['missions'] = mission_manager.generate_missions(game.get('mode',''))
        game['status'] = 'in_progress'; game['started_at'] = datetime.now().isoformat()
        game['round'] = 1; game['phase'] = 'night'
        print(f"Game {game_id} started by {user_id}")
        return True, "Game started!"

    def _assign_roles(self, game: dict):
        mode = game.get('mode','')
        num_players = len(game.get('players', []))
        roles = role_manager.assign_roles(num_players, mode)
        players_to_assign = game.get('players', [])[:len(roles)] # Slice safely
        print(f"Assigning roles for game {game.get('id','?')}: {roles}")
        for player, role in zip(players_to_assign, roles):
            if player and isinstance(player, dict): # Safety check
                player['role'] = role
                player['abilities'] = role_manager.get_role_abilities(role)
                player_manager.record_role_played(player.get('user_id'), role)

    def get_role_description(self, role: str) -> str:
        return role_manager.format_role_card(role)

    async def start_round(self, game_id: str, message, context):
        """ message and context are passed from mafia_bot_main.py """
        game = self.get_game(game_id)
        if not game or game.get('status') != 'in_progress': return
        print(f"Starting round {game.get('round', '?')} phase {game.get('phase','?')} for game {game_id}")
        self._trigger_random_event(game)
        if game.get('phase') == 'night':
            await self._night_phase(game_id, message, context)
        elif game.get('phase') == 'day':
            await self._day_phase(game_id, message, context)

    def _trigger_random_event(self, game: dict):
        if random.random() < 0.15:
            event = random.choice(RANDOM_EVENTS); game['active_event'] = event
            game.setdefault('events', []).append(event)
            print(f"Triggered event {event.get('id','?')} for game {game.get('id','?')}")

    async def _night_phase(self, game_id: str, message, context):
        from utils import send_phase_transition # Local import
        game = self.get_game(game_id)
        if not game: return

        night_duration = GAME_SETTINGS.get(game.get('mode',{}), {}).get('night_duration', 30)
        text = f"🌙 <b>NIGHT {game.get('round', '?')}</b> 🌙\nTown sleeps..."
        active_event = game.get('active_event')
        if active_event: text += f"\n{active_event.get('name','?')}\n{active_event.get('description','?')}"
        text += f"\nRoles act!\n⏰ {night_duration}s"

        await send_phase_transition(message, 'night')
        # Use reply_text from the message object passed in
        await message.reply_text(text, parse_mode='HTML')

        for player in game.get('players', []):
            if not player or not player.get('alive'): continue
            role = player.get('role')
            if role in ['mafia', 'godfather']:
                await self._send_mafia_action(game_id, player, context)
            elif role == 'detective':
                await self._send_detective_action(game_id, player, context)
            elif role == 'doctor':
                await self._send_doctor_action(game_id, player, context)
            # Add other roles like Vigilante here if implemented

        await asyncio.sleep(night_duration)
        await self._process_night_actions(game_id, message, context)

    async def _send_mafia_action(self, game_id: str, player: dict, context):
        from utils import create_player_action_keyboard
        game = self.get_game(game_id)
        targets = [p for p in game.get('players', []) if p and p.get('alive') and role_manager.get_role_team(p.get('role','')) != 'mafia']
        if not targets: return
        keyboard = create_player_action_keyboard('kill', targets)
        try: await context.bot.send_message(player.get('user_id'), "🔪 <b>Choose target:</b>", parse_mode='HTML', reply_markup=keyboard)
        except Exception as e: print(f"Error sending mafia action to {player.get('user_id')}: {e}")

    async def _send_detective_action(self, game_id: str, player: dict, context):
        from utils import create_player_action_keyboard
        game = self.get_game(game_id)
        targets = [p for p in game.get('players', []) if p and p.get('alive') and p.get('user_id') != player.get('user_id')]
        if not targets: return
        keyboard = create_player_action_keyboard('investigate', targets)
        try: await context.bot.send_message(player.get('user_id'), "🔍 <b>Investigate who?</b>", parse_mode='HTML', reply_markup=keyboard)
        except Exception as e: print(f"Error sending detective action to {player.get('user_id')}: {e}")

    async def _send_doctor_action(self, game_id: str, player: dict, context):
        from utils import create_player_action_keyboard
        game = self.get_game(game_id)
        targets = [p for p in game.get('players', []) if p and p.get('alive')]
        if not targets: return
        keyboard = create_player_action_keyboard('protect', targets)
        try: await context.bot.send_message(player.get('user_id'), "💉 <b>Protect who?</b>", parse_mode='HTML', reply_markup=keyboard)
        except Exception as e: print(f"Error sending doctor action to {player.get('user_id')}: {e}")

    async def _process_night_actions(self, game_id: str, message, context):
        from utils import send_animated_message, send_elimination_animation, format_night_summary
        game = self.get_game(game_id)
        if not game: return
        actions = self.pending_actions.get(game_id, {})
        await send_animated_message(message, ["⚡ Processing...", "🌙 Night reveals..."], delay=1.5)

        kill_target, protect_target, investigate_target = actions.get('kill'), actions.get('protect'), actions.get('investigate')
        eliminated_player, protected, investigation_result = None, False, None

        for player in game.get('players', []): player['protected'] = False # Reset protection

        # Process protection
        if protect_target:
            for player in game.get('players', []):
                if player.get('user_id') == protect_target: player['protected'] = True; protected = True; break

        # Process kill
        if kill_target:
            for player in game.get('players', []):
                if player.get('user_id') == kill_target:
                    if not player.get('protected', False):
                         player['alive'] = False; eliminated_player = player
                         print(f"Player {player.get('username')} eliminated in {game_id}")
                    else:
                         protected = True # Kill was blocked
                    break

        # Process investigation
        if investigate_target:
            for player in game.get('players', []):
                if player.get('user_id') == investigate_target:
                    role = player.get('role', '')
                    result = 'innocent' # Default
                    if role == 'godfather': result = 'innocent' # Godfather appears innocent
                    elif role_manager.get_role_team(role) == 'mafia': result = 'mafia'
                    investigation_result = {'player': player, 'result': result}
                    break

        # Send investigation result
        if investigation_result:
            detective = next((p for p in game.get('players', []) if p.get('role') == 'detective' and p.get('alive')), None)
            if detective:
                target_username = investigation_result['player'].get('username', 'Unknown')
                result = investigation_result['result'].upper()
                try: await context.bot.send_message(detective['user_id'], f"🔍 Result for <b>{target_username}</b>: <b>{result}</b>", parse_mode='HTML')
                except Exception as e: print(f"Failed to send invest result to {detective.get('user_id')}: {e}")

        # Announce results
        if eliminated_player:
            await send_elimination_animation(message, eliminated_player.get('username','?'), eliminated_player.get('role','?'))
        else:
            summary = format_night_summary(None, {'protected': protected}) # Pass correct protected status
            await message.reply_text(summary, parse_mode='HTML')

        self.pending_actions[game_id] = {} # Clear actions for next round
        game['active_event'] = None # Clear event

        game_ended, winner = self.check_game_end_condition(game)
        if game_ended: await self._end_game(game_id, winner, message, context); return

        game['phase'] = 'day'; await asyncio.sleep(2)
        await self._day_phase(game_id, message, context)

    async def _day_phase(self, game_id: str, message, context):
        from utils import send_phase_transition, create_voting_keyboard
        game = self.get_game(game_id)
        if not game: return
        await send_phase_transition(message, 'day')
        day_duration = GAME_SETTINGS.get(game.get('mode',{}), {}).get('day_duration', 60)
        alive_players = [p for p in game.get('players', []) if p and p.get('alive')]
        text = f"☀️ <b>DAY {game.get('round','?')}</b> ☀️\nTown gathers!\n<b>Alive ({len(alive_players)}):</b>\n"
        text += "\n".join(f"• {p.get('username','?')}" for p in alive_players)
        text += f"\n⏰ {day_duration}s to vote!"
        keyboard = create_voting_keyboard(alive_players)
        await message.reply_text(text, parse_mode='HTML', reply_markup=keyboard)
        await asyncio.sleep(day_duration)
        await self._process_day_votes(game_id, message, context)

    async def _process_day_votes(self, game_id: str, message, context):
        from utils import format_vote_results, format_day_summary
        from telegram import ReplyKeyboardRemove # Needed to remove keyboard

        game = self.get_game(game_id);
        if not game: return
        votes = game.get('day_votes', {}); eliminated_player = None

        # Remove voting keyboard first
        await message.reply_text("Processing votes...", reply_markup=ReplyKeyboardRemove())

        if not votes:
            await message.reply_text("🤷 <b>No votes cast!</b> Moving on...", parse_mode='HTML')
        else:
            vote_counts = {}
            for target_id in votes.values():
                if target_id == 'skip': continue
                try: # Ensure target_id is valid int
                    target_id = int(target_id)
                    vote_counts[target_id] = vote_counts.get(target_id, 0) + 1
                except ValueError:
                     print(f"Warning: Invalid target_id '{target_id}' in votes for game {game_id}")

            results_text = format_vote_results(game, vote_counts)
            await message.reply_text(results_text, parse_mode='HTML')

            if vote_counts:
                sorted_votes = sorted(vote_counts.items(), key=lambda item: item[1], reverse=True)
                # Check for tie
                if len(sorted_votes) > 1 and sorted_votes[0][1] == sorted_votes[1][1]:
                    await message.reply_text("⚖️ <b>A tie!</b> No one eliminated.", parse_mode='HTML')
                else:
                    eliminated_id = sorted_votes[0][0]
                    for player in game.get('players', []):
                        if player.get('user_id') == eliminated_id:
                            player['alive'] = False; eliminated_player = player;
                            print(f"Player {player.get('username')} eliminated by vote in {game_id}")
                            break
                    if eliminated_player:
                        summary = format_day_summary(eliminated_player, vote_counts[eliminated_id])
                        await message.reply_text(summary, parse_mode='HTML')
            else:
                 await message.reply_text("🤷 <b>Only skip votes!</b> Moving on...", parse_mode='HTML')

        game['day_votes'] = {} # Reset votes
        game_ended, winner = self.check_game_end_condition(game)
        if game_ended: await self._end_game(game_id, winner, message, context); return

        game['round'] = game.get('round', 0) + 1 # Increment round safely
        game['phase'] = 'night'; await asyncio.sleep(3)
        await self._night_phase(game_id, message, context)

    async def handle_action(self, update, context):
        from telegram import ReplyKeyboardRemove
        message, text, user_id = update.message, update.message.text, update.effective_user.id
        game_id, action_type = None, None

        # Find active game for user
        for gid, game_data in self.games.items():
            if game_data.get('status') == 'in_progress' and game_data.get('phase') == 'night':
                player_data = next((p for p in game_data.get('players', []) if p.get('user_id') == user_id and p.get('alive')), None)
                if player_data:
                    game_id = gid
                    action_type = self._detect_action_type(text, player_data.get('role',''))
                    break
        if not game_id or not action_type: return

        # Extract target username
        try: target_username = text.split(maxsplit=1)[1]
        except IndexError: await message.reply_text("Invalid format.", reply_markup=ReplyKeyboardRemove()); return

        game = self.get_game(game_id);
        if not game: return
        target_player = next((p for p in game.get('players', []) if p.get('username') == target_username and p.get('alive')), None)

        if target_player:
            target_user_id = target_player.get('user_id')
            # Validation
            if action_type == 'protect':
                 actor_player = next((p for p in game.get('players',[]) if p.get('user_id') == user_id), None)
                 if actor_player and actor_player.get('last_protected') == target_user_id:
                      await message.reply_text("⚠️ Cannot protect same twice.", reply_markup=ReplyKeyboardRemove()); return
                 if actor_player: actor_player['last_protected'] = target_user_id

            self.pending_actions.setdefault(game_id, {})[action_type] = target_user_id
            await message.reply_text(f"✅ Action: {target_username}", parse_mode='HTML', reply_markup=ReplyKeyboardRemove())
            print(f"Action '{action_type}' -> {target_username} from {user_id} in {game_id}")
        else:
             await message.reply_text(f"❌ Target '{target_username}' not found/dead.", reply_markup=ReplyKeyboardRemove())

    def _detect_action_type(self, text: str, role: str) -> Optional[str]:
        if not text or not role: return None
        if '🔪' in text and role in ['mafia', 'godfather']: return 'kill'
        if '🔍' in text and role == 'detective': return 'investigate'
        if '💉' in text and role == 'doctor': return 'protect'
        return None

    async def handle_vote(self, update, context):
        from telegram import ReplyKeyboardRemove
        message, text, user_id = update.message, update.message.text, update.effective_user.id
        game_id = None
        for gid, game_data in self.games.items():
            if game_data.get('status') == 'in_progress' and game_data.get('phase') == 'day':
                if any(p.get('user_id') == user_id and p.get('alive') for p in game_data.get('players', [])):
                    game_id = gid; break
        if not game_id: return
        game = self.get_game(game_id);
        if not game: return

        if '⏭️' in text or 'Skip' in text:
            game.setdefault('day_votes', {})[user_id] = 'skip'
            await message.reply_text("✅ Vote skipped!", parse_mode='HTML', reply_markup=ReplyKeyboardRemove())
            print(f"User {user_id} skipped vote in {game_id}")
            return

        if '🗳️' in text or 'Vote:' in text:
            try: target_username = text.split(':')[-1].strip() if ':' in text else text.split()[-1]
            except IndexError: await message.reply_text("Invalid vote.", reply_markup=ReplyKeyboardRemove()); return
            target_player = next((p for p in game.get('players', []) if p.get('username') == target_username and p.get('alive')), None)
            if target_player:
                target_user_id = target_player.get('user_id')
                game.setdefault('day_votes', {})[user_id] = target_user_id
                await message.reply_text(f"✅ Vote recorded for: {target_username}", parse_mode='HTML', reply_markup=ReplyKeyboardRemove())
                print(f"User {user_id} voted for {target_username} ({target_user_id}) in {game_id}")
            else: await message.reply_text(f"❌ Target '{target_username}' not found/dead.", reply_markup=ReplyKeyboardRemove())

    async def _end_game(self, game_id: str, winner: str, message, context):
        from utils import send_victory_animation
        from telegram import InlineKeyboardMarkup, InlineKeyboardButton

        game = self.get_game(game_id)
        if not game or game.get('status') == 'finished': return
        print(f"Ending game {game_id}. Winner: {winner}")
        game['status'], game['winner'] = 'finished', winner
        winners, losers = [], []

        for player in game.get('players', []):
            role = player.get('role', '')
            is_evil = role_manager.is_evil_role(role)
            if (winner == 'villagers' and not is_evil) or \
               (winner == 'mafia' and is_evil):
                winners.append(player)
            else: losers.append(player)

        await send_victory_animation(message, winner, winners)

        for player in game.get('players', []):
            user_id = player.get('user_id'); if not user_id: continue
            won = player in winners
            if won: player_manager.add_win(user_id)
            else: player_manager.add_loss(user_id)
            rewards = self._calculate_rewards(game, player, won)
            player_manager.add_xp(user_id, rewards.get('xp', 0))
            player_manager.add_coins(user_id, rewards.get('coins', 0))
            print(f"Game {game_id}: Player {user_id} ({'Win' if won else 'Loss'}) Rewards: {rewards}")

        stats_text = self._format_game_stats(game, winners)
        await message.reply_text(stats_text, parse_mode='HTML')
        await message.reply_text("Good game! Return to the menu?",
                                 reply_markup=InlineKeyboardMarkup([[
                                     InlineKeyboardButton("🏠 Main Menu", callback_data='menu_main_from_game')
                                 ]]))
        try: replay_system.save_replay(game_id, game)
        except Exception as e: print(f"Error saving replay {game_id}: {e}")
        self.pending_actions.pop(game_id, None)

    def _calculate_rewards(self, game: dict, player: dict, won: bool) -> dict:
        mode = game.get('mode', '1v1')
        base_xp = GAME_SETTINGS.get(mode, {}).get('base_xp_reward', 50)
        base_coins = 50; rewards = {'xp': base_xp, 'coins': base_coins}
        if won: rewards['xp'] += 100; rewards['coins'] += 50
        if player.get('alive'): rewards['xp'] += 50; rewards['coins'] += 25
        rewards['xp'] += game.get('round', 0) * 5
        return rewards

    def _format_game_stats(self, game: dict, winners: list) -> str:
        text = (f"📊 <b>GAME STATS</b> 📊\n🆔: {game.get('id','?')}\n🎯: {game.get('mode','?').upper()}\n"
                f"🔄: {game.get('round',0)}\n🏆: {str(game.get('winner','?')).upper()}\n\n<b>Roles:</b>\n")
        players_list = game.get('players', [])
        if players_list:
             text += "\n".join(f"{'✅' if p.get('alive') else '💀'} {p.get('username','?')} - {p.get('role','?').upper()}" for p in players_list)
        else: text += "No player data."
        return text

    def cancel_game(self, game_id: str, user_id: int) -> Tuple[bool, str]:
        game = self.get_game(game_id)
        if not game: return False, "Game not found!"
        if game.get('creator_id') != user_id: return False, "Only creator can cancel!"
        if game.get('status') != 'waiting': return False, "Game in progress!"
        if self.games.pop(game_id, None):
            self.pending_actions.pop(game_id, None)
            print(f"Game {game_id} cancelled by {user_id}")
            return True, "Game cancelled!"
        else: return False, "Game not found!"

# Global instance needed for utils and main
game_manager = GameManager()
