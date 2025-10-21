"""
Mafia RPG Telegram Bot - Main Entry Point
Complete implementation with INLINE keyboards
"""

import logging
import asyncio
import random
import os
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove, InputFile
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
# --- Import Tournament & Trading Systems ---
from enhanced_features import tournament_system, trading_system
# ----------------------------------------
from config import BOT_TOKEN, FEATURES, SHOP_ITEMS, ADMIN_IDS, MISSION_REWARDS, ANIMATION_SEQUENCES, BOT_USERNAME, MAFIA_PIC_URL
from utils import (
    create_main_menu_keyboard, create_play_menu_keyboard,
    format_player_stats, format_leaderboard_entry,
    send_animated_message, send_role_reveal_animation,
    create_shop_keyboard, create_lobby_keyboard,
    create_missions_menu_keyboard, get_role_emoji,
    # --- Import New Keyboards ---
    create_tournament_menu_keyboard, create_trade_menu_keyboard
    # ---------------------------
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
            # --- Add Econ Features to Welcome ---
            "⚔️ <b>Compete:</b> Join Tournaments for glory & prizes.\n"
            "📈 <b>Trade:</b> Exchange items and coins with others.\n\n"
            # -----------------------------------
            "Think you're ready? Show me."
        )
        keyboard = create_main_menu_keyboard(is_private=True)
        try:
            await context.bot.send_photo(
                chat_id=chat.id, photo=MAFIA_PIC_URL, caption=welcome_text,
                parse_mode='HTML', reply_markup=keyboard
            )
        except Exception as e:
            logger.error(f"Failed to send start photo: {e}. Sending text fallback.")
            await context.bot.send_message(
                chat_id=chat.id, text=welcome_text, parse_mode='HTML', reply_markup=keyboard
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
    text = (f"🏪 <b>SHOP</b> 🏪\n\n💰 Your Coins: <b>{player['coins']}</b>\n\n"
            "Select an item to purchase:")
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
    if not top_players: text += "No players yet! Be the first!"
    else:
        for i, player in enumerate(top_players, 1): text += format_leaderboard_entry(i, player) + "\n"
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

# --- NEW Tournament Command ---
async def tournament_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Shows the Tournament menu via /tournament command"""
    if not FEATURES['tournaments_enabled']:
         await update.message.reply_text("Tournaments are currently disabled.")
         return
    text = "🏆 <b>TOURNAMENTS</b> 🏆\n\nCompete for glory and coins!"
    keyboard = create_tournament_menu_keyboard()
    await update.message.reply_text(text, parse_mode='HTML', reply_markup=keyboard)

# --- NEW Trade Command ---
async def trade_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Shows the Trade menu via /trade command"""
    if not FEATURES['trading_enabled']:
         await update.message.reply_text("Trading is currently disabled.")
         return
    text = "📈 <b>TRADING POST</b> 📈\n\nExchange items and coins with other players."
    keyboard = create_trade_menu_keyboard()
    await update.message.reply_text(text, parse_mode='HTML', reply_markup=keyboard)

# --- Message Handler (for game actions) ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages (now only for in-game actions & trade setup)"""
    text = update.message.text
    user_id = update.effective_user.id
    username = update.effective_user.username or update.effective_user.first_name
    
    player_manager.register_player(user_id, username) # Ensure player exists
    
    # Check if waiting for trade input
    if context.user_data.get('state') == 'awaiting_trade_partner':
        await handle_trade_partner_input(update, context)
        return
    if context.user_data.get('state') == 'awaiting_trade_offer_coins':
        await handle_trade_offer_coins_input(update, context)
        return
    # Add similar handlers for offer_items, request_coins, request_items...

    # In-game actions
    if any(emoji in text for emoji in ['🔪', '🔍', '💉']):
        await game_manager.handle_action(update, context)
        return
    elif '🗳️' in text or 'Vote:' in text or '⏭️' in text:
        await game_manager.handle_vote(update, context)
        return
    
    # Fallback
    if update.effective_chat.type == 'private':
         await update.message.reply_text("Please use the commands like /start, /play, or the buttons.")


# --- Callback Query Handler (for ALL inline buttons) ---
async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all inline button presses"""
    query = update.callback_query
    await query.answer()
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
    elif data == 'menu_help': await show_help(query, context)
    # --- NEW Econ Menu Callbacks ---
    elif data == 'menu_tournament': await show_tournament_menu(query, context)
    elif data == 'menu_trade': await show_trade_menu(query, context)
    # -----------------------------

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
        
    # --- NEW Tournament Actions ---
    elif data == 'tourn_create': await create_new_tournament(query, context) # Placeholder
    elif data == 'tourn_list': await list_tournaments(query, context) # Placeholder
    elif data.startswith('tourn_view_'): await show_tournament_details(query, context, data.split('_')[-1]) # Placeholder
    elif data.startswith('tourn_register_'): await register_for_tournament(query, context, data.split('_')[-1]) # Placeholder
    elif data.startswith('tourn_start_'): await start_tournament_handler(query, context, data.split('_')[-1]) # Placeholder
        
    # --- NEW Trade Actions ---
    elif data == 'trade_create': await start_create_trade(query, context) # Start the multi-step process
    elif data == 'trade_list': await list_active_trades(query, context) # Placeholder
    elif data.startswith('trade_accept_'): await accept_trade_offer(query, context, data.split('_')[-1]) # Placeholder
    elif data.startswith('trade_cancel_'): await cancel_trade_offer(query, context, data.split('_')[-1]) # Placeholder


# --- MENU DISPLAY FUNCTIONS ---

async def show_main_menu_callback(query, context):
    """Shows the main menu via callback"""
    user = query.from_user
    welcome_text = (
        f"🚬 <b>Welcome back, {user.first_name}.</b>\n\n"
        "What's the move?"
    )
    keyboard = create_main_menu_keyboard(is_private=True)
    try:
        await query.edit_message_caption(caption=welcome_text, parse_mode='HTML', reply_markup=keyboard)
    except Exception:
        try:
            await query.edit_message_text(welcome_text, parse_mode='HTML', reply_markup=keyboard)
        except Exception as e:
            logger.warning(f"Failed to edit message in show_main_menu_callback: {e}")
            await query.message.reply_text(welcome_text, parse_mode='HTML', reply_markup=keyboard)

async def show_play_menu(query, context):
    """Show game mode selection menu"""
    text = "🎮 <b>SELECT GAME MODE</b> 🎮\n\nChoose your poison:"
    keyboard = create_play_menu_keyboard()
    await query.edit_message_text(text, parse_mode='HTML', reply_markup=keyboard)

async def show_profile(query, context):
    """Show player profile via callback"""
    user_id = query.from_user.id
    player_data = player_manager.get_player(user_id)
    if not player_data:
        await query.edit_message_text("❌ Profile not found! Use /start first.")
        return
    profile_text = format_player_stats(player_data)
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Menu", callback_data='menu_main')]])
    try:
        await query.edit_message_text(profile_text, parse_mode='HTML', reply_markup=keyboard)
    except Exception:
        await query.message.reply_photo(photo=MAFIA_PIC_URL, caption=profile_text, parse_mode='HTML', reply_markup=keyboard)
        await query.delete_message()

async def show_leaderboard(query, context):
    """Show top players via callback"""
    top_players = player_manager.get_leaderboard(10)
    text = "🏆 <b>TOP PLAYERS</b> 🏆\n\n"
    if not top_players: text += "No players yet! Be the first!"
    else:
        for i, player in enumerate(top_players, 1): text += format_leaderboard_entry(i, player) + "\n"
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Menu", callback_data='menu_main')]])
    await query.edit_message_text(text, parse_mode='HTML', reply_markup=keyboard)

async def claim_daily_reward(query, context):
    """Claim daily reward via callback"""
    user_id = query.from_user.id
    success, reward = player_manager.claim_daily_reward(user_id)
    if success:
        text = (f"🎉 <b>DAILY REWARD CLAIMED!</b> 🎉\n\n"
                f"You received:\n💎 {reward['xp']} XP\n🪙 {reward['coins']} Coins\n"
                f"🔥 Streak: {reward['streak']} days\n\nCome back tomorrow!")
    else:
        text = ("⏰ <b>Already Claimed!</b>\n\nYou've already claimed your daily reward.\n"
                "Come back tomorrow for more goodies!")
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Menu", callback_data='menu_main')]])
    await query.edit_message_text(text, parse_mode='HTML', reply_markup=keyboard)

async def show_shop(query, context):
    """Show shop items via callback"""
    user_id = query.from_user.id
    player = player_manager.get_player(user_id)
    text = (f"🏪 <b>SHOP</b> 🏪\n\n💰 Your Coins: <b>{player['coins']}</b>\n\n"
            "Select an item to purchase:")
    keyboard = create_shop_keyboard(player['items'])
    await query.edit_message_text(text, parse_mode='HTML', reply_markup=keyboard)

async def show_help(query, context):
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
        "/tournament - Tournament menu\n" # Added
        "/trade - Trade menu\n" # Added
        "/logs - (Admin) Get bot logs\n"
        "/botstats - (Admin) Get bot stats"
    )
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Menu", callback_data='menu_main')]])
    await query.edit_message_text(text, parse_mode='HTML', reply_markup=keyboard)
    
# --- NEW Tournament Menu ---
async def show_tournament_menu(query, context):
    """Displays the main tournament menu."""
    if not FEATURES['tournaments_enabled']: return await query.answer("Tournaments are disabled.", show_alert=True)
    text = "🏆 <b>TOURNAMENTS</b> 🏆\n\nCompete for glory and coins!"
    keyboard = create_tournament_menu_keyboard()
    await query.edit_message_text(text, parse_mode='HTML', reply_markup=keyboard)

# --- NEW Trade Menu ---
async def show_trade_menu(query, context):
    """Displays the main trade menu."""
    if not FEATURES['trading_enabled']: return await query.answer("Trading is disabled.", show_alert=True)
    text = "📈 <b>TRADING POST</b> 📈\n\nExchange items and coins with other players."
    keyboard = create_trade_menu_keyboard()
    await query.edit_message_text(text, parse_mode='HTML', reply_markup=keyboard)

# --- LOBBY/GAME FUNCTIONS --- (Mostly unchanged, ensure edit_message works)

async def create_game_lobby(query, context, mode: str):
    """Create a new game lobby via callback"""
    user_id = query.from_user.id
    chat_id = query.message.chat_id
    game_id = game_manager.create_game(mode, user_id, chat_id)
    context.chat_data['active_game'] = game_id
    game = game_manager.get_game(game_id)
    required = game_manager.get_required_players(mode)
    text = (f"🎮 <b>GAME LOBBY CREATED</b> 🎮\n\n🆔 Game ID: <code>{game_id}</code>\n"
            f"🎯 Mode: <b>{mode.upper()}</b>\n👥 Players: {len(game['players'])}/{required}\n"
            f"👑 Creator: {query.from_user.username or query.from_user.first_name}\n\n"
            f"<b>Waiting for players...</b>")
    keyboard = create_lobby_keyboard(game_id, is_creator=True)
    await query.edit_message_text(text, parse_mode='HTML', reply_markup=keyboard)

async def join_game_action(query, context, game_id: str, user_id: int, username: str):
    """Join an existing game via callback"""
    success, message = game_manager.join_game(game_id, user_id, username)
    if success:
        await query.answer("✅ You joined the game!")
        game = game_manager.get_game(game_id)
        required = game_manager.get_required_players(game['mode'])
        text = (f"🎮 <b>GAME LOBBY</b> 🎮\n\n🆔 Game ID: <code>{game_id}</code>\n"
                f"🎯 Mode: <b>{game['mode'].upper()}</b>\n👥 Players: {len(game['players'])}/{required}\n\n"
                "<b>Players in lobby:</b>\n")
        for i, player in enumerate(game['players'], 1):
            crown = "👑" if player['user_id'] == game['creator_id'] else "•"
            text += f"{crown} {player['username']}\n"
        if len(game['players']) >= required: text += "\n🎉 <b>Lobby is full! Ready to start!</b>"
        is_creator = user_id == game['creator_id']
        keyboard = create_lobby_keyboard(game_id, is_creator=is_creator)
        await query.edit_message_text(text, parse_mode='HTML', reply_markup=keyboard)
    else:
        await query.answer(f"❌ {message}", show_alert=True)

async def start_game_action(query, context, game_id: str, user_id: int):
    """Start the game via callback"""
    success, message = game_manager.start_game(game_id, user_id)
    if not success: return await query.answer(f"❌ {message}", show_alert=True)
    
    await query.answer("🚀 Game starting!")
    game = game_manager.get_game(game_id)
    await send_animated_message(query.message, ANIMATION_SEQUENCES['game_start'], delay=1.5)
    
    for player in game['players']:
        role_desc = game_manager.get_role_description(player['role'])
        await send_role_reveal_animation(context, player['user_id'], player['role'], role_desc)
    
    await query.edit_message_text("🎮 <b>Game Started!</b>\n\nCheck PMs for your role!", parse_mode='HTML', reply_markup=None)
    await asyncio.sleep(2)
    await game_manager.start_round(game_id, query.message, context)

async def cancel_game_action(query, context, game_id: str, user_id: int):
    """Cancel a game via callback"""
    success, message = game_manager.cancel_game(game_id, user_id)
    if success:
        await query.answer("✅ Game cancelled!")
        await show_main_menu_callback(query, context)
    else:
        await query.answer(f"❌ {message}", show_alert=True)

# --- SHOP FUNCTIONS --- (handle_purchase exists)

# --- MISSION FUNCTIONS --- (Rewritten above)
# ... (start_target_practice, handle_target_practice, etc.) ...

# --- NEW PLACEHOLDER TOURNAMENT FUNCTIONS ---

async def create_new_tournament(query, context):
    # TODO: Implement multi-step process to ask for name, mode, size, fee, prize
    await query.answer("Tournament creation coming soon!", show_alert=True)

async def list_tournaments(query, context):
    # TODO: Fetch tournaments from tournament_system and display with buttons
    tournaments = tournament_system.tournaments # Get active tournaments
    text = "🏆 <b>Available Tournaments</b> 🏆\n\n"
    buttons = []
    if not tournaments or all(t['status'] != 'registration' for t in tournaments.values()):
        text += "No tournaments currently open for registration."
    else:
         for t_id, t_data in tournaments.items():
             if t_data['status'] == 'registration':
                 text += f"• <b>{t_data['name']}</b> ({len(t_data['participants'])}/{t_data['max_players']}) - Fee: {t_data['entry_fee']} coins\n"
                 buttons.append([InlineKeyboardButton(f"View: {t_data['name']}", callback_data=f"tourn_view_{t_id}")])
                 
    buttons.append([InlineKeyboardButton("🔙 Back", callback_data='menu_tournament')])
    await query.edit_message_text(text, parse_mode='HTML', reply_markup=InlineKeyboardMarkup(buttons))


async def show_tournament_details(query, context, tournament_id):
    # TODO: Fetch details using tournament_system.format_tournament_info
    tournament = tournament_system.get_tournament(tournament_id)
    if not tournament:
        return await query.answer("Tournament not found!", show_alert=True)
        
    text = tournament_system.format_tournament_info(tournament_id)
    buttons = []
    if tournament['status'] == 'registration':
         buttons.append([InlineKeyboardButton("✍️ Register", callback_data=f"tourn_register_{tournament_id}")])
    # Add view brackets button if started
    if tournament['status'] in ['in_progress', 'finished']:
         buttons.append([InlineKeyboardButton("📊 View Brackets", callback_data=f"tourn_brackets_{tournament_id}")]) # Need handler for this
         
    buttons.append([InlineKeyboardButton("🔙 Back to List", callback_data='tourn_list')])
    await query.edit_message_text(text, parse_mode='HTML', reply_markup=InlineKeyboardMarkup(buttons))

async def register_for_tournament(query, context, tournament_id):
    user_id = query.from_user.id
    username = query.from_user.username or query.from_user.first_name
    success, message = tournament_system.register_player(tournament_id, user_id, username)
    await query.answer(message, show_alert=True)
    if success:
        await list_tournaments(query, context) # Refresh list

async def start_tournament_handler(query, context, tournament_id):
     # TODO: Check if user is creator? Or allow any admin?
     success, message = tournament_system.start_tournament(tournament_id)
     await query.answer(message, show_alert=True)
     if success:
          await show_tournament_details(query, context, tournament_id) # Refresh details


# --- NEW PLACEHOLDER TRADE FUNCTIONS ---

async def start_create_trade(query, context):
    """Starts the multi-step trade creation process"""
    context.user_data['state'] = 'awaiting_trade_partner'
    context.user_data['trade_setup'] = {'sender_id': query.from_user.id}
    await query.edit_message_text(
        "Who do you want to trade with? Please enter their exact @username.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data='menu_trade')]])
    )

async def handle_trade_partner_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles username input for trade partner"""
    partner_username = update.message.text.strip().lstrip('@')
    partner = player_manager.get_player_by_username(partner_username)
    
    if not partner:
        await update.message.reply_text("❌ Player not found. Please check the username and try again, or /cancel.")
        return
        
    if partner['user_id'] == context.user_data['trade_setup']['sender_id']:
         await update.message.reply_text("❌ You cannot trade with yourself. Enter a different username or /cancel.")
         return

    context.user_data['trade_setup']['receiver_id'] = partner['user_id']
    context.user_data['trade_setup']['receiver_username'] = partner['username']
    context.user_data['state'] = 'awaiting_trade_offer_coins'
    await update.message.reply_text(f"Trading with {partner['username']}.\nHow many coins do you want to OFFER? (Enter 0 if none)")

async def handle_trade_offer_coins_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles offer coins input"""
    try:
        coins = int(update.message.text.strip())
        if coins < 0: raise ValueError("Coins cannot be negative.")
        
        sender = player_manager.get_player(context.user_data['trade_setup']['sender_id'])
        if sender['coins'] < coins:
             await update.message.reply_text(f"❌ You only have {sender['coins']} coins. Enter a lower amount or 0.")
             return

        context.user_data['trade_setup']['offer_coins'] = coins
        context.user_data['state'] = 'awaiting_trade_offer_items' # Next step
        # TODO: Ask for offer items (e.g., "Enter item IDs separated by comma, or 'none'")
        await update.message.reply_text(f"Offering {coins} coins.\nNow, what items do you OFFER? (Enter 'none' or item IDs like 'skin_golden,emote_pack_1')")

    except ValueError:
         await update.message.reply_text("❌ Invalid number. Please enter a positive whole number for coins (or 0).")
         
# TODO: Implement handlers for offer_items, request_coins, request_items, and final confirmation


async def list_active_trades(query, context):
    # TODO: Fetch trades involving the user from trading_system and display
    await query.answer("Viewing active trades coming soon!", show_alert=True)

async def accept_trade_offer(query, context, trade_id):
    user_id = query.from_user.id
    success, message = trading_system.accept_trade(trade_id, user_id)
    await query.answer(message, show_alert=True)
    if success:
        # TODO: Refresh the trade list or show confirmation
        await show_trade_menu(query, context) # Go back to trade menu

async def cancel_trade_offer(query, context, trade_id):
    user_id = query.from_user.id
    success, message = trading_system.cancel_trade(trade_id, user_id)
    await query.answer(message, show_alert=True)
    if success:
        # TODO: Refresh the trade list
        await show_trade_menu(query, context) # Go back to trade menu


# --- ADMIN AND ERROR HANDLERS ---

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors"""
    logger.error(f"Update {update} caused error {context.error}", exc_info=context.error)
    try:
        if update and update.effective_message:
            await update.effective_message.reply_text(
                "⚠️ <b>An error occurred!</b>\n\nPlease try again or contact support.", parse_mode='HTML'
            )
        elif update and update.callback_query:
            await update.callback_query.answer("⚠️ An error occurred! Please try again.", show_alert=True)
            # Avoid editing message here as it might be the source of the error
    except Exception as e:
        logger.error(f"Failed to send error message: {e}")

async def get_logs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin command to get log file"""
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS: return await update.message.reply_text("❌ Unauthorized.")
    log_file = 'nohup.out'
    if os.path.exists(log_file):
        try:
            await context.bot.send_document(chat_id=user_id, document=InputFile(log_file), filename='bot_logs.txt')
        except Exception as e: await update.message.reply_text(f"❌ Failed to send logs: {e}")
    else: await update.message.reply_text("❌ `nohup.out` file not found.")

async def get_bot_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin command to get bot stats"""
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS: return await update.message.reply_text("❌ Unauthorized.")
    total_users = len(player_manager.players)
    active_games = len(game_manager.games) # Note: Includes lobbies
    text = (f"📊 <b>BOT STATISTICS</b> 📊\n\n"
            f"👥 <b>Total Users:</b> {total_users}\n"
            f"🎮 <b>Active Lobbies/Games:</b> {active_games}")
    await update.message.reply_text(text, parse_mode='HTML')

async def broadcast_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin command to broadcast messages"""
    # ... (code as provided) ...
    pass

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
    application.add_handler(CommandHandler("help", help_command))
    # --- NEW Econ Commands ---
    application.add_handler(CommandHandler("tournament", tournament_command))
    application.add_handler(CommandHandler("trade", trade_command))
    # -----------------------
    
    # Admin Commands
    application.add_handler(CommandHandler("logs", get_logs))
    application.add_handler(CommandHandler("botstats", get_bot_stats))
    application.add_handler(CommandHandler("broadcast", broadcast_message))
    
    # Callback Handler (for ALL inline buttons)
    application.add_handler(CallbackQueryHandler(handle_callback_query))

    # Message Handler (for game actions & trade setup)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Error Handler
    application.add_error_handler(error_handler)
    
    logger.info("🎭 Mafia RPG Bot is starting (Inline Mode)...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
