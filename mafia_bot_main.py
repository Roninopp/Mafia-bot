"""
Mafia RPG Telegram Bot - Main Entry Point
Complete implementation with INLINE keyboards
"""

import logging
import asyncio
import random
import os # Added for /logs command
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
from config import BOT_TOKEN, FEATURES, SHOP_ITEMS, ADMIN_IDS, MISSION_REWARDS, ANIMATION_SEQUENCES, BOT_USERNAME, MAFIA_PIC_URL
from utils import (
    create_main_menu_keyboard, create_play_menu_keyboard,
    format_player_stats, format_leaderboard_entry,
    send_animated_message, send_role_reveal_animation,
    create_shop_keyboard, create_lobby_keyboard,
    create_missions_menu_keyboard, get_role_emoji
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
    
    # Register player
    player_manager.register_player(user.id, user.username or user.first_name)
    
    # --- FIX 3: New Start Message ---
    if chat.type == 'private':
        # Send a private welcome with picture and "Create Gang" button
        welcome_text = (
            f"🚬 <b>Welcome to the family, {user.first_name}.</b>\n\n"
            "This city is run by gangs, wits, and bullets. "
            "You look like you've got what it takes to rise to the top.\n\n"
            "👥 <b>Join Games:</b> Fight in 5v5 and 1v1 battles.\n"
            "🚀 <b>Run Missions:</b> Take on solo challenges for cash.\n"
            "🏆 <b>Build Your Rep:</b> Level up, earn coins, and buy gear.\n\n"
            "Think you're ready? Show me."
        )
        
        # Add "Let's Create Gang" button
        keyboard = create_main_menu_keyboard(is_private=True)
        
        try:
            await context.bot.send_photo(
                chat_id=chat.id,
                photo=MAFIA_PIC_URL,
                caption=welcome_text,
                parse_mode='HTML',
                reply_markup=keyboard
            )
        except Exception as e:
            logger.error(f"Failed to send start photo: {e}. Sending text fallback.")
            # Fallback if photo fails
            await context.bot.send_message(
                chat_id=chat.id,
                text=welcome_text,
                parse_mode='HTML',
                reply_markup=keyboard
            )
    else:
        # Send a simple group welcome
        welcome_text = (
            f"🎭 <b>MAFIA RPG</b> 🎭\n\n"
            f"🔥 <b>Welcome, {user.first_name}!</b> 🔥\n\n"
            "I'm ready to manage your games. Use /play to start a lobby!"
        )
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🎮 Play Game (in PM)", url=f"https://t.me/{BOT_USERNAME}?start=play")]
        ])
        await update.message.reply_text(
            welcome_text,
            parse_mode='HTML',
            reply_markup=keyboard
        )

# --- FIX 2: NEW COMMAND HANDLERS ---

async def play_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Shows the Play menu via /play command"""
    text = (
        "🎮 <b>SELECT GAME MODE</b> 🎮\n\n"
        "Choose your poison:"
    )
    keyboard = create_play_menu_keyboard()
    await update.message.reply_text(text, parse_mode='HTML', reply_markup=keyboard)

async def shop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Shows the Shop menu via /shop command"""
    user_id = update.effective_user.id
    player = player_manager.get_player(user_id)
    if not player:
        await update.message.reply_text("Please /start the bot first to create your profile.")
        return
        
    text = (
        f"🏪 <b>SHOP</b> 🏪\n\n"
        f"💰 Your Coins: <b>{player['coins']}</b>\n\n"
        "Select an item to purchase:"
    )
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
            text += format_leaderboard_entry(i, player)
            text += "\n"
    await update.message.reply_text(text, parse_mode='HTML')

async def daily_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Claims daily reward via /daily command"""
    user_id = update.effective_user.id
    success, reward = player_manager.claim_daily_reward(user_id)
    
    if success:
        text = (
            f"🎉 <b>DAILY REWARD CLAIMED!</b> 🎉\n\n"
            f"You received:\n"
            f"💎 {reward['xp']} XP\n"
            f"🪙 {reward['coins']} Coins\n"
            f"🔥 Streak: {reward['streak']} days\n\n"
            f"Come back tomorrow for more!"
        )
    else:
        text = (
            "⏰ <b>Already Claimed!</b>\n\n"
            "You've already claimed your daily reward.\n"
            "Come back tomorrow for more goodies!"
        )
    await update.message.reply_text(text, parse_mode='HTML')

# ---------------------------------

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages (now only for in-game actions)"""
    text = update.message.text
    user_id = update.effective_user.id
    username = update.effective_user.username or update.effective_user.first_name
    
    # Register player if not exists
    player_manager.register_player(user_id, username)
    
    # In-game actions
    if any(emoji in text for emoji in ['🔪', '🔍', '💉']):
        await game_manager.handle_action(update, context)
    
    elif '🗳️' in text or 'Vote:' in text or '⏭️' in text:
        await game_manager.handle_vote(update, context)
    
    # Fallback for users who type commands instead of using buttons
    elif update.effective_chat.type == 'private':
         await update.message.reply_text("Please use the commands like /start, /play, or /shop.")


