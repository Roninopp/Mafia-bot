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
    create_shop_keyboard, create_lobby_keyboard,
    create_missions_menu_keyboard, get_role_emoji,
    create_tournament_menu_keyboard, create_trade_menu_keyboard
)

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Global managers
game_manager = GameManager()
player_manager = PlayerManager()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Welcome message and main menu"""
    user = update.effective_user
    chat = update.effective_chat

    player_manager.register_player(user.id, user.username or user.first_name)

    if chat.type == 'private':
        welcome_text = (
            f"🚬 <b>Welcome to the family, {user.first_name}.</b>\n\n"
            "This city is run by gangs, wits, and bullets. "
            "You look like you've got what it takes to rise to the top.\n\n"
            "👥 <b>Join Games:</b> Fight in 5v5 and 1v1 battles.\n"
            "🚀 <b>Run Missions:</b> Take on solo challenges for cash.\n"
            "🏆 <b>Build Your Rep:</b> Level up, earn coins, and buy gear.\n"
            "⚔️ <b>Compete:</b> Join Tournaments for glory & prizes.\n"
            "📈 <b>Trade:</b> Exchange items and coins with others.\n\n"
            "Think you're ready? Show me."
        )
        keyboard = create_main_menu_keyboard(is_private=True)

        try:
            await context.bot.send_photo(chat_id=chat.id, photo=MAFIA_PIC_URL)
        except Exception as e:
            logger.error(f"Failed to send start photo: {e}.")

        await context.bot.send_message(
            chat_id=chat.id,
            text=welcome_text,
            parse_mode='HTML',
            reply_markup=keyboard
        )
    else:
        welcome_text = (
            f"🎭 <b>MAFIA RPG</b> 🎭\n\n"
            f"🔥 <b>Welcome, {user.first_name}!</b> 🔥\n\n"
            "I'm ready to manage your games. Use /play to start a lobby!"
        )
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🎮 Play Game (in PM)", url=f"https://t.me/{BOT_USERNAME}?start=play")]
        ])
        await update.message.reply_text(welcome_text, parse_mode='HTML', reply_markup=keyboard)


# --- COMMAND HANDLERS ---
async def play_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Shows the Play menu via /play command"""
    text = "🎮 <b>SELECT GAME MODE</b> 🎮\n\nChoose your poison:"
    keyboard = create_play_menu_keyboard()
    await update.message.reply_text(text, parse_mode='HTML', reply_markup=keyboard)

async def shop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Shows the Shop menu via /shop command"""
    user_id = update.effective_user.id
    player = player_manager.get_player(user_id)
    if not player:
        await update.message.reply_text("Please /start the bot first to create your profile.")
        return
    text = f"🏪 <b>SHOP</b> 🏪\n\n💰 Your Coins: <b>{player['coins']}</b>\n\nSelect an item to purchase:"
    keyboard = create_shop_keyboard(player['items'])
    await update.message.reply_text(text, parse_mode='HTML', reply_markup=keyboard)

async def profile_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Shows the profile via /profile command"""
    user_id = update.effective_user.id
    player_data = player_manager.get_player(user_id)
    if not player_data:
        await update.message.reply_text("Please /start the bot first to create your profile.")
        return
    profile_text = format_player_stats(player_data)
    await update.message.reply_text(profile_text, parse_mode='HTML')

async def leaderboard_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Shows the leaderboard via /leaderboard command"""
    top_players = player_manager.get_leaderboard(10)
    text = "🏆 <b>TOP PLAYERS</b> 🏆\n\n"
    if not top_players:
        text += "No players yet! Be the first!"
    else:
        for i, player in enumerate(top_players, 1):
            text += format_leaderboard_entry(i, player) + "\n"
    await update.message.reply_text(text, parse_mode='HTML')

async def daily_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Claims daily reward via /daily command"""
    user_id = update.effective_user.id
    success, reward = player_manager.claim_daily_reward(user_id)
    if success:
        text = (f"🎉 <b>DAILY REWARD CLAIMED!</b> 🎉\n\n"
                f"You received:\n💎 {reward['xp']} XP\n🪙 {reward['coins']} Coins\n"
                f"🔥 Streak: {reward['streak']} days\n\nCome back tomorrow!")
    else:
        text = ("⏰ <b>Already Claimed!</b>\n\nYou've already claimed your daily reward.\n"
                "Come back tomorrow for more goodies!")
    await update.message.reply_text(text, parse_mode='HTML')

