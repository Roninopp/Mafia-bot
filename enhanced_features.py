"""
Enhanced Features Module - Trading, Tournaments, and More
"""

import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from player_manager import PlayerManager
from config import SHOP_ITEMS

player_manager = PlayerManager()


class TradingSystem:
    """Player trading system"""
    
    def __init__(self):
        self.active_trades: Dict[str, dict] = {}
        self.trade_counter = 0
    
    def create_trade_offer(self, sender_id: int, receiver_id: int, 
                          offer_coins: int, offer_items_ids: List[str],
                          request_coins: int, request_items_ids: List[str]) -> Tuple[Optional[str], str]:
        sender = player_manager.get_player(sender_id)
        receiver = player_manager.get_player(receiver_id)
        if not sender or not receiver: return None, "Player not found."
        if sender['coins'] < offer_coins: return None, "You don't have enough coins!"
        for item_id in offer_items_ids:
            if not player_manager.has_item(sender_id, item_id):
                 return None, f"You don't own the item {item_id}!"
                 
        self.trade_counter += 1
        trade_id = f"trade_{self.trade_counter}"
        self.active_trades[trade_id] = {
            'id': trade_id, 'sender_id': sender_id, 'sender_username': sender['username'],
            'receiver_id': receiver_id, 'receiver_username': receiver['username'],
            'offer': {'coins': offer_coins, 'items': offer_items_ids},
            'request': {'coins': request_coins, 'items': request_items_ids},
            'status': 'pending', 'created_at': datetime.now()
        }
        print(f"Trade {trade_id} created: {sender['username']} -> {receiver['username']}")
        return trade_id, f"Trade offer sent to {receiver['username']}!"
    
    def get_trade(self, trade_id: str) -> Optional[dict]:
        return self.active_trades.get(trade_id)

    def accept_trade(self, trade_id: str, accepting_user_id: int) -> Tuple[bool, str]:
        trade = self.active_trades.get(trade_id)
        if not trade: return False, "Trade not found!"
        if trade['status'] != 'pending': return False, "Trade already processed!"
        if trade['receiver_id'] != accepting_user_id: return False, "Not your trade!"
        
        sender = player_manager.get_player(trade['sender_id'])
        receiver = player_manager.get_player(trade['receiver_id'])
        if not sender or not receiver: return False, "Player data missing."

        # Validate resources
        if sender['coins'] < trade['offer']['coins']:
            trade['status'] = 'failed'; return False, f"{trade['sender_username']} lacks coins!"
        for item_id in trade['offer']['items']:
            if not player_manager.has_item(trade['sender_id'], item_id):
                trade['status'] = 'failed'; return False, f"{trade['sender_username']} lacks item: {item_id}"
        if receiver['coins'] < trade['request']['coins']:
            return False, "You don't have enough coins!"
        for item_id in trade['request']['items']:
            if not player_manager.has_item(trade['receiver_id'], item_id):
                return False, f"You don't own the item: {item_id}"
        
        # Process Trade
        try:
            player_manager.spend_coins(trade['sender_id'], trade['offer']['coins'])
            player_manager.add_coins(trade['receiver_id'], trade['offer']['coins'])
            player_manager.spend_coins(trade['receiver_id'], trade['request']['coins'])
            player_manager.add_coins(trade['sender_id'], trade['request']['coins'])
            
            all_items_map = {item['id']: item for item in SHOP_ITEMS}

            for item_id in trade['offer']['items']:
                item_details = all_items_map.get(item_id)
                if item_details and player_manager.remove_item(trade['sender_id'], item_id):
                    player_manager.add_item(trade['receiver_id'], item_details)
                else: raise ValueError(f"Failed to transfer item {item_id} from sender")
            
            for item_id in trade['request']['items']:
                item_details = all_items_map.get(item_id)
                if item_details and player_manager.remove_item(trade['receiver_id'], item_id):
                     player_manager.add_item(trade['sender_id'], item_details)
                else: raise ValueError(f"Failed to transfer item {item_id} from receiver")

            trade['status'] = 'completed'
            print(f"Trade {trade_id} completed!")
            return True, "Trade completed!"
        except Exception as e:
            print(f"ERROR during trade {trade_id}: {e}. Rolling back coins.")
            player_manager.add_coins(trade['sender_id'], trade['offer']['coins'])
            player_manager.spend_coins(trade['receiver_id'], trade['offer']['coins'])
            player_manager.add_coins(trade['receiver_id'], trade['request']['coins'])
            player_manager.spend_coins(trade['sender_id'], trade['request']['coins'])
            trade['status'] = 'failed'
            return False, f"An error occurred: {e}"
    
    def cancel_trade(self, trade_id: str, user_id: int) -> Tuple[bool, str]:
        trade = self.active_trades.get(trade_id)
        if not trade: return False, "Trade not found!"
        if trade['status'] != 'pending': return False, "Trade already processed!"
        if trade['sender_id'] != user_id and trade['receiver_id'] != user_id:
            return False, "Not your trade!"
        trade['status'] = 'cancelled'
        return True, "Trade cancelled!"

