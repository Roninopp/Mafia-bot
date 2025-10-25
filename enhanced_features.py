""""""
Enhanced Features Module - Trading, Tournaments, Replay
"""

import random
import json # Needed for ClanSystem load/save
import os   # Needed for ClanSystem load/save
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from player_manager import PlayerManager
from config import SHOP_ITEMS

# Use a single instance of PlayerManager
player_manager = PlayerManager()

class TradingSystem:
    def __init__(self):
        self.active_trades: Dict[str, dict] = {}
        self.trade_counter = 0

    def create_trade_offer(self, sender_id: int, receiver_id: int,
                          offer_coins: int, offer_items_ids: List[str],
                          request_coins: int, request_items_ids: List[str]) -> Tuple[Optional[str], str]:
        sender = player_manager.get_player(sender_id)
        receiver = player_manager.get_player(receiver_id)
        if not sender or not receiver: return None, "Player not found."
        if sender.get('coins', 0) < offer_coins: return None, "You don't have enough coins!"
        for item_id in offer_items_ids:
            if not player_manager.has_item(sender_id, item_id): return None, f"You don't own {item_id}!"

        self.trade_counter += 1
        trade_id = f"trade_{self.trade_counter}_{random.randint(100,999)}"
        self.active_trades[trade_id] = {
            'id': trade_id, 'sender_id': sender_id, 'sender_username': sender.get('username','?'),
            'receiver_id': receiver_id, 'receiver_username': receiver.get('username','?'),
            'offer': {'coins': offer_coins, 'items': offer_items_ids},
            'request': {'coins': request_coins, 'items': request_items_ids},
            'status': 'pending', 'created_at': datetime.now().isoformat()
        }
        print(f"Trade {trade_id} created: {sender.get('username','?')} -> {receiver.get('username','?')}")
        # In real bot: send message to receiver with accept/decline buttons
        return trade_id, f"Trade offer sent to {receiver.get('username','?')}!"

    def get_trade(self, trade_id: str) -> Optional[dict]:
        return self.active_trades.get(trade_id)

    def accept_trade(self, trade_id: str, accepting_user_id: int) -> Tuple[bool, str]:
        trade = self.active_trades.get(trade_id)
        if not trade: return False, "Trade not found!"
        if trade['status'] != 'pending': return False, "Trade processed!"
        if trade['receiver_id'] != accepting_user_id: return False, "Not your trade!"
        sender = player_manager.get_player(trade['sender_id'])
        receiver = player_manager.get_player(trade['receiver_id'])
        if not sender or not receiver: return False, "Player missing."

        # Validate resources
        if sender.get('coins', 0) < trade['offer']['coins']: trade['status'] = 'failed'; return False, f"{trade['sender_username']} lacks coins!"
        for item_id in trade['offer']['items']:
            if not player_manager.has_item(trade['sender_id'], item_id): trade['status'] = 'failed'; return False, f"{trade['sender_username']} lacks {item_id}"
        if receiver.get('coins', 0) < trade['request']['coins']: return False, "You lack coins!"
        for item_id in trade['request']['items']:
            if not player_manager.has_item(trade['receiver_id'], item_id): return False, f"You lack {item_id}"

        # Process Trade
        try:
            # Coins
            if not player_manager.spend_coins(trade['sender_id'], trade['offer']['coins']): raise ValueError("Sender coin spend failed")
            player_manager.add_coins(trade['receiver_id'], trade['offer']['coins'])
            if not player_manager.spend_coins(trade['receiver_id'], trade['request']['coins']): raise ValueError("Receiver coin spend failed")
            player_manager.add_coins(trade['sender_id'], trade['request']['coins'])
            
            # Items
            all_items_map = {item['id']: item for item in SHOP_ITEMS}
            for item_id in trade['offer']['items']:
                details = all_items_map.get(item_id)
                if details and player_manager.remove_item(trade['sender_id'], item_id): player_manager.add_item(trade['receiver_id'], details)
                else: raise ValueError(f"Failed transfer offer {item_id}")
            for item_id in trade['request']['items']:
                details = all_items_map.get(item_id)
                if details and player_manager.remove_item(trade['receiver_id'], item_id): player_manager.add_item(trade['sender_id'], details)
                else: raise ValueError(f"Failed transfer request {item_id}")

            trade['status'] = 'completed'; print(f"Trade {trade_id} completed!")
            return True, "Trade completed!"
        except Exception as e:
            print(f"ERROR trade {trade_id}: {e}. Rolling back coins.")
            # Basic rollback (might fail if accounts are empty)
            player_manager.add_coins(trade['sender_id'], trade['offer']['coins'])
            player_manager.spend_coins(trade['receiver_id'], trade['offer']['coins'])
            player_manager.add_coins(trade['receiver_id'], trade['request']['coins'])
            player_manager.spend_coins(trade['sender_id'], trade['request']['coins'])
            trade['status'] = 'failed'; return False, f"Error: {e}"

    def cancel_trade(self, trade_id: str, user_id: int) -> Tuple[bool, str]:
        trade = self.active_trades.get(trade_id)
        if not trade: return False, "Trade not found!"
        if trade['status'] != 'pending': return False, "Trade processed!"
        if trade['sender_id'] != user_id and trade['receiver_id'] != user_id: return False, "Not your trade!"
        trade['status'] = 'cancelled'; return True, "Trade cancelled!"

class TournamentSystem:
    # ... (Placeholder, code is okay but not fully integrated in main bot yet)
    pass

class ClanSystem:
    # ... (Placeholder, code is okay but not fully integrated in main bot yet)
    pass

class ReplaySystem:
    def __init__(self): self.replays: Dict[str, dict] = {}
    def save_replay(self, game_id: str, game_data: dict):
        replay_copy = { # Deep copy might be safer if game_data structure is complex
            k: v for k, v in game_data.items() if k in ['id', 'mode', 'players', 'events', 'winner', 'round']
        }
        replay_copy['saved_at'] = datetime.now().isoformat()
        self.replays[game_id] = replay_copy
        print(f"Replay saved for {game_id}")
    def get_replay(self, game_id: str) -> Optional[dict]: return self.replays.get(game_id)
    # ... (format_replay_summary etc.)

# --- Instantiate Global Systems ---
trading_system = TradingSystem()
tournament_system = TournamentSystem()
# clan_system = ClanSystem() # Keep commented if FEATURES['clans_enabled'] = False
replay_system = ReplaySystem() # This creates the instance