async def tournament_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Shows the Tournament menu via /tournament command"""
    if not FEATURES['tournaments_enabled']:
        await update.message.reply_text("Tournaments are currently disabled.")
        return
    text = "🏆 <b>TOURNAMENTS</b> 🏆\n\nCompete for glory and coins!"
    keyboard = create_tournament_menu_keyboard()
    await update.message.reply_text(text, parse_mode='HTML', reply_markup=keyboard)

async def trade_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Shows the Trade menu via /trade command"""
    if not FEATURES['trading_enabled']:
        await update.message.reply_text("Trading is currently disabled.")
        return
    text = "📈 <b>TRADING POST</b> 📈\n\nExchange items and coins with other players."
    keyboard = create_trade_menu_keyboard()
    await update.message.reply_text(text, parse_mode='HTML', reply_markup=keyboard)

# --- This function handles the /help command ---
async def help_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show help via command"""
    text = (
        "❓ <b>HOW TO PLAY</b> ❓\n\n"
        "<b>🎭 GAME BASICS:</b>\n"
        "• Players are assigned secret roles.\n"
        "• Mafia eliminates at night.\n"
        "• Villagers vote during the day.\n\n"
        "<b>⚡ COMMANDS:</b>\n"
        "/start - Main menu\n"
        "/play - Open game modes\n"
        "/shop - Open the item shop\n"
        "/profile - View your stats\n"
        "/leaderboard - See top players\n"
        "/daily - Claim your daily reward\n"
        "/tournament - Tournament menu\n"
        "/trade - Trade menu\n"
        "/logs - (Admin) Get bot logs\n"
        "/botstats - (Admin) Get bot stats"
    )
    await update.message.reply_text(text, parse_mode='HTML')


# --- Message Handler (for game actions) ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages (now only for in-game actions & trade setup)"""
    # ... (code unchanged) ...
    pass

