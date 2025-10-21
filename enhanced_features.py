"""
Enhanced Features Module - Trading, Tournaments, and More
"""

import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from player_manager import PlayerManager

player_manager = PlayerManager()


class TradingSystem:
    """Player trading system"""
    
    def __init__(self):
        self.active_trades: Dict[str, dict] = {}
        self.trade_counter = 0
    
    def create_trade_offer(self, sender_id: int, receiver_id: int, 
                          offer_coins: int, offer_items: list,
                          request_coins: int, request_items: list) -> str:
        """Create a trade offer"""
        self.trade_counter += 1
        trade_id = f"trade_{self.trade_counter}_{int(datetime.now().timestamp())}"
        
        self.active_trades[trade_id] = {
            'id': trade_id,
            'sender_id': sender_id,
            'receiver_id': receiver_id,
            'offer': {
                'coins': offer_coins,
                'items': offer_items
            },
            'request': {
                'coins': request_coins,
                'items': request_items
            },
            'status': 'pending',
            'created_at': datetime.now()
        }
        
        return trade_id
    
    def accept_trade(self, trade_id: str) -> Tuple[bool, str]:
        """Accept a trade"""
        trade = self.active_trades.get(trade_id)
        
        if not trade:
            return False, "Trade not found!"
        
        if trade['status'] != 'pending':
            return False, "Trade already processed!"
        
        sender = player_manager.get_player(trade['sender_id'])
        receiver = player_manager.get_player(trade['receiver_id'])
        
        # Validate sender has resources
        if sender['coins'] < trade['offer']['coins']:
            return False, "Sender doesn't have enough coins!"
        
        # Validate receiver has resources
        if receiver['coins'] < trade['request']['coins']:
            return False, "You don't have enough coins!"
        
        # Process trade
        player_manager.spend_coins(trade['sender_id'], trade['offer']['coins'])
        player_manager.add_coins(trade['receiver_id'], trade['offer']['coins'])
        
        player_manager.spend_coins(trade['receiver_id'], trade['request']['coins'])
        player_manager.add_coins(trade['sender_id'], trade['request']['coins'])
        
        # Transfer items
        for item in trade['offer']['items']:
            # Remove from sender, add to receiver
            pass  # Implement item transfer
        
        trade['status'] = 'completed'
        return True, "Trade completed successfully!"
    
    def cancel_trade(self, trade_id: str, user_id: int) -> Tuple[bool, str]:
        """Cancel a trade"""
        trade = self.active_trades.get(trade_id)
        
        if not trade:
            return False, "Trade not found!"
        
        if trade['sender_id'] != user_id and trade['receiver_id'] != user_id:
            return False, "Not your trade!"
        
        trade['status'] = 'cancelled'
        return True, "Trade cancelled!"


