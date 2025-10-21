"""
Mafia RPG Telegram Bot - Main Entry Point
Complete implementation with INLINE keyboards
"""

import logging
import asyncio
import random
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove
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
from config import BOT_TOKEN, FEATURES, SHOP_ITEMS, ADMIN_IDS, MISSION_REWARDS, ANIMATION_SEQUENCES
from utils import (
    create_main_menu_keyboard, create_game_mode_keyboard,
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
    
    # Register player
    player_manager.register_player(user.id, user.username or user.first_name)
    
    welcome_text = (
        f"🎭 <b>MAFIA RPG</b> 🎭\n\n"
        f"🔥 <b>Welcome, {user.first_name}!</b> 🔥\n\n"
        "Choose your destiny:\n"
        "🎮 <b>Game Modes:</b>\n"
        "• ⚔️ 5v5 Classic - Team battle\n"
        "• 🎯 1v1 Duel - Intense showdown\n"
        "• 🚀 Missions - Single-player challenges\n\n"
        "🎯 Complete missions, level up, become a legend!\n\n"
        "👇 <b>Use the menu below to get started!</b>"
    )
    
    keyboard = create_main_menu_keyboard()
    
    # Send the welcome message with the inline keyboard
    await update.message.reply_text(
        welcome_text,
        parse_mode='HTML',
        reply_markup=keyboard
    )

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
    elif text.lower() in ["/menu", "/start", "menu", "back"]:
         await update.message.reply_text("Please use the /start command to see the menu.")


async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all inline button presses"""
    query = update.callback_query
    await query.answer() # Acknowledge the button press
    
    data = query.data
    user_id = query.from_user.id
    username = query.from_user.username or query.from_user.first_name

    # Main Menu Navigation
    if data == 'menu_main':
        await show_main_menu(query, context)
    elif data == 'menu_play':
        await show_game_modes(query, context)
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
    elif data == 'mode_missions':
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

    # Mission Actions
    elif data == 'mission_target':
        await start_target_practice(query, context)
    elif data == 'mission_case':
        await start_detectives_case(query, context)
    elif data == 'mission_dilemma':
        await start_doctors_dilemma(query, context)
    elif data == 'mission_disarm':
        await start_timed_disarm(query, context)
    elif data == 'mission_heist':
        await start_mafia_heist(query, context)
    elif data.startswith('heist_'):
        await continue_mafia_heist(query, context, data)
        

async def show_main_menu(query, context):
    """Shows the main menu (used for 'Back' buttons)"""
    user = query.from_user
    text = (
        f"🎭 <b>MAFIA RPG</b> 🎭\n\n"
        f"🔥 <b>Welcome, {user.first_name}!</b> 🔥\n\n"
        "Choose your destiny:\n"
        "🎮 <b>Game Modes:</b>\n"
        "• ⚔️ 5v5 Classic - Team battle\n"
        "• 🎯 1v1 Duel - Intense showdown\n"
        "• 🚀 Missions - Single-player challenges\n\n"
        "👇 <b>Use the menu below to get started!</b>"
    )
    keyboard = create_main_menu_keyboard()
    await query.edit_message_text(text, parse_mode='HTML', reply_markup=keyboard)


async def show_game_modes(query, context):
    """Show game mode selection"""
    text = (
        "🎮 <b>SELECT GAME MODE</b> 🎮\n\n"
        "⚔️ <b>5v5 Classic</b>\n"
        "Team-based strategy with 10 players.\n\n"
        "🎯 <b>1v1 Duel</b>\n"
        "Fast-paced 2-player showdown.\n\n"
        "🚀 <b>Missions</b>\n"
        "Single-player challenges for rewards.\n\n"
        "Choose your mode:"
    )
    keyboard = create_game_mode_keyboard()
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
    
    await query.edit_message_text(profile_text, parse_mode='HTML', reply_markup=keyboard)


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
    
    # Process purchase
    success = player_manager.spend_coins(user_id, item_to_buy['price'])
    if success:
        player_manager.add_item(user_id, item_to_buy)
        await query.answer(f"🎉 Purchase successful! You bought: {item_to_buy['name']}", show_alert=True)
        # Refresh shop view
        await show_shop(query, context)
    else:
        await query.answer("❌ Transaction failed!", show_alert=True)


async def show_help(query, context):
    """Show help information"""
    text = (
        "❓ <b>HOW TO PLAY</b> ❓\n\n"
        "<b>🎭 GAME BASICS:</b>\n"
        "• Players are assigned secret roles\n"
        "• Mafia eliminates at night\n"
        "• Villagers vote during the day\n"
        "• Special roles have unique powers\n\n"
        "<b>⚔️ 5v5 CLASSIC:</b>\n"
        "• 3 Mafia vs 1 Detective, 1 Doctor, 5 Villagers\n\n"
        "<b>🎯 1v1 DUEL:</b>\n"
        "• Quick match: Mafia vs Detective\n\n"
        "<b>🚀 MISSIONS:</b>\n"
        "• Single-player mini-games to earn rewards.\n\n"
        "<b>🎮 PROGRESSION:</b>\n"
        "• Earn XP, level up, and collect coins.\n\n"
        "<b>⚡ COMMANDS:</b>\n"
        "/start - Begin your journey\n"
        "/profile - View your stats\n"
    )
    
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Menu", callback_data='menu_main')]])
    await query.edit_message_text(text, parse_mode='HTML', reply_markup=keyboard)


async def create_game_lobby(query, context, mode: str):
    """Create a new game lobby"""
    user_id = query.from_user.id
    chat_id = query.message.chat_id
    
    # Create game
    game_id = game_manager.create_game(mode, user_id, chat_id)
    
    # Store game_id in context for this chat
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
    
    # Edit the menu message to show the lobby
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
        
        # Update lobby message
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
    
    # Animated start sequence
    await send_animated_message(
        query.message,
        ANIMATION_SEQUENCES['game_start'],
        delay=1.5
    )
    
    # Send role information to each player privately
    for player in game['players']:
        role_desc = game_manager.get_role_description(player['role'])
        await send_role_reveal_animation(
            context,
            player['user_id'],
            player['role'],
            role_desc
        )
    
    # Remove lobby keyboard and show start message
    await query.edit_message_text(
        "🎮 <b>Game Started!</b>\n\nCheck your private messages for your role!",
        parse_mode='HTML',
        reply_markup=None # Remove buttons
    )
    
    await asyncio.sleep(2)
    
    # Start first round
    await game_manager.start_round(game_id, query.message, context)


async def cancel_game_action(query, context, game_id: str, user_id: int):
    """Cancel a game"""
    success, message = game_manager.cancel_game(game_id, user_id)
    
    if success:
        await query.answer("✅ Game cancelled!")
        await show_main_menu(query, context) # Go back to main menu
    else:
        await query.answer(f"❌ {message}", show_alert=True)

# --- NEW SINGLE PLAYER MISSIONS ---

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
    """Mission 1: Target Practice"""
    user_id = query.from_user.id
    score = 0
    await query.edit_message_text("🎯 <b>Target Practice</b>\n\nGet ready...", parse_mode='HTML')
    await asyncio.sleep(2)
    
    for _ in range(7): # 7 rounds
        target = random.choice(['👥 Villager', '👥 Villager', '🔪 Mafia', '💉 Doctor'])
        emoji = get_role_emoji(target.split(' ')[-1].lower())
        
        text = f"<b>SCORE: {score}</b>\n\n{emoji} <b>{target}</b> {emoji}\n\nSHOOT?"
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("💥 SHOOT!", callback_data=f"shoot_{target.split(' ')[-1]}"),
            InlineKeyboardButton(" HOLD FIRE ", callback_data="shoot_Hold")
        ]])
        
        await query.edit_message_text(text, parse_mode='HTML', reply_markup=keyboard)
        
        # Wait for user's action
        try:
            cb_update = await context.application.wait_for_update(
                lambda u: u.callback_query and u.callback_query.from_user.id == user_id and u.callback_query.data.startswith('shoot_'),
                timeout=2.0
            )
            await cb_update.callback_query.answer()
            action = cb_update.callback_query.data.split('_')[-1]
            
            if action == 'Mafia':
                score += 100
                await query.edit_message_text("💥 <b>Hit!</b> +100 points!", parse_mode='HTML')
            elif action == 'Hold':
                if target == 'Mafia':
                    score -= 50
                    await query.edit_message_text("❌ <b>Missed!</b> -50 points!", parse_mode='HTML')
                else:
                    score += 20
                    await query.edit_message_text("✅ <b>Good choice!</b> +20 points!", parse_mode='HTML')
            else: # Hit Villager or Doctor
                score -= 75
                await query.edit_message_text(" civilians!</b> -75 points!", parse_mode='HTML')
                
        except asyncio.TimeoutError:
            if target == 'Mafia':
                score -= 50
                await query.edit_message_text("❌ <b>Too slow!</b> -50 points!", parse_mode='HTML')
            else:
                score += 20
                await query.edit_message_text("✅ <b>Good hold!</b> +20 points!", parse_mode='HTML')
        
        await asyncio.sleep(1.5)

    # End game
    rewards = MISSION_REWARDS['target_practice']
    xp_reward = rewards['xp'] + (score // 10)
    coin_reward = rewards['coins'] + (score // 5)
    
    player_manager.add_xp(user_id, xp_reward)
    player_manager.add_coins(user_id, coin_reward)
    
    text = (
        f"🎯 <b>MISSION COMPLETE</b> 🎯\n\n"
        f"Final Score: <b>{score}</b>\n\n"
        f"<b>Rewards:</b>\n"
        f"💎 {xp_reward} XP\n"
        f"🪙 {coin_reward} Coins"
    )
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Missions", callback_data='mode_missions')]])
    await query.edit_message_text(text, parse_mode='HTML', reply_markup=keyboard)


async def start_detectives_case(query, context):
    """Mission 2: Detective's Case (Memory)"""
    user_id = query.from_user.id
    await query.edit_message_text("🔍 <b>Detective's Case</b>\n\nMemorize the sequence...", parse_mode='HTML')
    await asyncio.sleep(2)
    
    roles = ['mafia', 'detective', 'doctor', 'villager']
    sequence = [get_role_emoji(random.choice(roles)) for _ in range(4)]
    sequence_str = " ".join(sequence)
    
    await query.edit_message_text(f"Memorize:\n\n<b>{sequence_str}</b>\n\n(Disappears in 5 seconds!)", parse_mode='HTML')
    await asyncio.sleep(5)
    
    # Create options
    options = [sequence_str]
    for _ in range(3):
        fake_seq = " ".join([get_role_emoji(random.choice(roles)) for _ in range(4)])
        while fake_seq in options:
            fake_seq = " ".join([get_role_emoji(random.choice(roles)) for _ in range(4)])
        options.append(fake_seq)
    
    random.shuffle(options)
    
    buttons = []
    for i, opt in enumerate(options):
        callback = "case_correct" if opt == sequence_str else "case_wrong"
        buttons.append([InlineKeyboardButton(opt, callback_data=callback)])
    
    await query.edit_message_text("<b>What was the sequence?</b>", parse_mode='HTML', reply_markup=InlineKeyboardMarkup(buttons))
    
    # Wait for answer
    cb_update = await context.application.wait_for_update(
        lambda u: u.callback_query and u.callback_query.from_user.id == user_id and u.callback_query.data.startswith('case_'),
        timeout=15.0
    )
    await cb_update.callback_query.answer()
    
    rewards = MISSION_REWARDS['detectives_case']
    if cb_update.callback_query.data == 'case_correct':
        player_manager.add_xp(user_id, rewards['xp'])
        player_manager.add_coins(user_id, rewards['coins'])
        text = (
            f"✅ <b>Case Solved!</b>\n\n"
            f"<b>Rewards:</b>\n"
            f"💎 {rewards['xp']} XP\n"
            f"🪙 {rewards['coins']} Coins"
        )
    else:
        text = "❌ <b>Wrong sequence!</b>\n\nNo reward this time."
    
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Missions", callback_data='mode_missions')]])
    await query.edit_message_text(text, parse_mode='HTML', reply_markup=keyboard)


async def start_doctors_dilemma(query, context):
    """Mission 3: Doctor's Dilemma (Logic)"""
    user_id = query.from_user.id
    
    puzzles = [
        {
            "q": "One of these patients is Mafia. The other is a Villager.\n\n👤 <b>Patient A:</b> \"I am a Villager.\"\n👤 <b>Patient B:</b> \"Patient A is lying.\"\n\nThe Mafia member is lying. Who is the Mafia?",
            "a": "dilemma_A",
            "options": [("Patient A", "dilemma_A"), ("Patient B", "dilemma_B")]
        },
        {
            "q": "A Detective investigated 2 people.\n\n👤 <b>Person 1:</b> Innocent\n👤 <b>Person 2:</b> Innocent\n\nHe knows one of them *must* be the Godfather (who shows as innocent).\n\nPerson 1 says: \"I am just a Villager.\"\nPerson 2 says: \"At least one of us is telling the truth.\"\n\nIf the Godfather always lies, who is the Godfather?",
            "a": "dilemma_B",
            "options": [("Person 1", "dilemma_A"), ("Person 2", "dilemma_B")]
        }
    ]
    puzzle = random.choice(puzzles)
    buttons = [[InlineKeyboardButton(text, cb) for text, cb in puzzle['options']]]
    
    await query.edit_message_text(f"💉 <b>Doctor's Dilemma</b>\n\n{puzzle['q']}", parse_mode='HTML', reply_markup=InlineKeyboardMarkup(buttons))
    
    # Wait for answer
    cb_update = await context.application.wait_for_update(
        lambda u: u.callback_query and u.callback_query.from_user.id == user_id and u.callback_query.data.startswith('dilemma_'),
        timeout=30.0
    )
    await cb_update.callback_query.answer()
    
    rewards = MISSION_REWARDS['doctors_dilemma']
    if cb_update.callback_query.data == puzzle['a']:
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
    
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Missions", callback_data='mode_missions')]])
    await query.edit_message_text(text, parse_mode='HTML', reply_markup=keyboard)


async def start_timed_disarm(query, context):
    """Mission 4: Timed Disarm (Button Mash)"""
    user_id = query.from_user.id
    
    text = "💣 <b>DISARM THE BOMB!</b> 💣\n\nTap as fast as you can!\n\nTime: <b>10s</b>\nClicks: <b>0</b>"
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("CLICK!", callback_data="disarm_click_0")]])
    await query.edit_message_text(text, parse_mode='HTML', reply_markup=keyboard)
    
    end_time = asyncio.get_event_loop().time() + 10.0
    clicks = 0
    
    while asyncio.get_event_loop().time() < end_time:
        time_left = end_time - asyncio.get_event_loop().time()
        
        try:
            cb_update = await context.application.wait_for_update(
                lambda u: u.callback_query and u.callback_query.from_user.id == user_id and u.callback_query.data.startswith('disarm_'),
                timeout=time_left
            )
            
            clicks += 1
            await cb_update.callback_query.answer(f"Clicks: {clicks}")
            
            new_text = f"💣 <b>DISARM THE BOMB!</b> 💣\n\nTap as fast as you can!\n\nTime: <b>{time_left:.1f}s</b>\nClicks: <b>{clicks}</b>"
            new_kb = InlineKeyboardMarkup([[InlineKeyboardButton(f"CLICK! [{clicks}]", callback_data=f"disarm_click_{clicks}")]])
            
            # Only edit if text or keyboard changed
            if clicks % 5 == 0: # Reduce edits to avoid rate limits
                 await query.edit_message_text(new_text, parse_mode='HTML', reply_markup=new_kb)
            
        except asyncio.TimeoutError:
            break
        except Exception as e:
            logger.warning(f"Disarm click error: {e}")
            break # Stop on error

    # End game
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
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Missions", callback_data='mode_missions')]])
    await query.edit_message_text(text, parse_mode='HTML', reply_markup=keyboard)


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