async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all inline button presses"""
    query = update.callback_query
    await query.answer() # Acknowledge the button press
    
    data = query.data
    user_id = query.from_user.id
    username = query.from_user.username or query.from_user.first_name
    
    # Clear mission state if not a mission action
    if not data.startswith(('mission_', 'shoot_', 'case_', 'dilemma_', 'disarm_', 'heist_')):
        if 'mission_state' in context.user_data:
            del context.user_data['mission_state']

    # Main Menu Navigation
    if data == 'menu_main':
        await show_main_menu_callback(query, context)
    elif data == 'menu_play':
        await show_play_menu(query, context)
    elif data == 'menu_profile':
        await show_profile(query, context)
    elif data == 'menu_leaderboard':
        await show_leaderboard(query, context)
    elif data == 'menu_daily':
        await claim_daily_reward(query, context)
    elif data == 'menu_shop':
        await show_shop(query, context)
    elif data == 'menu_help':
        await show_help(query, context)

    # Game Mode Selection
    elif data == 'mode_5v5':
        await create_game_lobby(query, context, '5v5')
    elif data == 'mode_1v1':
        await create_game_lobby(query, context, '1v1')
    elif data == 'menu_missions':
        await show_missions_menu(query, context)

    # Lobby Actions
    elif data.startswith('join_game_'):
        game_id = data.split('_')[-1]
        await join_game_action(query, context, game_id, user_id, username)
    elif data.startswith('start_game_'):
        game_id = data.split('_')[-1]
        await start_game_action(query, context, game_id, user_id)
    elif data.startswith('cancel_game_'):
        game_id = data.split('_')[-1]
        await cancel_game_action(query, context, game_id, user_id)

    # Shop Actions
    elif data.startswith('buy_item_'):
        item_id = data.split('_')[-1]
        await handle_purchase(query, context, item_id, user_id)

    # --- FIX 1: New Mission Handlers ---
    elif data == 'mission_target_practice':
        await start_target_practice(query, context)
    elif data.startswith('shoot_'):
        await handle_target_practice(query, context, data)
        
    elif data == 'mission_detectives_case':
        await start_detectives_case(query, context)
    elif data.startswith('case_'):
        await handle_detectives_case(query, context, data)

    elif data == 'mission_doctors_dilemma':
        await start_doctors_dilemma(query, context)
    elif data.startswith('dilemma_'):
        await handle_doctors_dilemma(query, context, data)
        
    elif data == 'mission_timed_disarm':
        await start_timed_disarm(query, context)
    elif data.startswith('disarm_click_'):
        await handle_timed_disarm(query, context, data)
        
    elif data == 'mission_mafia_heist':
        await start_mafia_heist(query, context)
    elif data.startswith('heist_'):
        await handle_mafia_heist(query, context, data)
    # ---------------------------------
        

async def show_main_menu_callback(query, context):
    """Shows the main menu (used for 'Back' buttons)"""
    user = query.from_user
    text = (
        f"🚬 <b>Welcome to the family, {user.first_name}.</b>\n\n"
        "This city is run by gangs, wits, and bullets. "
        "You look like you've got what it takes to rise to the top.\n\n"
        "👥 <b>Join Games:</b> Fight in 5v5 and 1v1 battles.\n"
        "🚀 <b>Run Missions:</b> Take on solo challenges for cash.\n"
        "🏆 <b>Build Your Rep:</b> Level up, earn coins, and buy gear.\n\n"
        "Think you're ready? Show me."
    )
    keyboard = create_main_menu_keyboard(is_private=True)
    try:
        # Try to edit the caption if it's a photo
        await query.edit_message_caption(caption=text, parse_mode='HTML', reply_markup=keyboard)
    except Exception: 
        # Fallback if it's a text message
        try:
            await query.edit_message_text(text, parse_mode='HTML', reply_markup=keyboard)
        except Exception as e:
            logger.warning(f"Failed to edit message in show_main_menu_callback: {e}")
            # As a last resort, send a new message
            await query.message.reply_text(text, parse_mode='HTML', reply_markup=keyboard)


async def show_play_menu(query, context):
    """Show game mode selection"""
    text = (
        "🎮 <b>SELECT GAME MODE</b> 🎮\n\n"
        "Choose your poison:"
    )
    keyboard = create_play_menu_keyboard()
    await query.edit_message_text(text, parse_mode='HTML', reply_markup=keyboard)


async def show_profile(query, context):
    """Show player profile"""
    user_id = query.from_user.id
    player_data = player_manager.get_player(user_id)
    
    if not player_data:
        await query.edit_message_text("❌ Profile not found! Use /start first.")
        return
    
    profile_text = format_player_stats(player_data)
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Menu", callback_data='menu_main')]])
    
    try:
        await query.edit_message_text(profile_text, parse_mode='HTML', reply_markup=keyboard)
    except Exception: # Can't edit a photo caption to text
        await query.message.reply_photo(
            photo=MAFIA_PIC_URL,
            caption=profile_text,
            parse_mode='HTML',
            reply_markup=keyboard
        )
        await query.delete_message()


async def show_leaderboard(query, context):
    """Show top players"""
    top_players = player_manager.get_leaderboard(10)
    text = "🏆 <b>TOP PLAYERS</b> 🏆\n\n"
    if not top_players:
        text += "No players yet! Be the first!"
    else:
        for i, player in enumerate(top_players, 1):
            text += format_leaderboard_entry(i, player)
            text += "\n"
    
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Menu", callback_data='menu_main')]])
    await query.edit_message_text(text, parse_mode='HTML', reply_markup=keyboard)


async def claim_daily_reward(query, context):
    """Claim daily reward"""
    user_id = query.from_user.id
    success, reward = player_manager.claim_daily_reward(user_id)
    
    if success:
        text = (
            f"🎉 <b>DAILY REWARD CLAIMED!</b> 🎉\n\n"
            f"You received:\n"
            f"💎 {reward['xp']} XP\n"
            f"🪙 {reward['coins']} Coins\n"
            f"🔥 Streak: {reward['streak']} days\n\n"
            f"Come back tomorrow for more!"
        )
    else:
        text = (
            "⏰ <b>Already Claimed!</b>\n\n"
            "You've already claimed your daily reward.\n"
            "Come back tomorrow for more goodies!"
        )
    
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Menu", callback_data='menu_main')]])
    await query.edit_message_text(text, parse_mode='HTML', reply_markup=keyboard)


async def show_shop(query, context):
    """Show shop items"""
    user_id = query.from_user.id
    player = player_manager.get_player(user_id)
    
    text = (
        f"🏪 <b>SHOP</b> 🏪\n\n"
        f"💰 Your Coins: <b>{player['coins']}</b>\n\n"
        "Select an item to purchase:"
    )
    
    keyboard = create_shop_keyboard(player['items'])
    await query.edit_message_text(text, parse_mode='HTML', reply_markup=keyboard)


async def handle_purchase(query, context, item_id, user_id):
    """Handle item purchase logic"""
    player = player_manager.get_player(user_id)
    item_to_buy = next((item for item in SHOP_ITEMS if item['id'] == item_id), None)
    
    if not item_to_buy:
        await query.answer("❌ Item not found!", show_alert=True)
        return
    
    if player_manager.has_item(user_id, item_to_buy['id']):
        await query.answer("✅ You already own this item!", show_alert=True)
        return
    
    if player['coins'] < item_to_buy['price']:
        await query.answer(f"❌ Not enough coins! You need {item_to_buy['price']} coins.", show_alert=True)
        return
    
    success = player_manager.spend_coins(user_id, item_to_buy['price'])
    if success:
        player_manager.add_item(user_id, item_to_buy)
        await query.answer(f"🎉 Purchase successful! You bought: {item_to_buy['name']}", show_alert=True)
        await show_shop(query, context)
    else:
        await query.answer("❌ Transaction failed!", show_alert=True)


async def show_help(query, context):
    """Show help information"""
    text = (
        "❓ <b>HOW TO PLAY</b> ❓\n\n"
        "<b>🎭 GAME BASICS:</b>\n"
        "• Players are assigned secret roles.\n"
        "• Mafia eliminates at night.\n"
        "• Villagers vote during the day.\n\n"
        "<b>⚔️ 5v5 CLASSIC:</b>\n"
        "• 3 Mafia vs 1 Detective, 1 Doctor, 5 Villagers.\n\n"
        "<b>🎯 1v1 DUEL:</b>\n"
        "• Quick match: Mafia vs Detective.\n\n"
        "<b>🚀 MISSIONS:</b>\n"
        "• Single-player mini-games to earn rewards.\n\n"
        "<b>⚡ COMMANDS:</b>\n"
        "/start - Main menu\n"
        "/play - Open game modes\n"
        "/shop - Open the item shop\n"
        "/profile - View your stats\n"
        "/leaderboard - See top players\n"
        "/daily - Claim your daily reward\n"
        "/logs - (Admin) Get bot logs\n"
        "/botstats - (Admin) Get bot stats"
    )
    
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Menu", callback_data='menu_main')]])
    await query.edit_message_text(text, parse_mode='HTML', reply_markup=keyboard)


async def create_game_lobby(query, context, mode: str):
    """Create a new game lobby"""
    user_id = query.from_user.id
    chat_id = query.message.chat_id
    
    game_id = game_manager.create_game(mode, user_id, chat_id)
    context.chat_data['active_game'] = game_id
    game = game_manager.get_game(game_id)
    required = game_manager.get_required_players(mode)
    
    text = (
        f"🎮 <b>GAME LOBBY CREATED</b> 🎮\n\n"
        f"🆔 Game ID: <code>{game_id}</code>\n"
        f"🎯 Mode: <b>{mode.upper()}</b>\n"
        f"👥 Players: {len(game['players'])}/{required}\n"
        f"👑 Creator: {query.from_user.username or query.from_user.first_name}\n\n"
        f"<b>Waiting for players...</b>"
    )
    
    keyboard = create_lobby_keyboard(game_id, is_creator=True)
    await query.edit_message_text(text, parse_mode='HTML', reply_markup=keyboard)


async def join_game_action(query, context, game_id: str, user_id: int, username: str):
    """Join an existing game"""
    success, message = game_manager.join_game(game_id, user_id, username)
    
    if success:
        await query.answer("✅ You joined the game!")
        game = game_manager.get_game(game_id)
        required = game_manager.get_required_players(game['mode'])
        
        text = (
            f"🎮 <b>GAME LOBBY</b> 🎮\n\n"
            f"🆔 Game ID: <code>{game_id}</code>\n"
            f"🎯 Mode: <b>{game['mode'].upper()}</b>\n"
            f"👥 Players: {len(game['players'])}/{required}\n\n"
            "<b>Players in lobby:</b>\n"
        )
        
        for i, player in enumerate(game['players'], 1):
            crown = "👑" if player['user_id'] == game['creator_id'] else "•"
            text += f"{crown} {player['username']}\n"
        
        if len(game['players']) >= required:
            text += "\n🎉 <b>Lobby is full! Ready to start!</b>"
        
        is_creator = user_id == game['creator_id']
        keyboard = create_lobby_keyboard(game_id, is_creator=is_creator)
        await query.edit_message_text(text, parse_mode='HTML', reply_markup=keyboard)
    else:
        await query.answer(f"❌ {message}", show_alert=True)


async def start_game_action(query, context, game_id: str, user_id: int):
    """Start the game"""
    success, message = game_manager.start_game(game_id, user_id)
    
    if not success:
        await query.answer(f"❌ {message}", show_alert=True)
        return
    
    await query.answer("🚀 Game starting!")
    game = game_manager.get_game(game_id)
    
    await send_animated_message(
        query.message,
        ANIMATION_SEQUENCES['game_start'],
        delay=1.5
    )
    
    for player in game['players']:
        role_desc = game_manager.get_role_description(player['role'])
        await send_role_reveal_animation(
            context,
            player['user_id'],
            player['role'],
            role_desc
        )
    
    await query.edit_message_text(
        "🎮 <b>Game Started!</b>\n\nCheck your private messages for your role!",
        parse_mode='HTML',
        reply_markup=None
    )
    
    await asyncio.sleep(2)
    await game_manager.start_round(game_id, query.message, context)


async def cancel_game_action(query, context, game_id: str, user_id: int):
    """Cancel a game"""
    success, message = game_manager.cancel_game(game_id, user_id)
    
    if success:
        await query.answer("✅ Game cancelled!")
        await show_main_menu_callback(query, context)
    else:
        await query.answer(f"❌ {message}", show_alert=True)

# --- FIX 1: REWRITTEN SINGLE PLAYER MISSIONS ---

async def show_missions_menu(query, context):
    """Display the 5 single-player missions"""
    text = (
        "🚀 <b>SINGLE-PLAYER MISSIONS</b> 🚀\n\n"
        "Choose a challenge to earn XP and Coins!\n\n"
        "1. <b>🎯 Target Practice</b>\n   Test your reaction speed.\n\n"
        "2. <b>🔍 Detective's Case</b>\n   Test your memory.\n\n"
        "3. <b>💉 Doctor's Dilemma</b>\n   Solve a logic puzzle.\n\n"
        "4. <b>💣 Timed Disarm</b>\n   Test your clicking speed.\n\n"
        "5. <b>💰 Mafia Heist</b>\n   A mini text-adventure."
    )
    keyboard = create_missions_menu_keyboard()
    await query.edit_message_text(text, parse_mode='HTML', reply_markup=keyboard)


async def start_target_practice(query, context):
    """Mission 1: Target Practice - Start"""
    context.user_data['mission_state'] = {'score': 0, 'round': 0}
    
    await query.edit_message_text("🎯 <b>Target Practice</b>\n\nGet ready...", parse_mode='HTML')
    await asyncio.sleep(2)
    await send_target_practice_round(query, context)

async def send_target_practice_round(query, context):
    """Mission 1: Send a new target"""
    state = context.user_data.get('mission_state', {'score': 0, 'round': 0})
    score = state['score']
    round_num = state['round']
    
    if round_num >= 7: # 7 rounds
        await end_target_practice(query, context)
        return

    target = random.choice(['👥 Villager', '👥 Villager', '🔪 Mafia', '💉 Doctor'])
    emoji = get_role_emoji(target.split(' ')[-1].lower())
    state['current_target'] = target.split(' ')[-1]
    state['round'] += 1
    
    text = f"<b>SCORE: {score}</b> | Round: {round_num + 1}/7\n\n{emoji} <b>{target}</b> {emoji}\n\nSHOOT?"
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("💥 SHOOT!", callback_data="shoot_Shoot"),
        InlineKeyboardButton(" HOLD FIRE ", callback_data="shoot_Hold")
    ]])
    
    await query.edit_message_text(text, parse_mode='HTML', reply_markup=keyboard)

async def handle_target_practice(query, context, data):
    """Mission 1: Process the player's shot"""
    if 'mission_state' not in context.user_data or 'current_target' not in context.user_data['mission_state']:
        await query.edit_message_text("Error: Mission expired. Please start again.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Missions", callback_data='menu_missions')]]))
        return

    state = context.user_data['mission_state']
    target = state['current_target']
    action = data.split('_')[-1]
    
    feedback = ""
    if action == 'Shoot':
        if target == 'Mafia':
            state['score'] += 100
            feedback = "💥 <b>Hit!</b> +100 points!"
        else: # Hit Villager or Doctor
            state['score'] -= 75
            feedback = "❌ <b>Hit civilians!</b> -75 points!"
    elif action == 'Hold':
        if target == 'Mafia':
            state['score'] -= 50
            feedback = "❌ <b>Missed!</b> -50 points!"
        else:
            state['score'] += 20
            feedback = "✅ <b>Good choice!</b> +20 points!"
            
    await query.edit_message_text(f"<b>{feedback}</b>\n\nNext round...", parse_mode='HTML')
    await asyncio.sleep(1.5)
    await send_target_practice_round(query, context)