# --- Callback Query Handler (for ALL inline buttons) ---
async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all inline button presses"""
    query = update.callback_query
    # Check if the query message still exists before answering
    if not query.message:
        logger.warning("Query message not found, skipping answer.")
        return
    try:
        await query.answer()
    except BadRequest as e:
        # Ignore errors like "query is too old" if the user double-clicks fast
        if "query is too old" not in str(e).lower():
            logger.error(f"Error answering callback query: {e}")
        return # Stop processing if we can't answer

    data = query.data
    user_id = query.from_user.id
    username = query.from_user.username or query.from_user.first_name

    # Clear mission/trade state if not relevant
    if not data.startswith(('mission_', 'shoot_', 'case_', 'dilemma_', 'disarm_', 'heist_', 'trade_', 'tourn_')):
        context.user_data.pop('mission_state', None)
        context.user_data.pop('trade_setup', None)
        context.user_data.pop('state', None)

    # Main Menu Navigation
    if data == 'menu_main': await show_main_menu_callback(query, context)
    elif data == 'menu_play': await show_play_menu(query, context)
    elif data == 'menu_profile': await show_profile(query, context)
    elif data == 'menu_leaderboard': await show_leaderboard(query, context)
    elif data == 'menu_daily': await claim_daily_reward(query, context)
    elif data == 'menu_shop': await show_shop(query, context)
    elif data == 'menu_help': await show_help_callback(query, context) # Changed to use callback version
    elif data == 'menu_tournament': await show_tournament_menu(query, context)
    elif data == 'menu_trade': await show_trade_menu(query, context)

    # Game Mode Selection
    elif data == 'mode_5v5': await create_game_lobby(query, context, '5v5')
    elif data == 'mode_1v1': await create_game_lobby(query, context, '1v1')
    elif data == 'menu_missions': await show_missions_menu(query, context)

    # Lobby Actions
    elif data.startswith('join_game_'): await join_game_action(query, context, data.split('_')[-1], user_id, username)
    elif data.startswith('start_game_'): await start_game_action(query, context, data.split('_')[-1], user_id)
    elif data.startswith('cancel_game_'): await cancel_game_action(query, context, data.split('_')[-1], user_id)

    # Shop Actions
    elif data.startswith('buy_item_'): await handle_purchase(query, context, data.split('_')[-1], user_id)

    # Mission Actions
    elif data == 'mission_target_practice': await start_target_practice(query, context)
    elif data.startswith('shoot_'): await handle_target_practice(query, context, data)
    elif data == 'mission_detectives_case': await start_detectives_case(query, context)
    elif data.startswith('case_'): await handle_detectives_case(query, context, data)
    elif data == 'mission_doctors_dilemma': await start_doctors_dilemma(query, context)
    elif data.startswith('dilemma_'): await handle_doctors_dilemma(query, context, data)
    elif data == 'mission_timed_disarm': await start_timed_disarm(query, context)
    elif data.startswith('disarm_click_'): await handle_timed_disarm(query, context, data)
    elif data == 'mission_mafia_heist': await start_mafia_heist(query, context)
    elif data.startswith('heist_'): await handle_mafia_heist(query, context, data)

    # Tournament Actions
    elif data == 'tourn_create': await create_new_tournament(query, context)
    elif data == 'tourn_list': await list_tournaments(query, context)
    elif data.startswith('tourn_view_'): await show_tournament_details(query, context, data.split('_')[-1])
    elif data.startswith('tourn_register_'): await register_for_tournament(query, context, data.split('_')[-1])
    elif data.startswith('tourn_start_'): await start_tournament_handler(query, context, data.split('_')[-1])
    elif data.startswith('tourn_brackets_'): await show_tournament_brackets(query, context, data.split('_')[-1]) # Added handler

    # Trade Actions
    elif data == 'trade_create': await start_create_trade(query, context)
    elif data == 'trade_list': await list_active_trades(query, context)
    elif data.startswith('trade_accept_'): await accept_trade_offer(query, context, data.split('_')[-1])
    elif data.startswith('trade_cancel_'): await cancel_trade_offer(query, context, data.split('_')[-1])


# --- MENU DISPLAY FUNCTIONS ---
async def safe_edit_message(query, text, keyboard):
    """Helper to safely edit a message, falling back if needed."""
    if not query or not query.message:
        logger.warning("safe_edit_message called with invalid query or message.")
        return
    try:
        await query.edit_message_text(text, parse_mode='HTML', reply_markup=keyboard)
    except BadRequest as e:
        if "message is not modified" not in str(e).lower():
            logger.warning(f"Failed to edit message (BadRequest), sending new one. Error: {e}")
            await query.message.reply_text(text, parse_mode='HTML', reply_markup=keyboard)
    except Exception as e:
        logger.error(f"Unhandled error in safe_edit_message: {e}")
        # Send a new message as a fallback
        try:
            await query.message.reply_text(text, parse_mode='HTML', reply_markup=keyboard)
        except Exception as e2:
             logger.error(f"Fallback reply_text also failed: {e2}")


async def show_main_menu_callback(query, context):
    """Shows the main menu via callback"""
    user = query.from_user
    welcome_text = f"🚬 <b>Welcome back, {user.first_name}.</b>\n\nWhat's the move?"
    keyboard = create_main_menu_keyboard(is_private=True)
    await safe_edit_message(query, welcome_text, keyboard)

async def show_play_menu(query, context):
    """Show game mode selection menu"""
    text = "🎮 <b>SELECT GAME MODE</b> 🎮\n\nChoose your poison:"
    keyboard = create_play_menu_keyboard()
    await safe_edit_message(query, text, keyboard)

async def show_profile(query, context):
    """Show player profile via callback"""
    user_id = query.from_user.id
    player_data = player_manager.get_player(user_id)
    if not player_data:
        await safe_edit_message(query, "❌ Profile not found! Use /start first.", None)
        return
    profile_text = format_player_stats(player_data)
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Menu", callback_data='menu_main')]])
    await safe_edit_message(query, profile_text, keyboard)

async def show_leaderboard(query, context):
    """Show top players via callback"""
    # ... (code unchanged) ...
    pass

async def claim_daily_reward(query, context):
    """Claim daily reward via callback"""
    # ... (code unchanged) ...
    pass

async def show_shop(query, context):
    """Show shop items via callback"""
    # ... (code unchanged) ...
    pass

# --- Renamed help function for callback ---
async def show_help_callback(query, context):
    """Show help information via callback"""
    text = (
        "❓ <b>HOW TO PLAY</b> ❓\n\n"
        "<b>🎭 GAME BASICS:</b>\n"
        "• Players are assigned secret roles.\n"
        "• Mafia eliminates at night.\n"
        "• Villagers vote during the day.\n\n"
        "<b>⚡ COMMANDS:</b>\n"
        "/start - Main menu\n"
        "/play - Open game modes\n"
        "/shop - Open the item shop\n"
        "/profile - View your stats\n"
        "/leaderboard - See top players\n"
        "/daily - Claim your daily reward\n"
        "/tournament - Tournament menu\n"
        "/trade - Trade menu\n"
        "/logs - (Admin) Get bot logs\n"
        "/botstats - (Admin) Get bot stats"
    )
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Menu", callback_data='menu_main')]])
    await safe_edit_message(query, text, keyboard)


# --- TOURNAMENT/TRADE MENUS ---
async def show_tournament_menu(query, context):
    """Displays the main tournament menu."""
    if not FEATURES['tournaments_enabled']: await query.answer("Tournaments disabled.", show_alert=True); return
    text = "🏆 <b>TOURNAMENTS</b> 🏆\n\nCompete for glory and coins!"
    keyboard = create_tournament_menu_keyboard()
    await safe_edit_message(query, text, keyboard)

async def show_trade_menu(query, context):
    """Displays the main trade menu."""
    if not FEATURES['trading_enabled']: await query.answer("Trading disabled.", show_alert=True); return
    text = "📈 <b>TRADING POST</b> 📈\n\nExchange items and coins."
    keyboard = create_trade_menu_keyboard()
    await safe_edit_message(query, text, keyboard)


# --- LOBBY/GAME FUNCTIONS ---
# ... (create_game_lobby, join_game_action, etc. unchanged)


# --- SHOP FUNCTIONS ---
# ... (handle_purchase unchanged)


# --- MISSION FUNCTIONS ---
# ... (show_missions_menu, start_target_practice, etc. unchanged)


# --- TOURNAMENT FUNCTIONS ---
async def create_new_tournament(query, context):
    await query.answer("Tournament creation coming soon!", show_alert=True)

async def list_tournaments(query, context):
    tournaments = tournament_system.tournaments
    text = "🏆 <b>Available Tournaments</b> 🏆\n\n"
    buttons = []
    reg_open = False
    for t_id, t_data in tournaments.items():
        if t_data['status'] == 'registration':
            text += f"• <b>{t_data['name']}</b> ({len(t_data['participants'])}/{t_data['max_players']}) - Fee: {t_data['entry_fee']} coins\n"
            buttons.append([InlineKeyboardButton(f"View: {t_data['name']}", callback_data=f"tourn_view_{t_id}")])
            reg_open = True
    if not reg_open:
        text += "No tournaments currently open for registration."
    buttons.append([InlineKeyboardButton("🔙 Back", callback_data='menu_tournament')])
    await safe_edit_message(query, text, InlineKeyboardMarkup(buttons))


async def show_tournament_details(query, context, tournament_id):
    tournament = tournament_system.get_tournament(tournament_id)
    if not tournament: await query.answer("Tournament not found!", show_alert=True); return
    text = tournament_system.format_tournament_info(tournament_id)
    buttons = []
    if tournament['status'] == 'registration':
         buttons.append([InlineKeyboardButton("✍️ Register", callback_data=f"tourn_register_{tournament_id}")])
    if tournament['status'] in ['in_progress', 'finished']:
         buttons.append([InlineKeyboardButton("📊 View Brackets", callback_data=f"tourn_brackets_{tournament_id}")])
    buttons.append([InlineKeyboardButton("🔙 Back to List", callback_data='tourn_list')])
    await safe_edit_message(query, text, InlineKeyboardMarkup(buttons))

async def register_for_tournament(query, context, tournament_id):
    user_id = query.from_user.id
    username = query.from_user.username or query.from_user.first_name
    success, message = tournament_system.register_player(tournament_id, user_id, username)
    await query.answer(message, show_alert=True)
    if success: await list_tournaments(query, context) # Refresh list

async def start_tournament_handler(query, context, tournament_id):
     success, message = tournament_system.start_tournament(tournament_id)
     await query.answer(message, show_alert=True)
     if success: await show_tournament_details(query, context, tournament_id)

async def show_tournament_brackets(query, context, tournament_id):
    """Handles the callback to show tournament brackets"""
    text = tournament_system.format_tournament_brackets(tournament_id)
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Details", callback_data=f"tourn_view_{tournament_id}")]])
    await safe_edit_message(query, text, keyboard)


# --- TRADE FUNCTIONS ---
async def start_create_trade(query, context):
    """Starts the multi-step trade creation process"""
    context.user_data['state'] = 'awaiting_trade_partner'
    context.user_data['trade_setup'] = {'sender_id': query.from_user.id}
    await safe_edit_message(query, "Who do you want to trade with? Reply with their exact @username.",
                           InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data='menu_trade')]]))

async def handle_trade_partner_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles username input for trade partner"""
    # ... (code unchanged) ...
    pass

