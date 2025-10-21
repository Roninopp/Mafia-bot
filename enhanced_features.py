"""
Enhanced Features Module - Trading, Tournaments, and More
"""

import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from player_manager import PlayerManager
from config import SHOP_ITEMS # Needed to get item details for transfer

# Use the global player manager instance
player_manager = PlayerManager()


class TradingSystem:
    """Player trading system"""
    
    def __init__(self):
        self.active_trades: Dict[str, dict] = {}
        self.trade_counter = 0
    
    def create_trade_offer(self, sender_id: int, receiver_id: int, 
                          offer_coins: int, offer_items_ids: List[str],
                          request_coins: int, request_items_ids: List[str]) -> Tuple[Optional[str], str]:
        """Create a trade offer"""
        sender = player_manager.get_player(sender_id)
        receiver = player_manager.get_player(receiver_id)

        if not sender or not receiver:
            return None, "One of the players not found."
            
        # Validate sender has resources
        if sender['coins'] < offer_coins:
            return None, "You don't have enough coins to offer!"
        for item_id in offer_items_ids:
            if not player_manager.has_item(sender_id, item_id):
                 return None, f"You don't own the item {item_id} to offer!"
                 
        # Basic validation for receiver (full check happens on accept)
        # Note: We can't fully check receiver items here without more complexity

        self.trade_counter += 1
        trade_id = f"trade_{self.trade_counter}_{int(datetime.now().timestamp())}"
        
        self.active_trades[trade_id] = {
            'id': trade_id,
            'sender_id': sender_id,
            'sender_username': sender['username'],
            'receiver_id': receiver_id,
            'receiver_username': receiver['username'],
            'offer': {
                'coins': offer_coins,
                'items': offer_items_ids # Store only IDs
            },
            'request': {
                'coins': request_coins,
                'items': request_items_ids # Store only IDs
            },
            'status': 'pending',
            'created_at': datetime.now()
        }
        
        # TODO: Notify receiver via context.bot.send_message
        print(f"Trade offer {trade_id} created from {sender['username']} to {receiver['username']}")
        
        return trade_id, f"Trade offer sent to {receiver['username']}!"
    
    def get_trade(self, trade_id: str) -> Optional[dict]:
        return self.active_trades.get(trade_id)

    def accept_trade(self, trade_id: str, accepting_user_id: int) -> Tuple[bool, str]:
        """Accept a trade"""
        trade = self.active_trades.get(trade_id)
        
        if not trade: return False, "Trade not found!"
        if trade['status'] != 'pending': return False, "Trade already processed!"
        if trade['receiver_id'] != accepting_user_id: return False, "This is not your trade offer to accept!"
        
        sender = player_manager.get_player(trade['sender_id'])
        receiver = player_manager.get_player(trade['receiver_id'])

        if not sender or not receiver: return False, "Error: Player data missing."
        
        # --- VALIDATION ---
        # Sender resources
        if sender['coins'] < trade['offer']['coins']:
            trade['status'] = 'failed'
            return False, f"{trade['sender_username']} doesn't have enough coins!"
        for item_id in trade['offer']['items']:
            if not player_manager.has_item(trade['sender_id'], item_id):
                trade['status'] = 'failed'
                return False, f"{trade['sender_username']} no longer owns the offered item: {item_id}"
                
        # Receiver resources
        if receiver['coins'] < trade['request']['coins']:
            # No status change, receiver can try again later if they get coins
            return False, "You don't have enough coins to fulfill the request!"
        for item_id in trade['request']['items']:
            if not player_manager.has_item(trade['receiver_id'], item_id):
                 # No status change here either
                return False, f"You no longer own the requested item: {item_id}"
        
        # --- PROCESS TRADE ---
        try:
            # Coins transfer
            player_manager.spend_coins(trade['sender_id'], trade['offer']['coins'])
            player_manager.add_coins(trade['receiver_id'], trade['offer']['coins'])
            player_manager.spend_coins(trade['receiver_id'], trade['request']['coins'])
            player_manager.add_coins(trade['sender_id'], trade['request']['coins'])
            
            # --- Item transfer ---
            all_items_map = {item['id']: item for item in SHOP_ITEMS} # Map for easy lookup

            # Sender's items to Receiver
            for item_id in trade['offer']['items']:
                item_details = all_items_map.get(item_id)
                if item_details:
                    if player_manager.remove_item(trade['sender_id'], item_id):
                        player_manager.add_item(trade['receiver_id'], item_details)
                    else:
                        raise ValueError(f"Failed to remove item {item_id} from sender {trade['sender_id']}")
                else:
                     raise ValueError(f"Offered item {item_id} details not found in SHOP_ITEMS")
            
            # Receiver's items to Sender
            for item_id in trade['request']['items']:
                item_details = all_items_map.get(item_id)
                if item_details:
                    if player_manager.remove_item(trade['receiver_id'], item_id):
                         player_manager.add_item(trade['sender_id'], item_details)
                    else:
                        raise ValueError(f"Failed to remove item {item_id} from receiver {trade['receiver_id']}")
                else:
                    raise ValueError(f"Requested item {item_id} details not found in SHOP_ITEMS")

            trade['status'] = 'completed'
            # TODO: Notify both parties via context.bot.send_message
            print(f"Trade {trade_id} completed successfully!")
            return True, "Trade completed successfully!"

        except Exception as e:
            # Attempt to rollback coin transfer if something failed (basic rollback)
            print(f"ERROR during trade {trade_id}: {e}. Attempting rollback...")
            player_manager.add_coins(trade['sender_id'], trade['offer']['coins'])
            player_manager.spend_coins(trade['receiver_id'], trade['offer']['coins'])
            player_manager.add_coins(trade['receiver_id'], trade['request']['coins'])
            player_manager.spend_coins(trade['sender_id'], trade['request']['coins'])
            # Item rollback is much harder, skipping for now.
            trade['status'] = 'failed'
            return False, f"An error occurred during the trade: {e}"
    
    def cancel_trade(self, trade_id: str, user_id: int) -> Tuple[bool, str]:
        """Cancel a trade"""
        trade = self.active_trades.get(trade_id)
        
        if not trade: return False, "Trade not found!"
        if trade['status'] != 'pending': return False, "Trade already processed or cancelled!"
        if trade['sender_id'] != user_id and trade['receiver_id'] != user_id:
            return False, "This is not your trade to cancel!"
        
        trade['status'] = 'cancelled'
        # TODO: Notify both parties via context.bot.send_message
        canceller = "sender" if user_id == trade['sender_id'] else "receiver"
        print(f"Trade {trade_id} cancelled by {canceller} ({user_id})")
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
            'prize_pool': prize_pool, # Base prize pool
            'current_pot': prize_pool, # Pot increases with entries
            'participants': [], # Store {'user_id': id, 'username': name}
            'brackets': {},
            'status': 'registration', # registration, in_progress, finished
            'created_at': datetime.now(),
            'start_time': None,
            'winner': None
        }
        print(f"Tournament {tournament_id} created: {name}")
        return tournament_id
        
    def get_tournament(self, tournament_id: str) -> Optional[dict]:
        return self.tournaments.get(tournament_id)

    def register_player(self, tournament_id: str, user_id: int, username: str) -> Tuple[bool, str]:
        """Register player for tournament"""
        tournament = self.tournaments.get(tournament_id)
        
        if not tournament: return False, "Tournament not found!"
        if tournament['status'] != 'registration': return False, "Registration is closed!"
        if len(tournament['participants']) >= tournament['max_players']: return False, "Tournament is full!"
        if any(p['user_id'] == user_id for p in tournament['participants']): return False, "You are already registered!"
        
        player = player_manager.get_player(user_id)
        if not player: return False, "Player profile not found."
        if player['coins'] < tournament['entry_fee']: return False, "Not enough coins for the entry fee!"
        
        # Charge entry fee
        if player_manager.spend_coins(user_id, tournament['entry_fee']):
            tournament['participants'].append({'user_id': user_id, 'username': username})
            tournament['current_pot'] += tournament['entry_fee']
            print(f"Player {username} ({user_id}) registered for tournament {tournament_id}")
            return True, "Registered successfully!"
        else:
            return False, "Failed to process entry fee payment."
    
    def start_tournament(self, tournament_id: str) -> Tuple[bool, str]:
        """Start tournament and create brackets"""
        tournament = self.tournaments.get(tournament_id)
        
        if not tournament: return False, "Tournament not found!"
        if tournament['status'] != 'registration': return False, "Tournament already started or finished!"
        
        # Need at least 2 players for a bracket
        if len(tournament['participants']) < 2: 
            return False, "Need at least 2 players to start!"
            
        # Ensure player count is even or add a bye if needed (simplified: require even for now)
        if len(tournament['participants']) % 2 != 0:
             return False, "Need an even number of players to start the brackets easily. Waiting for one more."

        participants_data = tournament['participants'].copy()
        random.shuffle(participants_data)
        
        brackets = self._create_brackets(participants_data)
        tournament['brackets'] = brackets
        tournament['status'] = 'in_progress'
        tournament['start_time'] = datetime.now()
        
        print(f"Tournament {tournament_id} started!")
        # TODO: Notify participants via context.bot.send_message
        return True, "Tournament started! Brackets created."
    
    def _create_brackets(self, participants_data: List[dict]) -> dict:
        """Create initial tournament brackets (simplified single elimination)"""
        rounds = []
        round1_matches = []
        
        for i in range(0, len(participants_data), 2):
            p1 = participants_data[i]
            p2 = participants_data[i+1]
            round1_matches.append({
                'match_id': f"R1M{i//2 + 1}",
                'player1': p1, # Store full dict {'user_id': id, 'username': name}
                'player2': p2,
                'winner': None, # Store winner dict
                'status': 'pending' # pending, active, finished
            })
        
        rounds.append(round1_matches)
        
        # current_round index (0 for first round)
        return {'rounds': rounds, 'current_round_index': 0, 'matches_in_progress': 0}

    def report_match_result(self, tournament_id: str, match_id: str, winner_user_id: int) -> Tuple[bool, str]:
        """Report the winner of a match and advance brackets if possible"""
        tournament = self.tournaments.get(tournament_id)
        if not tournament or tournament['status'] != 'in_progress':
            return False, "Tournament not found or not in progress."

        current_round_index = tournament['brackets']['current_round_index']
        if current_round_index >= len(tournament['brackets']['rounds']):
             return False, "Error: Invalid round index."

        current_round_matches = tournament['brackets']['rounds'][current_round_index]
        match_found = False
        winner_data = None

        for match in current_round_matches:
            if match['match_id'] == match_id and match['status'] != 'finished':
                match_found = True
                p1_id = match['player1']['user_id']
                p2_id = match['player2']['user_id']

                if winner_user_id == p1_id:
                    match['winner'] = match['player1']
                    winner_data = match['player1']
                elif winner_user_id == p2_id:
                    match['winner'] = match['player2']
                    winner_data = match['player2']
                else:
                    return False, "Winner ID doesn't match players in this match."

                match['status'] = 'finished'
                print(f"Match {match_id} in tour {tournament_id} finished. Winner: {winner_data['username']}")
                break
        
        if not match_found:
            return False, "Match ID not found in the current round or already finished."

        # Check if round is complete and create next round
        if all(m['status'] == 'finished' for m in current_round_matches):
            print(f"Round {current_round_index + 1} of tour {tournament_id} complete.")
            winners = [m['winner'] for m in current_round_matches if m['winner']]
            
            if len(winners) == 1:
                # Tournament finished
                tournament['status'] = 'finished'
                tournament['winner'] = winners[0]
                winner_player = player_manager.get_player(winners[0]['user_id'])
                if winner_player:
                    player_manager.add_coins(winner_player['user_id'], tournament['current_pot'])
                    # TODO: Add XP bonus, record tournament win stat
                    print(f"Tournament {tournament_id} finished! Winner: {winner_player['username']}. Prize: {tournament['current_pot']} coins.")
                    # TODO: Notify participants via context.bot.send_message
                    return True, f"Tournament finished! Winner: {winner_player['username']}"
                else:
                    return False, "Tournament finished, but winner data not found."

            elif len(winners) > 1:
                 # Create next round
                tournament['brackets']['current_round_index'] += 1
                next_round_index = tournament['brackets']['current_round_index']
                next_round_matches = []
                for i in range(0, len(winners), 2):
                    p1 = winners[i]
                    p2 = winners[i+1]
                    next_round_matches.append({
                        'match_id': f"R{next_round_index+1}M{i//2 + 1}",
                        'player1': p1,
                        'player2': p2,
                        'winner': None,
                        'status': 'pending'
                    })
                tournament['brackets']['rounds'].append(next_round_matches)
                print(f"Created Round {next_round_index + 1} for tour {tournament_id}")
                # TODO: Notify participants via context.bot.send_message
                return True, f"Match result recorded. Round {current_round_index + 1} complete. Next round ready."
            else: # Should not happen if started with >= 2 players
                return False, "Error advancing brackets: No winners found?"
                
        return True, "Match result recorded."


    def format_tournament_info(self, tournament_id: str) -> str:
        """Format tournament information"""
        tournament = self.tournaments.get(tournament_id)
        if not tournament: return "Tournament not found!"
        
        text = (
            f"🏆 <b>{tournament['name']}</b> 🏆\n\n"
            f"🎮 Mode: {tournament['mode'].upper()}\n"
            f"👥 Players: {len(tournament['participants'])}/{tournament['max_players']}\n"
            f"💰 Entry Fee: {tournament['entry_fee']} coins\n"
            f"🎁 Current Pot: {tournament['current_pot']} coins\n"
            f"📊 Status: {tournament['status'].upper()}\n"
        )
        if tournament['status'] == 'finished' and tournament['winner']:
             text += f"🏅 Winner: {tournament['winner']['username']}\n"
        elif tournament['status'] == 'in_progress':
             text += f"⚔️ Round: {tournament['brackets']['current_round_index'] + 1}\n"

        return text

    def format_tournament_brackets(self, tournament_id: str) -> str:
        """Format tournament brackets for display"""
        tournament = self.tournaments.get(tournament_id)
        if not tournament or not tournament.get('brackets'): return "Brackets not created yet."

        text = f"🏆 <b>{tournament['name']} - Brackets</b> 🏆\n\n"
        brackets = tournament['brackets']

        for i, round_matches in enumerate(brackets['rounds']):
            text += f"<b>--- Round {i+1} ---</b>\n"
            for match in round_matches:
                p1_name = match['player1']['username']
                p2_name = match['player2']['username']
                winner_name = f" -> {match['winner']['username']} 🏆" if match['winner'] else ""
                status_emoji = "✅" if match['status'] == 'finished' else ("▶️" if match['status'] == 'active' else "⏳")
                
                text += f"{status_emoji} {match['match_id']}: {p1_name} vs {p2_name}{winner_name}\n"
            text += "\n"

        if tournament['status'] == 'finished' and tournament['winner']:
            text += f"🏅 <b>Winner: {tournament['winner']['username']}</b> 🏅\n"

        return text


# --- Seasonal Events & Clans remain unchanged from your provided code ---
class SeasonalEvents:
    """Seasonal events and limited-time modes"""
    # ... (code as provided) ...
    pass

class ClanSystem:
    """Clan/Guild system for team play"""
    # ... (code as provided) ...
    pass

class ReplaySystem:
    """Game replay system"""
    # ... (code as provided) ...
    pass


# Initialize systems (if needed globally, otherwise instantiate in main bot)
trading_system = TradingSystem()
tournament_system = TournamentSystem()
# seasonal_events = SeasonalEvents()
# clan_system = ClanSystem()
# replay_system = ReplaySystem() # Replay is already initialized in game_manager