async def end_target_practice(query, context):
    """Mission 1: End the game and give rewards"""
    if 'mission_state' not in context.user_data: return
    
    user_id = query.from_user.id
    score = context.user_data['mission_state']['score']
    del context.user_data['mission_state']

    rewards = MISSION_REWARDS['target_practice']
    xp_reward = rewards['xp'] + (score // 10)
    coin_reward = rewards['coins'] + (score // 5)
    
    if xp_reward > 0: player_manager.add_xp(user_id, xp_reward)
    if coin_reward > 0: player_manager.add_coins(user_id, coin_reward)
    
    text = (
        f"🎯 <b>MISSION COMPLETE</b> 🎯\n\n"
        f"Final Score: <b>{score}</b>\n\n"
        f"<b>Rewards:</b>\n"
        f"💎 {xp_reward} XP\n"
        f"🪙 {coin_reward} Coins"
    )
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Missions", callback_data='menu_missions')]])
    await query.edit_message_text(text, parse_mode='HTML', reply_markup=keyboard)


async def start_detectives_case(query, context):
    """Mission 2: Detective's Case (Memory) - Start"""
    await query.edit_message_text("🔍 <b>Detective's Case</b>\n\nMemorize the sequence...", parse_mode='HTML')
    await asyncio.sleep(2)
    
    roles = ['mafia', 'detective', 'doctor', 'villager']
    sequence = [get_role_emoji(random.choice(roles)) for _ in range(4)]
    sequence_str = " ".join(sequence)
    
    # Store correct answer
    context.user_data['mission_state'] = {'correct_answer': sequence_str}
    
    await query.edit_message_text(f"Memorize:\n\n<b>{sequence_str}</b>\n\n(Disappears in 5 seconds!)", parse_mode='HTML')
    await asyncio.sleep(5)
    
    options = [sequence_str]
    for _ in range(3):
        fake_seq = " ".join([get_role_emoji(random.choice(roles)) for _ in range(4)])
        while fake_seq in options:
            fake_seq = " ".join([get_role_emoji(random.choice(roles)) for _ in range(4)])
        options.append(fake_seq)
    
    random.shuffle(options)
    
    buttons = []
    for i, opt in enumerate(options):
        buttons.append([InlineKeyboardButton(opt, callback_data=f"case_answer_{i}")])
    
    # Store the options to check answer
    context.user_data['mission_state']['options'] = options
    
    await query.edit_message_text("<b>What was the sequence?</b>", parse_mode='HTML', reply_markup=InlineKeyboardMarkup(buttons))

async def handle_detectives_case(query, context, data):
    """Mission 2: Check the answer"""
    if 'mission_state' not in context.user_data:
        await query.edit_message_text("Error: Mission expired. Please start again.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Missions", callback_data='menu_missions')]]))
        return

    state = context.user_data['mission_state']
    correct_answer = state['correct_answer']
    options = state['options']
    
    try:
        answer_index = int(data.split('_')[-1])
        chosen_answer = options[answer_index]
    except:
        await query.edit_message_text("Error: Invalid answer. Please start again.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Missions", callback_data='menu_missions')]]))
        return

    rewards = MISSION_REWARDS['detectives_case']
    user_id = query.from_user.id
    
    if chosen_answer == correct_answer:
        player_manager.add_xp(user_id, rewards['xp'])
        player_manager.add_coins(user_id, rewards['coins'])
        text = (
            f"✅ <b>Case Solved!</b>\n\n"
            f"<b>Rewards:</b>\n"
            f"💎 {rewards['xp']} XP\n"
            f"🪙 {rewards['coins']} Coins"
        )
    else:
        text = f"❌ <b>Wrong sequence!</b>\n\nThe correct one was:\n{correct_answer}\n\nNo reward this time."
    
    del context.user_data['mission_state']
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Missions", callback_data='menu_missions')]])
    await query.edit_message_text(text, parse_mode='HTML', reply_markup=keyboard)