class TournamentSystem:
    """Tournament and competitive mode"""
    
    def __init__(self):
        self.tournaments: Dict[str, dict] = {}
        self.tournament_counter = 0
    
    def create_tournament(self, name: str, mode: str, max_players: int, 
                         entry_fee: int, prize_pool: int) -> str:
        """Create a tournament"""
        self.tournament_counter += 1
        tournament_id = f"tour_{self.tournament_counter}"
        
        self.tournaments[tournament_id] = {
            'id': tournament_id,
            'name': name,
            'mode': mode,
            'max_players': max_players,
            'entry_fee': entry_fee,
            'prize_pool': prize_pool,
            'participants': [],
            'brackets': {},
            'status': 'registration',
            'created_at': datetime.now(),
            'start_time': None
        }
        
        return tournament_id
    
    def register_player(self, tournament_id: str, user_id: int) -> Tuple[bool, str]:
        """Register player for tournament"""
        tournament = self.tournaments.get(tournament_id)
        
        if not tournament:
            return False, "Tournament not found!"
        
        if tournament['status'] != 'registration':
            return False, "Registration closed!"
        
        if len(tournament['participants']) >= tournament['max_players']:
            return False, "Tournament full!"
        
        player = player_manager.get_player(user_id)
        
        if player['coins'] < tournament['entry_fee']:
            return False, "Not enough coins for entry fee!"
        
        if user_id in tournament['participants']:
            return False, "Already registered!"
        
        # Charge entry fee
        player_manager.spend_coins(user_id, tournament['entry_fee'])
        
        tournament['participants'].append(user_id)
        tournament['prize_pool'] += tournament['entry_fee']
        
        return True, "Registered successfully!"
    
    def start_tournament(self, tournament_id: str) -> Tuple[bool, str]:
        """Start tournament and create brackets"""
        tournament = self.tournaments.get(tournament_id)
        
        if not tournament:
            return False, "Tournament not found!"
        
        if len(tournament['participants']) < 4:
            return False, "Need at least 4 players!"
        
        # Create brackets
        participants = tournament['participants'].copy()
        random.shuffle(participants)
        
        brackets = self._create_brackets(participants)
        tournament['brackets'] = brackets
        tournament['status'] = 'in_progress'
        tournament['start_time'] = datetime.now()
        
        return True, "Tournament started!"
    
    def _create_brackets(self, players: list) -> dict:
        """Create tournament brackets"""
        rounds = []
        current_round = []
        
        for i in range(0, len(players), 2):
            if i + 1 < len(players):
                current_round.append({
                    'player1': players[i],
                    'player2': players[i + 1],
                    'winner': None,
                    'status': 'pending'
                })
        
        rounds.append(current_round)
        
        return {'rounds': rounds, 'current_round': 0}
    
    def format_tournament_info(self, tournament_id: str) -> str:
        """Format tournament information"""
        tournament = self.tournaments.get(tournament_id)
        
        if not tournament:
            return "Tournament not found!"
        
        text = (
            f"🏆 <b>{tournament['name']}</b> 🏆\n\n"
            f"🎮 Mode: {tournament['mode'].upper()}\n"
            f"👥 Players: {len(tournament['participants'])}/{tournament['max_players']}\n"
            f"💰 Entry Fee: {tournament['entry_fee']} coins\n"
            f"🎁 Prize Pool: {tournament['prize_pool']} coins\n"
            f"📊 Status: {tournament['status'].upper()}\n"
        )
        
        return text


class SeasonalEvents:
    """Seasonal events and limited-time modes"""
    
    def __init__(self):
        self.active_events: List[dict] = []
        self.event_history: List[dict] = []
    
    def create_event(self, name: str, description: str, 
                    duration_days: int, rewards: dict) -> dict:
        """Create a seasonal event"""
        event = {
            'id': f"event_{int(datetime.now().timestamp())}",
            'name': name,
            'description': description,
            'start_date': datetime.now(),
            'end_date': datetime.now() + timedelta(days=duration_days),
            'rewards': rewards,
            'participants': [],
            'leaderboard': {},
            'active': True
        }
        
        self.active_events.append(event)
        return event
    
    def get_active_events(self) -> List[dict]:
        """Get all active events"""
        current_time = datetime.now()
        active = []
        
        for event in self.active_events:
            if event['end_date'] > current_time:
                active.append(event)
            else:
                event['active'] = False
                self.event_history.append(event)
        
        self.active_events = active
        return active
    
    def format_event_info(self, event: dict) -> str:
        """Format event information"""
        time_remaining = event['end_date'] - datetime.now()
        days_left = time_remaining.days
        hours_left = time_remaining.seconds // 3600
        
        text = (
            f"🎉 <b>{event['name']}</b> 🎉\n\n"
            f"{event['description']}\n\n"
            f"⏰ Time Remaining: {days_left}d {hours_left}h\n"
            f"👥 Participants: {len(event['participants'])}\n\n"
            f"<b>Rewards:</b>\n"
        )
        
        for reward_type, amount in event['rewards'].items():
            text += f"• {reward_type}: {amount}\n"
        
        return text


