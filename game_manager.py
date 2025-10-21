"""
Game Manager - Complete Implementation with Fixed Issues
"""

import random
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from player_manager import PlayerManager
from missions import MissionManager
from roles import RoleManager
from utils import *
from config import GAME_SETTINGS, RANDOM_EVENTS

player_manager = PlayerManager()
mission_manager = MissionManager()
role_manager = RoleManager()


class GameManager:
    def __init__(self):
        self.games: Dict[str, dict] = {}
        self.game_counter = 0
        self.pending_actions: Dict[str, dict] = {}
    
    def create_game(self, mode: str, creator_id: int, chat_id: int) -> str:
        """Create a new game lobby"""
        self.game_counter += 1
        game_id = generate_game_id()
        
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
                'investigated': False,
                'items_used': [],
                'last_protected': None
            }],
            'status': 'waiting',
            'phase': 'day',
            'round': 0,
            'started_at': None,
            'winner': None,
            'missions': [],
            'events': [],
            'night_actions': {},
            'day_votes': {},
            'active_event': None
        }
        
        self.pending_actions[game_id] = {}
        
        return game_id
    
    def get_game(self, game_id: str) -> Optional[dict]:
        """Get game by ID"""
        return self.games.get(game_id)
    
    def get_required_players(self, mode: str) -> int:
        """Get required number of players for mode"""
        return GAME_SETTINGS.get(mode, {}).get('min_players', 2)
    
    def join_game(self, game_id: str, user_id: int, username: str) -> Tuple[bool, str]:
        """Join a game lobby"""
        game = self.get_game(game_id)
        
        if not game:
            return False, "Game not found!"
        
        if game['status'] != 'waiting':
            return False, "Game already started!"
        
        if any(p['user_id'] == user_id for p in game['players']):
            return False, "You're already in this game!"
        
        max_players = self.get_required_players(game['mode'])
        if len(game['players']) >= max_players:
            return False, "Game lobby is full!"
        
        game['players'].append({
            'user_id': user_id,
            'username': username,
            'role': None,
            'alive': True,
            'votes': 0,
            'protected': False,
            'investigated': False,
            'items_used': [],
            'last_protected': None
        })
        
        player_manager.register_player(user_id, username)
        
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
        roles = role_manager.assign_roles(len(game['players']), mode)
        
        for player, role in zip(game['players'], roles):
            player['role'] = role
            player['abilities'] = role_manager.get_role_abilities(role)
            player_manager.record_role_played(player['user_id'], role)
    
    def get_role_description(self, role: str) -> str:
        """Get role description"""
        return role_manager.format_role_card(role)
    
    async def start_round(self, game_id: str, message, context):
        """Start a new round"""
        game = self.get_game(game_id)
        
        if not game:
            return
        
        # Check for random events
        self._trigger_random_event(game)
        
        if game['phase'] == 'night':
            await self._night_phase(game_id, message, context)
        elif game['phase'] == 'day':
            await self._day_phase(game_id, message, context)
    
    def _trigger_random_event(self, game: dict):
        """Trigger random events with probability"""
        if random.random() < 0.15:  # 15% chance
            event = random.choice(RANDOM_EVENTS)
            game['active_event'] = event
            game['events'].append(event)
    
    async def _night_phase(self, game_id: str, message, context):
        """Handle night phase"""
        game = self.get_game(game_id)
        
        # Phase transition animation
        await send_phase_transition(message, 'night')
        
        night_duration = GAME_SETTINGS[game['mode']]['night_duration']
        
        text = (
            f"🌙 <b>NIGHT {game['round']}</b> 🌙\n\n"
            "The town sleeps... but evil lurks in the shadows.\n\n"
        )
        
        if game.get('active_event'):
            event = game['active_event']
            text += f"{event['name']}\n{event['description']}\n\n"
        
        text += (
            "🔪 Mafia, choose your target\n"
            "🔍 Detective, investigate someone\n"
            "💉 Doctor, protect someone\n\n"
            f"⏰ You have {night_duration} seconds!"
        )
        
        await message.reply_text(text, parse_mode='HTML')
        
        # Send action prompts to role players
        for player in game['players']:
            if not player['alive']:
                continue
            
            if player['role'] in ['mafia', 'boss', 'godfather']:
                await self._send_mafia_action(game_id, player, context)
            elif player['role'] == 'detective':
                await self._send_detective_action(game_id, player, context)
            elif player['role'] == 'doctor':
                await self._send_doctor_action(game_id, player, context)
        
        # Wait for actions
        await asyncio.sleep(night_duration)
        
        # Process night actions
        await self._process_night_actions(game_id, message, context)
    
    async def _send_mafia_action(self, game_id: str, player: dict, context):
        """Send mafia action choice"""
        game = self.get_game(game_id)
        
        targets = [p for p in game['players'] 
                  if p['alive'] and p['role'] not in ['mafia', 'boss', 'godfather']]
        
        if not targets:
            return
        
        # --- FIX ---
        # Was: keyboard = create_action_keyboard('kill', targets)
        keyboard = create_player_action_keyboard('kill', targets)
        
        try:
            await context.bot.send_message(
                chat_id=player['user_id'],
                text=f"🔪 <b>Choose your target:</b>\n\n⏰ You have {GAME_SETTINGS[game['mode']]['night_duration']} seconds to decide!",
                parse_mode='HTML',
                reply_markup=keyboard
            )
        except Exception as e:
            print(f"Error sending mafia action: {e}")
    
    async def _send_detective_action(self, game_id: str, player: dict, context):
        """Send detective action choice"""
        game = self.get_game(game_id)
        
        targets = [p for p in game['players'] 
                  if p['alive'] and p['user_id'] != player['user_id']]
        
        if not targets:
            return
        
        # --- FIX ---
        # Was: keyboard = create_action_keyboard('investigate', targets)
        keyboard = create_player_action_keyboard('investigate', targets)
        
        try:
            await context.bot.send_message(
                chat_id=player['user_id'],
                text=f"🔍 <b>Who do you want to investigate?</b>\n\n⏰ You have {GAME_SETTINGS[game['mode']]['night_duration']} seconds!",
                parse_mode='HTML',
                reply_markup=keyboard
            )
        except Exception as e:
            print(f"Error sending detective action: {e}")
    
    async def _send_doctor_action(self, game_id: str, player: dict, context):
        """Send doctor action choice"""
        game = self.get_game(game_id)
        
        targets = [p for p in game['players'] if p['alive']]
        
        if not targets:
            return
        
        # --- FIX ---
        # Was: keyboard = create_action_keyboard('protect', targets)
        keyboard = create_player_action_keyboard('protect', targets)
        
        try:
            await context.bot.send_message(
                chat_id=player['user_id'],
                text=f"💉 <b>Who do you want to protect?</b>\n\n⚠️ Cannot protect same player twice in a row!\n⏰ You have {GAME_SETTINGS[game['mode']]['night_duration']} seconds!",
                parse_mode='HTML',
                reply_markup=keyboard
            )
        except Exception as e:
            print(f"Error sending doctor action: {e}")
    
    async def _process_night_actions(self, game_id: str, message, context):
        """Process all night actions - COMPLETE IMPLEMENTATION"""
        game = self.get_game(game_id)
        actions = self.pending_actions.get(game_id, {})
        
        # Animation
        await send_animated_message(
            message,
            ["⚡ <b>Processing night actions...</b>", "🌙 <b>The night reveals its secrets...</b>"],
            delay=1.5
        )
        
        # Extract actions
        kill_target = actions.get('kill')
        protect_target = actions.get('protect')
        investigate_target = actions.get('investigate')
        
        eliminated_player = None
        protected = False
        investigation_result = None
        
        # Process protection first
        if protect_target:
            for player in game['players']:
                if player['user_id'] == protect_target:
                    player['protected'] = True
                    protected = True
                    break
        
        # Process kill
        if kill_target:
            for player in game['players']:
                if player['user_id'] == kill_target:
                    if player.get('protected', False):
                        protected = True
                    else:
                        player['alive'] = False
                        eliminated_player = player
                    player['protected'] = False  # Reset protection
                    break
        
        # Process investigation
        if investigate_target:
            for player in game['players']:
                if player['user_id'] == investigate_target:
                    # Check for Godfather disguise
                    if player['role'] == 'godfather':
                        investigation_result = {
                            'player': player,
                            'result': 'innocent',
                            'actual_role': player['role']
                        }
                    else:
                        investigation_result = {
                            'player': player,
                            'result': 'mafia' if role_manager.is_evil_role(player['role']) else 'innocent',
                            'actual_role': player['role']
                        }
                    break
        
        # Send investigation results privately
        if investigation_result:
            detective = next((p for p in game['players'] if p['role'] == 'detective' and p['alive']), None)
            if detective:
                try:
                    result_text = (
                        f"🔍 <b>INVESTIGATION RESULT</b> 🔍\n\n"
                        f"Target: <b>{investigation_result['player']['username']}</b>\n"
                        f"Result: <b>{investigation_result['result'].upper()}</b>"
                    )
                    await context.bot.send_message(
                        chat_id=detective['user_id'],
                        text=result_text,
                        parse_mode='HTML'
                    )
                except:
                    pass
        
        # Display night summary
        if eliminated_player:
            await send_elimination_animation(message, eliminated_player['username'], eliminated_player['role'])
        else:
            summary = format_night_summary(eliminated_player, {'protected': protected})
            await message.reply_text(summary, parse_mode='HTML')
        
        # Clear actions
        self.pending_actions[game_id] = {}
        
        # Check win condition
        game_ended, winner = check_game_end_condition(game)
        if game_ended:
            await self._end_game(game_id, winner, message, context)
            return
        
        # Move to day phase
        game['phase'] = 'day'
        await asyncio.sleep(2)
        await self._day_phase(game_id, message, context)
    
    async def _day_phase(self, game_id: str, message, context):
        """Handle day phase - COMPLETE IMPLEMENTATION"""
        game = self.get_game(game_id)
        
        # Phase transition
        await send_phase_transition(message, 'day')
        
        day_duration = GAME_SETTINGS[game['mode']]['day_duration']
        
        alive_players = [p for p in game['players'] if p['alive']]
        
        text = (
            f"☀️ <b>DAY {game['round']}</b> ☀️\n\n"
            f"🌅 The town gathers to discuss and vote!\n\n"
            f"<b>Alive Players ({len(alive_players)}):</b>\n"
        )
        
        for player in alive_players:
            text += f"• {player['username']}\n"
        
        text += f"\n⏰ You have {day_duration} seconds to vote!"
        
        # Send voting keyboard
        # --- FIX ---
        # The signature for create_voting_keyboard in utils.py was changed
        # to accept a list of players, so this call is now correct.
        keyboard = create_voting_keyboard(alive_players)
        
        await message.reply_text(text, parse_mode='HTML', reply_markup=keyboard)
        
        # Wait for votes
        await asyncio.sleep(day_duration)
        
        # Process votes
        await self._process_day_votes(game_id, message, context)
    
    async def _process_day_votes(self, game_id: str, message, context):
        """Process voting results"""
        game = self.get_game(game_id)
        votes = game.get('day_votes', {})
        
        if not votes:
            await message.reply_text(
                "🤷 <b>No votes were cast!</b>\n\nMoving to next round...",
                parse_mode='HTML'
            )
        else:
            # Count votes
            vote_counts = {}
            for voter_id, target_id in votes.items():
                if target_id == 'skip':
                    continue
                vote_counts[target_id] = vote_counts.get(target_id, 0) + 1
            
            # Display results
            results_text = format_vote_results(game, vote_counts)
            await message.reply_text(results_text, parse_mode='HTML')
            
            # Eliminate player with most votes
            if vote_counts:
                eliminated_id = max(vote_counts.items(), key=lambda x: x[1])[0]
                eliminated_player = None
                
                for player in game['players']:
                    if player['user_id'] == eliminated_id:
                        player['alive'] = False
                        eliminated_player = player
                        break
                
                if eliminated_player:
                    summary = format_day_summary(eliminated_player, vote_counts[eliminated_id])
                    await message.reply_text(summary, parse_mode='HTML')
        
        # Clear votes
        game['day_votes'] = {}
        
        # Check win condition
        game_ended, winner = check_game_end_condition(game)
        if game_ended:
            await self._end_game(game_id, winner, message, context)
            return
        
        # Next round
        game['round'] += 1
        game['phase'] = 'night'
        await asyncio.sleep(3)
        await self._night_phase(game_id, message, context)
    
    async def handle_action(self, update, context):
        """Handle player actions during night"""
        message = update.message
        text = message.text
        user_id = update.effective_user.id
        
        # Find active game for this player
        game_id = None
        action_type = None
        
        for gid, game in self.games.items():
            if game['status'] == 'in_progress' and game['phase'] == 'night':
                for player in game['players']:
                    if player['user_id'] == user_id and player['alive']:
                        game_id = gid
                        action_type = self._detect_action_type(text, player['role'])
                        break
                if game_id:
                    break
        
        if not game_id or not action_type:
            return
        
        # Extract target from message
        target_username = text.split(maxsplit=1)[1] if len(text.split()) > 1 else None
        
        if target_username:
            game = self.get_game(game_id)
            target_player = next((p for p in game['players'] 
                                 if p['username'] == target_username and p['alive']), None)
            
            if target_player:
                self.pending_actions.setdefault(game_id, {})[action_type] = target_player['user_id']
                await message.reply_text(
                    f"✅ <b>Action recorded!</b>\n\nTarget: {target_username}",
                    parse_mode='HTML'
                )
    
    def _detect_action_type(self, text: str, role: str) -> Optional[str]:
        """Detect action type from message"""
        if '🔪' in text and role in ['mafia', 'boss', 'godfather']:
            return 'kill'
        elif '🔍' in text and role == 'detective':
            return 'investigate'
        elif '💉' in text and role == 'doctor':
            return 'protect'
        return None
    
    async def handle_vote(self, update, context):
        """Handle voting during day phase"""
        message = update.message
        text = message.text
        user_id = update.effective_user.id
        
        # Find active game
        game_id = None
        for gid, game in self.games.items():
            if game['status'] == 'in_progress' and game['phase'] == 'day':
                if any(p['user_id'] == user_id and p['alive'] for p in game['players']):
                    game_id = gid
                    break
        
        if not game_id:
            return
        
        game = self.get_game(game_id)
        
        # Skip vote
        if '⏭️' in text or 'Skip' in text:
            game['day_votes'][user_id] = 'skip'
            await message.reply_text("✅ <b>Vote skipped!</b>", parse_mode='HTML')
            return
        
        # Extract target
        if '🗳️' in text or 'Vote:' in text:
            target_username = text.split(':')[1].strip() if ':' in text else text.split()[-1]
            target_player = next((p for p in game['players'] 
                                 if p['username'] == target_username and p['alive']), None)
            
            if target_player:
                game['day_votes'][user_id] = target_player['user_id']
                await message.reply_text(
                    f"✅ <b>Vote recorded!</b>\n\nVoting for: {target_username}",
                    parse_mode='HTML'
                )
    
    async def _end_game(self, game_id: str, winner: str, message, context):
        """End game and distribute rewards"""
        game = self.get_game(game_id)
        game['status'] = 'finished'
        game['winner'] = winner
        
        # Get winners
        winners = []
        losers = []
        
        for player in game['players']:
            if winner == 'villagers':
                if player['role'] not in ['mafia', 'boss', 'godfather']:
                    winners.append(player)
                else:
                    losers.append(player)
            else:  # mafia wins
                if player['role'] in ['mafia', 'boss', 'godfather']:
                    winners.append(player)
                else:
                    losers.append(player)
        
        # Victory animation
        await send_victory_animation(message, winner, winners)
        
        # Distribute rewards
        for player in winners:
            player_manager.add_win(player['user_id'])
            rewards = self._calculate_rewards(game, player, won=True)
            player_manager.add_xp(player['user_id'], rewards['xp'])
            player_manager.add_coins(player['user_id'], rewards['coins'])
        
        for player in losers:
            player_manager.add_loss(player['user_id'])
            rewards = self._calculate_rewards(game, player, won=False)
            player_manager.add_xp(player['user_id'], rewards['xp'])
            player_manager.add_coins(player['user_id'], rewards['coins'])
        
        # Show final stats
        stats_text = self._format_game_stats(game, winners)
        await message.reply_text(stats_text, parse_mode='HTML')
        
        # Cleanup
        if game_id in self.pending_actions:
            del self.pending_actions[game_id]
    
    def _calculate_rewards(self, game: dict, player: dict, won: bool) -> dict:
        """Calculate player rewards"""
        base_xp = GAME_SETTINGS[game['mode']]['base_xp_reward']
        base_coins = 50
        
        rewards = {'xp': base_xp, 'coins': base_coins}
        
        if won:
            rewards['xp'] += 100
            rewards['coins'] += 50
        
        if player['alive']:
            rewards['xp'] += 50
            rewards['coins'] += 25
        
        return rewards
    
    def _format_game_stats(self, game: dict, winners: list) -> str:
        """Format final game statistics"""
        text = (
            "📊 <b>GAME STATISTICS</b> 📊\n\n"
            f"🎮 Game ID: {game['id']}\n"
            f"🎯 Mode: {game['mode'].upper()}\n"
            f"🔄 Rounds: {game['round']}\n"
            f"🏆 Winner: {game['winner'].upper()}\n\n"
            "<b>Final Roles:</b>\n"
        )
        
        for player in game['players']:
            status = "✅" if player['alive'] else "💀"
            text += f"{status} {player['username']} - {player['role'].upper()}\n"
        
        return text
    
    def cancel_game(self, game_id: str, user_id: int) -> Tuple[bool, str]:
        """Cancel a game"""
        game = self.get_game(game_id)
        
        if not game:
            return False, "Game not found!"
        
        if game['creator_id'] != user_id:
            return False, "Only creator can cancel!"
        
        if game['status'] != 'waiting':
            return False, "Cannot cancel ongoing game!"
        
        del self.games[game_id]
        return True, "Game cancelled!"