async def start_doctors_dilemma(query, context):
    """Mission 3: Doctor's Dilemma (Logic) - Start"""
    puzzles = [
        {
            "q": "One of these patients is Mafia. The other is a Villager.\n\n👤 <b>Patient A:</b> \"I am a Villager.\"\n👤 <b>Patient B:</b> \"Patient A is lying.\"\n\nThe Mafia member is lying. Who is the Mafia?",
            "a": "dilemma_answer_A",
            "options": [("Patient A", "dilemma_answer_A"), ("Patient B", "dilemma_answer_B")]
        },
        {
            "q": "A Detective investigated 2 people.\n\n👤 <b>Person 1:</b> Innocent\n👤 <b>Person 2:</b> Innocent\n\nHe knows one of them *must* be the Godfather (who shows as innocent).\n\nPerson 1 says: \"I am just a Villager.\"\nPerson 2 says: \"At least one of us is telling the truth.\"\n\nIf the Godfather always lies, who is the Godfather?",
            "a": "dilemma_answer_B",
            "options": [("Person 1", "dilemma_answer_A"), ("Person 2", "dilemma_answer_B")]
        }
    ]
    puzzle = random.choice(puzzles)
    context.user_data['mission_state'] = {'correct_answer': puzzle['a']}
    
    buttons = [[InlineKeyboardButton(text, cb) for text, cb in puzzle['options']]]
    await query.edit_message_text(f"💉 <b>Doctor's Dilemma</b>\n\n{puzzle['q']}", parse_mode='HTML', reply_markup=InlineKeyboardMarkup(buttons))