async def continue_mafia_heist(query, context, data):
    """Mission 5: Mafia Heist - Continuation"""
    user_id = query.from_user.id
    
    if data == 'heist_sneak':
        text = "You slipped past! You're at the vault. It needs a code or a drill."
        buttons = [
            [InlineKeyboardButton("💻 Hack the code", callback_data="heist_hack")],
            [InlineKeyboardButton("🛠️ Use the drill", callback_data="heist_drill")]
        ]
        await query.edit_message_text(text, parse_mode='HTML', reply_markup=InlineKeyboardMarkup(buttons))
        
    elif data == 'heist_distract':
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
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Missions", callback_data='mode_missions')]])
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
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Missions", callback_data='mode_missions')]])
        await query.edit_message_text(end_text, parse_mode='HTML', reply_markup=keyboard)


# --- ADMIN AND ERROR HANDLERS ---

async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show profile via command"""
    user_id = update.effective_user.id
    player_data = player_manager.get_player(user_id)
    profile_text = format_player_stats(player_data)
    await update.message.reply_text(profile_text, parse_mode='HTML')


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show help via command"""
    text = "Please use the /start command to see the full interactive menu."
    await update.message.reply_text(text, parse_mode='HTML')


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors"""
    logger.error(f"Update {update} caused error {context.error}", exc_info=context.error)
    
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "⚠️ <b>An error occurred!</b>\n\nPlease try again or contact support.",
            parse_mode='HTML'
        )
    elif update and update.callback_query:
        try:
            await update.callback_query.answer("⚠️ An error occurred!", show_alert=True)
        except Exception as e:
            logger.error(f"Failed to send error alert: {e}")


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
    
    # Command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("profile", profile_command))
    application.add_handler(CommandHandler("help", help_command))
    
    # Admin commands
    application.add_handler(CommandHandler("broadcast", broadcast_message))
    
    # --- NEW: Callback query handler for ALL inline buttons ---
    application.add_handler(CallbackQueryHandler(handle_callback_query))

    # Message handler for in-game actions
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Error handler
    application.add_error_handler(error_handler)
    
    logger.info("🎭 Mafia RPG Bot is starting (Inline Mode)...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