async def handle_trade_offer_coins_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles offer coins input"""
    # ... (code unchanged) ...
    pass

async def list_active_trades(query, context):
    # TODO: Implement listing trades
    await query.answer("Viewing active trades coming soon!", show_alert=True)

async def accept_trade_offer(query, context, trade_id):
    # ... (code unchanged) ...
    pass

async def cancel_trade_offer(query, context, trade_id):
    # ... (code unchanged) ...
    pass


# --- ADMIN AND ERROR HANDLERS ---
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors"""
    logger.error(f"Update {update} caused error {context.error}", exc_info=context.error)
    try:
        if update and update.effective_message:
            await update.effective_message.reply_text(
                "⚠️ <b>An error occurred!</b>\n\nPlease try again or contact support.", parse_mode='HTML'
            )
        elif update and update.callback_query:
            # Avoid editing if the original message caused the error
            if isinstance(context.error, BadRequest) and "message is not modified" in str(context.error).lower():
                 await update.callback_query.answer() # Ignore harmless error
            else:
                 await update.callback_query.answer("⚠️ An error occurred! Please try again.", show_alert=True)
    except Exception as e:
        logger.error(f"Failed to even send error message: {e}")


async def get_logs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin command to get log file"""
    # ... (code unchanged) ...
    pass

async def get_bot_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin command to get bot stats"""
    # ... (code unchanged) ...
    pass

# ... (broadcast_message if you have it) ...


def main():
    """Start the bot"""
    application = Application.builder().token(BOT_TOKEN).build()

    # Command Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("play", play_command))
    application.add_handler(CommandHandler("shop", shop_command))
    application.add_handler(CommandHandler("profile", profile_command_handler))
    application.add_handler(CommandHandler("leaderboard", leaderboard_command_handler))
    application.add_handler(CommandHandler("daily", daily_command_handler))
    # --- FIX: Use correct function name for /help ---
    application.add_handler(CommandHandler("help", help_command_handler))
    # ---------------------------------------------
    application.add_handler(CommandHandler("tournament", tournament_command))
    application.add_handler(CommandHandler("trade", trade_command))

    # Admin Commands
    application.add_handler(CommandHandler("logs", get_logs))
    application.add_handler(CommandHandler("botstats", get_bot_stats))
    # application.add_handler(CommandHandler("broadcast", broadcast_message))

    # Callback Handler
    application.add_handler(CallbackQueryHandler(handle_callback_query))

    # Message Handler
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Error Handler
    application.add_error_handler(error_handler)

    logger.info("🎭 Mafia RPG Bot is starting (Inline Mode)...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