async def handle_doctors_dilemma(query, context, data):
    """Mission 3: Check the answer"""
    if 'mission_state' not in context.user_data:
        await query.edit_message_text("Error: Mission expired. Please start again.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Missions", callback_data='menu_missions')]]))
        return
        
    correct_answer = context.user_data['mission_state']['correct_answer']
    user_id = query.from_user.id
    rewards = MISSION_REWARDS['doctors_dilemma']
    
    if data == correct_answer:
        player_manager.add_xp(user_id, rewards['xp'])
        player_manager.add_coins(user_id, rewards['coins'])
        text = (
            f"✅ <b>Correct! You saved the town!</b>\n\n"
            f"<b>Rewards:</b>\n"
            f"💎 {rewards['xp']} XP\n"
            f"🪙 {rewards['coins']} Coins"
        )
    else:
        text = "❌ <b>Wrong choice!</b>\n\nThe town blames you... No reward."
        
    del context.user_data['mission_state']
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Missions", callback_data='menu_missions')]])
    await query.edit_message_text(text, parse_mode='HTML', reply_markup=keyboard)


async def start_timed_disarm(query, context):
    """Mission 4: Timed Disarm (Button Mash) - Start"""
    context.user_data['mission_state'] = {
        'clicks': 0,
        'end_time': asyncio.get_event_loop().time() + 10.0
    }
    
    text = "💣 <b>DISARM THE BOMB!</b> 💣\n\nTap as fast as you can!\n\nTime: <b>10.0s</b>\nClicks: <b>0</b>"
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("CLICK!", callback_data="disarm_click_0")]])
    await query.edit_message_text(text, parse_mode='HTML', reply_markup=keyboard)