class TournamentSystem:
    def __init__(self):
        self.tournaments: Dict[str, dict] = {}
        self.tournament_counter = 0
    
    def create_tournament(self, name: str, mode: str, max_players: int, 
                         entry_fee: int, prize_pool: int) -> str:
        self.tournament_counter += 1; tournament_id = f"tour_{self.tournament_counter}"
        self.tournaments[tournament_id] = {
            'id': tournament_id, 'name': name, 'mode': mode, 'max_players': max_players,
            'entry_fee': entry_fee, 'prize_pool': prize_pool, 'current_pot': prize_pool,
            'participants': [], 'brackets': {}, 'status': 'registration',
            'created_at': datetime.now(), 'start_time': None, 'winner': None
        }
        return tournament_id
        
    def get_tournament(self, tournament_id: str) -> Optional[dict]:
        return self.tournaments.get(tournament_id)

    def register_player(self, tournament_id: str, user_id: int, username: str) -> Tuple[bool, str]:
        tournament = self.tournaments.get(tournament_id)
        if not tournament: return False, "Tournament not found!"
        if tournament['status'] != 'registration': return False, "Registration closed!"
        if len(tournament['participants']) >= tournament['max_players']: return False, "Tournament full!"
        if any(p['user_id'] == user_id for p in tournament['participants']): return False, "Already registered!"
        player = player_manager.get_player(user_id)
        if not player: return False, "Player profile not found."
        if player['coins'] < tournament['entry_fee']: return False, "Not enough coins!"
        
        if player_manager.spend_coins(user_id, tournament['entry_fee']):
            tournament['participants'].append({'user_id': user_id, 'username': username})
            tournament['current_pot'] += tournament['entry_fee']
            return True, "Registered successfully!"
        else:
            return False, "Payment failed."
    
    def start_tournament(self, tournament_id: str) -> Tuple[bool, str]:
        tournament = self.tournaments.get(tournament_id)
        if not tournament: return False, "Tournament not found!"
        if tournament['status'] != 'registration': return False, "Already started!"
        if len(tournament['participants']) < 2: return False, "Need at least 2 players!"
        if len(tournament['participants']) % 2 != 0: return False, "Need an even number of players."

        participants_data = tournament['participants'].copy(); random.shuffle(participants_data)
        brackets = self._create_brackets(participants_data)
        tournament['brackets'] = brackets
        tournament['status'] = 'in_progress'; tournament['start_time'] = datetime.now()
        return True, "Tournament started!"
    
    def _create_brackets(self, participants_data: List[dict]) -> dict:
        rounds, round1_matches = [], []
        for i in range(0, len(participants_data), 2):
            p1, p2 = participants_data[i], participants_data[i+1]
            round1_matches.append({
                'match_id': f"R1M{i//2 + 1}", 'player1': p1, 'player2': p2,
                'winner': None, 'status': 'pending'
            })
        rounds.append(round1_matches)
        return {'rounds': rounds, 'current_round_index': 0, 'matches_in_progress': 0}

    def report_match_result(self, tournament_id: str, match_id: str, winner_user_id: int) -> Tuple[bool, str]:
        tournament = self.tournaments.get(tournament_id)
        if not tournament or tournament['status'] != 'in_progress': return False, "Tournament not active."
        brackets, current_round_index = tournament['brackets'], brackets['current_round_index']
        if current_round_index >= len(brackets['rounds']): return False, "Invalid round."
        current_round_matches = brackets['rounds'][current_round_index]
        match_found, winner_data = False, None
        for match in current_round_matches:
            if match['match_id'] == match_id and match['status'] != 'finished':
                match_found = True
                p1_id, p2_id = match['player1']['user_id'], match['player2']['user_id']
                if winner_user_id == p1_id: winner_data = match['player1']
                elif winner_user_id == p2_id: winner_data = match['player2']
                else: return False, "Winner ID mismatch."
                match['winner'], match['status'] = winner_data, 'finished'
                break
        if not match_found: return False, "Match not found or finished."
        if all(m['status'] == 'finished' for m in current_round_matches):
            winners = [m['winner'] for m in current_round_matches if m['winner']]
            if len(winners) == 1:
                tournament['status'], tournament['winner'] = 'finished', winners[0]
                player_manager.add_coins(winners[0]['user_id'], tournament['current_pot'])
                return True, f"Tournament finished! Winner: {winners[0]['username']}"
            elif len(winners) > 1:
                 brackets['current_round_index'] += 1; next_round_index = brackets['current_round_index']
                 next_round_matches = []
                 for i in range(0, len(winners), 2):
                    p1, p2 = winners[i], winners[i+1]
                    next_round_matches.append({
                        'match_id': f"R{next_round_index+1}M{i//2 + 1}", 'player1': p1, 'player2': p2,
                        'winner': None, 'status': 'pending'
                    })
                 brackets['rounds'].append(next_round_matches)
                 return True, "Round complete. Next round ready."
        return True, "Match result recorded."

    def format_tournament_info(self, tournament_id: str) -> str:
        tournament = self.tournaments.get(tournament_id)
        if not tournament: return "Tournament not found!"
        text = (f"🏆 <b>{tournament['name']}</b> 🏆\n\n🎮 Mode: {tournament['mode'].upper()}\n"
                f"👥 Players: {len(tournament['participants'])}/{tournament['max_players']}\n"
                f"💰 Entry: {tournament['entry_fee']} | 🎁 Pot: {tournament['current_pot']} coins\n"
                f"📊 Status: {tournament['status'].upper()}\n")
        if tournament['status'] == 'finished': text += f"🏅 Winner: {tournament['winner']['username']}\n"
        elif tournament['status'] == 'in_progress': text += f"⚔️ Round: {tournament['brackets']['current_round_index'] + 1}\n"
        return text

    def format_tournament_brackets(self, tournament_id: str) -> str:
        tournament = self.tournaments.get(tournament_id)
        if not tournament or not tournament.get('brackets'): return "Brackets not created."
        text = f"🏆 <b>{tournament['name']} - Brackets</b> 🏆\n\n"
        for i, round_matches in enumerate(tournament['brackets']['rounds']):
            text += f"<b>--- Round {i+1} ---</b>\n"
            for match in round_matches:
                p1, p2 = match['player1']['username'], match['player2']['username']
                winner = f" -> {match['winner']['username']} 🏆" if match['winner'] else ""
                status = "✅" if match['status'] == 'finished' else ("▶️" if match['status'] == 'active' else "⏳")
                text += f"{status} {match['match_id']}: {p1} vs {p2}{winner}\n"
            text += "\n"
        if tournament['status'] == 'finished': text += f"🏅 <b>Winner: {tournament['winner']['username']}</b> 🏅\n"
        return text

