"""
Utility Functions for Mafia RPG Bot
"""

import asyncio
import logging
from datetime import datetime, timedelta
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from config import EMOJIS, LOADING_FRAMES, ANIMATION_SEQUENCES, SHOP_ITEMS, BOT_USERNAME
# --- Import GameManager to check game state ---
from game_manager import GameManager, game_manager # Use the global instance
# -------------------------------------------

logger = logging.getLogger(__name__)

# --- INLINE KEYBOARD FUNCTIONS ---

def create_main_menu_keyboard(is_private: bool = False) -> InlineKeyboardMarkup:
    """Creates the main menu inline keyboard."""
    # ... (code unchanged)
    pass

def create_play_menu_keyboard() -> InlineKeyboardMarkup:
    """Creates the game mode selection inline keyboard."""
    # ... (code unchanged)
    pass

def create_shop_keyboard(player_items: list) -> InlineKeyboardMarkup:
    """Creates the inline shop keyboard."""
    # ... (code unchanged)
    pass

# --- FIX: Updated create_lobby_keyboard ---
def create_lobby_keyboard(game_id: str, viewer_user_id: int) -> InlineKeyboardMarkup:
    """Create game lobby inline keyboard, showing Start only if viewer is creator and lobby is ready."""
    keyboard = []
    game = game_manager.get_game(game_id) # Fetch game state

    if not game: # Should not happen, but safety check
        return InlineKeyboardMarkup([[InlineKeyboardButton("Error: Game not found", callback_data="none")]])

    # Show "Join Game" button only if the game is waiting and viewer isn't already in
    is_player_in_game = any(p['user_id'] == viewer_user_id for p in game['players'])
    if game['status'] == 'waiting' and not is_player_in_game:
        max_players = game_manager.get_required_players(game['mode']) # Get correct max players
        if len(game['players']) < max_players:
             keyboard.append([InlineKeyboardButton("✅ Join Game", callback_data=f"join_game_{game_id}")])

    # Show "Start Game" button *only* if viewer is creator AND min players met
    is_creator = (viewer_user_id == game['creator_id'])
    required_players = game_manager.get_required_players(game['mode'])
    if is_creator and game['status'] == 'waiting' and len(game['players']) >= required_players:
        keyboard.append([InlineKeyboardButton("🚀 Start Game", callback_data=f"start_game_{game_id}")])

    # Show "Cancel Game" button *only* if viewer is creator AND game is waiting
    if is_creator and game['status'] == 'waiting':
        keyboard.append([InlineKeyboardButton("❌ Cancel Game", callback_data=f"cancel_game_{game_id}")])

    # Add a Back button if appropriate (e.g., if viewer is not in game or game ended)
    # For simplicity, maybe just always show it? Or rely on /start. Let's omit for now.

    # If keyboard is empty (e.g., game started and viewer is not creator), show something
    if not keyboard:
         keyboard.append([InlineKeyboardButton("Game in Progress or Ended", callback_data="none")])

    return InlineKeyboardMarkup(keyboard)
# ------------------------------------------

def create_missions_menu_keyboard() -> InlineKeyboardMarkup:
    """Creates the missions menu inline keyboard."""
    # ... (code unchanged)
    pass

def create_tournament_menu_keyboard() -> InlineKeyboardMarkup:
    """Creates the tournament menu inline keyboard."""
    # ... (code unchanged)
    pass

def create_trade_menu_keyboard() -> InlineKeyboardMarkup:
    """Creates the trade menu inline keyboard."""
    # ... (code unchanged)
    pass

# --- REPLY KEYBOARD FUNCTIONS (FOR IN-GAME ACTIONS) ---
def create_voting_keyboard(players: list) -> ReplyKeyboardMarkup:
    # ... (code unchanged)
    pass

def create_player_action_keyboard(action: str, players: list) -> ReplyKeyboardMarkup:
    # ... (code unchanged)
    pass


# --- FORMATTING AND ANIMATION FUNCTIONS --- (Unchanged)
def format_player_stats(player: dict) -> str:
    # ... (code unchanged)
    pass
def create_progress_bar(percentage: float, length: int = 10) -> str:
    # ... (code unchanged)
    pass
def calculate_xp_for_level(level: int) -> int:
    # ... (code unchanged)
    pass
async def send_animated_message(message, frames: list, delay: float = 1.0):
    # ... (code unchanged)
    pass
def format_leaderboard_entry(rank: int, player: dict) -> str:
    # ... (code unchanged)
    pass
def generate_game_id() -> str:
    # ... (code unchanged)
    pass
def get_role_emoji(role: str) -> str:
    # ... (code unchanged)
    pass
def format_night_summary(eliminated: dict, protected_info: dict, investigated: dict = None) -> str:
    # ... (code unchanged)
    pass
def format_day_summary(eliminated: dict, vote_count: int) -> str:
    # ... (code unchanged)
    pass
def get_rank_title(level: int) -> str:
    # ... (code unchanged)
    pass
def format_vote_results(game: dict, vote_counts: dict) -> str:
    # ... (code unchanged)
    pass
async def send_role_reveal_animation(context, user_id: int, role: str, description: str):
    # ... (code unchanged)
    pass
async def send_elimination_animation(message, username: str, role: str):
    # ... (code unchanged)
    pass
async def send_phase_transition(message, phase: str):
    # ... (code unchanged)
    pass
async def send_victory_animation(message, winner: str, winners: list):
    # ... (code unchanged)
    pass