async def handle_timed_disarm(query, context, data):
    """Mission 4: Handle the clicks"""
    if 'mission_state' not in context.user_data:
        await query.answer()
        return

    state = context.user_data['mission_state']
    time_left = state['end_time'] - asyncio.get_event_loop().time()
    
    if time_left <= 0:
        await query.answer("Time's up!")
        user_id = query.from_user.id
        clicks = state['clicks']
        del context.user_data['mission_state']
        
        rewards = MISSION_REWARDS['timed_disarm']
        xp_reward = rewards['xp'] + (clicks * 2)
        coin_reward = rewards['coins'] + clicks
        
        player_manager.add_xp(user_id, xp_reward)
        player_manager.add_coins(user_id, coin_reward)
        
        text = (
            f"🎉 <b>BOMB DISARMED!</b> 🎉\n\n"
            f"Final Clicks: <b>{clicks}</b>\n\n"
            f"<b>Rewards:</b>\n"
            f"💎 {xp_reward} XP\n"
            f"🪙 {coin_reward} Coins"
        )
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Missions", callback_data='menu_missions')]])
        await query.edit_message_text(text, parse_mode='HTML', reply_markup=keyboard)
        return

    state['clicks'] += 1
    await query.answer(f"Clicks: {state['clicks']}")
    
    if state['clicks'] % 5 == 0:
        new_text = f"💣 <b>DISARM THE BOMB!</b> 💣\n\nTap as fast as you can!\n\nTime: <b>{time_left:.1f}s</b>\nClicks: <b>{state['clicks']}</b>"
        new_kb = InlineKeyboardMarkup([[InlineKeyboardButton(f"CLICK! [{state['clicks']}]", callback_data=f"disarm_click_{state['clicks']}")]])
        try:
            await query.edit_message_text(new_text, parse_mode='HTML', reply_markup=new_kb)
        except Exception:
            pass


