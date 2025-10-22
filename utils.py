"""
Mafia RPG Telegram Bot - Main Entry Point
Complete implementation with INLINE keyboards
"""

import logging
import asyncio
import random
import os
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove, InputFile
from telegram.error import BadRequest
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
    CallbackQueryHandler
)
from game_manager import GameManager
from player_manager import PlayerManager
from enhanced_features import tournament_system, trading_system
from config import BOT_TOKEN, FEATURES, SHOP_ITEMS, ADMIN_IDS, MISSION_REWARDS, ANIMATION_SEQUENCES, BOT_USERNAME, MAFIA_PIC_URL
from utils import (
    create_main_menu_keyboard, create_play_menu_keyboard,
    format_player_stats, format_leaderboard_entry,
    send_animated_message, send_role_reveal_animation,
    create_shop_keyboard, create_lobby_keyboard, # <- Uses the updated version
    create_missions_menu_keyboard, get_role_emoji,
    create_tournament_menu_keyboard, create_trade_menu_keyboard
)

# Configure logging (Unchanged)
# ...

# Global managers (Unchanged)
# ...

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Welcome message and main menu"""
    # ... (code unchanged)
    pass

# --- COMMAND HANDLERS ---
# ... (play_command, shop_command, etc. - unchanged)
async def play_command(update: Update, context: ContextTypes.DEFAULT_TYPE): await update.message.reply_text("🎮 Choose Mode:", reply_markup=create_play_menu_keyboard())
async def shop_command(update: Update, context: ContextTypes.DEFAULT_TYPE): player = player_manager.get_player(update.effective_user.id); text = f"🏪 SHOP | 💰 Coins: <b>{player['coins']}</b>"; keyboard = create_shop_keyboard(player['items']); await update.message.reply_text(text, parse_mode='HTML', reply_markup=keyboard)
async def profile_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE): player = player_manager.get_player(update.effective_user.id); await update.message.reply_text(format_player_stats(player), parse_mode='HTML')
async def leaderboard_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE): top = player_manager.get_leaderboard(10); text = "🏆 TOP PLAYERS 🏆\n\n" + ("None yet!" if not top else "\n".join(format_leaderboard_entry(i, p) for i, p in enumerate(top, 1))); await update.message.reply_text(text, parse_mode='HTML')
async def daily_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE): success, reward = player_manager.claim_daily_reward(update.effective_user.id); text = f"🎉 DAILY! 🎉\n💎{reward['xp']} XP\n🪙{reward['coins']} Coins\n🔥Streak: {reward['streak']}" if success else "⏰ Claimed!"; await update.message.reply_text(text, parse_mode='HTML')
async def tournament_command(update: Update, context: ContextTypes.DEFAULT_TYPE): await update.message.reply_text("🏆 TOURNAMENTS 🏆", reply_markup=create_tournament_menu_keyboard())
async def trade_command(update: Update, context: ContextTypes.DEFAULT_TYPE): await update.message.reply_text("📈 TRADING POST 📈", reply_markup=create_trade_menu_keyboard())
async def help_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE): text = ("❓ HELP ❓\n\nBasics...\n\n⚡ COMMANDS:\n/start /play /shop /profile...\n/logs (A) /botstats (A)"); await update.message.reply_text(text, parse_mode='HTML')


# --- Message Handler ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # ... (code unchanged)
    pass

# --- Callback Query Handler ---
async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # ... (routing logic unchanged)
    pass

# --- MENU DISPLAY FUNCTIONS ---
async def safe_edit_message(query, text, keyboard):
    # ... (code unchanged)
    pass
async def show_main_menu_callback(query, context):
    # ... (code unchanged)
    pass
async def show_play_menu(query, context):
    # ... (code unchanged)
    pass
async def show_profile(query, context):
    # ... (code unchanged)
    pass
async def show_leaderboard(query, context):
    # ... (code unchanged)
    pass
async def claim_daily_reward(query, context):
    # ... (code unchanged)
    pass
async def show_shop(query, context):
    # ... (code unchanged)
    pass
async def show_help_callback(query, context):
    # ... (code unchanged)
    pass
async def show_tournament_menu(query, context):
    # ... (code unchanged)
    pass
async def show_trade_menu(query, context):
    # ... (code unchanged)
    pass

# --- LOBBY/GAME FUNCTIONS ---
async def create_game_lobby(query, context, mode: str):
    """Create a new game lobby via callback"""
    user_id = query.from_user.id
    chat_id = query.message.chat_id
    game_id = game_manager.create_game(mode, user_id, chat_id)
    context.chat_data['active_game'] = game_id
    game = game_manager.get_game(game_id)
    req = game_manager.get_required_players(mode)
    text = (f"🎮 LOBBY <code>{game_id}</code> | <b>{mode.upper()}</b>\n"
            f"👥 {len(game['players'])}/{req} | 👑 {query.from_user.username or query.from_user.first_name}\nWaiting...")
    # --- FIX: Pass viewer_user_id ---
    keyboard = create_lobby_keyboard(game_id, viewer_user_id=user_id)
    # --------------------------------
    await safe_edit_message(query, text, keyboard)

async def join_game_action(query, context, game_id: str, user_id: int, username: str):
    """Join an existing game via callback"""
    success, msg = game_manager.join_game(game_id, user_id, username)
    if success:
        await query.answer("✅ Joined!")
        game = game_manager.get_game(game_id); req = game_manager.get_required_players(game['mode'])
        text = f"🎮 LOBBY <code>{game_id}</code> | <b>{game['mode'].upper()}</b>\n👥 {len(game['players'])}/{req}\n\nPlayers:\n"
        text += "\n".join(f"{'👑' if p['user_id']==game['creator_id'] else '•'} {p['username']}" for p in game['players'])
        if len(game['players'])>=req: text+="\n🎉 Full! Ready to start!"
        # --- FIX: Pass viewer_user_id (the user who clicked Join) ---
        keyboard = create_lobby_keyboard(game_id, viewer_user_id=user_id)
        # ---------------------------------------------------------
        await safe_edit_message(query, text, keyboard)
        # --- FIX: Also update for the creator ---
        # If the lobby is now full, try to update the message for the creator too
        if len(game['players']) >= req and game['creator_id'] != user_id:
             creator_keyboard = create_lobby_keyboard(game_id, viewer_user_id=game['creator_id'])
             try:
                 # Need the original message ID sent to the creator. This is tricky.
                 # A better approach might be to just notify the creator separately.
                 await context.bot.send_message(
                     chat_id=game['chat_id'], # Send to the group/chat where lobby is
                     text=f"@{game['players'][0]['username']} The lobby is full! You can now /start the game.",
                     # Ideally we would edit the original message, but getting its ID is complex here.
                 )
                 # Or update the message with the keyboard including the start button for everyone
                 await query.edit_message_text(text, parse_mode='HTML', reply_markup=creator_keyboard)

             except Exception as e:
                 logger.error(f"Could not update creator's lobby view: {e}")

    else: await query.answer(f"❌ {msg}", True)


async def start_game_action(query, context, game_id: str, user_id: int):
    # ... (code unchanged)
    pass
async def cancel_game_action(query, context, game_id: str, user_id: int):
    # ... (code unchanged)
    pass

# --- SHOP ---
async def handle_purchase(query, context, item_id, user_id):
    # ... (code unchanged)
    pass

# --- MISSIONS ---
# ... (All mission functions unchanged)
async def show_missions_menu(query, context): pass
async def start_target_practice(query, context): pass
async def send_target_practice_round(query, context): pass
async def handle_target_practice(query, context, data): pass
async def end_target_practice(query, context): pass
async def start_detectives_case(query, context): pass
async def handle_detectives_case(query, context, data): pass
async def start_doctors_dilemma(query, context): pass
async def handle_doctors_dilemma(query, context, data): pass
async def start_timed_disarm(query, context): pass
async def handle_timed_disarm(query, context, data): pass
async def start_mafia_heist(query, context): pass
async def handle_mafia_heist(query, context, data): pass

# --- TOURNAMENT/TRADE FUNCTIONS ---
# ... (Placeholders unchanged)
async def create_new_tournament(query, context): pass
async def list_tournaments(query, context): pass
async def show_tournament_details(query, context, tournament_id): pass
async def register_for_tournament(query, context, tournament_id): pass
async def start_tournament_handler(query, context, tournament_id): pass
async def show_tournament_brackets(query, context, tournament_id): pass
async def start_create_trade(query, context): pass
async def handle_trade_partner_input(update: Update, context: ContextTypes.DEFAULT_TYPE): pass
async def handle_trade_offer_coins_input(update: Update, context: ContextTypes.DEFAULT_TYPE): pass
async def list_active_trades(query, context): pass
async def accept_trade_offer(query, context, trade_id): pass
async def cancel_trade_offer(query, context, trade_id): pass

# --- ADMIN AND ERROR HANDLERS ---
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # ... (code unchanged)
    pass
async def get_logs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # ... (code unchanged)
    pass
async def get_bot_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # ... (code unchanged)
    pass

def main():
    """Start the bot"""
    # ... (code unchanged)
    pass

if __name__ == '__main__':
    # ... (code unchanged)
    pass