class SeasonalEvents: pass
class ClanSystem: pass
class ReplaySystem:
    def __init__(self): self.replays: Dict[str, dict] = {}
    def save_replay(self, game_id: str, game_data: dict):
        self.replays[game_id] = {
            'game_id': game_id, 'mode': game_data.get('mode'),
            'players': game_data.get('players'), 'events': game_data.get('events'),
            'winner': game_data.get('winner'), 'rounds': game_data.get('round'),
            'saved_at': datetime.now().isoformat()
        }
        print(f"Replay saved for {game_id}")
    def get_replay(self, game_id: str) -> Optional[dict]: return self.replays.get(game_id)
    def format_replay_summary(self, game_id: str) -> str:
        replay = self.get_replay(game_id)
        if not replay: return "Replay not found!"
        text = (f"🎬 <b>REPLAY: {game_id}</b> 🎬\n🎯 Mode: {replay['mode'].upper()}\n"
                f"🔄 Rounds: {replay['rounds']}\n🏆 Winner: {str(replay['winner']).upper()}\n\n<b>Players:</b>\n")
        text += "\n".join(f"{'✅' if p.get('alive') else '💀'} {p.get('username')} - {p.get('role').upper()}" for p in replay['players'])
        return text

# --- Instantiate Global Systems ---
trading_system = TradingSystem()
tournament_system = TournamentSystem()
replay_system = ReplaySystem() # This creates the instance