async def start_mafia_heist(query, context):
    """Mission 5: Mafia Heist (Text Adventure) - Start"""
    text = (
        "💰 <b>THE HEIST</b> 💰\n\n"
        "You're at the bank entrance. The guard is looking away. What's the plan?"
    )
    buttons = [
        [InlineKeyboardButton("🚪 Sneak past the guard", callback_data="heist_sneak")],
        [InlineKeyboardButton("🥊 Distract the guard", callback_data="heist_distract")]
    ]
    await query.edit_message_text(text, parse_mode='HTML', reply_markup=InlineKeyboardMarkup(buttons))

async def handle_mafia_heist(query, context, data):
    """Mission 5: Mafia Heist - Continuation"""
    user_id = query.from_user.id
    
    if data == 'heist_sneak' or data == 'heist_distract':
        if data == 'heist_sneak':
            text = "You slipped past! You're at the vault. It needs a code or a drill."
        else:
            text = "You caused a distraction! The guard ran off. You reach the vault. It needs a code or a drill."
        buttons = [
            [InlineKeyboardButton("💻 Hack the code", callback_data="heist_hack")],
            [InlineKeyboardButton("🛠️ Use the drill", callback_data="heist_drill")]
        ]
        await query.edit_message_text(text, parse_mode='HTML', reply_markup=InlineKeyboardMarkup(buttons))

    elif data == 'heist_hack':
        text = "You're in! The vault is open. You grab the loot, but... <b>Click.</b> A gun is at your back. It's the Boss!\n\n\"Did you really think I'd let you keep it?\"\n\n...you were set up!"
        rewards = MISSION_REWARDS['mafia_heist_fail']
        player_manager.add_xp(user_id, rewards['xp'])
        player_manager.add_coins(user_id, rewards['coins'])
        
        end_text = (
            f"{text}\n\n"
            f"💔 <b>HEIST FAILED</b> 💔\n\n"
            f"You got a small cut for your trouble:\n"
            f"💎 {rewards['xp']} XP\n"
            f"🪙 {rewards['coins']} Coins"
        )
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Missions", callback_data='menu_missions')]])
        await query.edit_message_text(end_text, parse_mode='HTML', reply_markup=keyboard)

    elif data == 'heist_drill':
        text = "The drill is loud! You bust it open and grab the loot... but the alarms are blaring! You barely escape!"
        rewards = MISSION_REWARDS['mafia_heist_success']
        player_manager.add_xp(user_id, rewards['xp'])
        player_manager.add_coins(user_id, rewards['coins'])
        
        end_text = (
            f"{text}\n\n"
            f"🎉 <b>HEIST SUCCESSFUL!</b> 🎉\n\n"
            f"You got the score!\n"
            f"💎 {rewards['xp']} XP\n"
            f"🪙 {rewards['coins']} Coins"
        )
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Missions", callback_data='menu_missions')]])
        await query.edit_message_text(end_text, parse_mode='HTML', reply_markup=keyboard)


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
        "/logs - (Admin) Get bot logs\n"
        "/botstats - (Admin) Get bot stats"
    )
    await update.message.reply_text(text, parse_mode='HTML')