class ClanSystem:
    """Clan/Guild system for team play"""
    
    def __init__(self):
        self.clans: Dict[str, dict] = {}
        self.clan_counter = 0
    
    def create_clan(self, name: str, leader_id: int, description: str = "") -> Tuple[bool, str]:
        """Create a new clan"""
        # Check if name exists
        if any(clan['name'].lower() == name.lower() for clan in self.clans.values()):
            return False, "Clan name already taken!"
        
        self.clan_counter += 1
        clan_id = f"clan_{self.clan_counter}"
        
        self.clans[clan_id] = {
            'id': clan_id,
            'name': name,
            'description': description,
            'leader_id': leader_id,
            'members': [leader_id],
            'level': 1,
            'xp': 0,
            'wins': 0,
            'created_at': datetime.now(),
            'treasury': 0
        }
        
        return True, clan_id
    
    def join_clan(self, clan_id: str, user_id: int) -> Tuple[bool, str]:
        """Join a clan"""
        clan = self.clans.get(clan_id)
        
        if not clan:
            return False, "Clan not found!"
        
        if len(clan['members']) >= 50:
            return False, "Clan is full!"
        
        if user_id in clan['members']:
            return False, "Already in this clan!"
        
        # Check if player is in another clan
        for c in self.clans.values():
            if user_id in c['members']:
                return False, "Leave your current clan first!"
        
        clan['members'].append(user_id)
        return True, "Joined clan successfully!"
    
    def leave_clan(self, clan_id: str, user_id: int) -> Tuple[bool, str]:
        """Leave a clan"""
        clan = self.clans.get(clan_id)
        
        if not clan:
            return False, "Clan not found!"
        
        if user_id not in clan['members']:
            return False, "Not in this clan!"
        
        if clan['leader_id'] == user_id:
            if len(clan['members']) > 1:
                return False, "Transfer leadership first!"
            else:
                # Disband clan
                del self.clans[clan_id]
                return True, "Clan disbanded!"
        
        clan['members'].remove(user_id)
        return True, "Left clan successfully!"
    
    def format_clan_info(self, clan_id: str) -> str:
        """Format clan information"""
        clan = self.clans.get(clan_id)
        
        if not clan:
            return "Clan not found!"
        
        leader = player_manager.get_player(clan['leader_id'])
        leader_name = leader['username'] if leader else "Unknown"
        
        text = (
            f"🛡️ <b>{clan['name']}</b> 🛡️\n\n"
            f"{clan['description']}\n\n"
            f"👑 Leader: {leader_name}\n"
            f"👥 Members: {len(clan['members'])}/50\n"
            f"⭐ Level: {clan['level']}\n"
            f"🏆 Wins: {clan['wins']}\n"
            f"💰 Treasury: {clan['treasury']} coins\n"
        )
        
        return text


class ReplaySystem:
    """Game replay system"""
    
    def __init__(self):
        self.replays: Dict[str, dict] = {}
    
    def save_replay(self, game_id: str, game_data: dict):
        """Save game replay"""
        self.replays[game_id] = {
            'game_id': game_id,
            'mode': game_data['mode'],
            'players': game_data['players'],
            'events': game_data['events'],
            'winner': game_data['winner'],
            'rounds': game_data['round'],
            'saved_at': datetime.now()
        }
    
    def get_replay(self, game_id: str) -> Optional[dict]:
        """Get replay data"""
        return self.replays.get(game_id)
    
    def format_replay_summary(self, game_id: str) -> str:
        """Format replay summary"""
        replay = self.get_replay(game_id)
        
        if not replay:
            return "Replay not found!"
        
        text = (
            f"🎬 <b>GAME REPLAY</b> 🎬\n\n"
            f"🆔 Game ID: {game_id}\n"
            f"🎯 Mode: {replay['mode'].upper()}\n"
            f"🔄 Rounds: {replay['rounds']}\n"
            f"🏆 Winner: {replay['winner'].upper()}\n\n"
            f"<b>Players:</b>\n"
        )
        
        for player in replay['players']:
            status = "✅" if player['alive'] else "💀"
            text += f"{status} {player['username']} - {player['role'].upper()}\n"
        
        return text


# Initialize systems
trading_system = TradingSystem()
tournament_system = TournamentSystem()
seasonal_events = SeasonalEvents()
clan_system = ClanSystem()
replay_system = ReplaySystem()