# --- FIX 1: Improved Error Handler ---
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors"""
    logger.error(f"Update {update} caused error {context.error}", exc_info=context.error)
    
    try:
        if update and update.effective_message:
            await update.effective_message.reply_text(
                "⚠️ <b>An error occurred!</b>\n\nPlease try again or contact support.",
                parse_mode='HTML'
            )
        elif update and update.callback_query:
            # Just send an alert, don't try to edit the message
            await update.callback_query.answer(
                "⚠️ An error occurred! Please try again.", 
                show_alert=True
            )
    except Exception as e:
        logger.error(f"Failed to send error message: {e}")

# --- FIX 3: New Admin Commands ---
async def get_logs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin command to get log file"""
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ You are not authorized to use this command.")
        return

    log_file = 'nohup.out'
    if os.path.exists(log_file):
        try:
            await context.bot.send_document(
                chat_id=user_id,
                document=InputFile(log_file),
                filename='bot_logs.txt'
            )
        except Exception as e:
            await update.message.reply_text(f"❌ Failed to send logs: {e}")
    else:
        await update.message.reply_text("❌ `nohup.out` file not found.")

async def get_bot_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin command to get bot stats"""
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ You are not authorized to use this command.")
        return
        
    total_users = len(player_manager.players)
    active_games = len(game_manager.games)
    
    text = (
        "📊 <b>BOT STATISTICS</b> 📊\n\n"
        f"👥 <b>Total Users:</b> {total_users}\n"
        f"🎮 <b>Active Lobbies/Games:</b> {active_games}"
    )
    await update.message.reply_text(text, parse_mode='HTML')


async def broadcast_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin command to broadcast messages"""
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ Unauthorized!")
        return
    
    if not context.args:
        await update.message.reply_text("Usage: /broadcast <message>")
        return
    
    message = ' '.join(context.args)
    players = player_manager.players
    
    success_count = 0
    for user_id in players.keys():
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=f"📢 <b>Announcement:</b>\n\n{message}",
                parse_mode='HTML'
            )
            success_count += 1
        except:
            pass
    
    await update.message.reply_text(
        f"✅ Broadcast sent to {success_count} players!"
    )

def main():
    """Start the bot"""
    application = Application.builder().token(BOT_TOKEN).build()
    
    # --- FIX 2: Added new Command Handlers ---
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("play", play_command))
    application.add_handler(CommandHandler("shop", shop_command))
    application.add_handler(CommandHandler("profile", profile_command_handler))
    application.add_handler(CommandHandler("leaderboard", leaderboard_command_handler))
    application.add_handler(CommandHandler("daily", daily_command_handler))
    application.add_handler(CommandHandler("help", help_command))
    
    # --- FIX 3: Add new Admin Command Handlers ---
    application.add_handler(CommandHandler("logs", get_logs))
    application.add_handler(CommandHandler("botstats", get_bot_stats))
    application.add_handler(CommandHandler("broadcast", broadcast_message))
    
    # --- Callback query handler for ALL inline buttons ---
    application.add_handler(CallbackQueryHandler(handle_callback_query))

    # Message handler for in-game actions
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Error handler
    application.add_error_handler(error_handler)
    
    logger.info("🎭 Mafia RPG Bot is starting (Inline Mode)...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
