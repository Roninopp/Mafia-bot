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
    CallbackQueryHandler,
    # Need BaseHandler for type check in main if needed, but not required for fix
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
    text = update.message.text
    user_id = update.effective_user.id
    username = update.effective_user.username or update.effective_user.first_name

    player_manager.register_player(user_id, username)

    if any(emoji in text for emoji in ['🔪', '🔍', '💉']):
        await game_manager.handle_action(update, context)
        return
    elif '🗳️' in text or 'Vote:' in text or '⏭️' in text:
        await game_manager.handle_vote(update, context)
        return

    if update.effective_chat.type == 'private':
         await update.message.reply_text("Please use the commands like /start, /play, or the buttons.")


# --- Callback Query Handler (with detailed logging) ---
async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all inline button presses"""
    query = update.callback_query
    if not query or not query.message: return

    try:
        await query.answer()
    except BadRequest as e:
        if "query is too old" in str(e).lower(): return
        logger.error(f"Error answering callback query: {e}")
        return

    data = query.data
    user_id = query.from_user.id
    username = query.from_user.username or query.from_user.first_name

    logger.info(f"Callback query received: data='{data}', user_id={user_id}")

    if not data.startswith(('mission_', 'shoot_', 'case_', 'dilemma_', 'disarm_', 'heist_', 'trade_', 'tourn_')):
        context.user_data.pop('mission_state', None)
        context.user_data.pop('trade_setup', None)
        context.user_data.pop('state', None)

    try:
        if data == 'menu_main': await show_main_menu_callback(query, context)
        elif data == 'menu_play': await show_play_menu(query, context)
        elif data == 'menu_profile': await show_profile(query, context)
        elif data == 'menu_leaderboard': await show_leaderboard(query, context)
        elif data == 'menu_daily': await claim_daily_reward(query, context)
        elif data == 'menu_shop': await show_shop(query, context)
        elif data == 'menu_help': await show_help_callback(query, context)
        elif data == 'menu_tournament': await show_tournament_menu(query, context)
        elif data == 'menu_trade': await show_trade_menu(query, context)
        elif data == 'mode_5v5': logger.info("Handling mode_5v5"); await create_game_lobby(query, context, '5v5')
        elif data == 'mode_1v1': logger.info("Handling mode_1v1"); await create_game_lobby(query, context, '1v1')
        elif data == 'menu_missions': logger.info("Handling menu_missions"); await show_missions_menu(query, context)
        elif data.startswith('join_game_'): await join_game_action(query, context, data.split('_')[-1], user_id, username)
        elif data.startswith('start_game_'): await start_game_action(query, context, data.split('_')[-1], user_id)
        elif data.startswith('cancel_game_'): await cancel_game_action(query, context, data.split('_')[-1], user_id)
        elif data.startswith('buy_item_'): await handle_purchase(query, context, data.split('_')[-1], user_id)
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
        elif data == 'tourn_create': await create_new_tournament(query, context)
        elif data == 'tourn_list': await list_tournaments(query, context)
        elif data.startswith('tourn_view_'): await show_tournament_details(query, context, data.split('_')[-1])
        elif data.startswith('tourn_register_'): await register_for_tournament(query, context, data.split('_')[-1])
        elif data.startswith('tourn_start_'): await start_tournament_handler(query, context, data.split('_')[-1])
        elif data.startswith('tourn_brackets_'): await show_tournament_brackets(query, context, data.split('_')[-1])
        elif data == 'trade_create': await start_create_trade(query, context)
        elif data == 'trade_list': await list_active_trades(query, context)
        elif data.startswith('trade_accept_'): await accept_trade_offer(query, context, data.split('_')[-1])
        elif data.startswith('trade_cancel_'): await cancel_trade_offer(query, context, data.split('_')[-1])
        else:
            logger.warning(f"Unhandled callback query data: {data}")
            await query.answer("Action not recognised.", show_alert=True)
    except Exception as e:
        logger.error(f"Error handling callback data '{data}' for user {user_id}: {e}", exc_info=True)
        await query.answer("⚠️ An error occurred! Check logs.", show_alert=True)


# --- MENU DISPLAY FUNCTIONS ---
async def safe_edit_message(query, text, keyboard):
    """Helper to safely edit a message."""
    if not query or not query.message: logger.warning("safe_edit_message: invalid query/message."); return
    try: await query.edit_message_text(text, parse_mode='HTML', reply_markup=keyboard)
    except BadRequest as e:
        if "message is not modified" not in str(e).lower():
            logger.error(f"Failed to edit message (BadRequest): {e}")
            await query.message.reply_text("Issue updating menu. Try again.")
    except Exception as e: logger.error(f"Unhandled error in safe_edit_message: {e}")

# ... (show_main_menu_callback, show_play_menu, show_profile, etc. - ALL UNCHANGED from previous version)
async def show_main_menu_callback(query, context):
    user = query.from_user
    welcome_text = f"🚬 <b>Welcome back, {user.first_name}.</b>\n\nWhat's the move?"
    keyboard = create_main_menu_keyboard(is_private=True)
    await safe_edit_message(query, welcome_text, keyboard)

async def show_play_menu(query, context):
    text = "🎮 <b>SELECT GAME MODE</b> 🎮\n\nChoose your poison:"
    keyboard = create_play_menu_keyboard()
    await safe_edit_message(query, text, keyboard)

async def show_profile(query, context):
    user_id = query.from_user.id
    player_data = player_manager.get_player(user_id)
    if not player_data: await safe_edit_message(query, "❌ Profile not found!", None); return
    profile_text = format_player_stats(player_data)
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Menu", callback_data='menu_main')]])
    await safe_edit_message(query, profile_text, keyboard)

async def show_leaderboard(query, context):
    top_players = player_manager.get_leaderboard(10)
    text = "🏆 <b>TOP PLAYERS</b> 🏆\n\n"
    if not top_players: text += "No players yet!"
    else:
        for i, player in enumerate(top_players, 1): text += format_leaderboard_entry(i, player) + "\n"
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Menu", callback_data='menu_main')]])
    await safe_edit_message(query, text, keyboard)

async def claim_daily_reward(query, context):
    user_id = query.from_user.id
    success, reward = player_manager.claim_daily_reward(user_id)
    if success: text = (f"🎉 <b>DAILY REWARD CLAIMED!</b> 🎉\n\n💎 {reward['xp']} XP\n🪙 {reward['coins']} Coins\n🔥 Streak: {reward['streak']} days")
    else: text = ("⏰ <b>Already Claimed!</b>\n\nCome back tomorrow.")
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Menu", callback_data='menu_main')]])
    await safe_edit_message(query, text, keyboard)

async def show_shop(query, context):
    user_id = query.from_user.id
    player = player_manager.get_player(user_id)
    text = f"🏪 <b>SHOP</b> 🏪\n\n💰 Coins: <b>{player['coins']}</b>\n\nSelect item:"
    keyboard = create_shop_keyboard(player['items'])
    await safe_edit_message(query, text, keyboard)

async def show_help_callback(query, context):
    text = ("❓ <b>HOW TO PLAY</b> ❓\n\n..." # Same help text as before
            "<b>⚡ COMMANDS:</b>\n"
            "/start, /play, /shop, /profile, /leaderboard, /daily, /tournament, /trade\n"
            "/logs (Admin), /botstats (Admin)")
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Menu", callback_data='menu_main')]])
    await safe_edit_message(query, text, keyboard)

async def show_tournament_menu(query, context):
    if not FEATURES['tournaments_enabled']: await query.answer("Tournaments disabled.", True); return
    text = "🏆 <b>TOURNAMENTS</b> 🏆"
    keyboard = create_tournament_menu_keyboard()
    await safe_edit_message(query, text, keyboard)

async def show_trade_menu(query, context):
    if not FEATURES['trading_enabled']: await query.answer("Trading disabled.", True); return
    text = "📈 <b>TRADING POST</b> 📈"
    keyboard = create_trade_menu_keyboard()
    await safe_edit_message(query, text, keyboard)

# --- LOBBY/GAME FUNCTIONS ---
async def create_game_lobby(query, context, mode: str):
    user_id = query.from_user.id
    chat_id = query.message.chat_id
    game_id = game_manager.create_game(mode, user_id, chat_id)
    context.chat_data['active_game'] = game_id
    game = game_manager.get_game(game_id)
    required = game_manager.get_required_players(mode)
    text = (f"🎮 <b>LOBBY CREATED</b> 🎮\n\n🆔 <code>{game_id}</code>\n🎯 <b>{mode.upper()}</b>\n👥 {len(game['players'])}/{required}\n"
            f"👑 Creator: {query.from_user.username or query.from_user.first_name}\n\nWaiting...")
    keyboard = create_lobby_keyboard(game_id, is_creator=True)
    await safe_edit_message(query, text, keyboard)

async def join_game_action(query, context, game_id: str, user_id: int, username: str):
    success, message = game_manager.join_game(game_id, user_id, username)
    if success:
        await query.answer("✅ Joined!")
        game = game_manager.get_game(game_id)
        required = game_manager.get_required_players(game['mode'])
        text = (f"🎮 <b>LOBBY</b> 🎮\n\n🆔 <code>{game_id}</code>\n🎯 <b>{game['mode'].upper()}</b>\n👥 {len(game['players'])}/{required}\n\nPlayers:\n")
        for i, player in enumerate(game['players'], 1): text += f"{'👑' if player['user_id'] == game['creator_id'] else '•'} {player['username']}\n"
        if len(game['players']) >= required: text += "\n🎉 Full! Ready!"
        keyboard = create_lobby_keyboard(game_id, is_creator=(user_id == game['creator_id']))
        await safe_edit_message(query, text, keyboard)
    else: await query.answer(f"❌ {message}", True)

async def start_game_action(query, context, game_id: str, user_id: int):
    success, message = game_manager.start_game(game_id, user_id)
    if not success: await query.answer(f"❌ {message}", True); return
    await query.answer("🚀 Starting!")
    game = game_manager.get_game(game_id)
    await send_animated_message(query.message, ANIMATION_SEQUENCES['game_start'], 1.5)
    for player in game['players']:
        role_desc = game_manager.get_role_description(player['role'])
        await send_role_reveal_animation(context, player['user_id'], player['role'], role_desc)
    await query.edit_message_text("🎮 Game Started! Check PMs!", reply_markup=None)
    await asyncio.sleep(2); await game_manager.start_round(game_id, query.message, context)

async def cancel_game_action(query, context, game_id: str, user_id: int):
    success, message = game_manager.cancel_game(game_id, user_id)
    if success: await query.answer("✅ Cancelled!"); await show_main_menu_callback(query, context)
    else: await query.answer(f"❌ {message}", True)

# --- SHOP ---
async def handle_purchase(query, context, item_id, user_id):
    player = player_manager.get_player(user_id)
    item_to_buy = next((item for item in SHOP_ITEMS if item['id'] == item_id), None)
    if not item_to_buy: await query.answer("❌ Not found!", True); return
    if player_manager.has_item(user_id, item_id): await query.answer("✅ Owned!", True); return
    if player['coins'] < item_to_buy['price']: await query.answer(f"❌ Need {item_to_buy['price']} coins.", True); return
    if player_manager.spend_coins(user_id, item_to_buy['price']):
        player_manager.add_item(user_id, item_to_buy)
        await query.answer(f"🎉 Bought: {item_to_buy['name']}", True); await show_shop(query, context)
    else: await query.answer("❌ Failed!", True)

# --- MISSIONS ---
# ... (All mission functions are unchanged from previous correct version)
async def show_missions_menu(query, context): await safe_edit_message(query, "🚀 SINGLE-PLAYER MISSIONS 🚀...", create_missions_menu_keyboard())
async def start_target_practice(query, context): context.user_data['mission_state'] = {'score': 0, 'round': 0}; await safe_edit_message(query, "🎯 Get ready...", None); await asyncio.sleep(2); await send_target_practice_round(query, context)
async def send_target_practice_round(query, context): state = context.user_data.get('mission_state'); score, round_num = state['score'], state['round']; if round_num >= 7: await end_target_practice(query, context); return; target = random.choice(['👥 Villager','👥 Villager','🔪 Mafia','💉 Doctor']); emoji = get_role_emoji(target.split(' ')[-1].lower()); state['current_target'] = target.split(' ')[-1]; state['round']+=1; text = f"SCORE:{score}|R:{round_num+1}/7\n{emoji}<b>{target}</b>{emoji}\nSHOOT?"; keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("💥", callback_data="shoot_Shoot"), InlineKeyboardButton("✋", callback_data="shoot_Hold")]]); await safe_edit_message(query, text, keyboard)
async def handle_target_practice(query, context, data): state = context.user_data.get('mission_state'); if not state or 'current_target' not in state: await safe_edit_message(query, "Expired.", InlineKeyboardMarkup([[InlineKeyboardButton("🔙", callback_data='menu_missions')]])); return; target, action = state['current_target'], data.split('_')[-1]; feedback = ""; if action=='Shoot': state['score'] += 100 if target=='Mafia' else -75; feedback = "💥 Hit!" if target=='Mafia' else "❌ Civilian!" else: state['score'] += 20 if target!='Mafia' else -50; feedback = "✅ Good!" if target!='Mafia' else "❌ Missed!"; await safe_edit_message(query, f"<b>{feedback}</b>\nNext...", None); await asyncio.sleep(1.5); await send_target_practice_round(query, context)
async def end_target_practice(query, context): state = context.user_data.pop('mission_state', None); if not state: return; user_id, score = query.from_user.id, state['score']; rewards = MISSION_REWARDS['target_practice']; xp, coin = rewards['xp']+(score//10), rewards['coins']+(score//5); if xp>0: player_manager.add_xp(user_id,xp); if coin>0: player_manager.add_coins(user_id, coin); text = f"🎯 DONE! Score:<b>{score}</b>\n💎{xp} XP\n🪙{coin} Coins"; keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data='menu_missions')]]); await safe_edit_message(query, text, keyboard)
async def start_detectives_case(query, context): await safe_edit_message(query, "🔍 Memorize...", None); await asyncio.sleep(2); roles = ['mafia','detective','doctor','villager']; sequence=[get_role_emoji(random.choice(roles)) for _ in range(4)]; seq_str=" ".join(sequence); context.user_data['mission_state']={'correct_answer':seq_str}; await query.edit_message_text(f"Memorize:\n<b>{seq_str}</b>\n(5s!)", parse_mode='HTML'); await asyncio.sleep(5); options=[seq_str]; for _ in range(3): fake=" ".join([get_role_emoji(random.choice(roles)) for _ in range(4)]); while fake in options: fake=" ".join([get_role_emoji(random.choice(roles)) for _ in range(4)]); options.append(fake); random.shuffle(options); buttons=[[InlineKeyboardButton(opt, callback_data=f"case_answer_{i}")] for i,opt in enumerate(options)]; context.user_data['mission_state']['options']=options; await safe_edit_message(query, "Sequence?", InlineKeyboardMarkup(buttons))
async def handle_detectives_case(query, context, data): state = context.user_data.pop('mission_state', None); if not state: await safe_edit_message(query, "Expired.", InlineKeyboardMarkup([[InlineKeyboardButton("🔙", callback_data='menu_missions')]])); return; correct, options = state['correct_answer'], state['options']; try: chosen=options[int(data.split('_')[-1])] except: await safe_edit_message(query, "Invalid.", InlineKeyboardMarkup([[InlineKeyboardButton("🔙", callback_data='menu_missions')]])); return; rewards, user_id = MISSION_REWARDS['detectives_case'], query.from_user.id; if chosen==correct: player_manager.add_xp(user_id,rewards['xp']); player_manager.add_coins(user_id,rewards['coins']); text=f"✅ Solved!\n💎{rewards['xp']} XP\n🪙{rewards['coins']} Coins" else: text=f"❌ Wrong!\nCorrect:\n{correct}"; keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data='menu_missions')]]); await safe_edit_message(query, text, keyboard)
async def start_doctors_dilemma(query, context): puzzles=[{"q":"P A:\"Villager\", P B:\"A lies\". Mafia lies. Who?", "a":"dilemma_answer_A", "options":[("A","dilemma_answer_A"),("B","dilemma_answer_B")]},{"q":"P1:Innocent, P2:Innocent. One is Godfather(lies). P1:\"Villager\", P2:\"One true\". Who GF?", "a":"dilemma_answer_B", "options":[("P1","dilemma_answer_A"),("P2","dilemma_answer_B")]}]; puzzle=random.choice(puzzles); context.user_data['mission_state']={'correct_answer': puzzle['a']}; buttons=[[InlineKeyboardButton(t,cb) for t,cb in puzzle['options']]]; await safe_edit_message(query, f"💉 Dilemma:\n{puzzle['q']}", InlineKeyboardMarkup(buttons))
async def handle_doctors_dilemma(query, context, data): state = context.user_data.pop('mission_state', None); if not state: await safe_edit_message(query, "Expired.", InlineKeyboardMarkup([[InlineKeyboardButton("🔙", callback_data='menu_missions')]])); return; correct, user_id, rewards = state['correct_answer'], query.from_user.id, MISSION_REWARDS['doctors_dilemma']; if data==correct: player_manager.add_xp(user_id,rewards['xp']); player_manager.add_coins(user_id,rewards['coins']); text=f"✅ Correct!\n💎{rewards['xp']} XP\n🪙{rewards['coins']} Coins" else: text="❌ Wrong!"; keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data='menu_missions')]]); await safe_edit_message(query, text, keyboard)
async def start_timed_disarm(query, context): context.user_data['mission_state']={'clicks':0,'end_time':asyncio.get_event_loop().time()+10.0}; text="💣 DISARM! (10s)"; keyboard=InlineKeyboardMarkup([[InlineKeyboardButton("CLICK!", callback_data="disarm_click_0")]]); await safe_edit_message(query, text, keyboard)
async def handle_timed_disarm(query, context, data): state = context.user_data.get('mission_state'); if not state: await query.answer(); return; time_left = state['end_time']-asyncio.get_event_loop().time(); if time_left<=0: await query.answer("Time!"); user_id, clicks = query.from_user.id, state['clicks']; context.user_data.pop('mission_state', None); rewards = MISSION_REWARDS['timed_disarm']; xp, coin = rewards['xp']+(clicks*2), rewards['coins']+clicks; player_manager.add_xp(user_id,xp); player_manager.add_coins(user_id,coin); text=f"🎉 DISARMED! Clicks:<b>{clicks}</b>\n💎{xp} XP\n🪙{coin} Coins"; keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data='menu_missions')]]); await safe_edit_message(query, text, keyboard); return; state['clicks']+=1; await query.answer(f"{state['clicks']}"); if state['clicks']%5==0: new_text=f"💣 DISARM! ({time_left:.1f}s)\nClicks:<b>{state['clicks']}</b>"; new_kb=InlineKeyboardMarkup([[InlineKeyboardButton(f"CLICK! [{state['clicks']}]", callback_data=f"disarm_click_{state['clicks']}")]]); try: await query.edit_message_text(new_text, reply_markup=new_kb) except: pass
async def start_mafia_heist(query, context): text="💰 HEIST: Bank entrance. Guard away."; buttons=[[InlineKeyboardButton("🚪 Sneak", callback_data="heist_sneak")],[InlineKeyboardButton("🥊 Distract", callback_data="heist_distract")]]; await safe_edit_message(query, text, InlineKeyboardMarkup(buttons))
async def handle_mafia_heist(query, context, data): user_id = query.from_user.id; if data in ['heist_sneak','heist_distract']: text = "At vault. Code or drill?"; buttons=[[InlineKeyboardButton("💻 Hack", callback_data="heist_hack")],[InlineKeyboardButton("🛠️ Drill", callback_data="heist_drill")]]; await safe_edit_message(query, text, InlineKeyboardMarkup(buttons)) elif data=='heist_hack': text="In! Loot! ...Click. Gun. Boss! Set up!"; rewards=MISSION_REWARDS['mafia_heist_fail']; player_manager.add_xp(user_id,rewards['xp']); player_manager.add_coins(user_id,rewards['coins']); end_text=f"{text}\n💔 FAILED\n💎{rewards['xp']} XP\n🪙{rewards['coins']} Coins"; keyboard=InlineKeyboardMarkup([[InlineKeyboardButton("🔙", callback_data='menu_missions')]]); await safe_edit_message(query, end_text, keyboard) elif data=='heist_drill': text="Loud! Open! Loot! Alarms! Escape!"; rewards=MISSION_REWARDS['mafia_heist_success']; player_manager.add_xp(user_id,rewards['xp']); player_manager.add_coins(user_id,rewards['coins']); end_text=f"{text}\n🎉 SUCCESS!\n💎{rewards['xp']} XP\n🪙{rewards['coins']} Coins"; keyboard=InlineKeyboardMarkup([[InlineKeyboardButton("🔙", callback_data='menu_missions')]]); await safe_edit_message(query, end_text, keyboard)

# --- TOURNAMENT FUNCTIONS ---
async def create_new_tournament(query, context): await query.answer("Coming soon!", True)
async def list_tournaments(query, context): tournaments=tournament_system.tournaments; text="🏆 Tournaments 🏆\n"; buttons=[]; reg_open=False; for t_id,t in tournaments.items(): if t['status']=='registration': text+=f"•<b>{t['name']}</b> ({len(t['participants'])}/{t['max_players']}) Fee:{t['entry_fee']}\n"; buttons.append([InlineKeyboardButton(f"View:{t['name']}", callback_data=f"tourn_view_{t_id}")]); reg_open=True; if not reg_open: text+="None open."; buttons.append([InlineKeyboardButton("🔙 Back", callback_data='menu_tournament')]); await safe_edit_message(query, text, InlineKeyboardMarkup(buttons))
async def show_tournament_details(query, context, tournament_id): t=tournament_system.get_tournament(tournament_id); if not t: await query.answer("Not found!", True); return; text=tournament_system.format_tournament_info(tournament_id); buttons=[]; if t['status']=='registration': buttons.append([InlineKeyboardButton("✍️ Register", callback_data=f"tourn_register_{t_id}")]); if t['status'] in ['in_progress','finished']: buttons.append([InlineKeyboardButton("📊 Brackets", callback_data=f"tourn_brackets_{t_id}")]); buttons.append([InlineKeyboardButton("🔙 List", callback_data='tourn_list')]); await safe_edit_message(query, text, InlineKeyboardMarkup(buttons))
async def register_for_tournament(query, context, tournament_id): user_id, username = query.from_user.id, query.from_user.username or query.from_user.first_name; success, msg = tournament_system.register_player(tournament_id, user_id, username); await query.answer(msg, True); if success: await list_tournaments(query, context)
async def start_tournament_handler(query, context, tournament_id): success, msg = tournament_system.start_tournament(tournament_id); await query.answer(msg, True); if success: await show_tournament_details(query, context, tournament_id)
async def show_tournament_brackets(query, context, tournament_id): text=tournament_system.format_tournament_brackets(tournament_id); keyboard=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Details", callback_data=f"tourn_view_{tournament_id}")]]); await safe_edit_message(query, text, keyboard)

# --- TRADE FUNCTIONS ---
async def start_create_trade(query, context): context.user_data['state']='awaiting_trade_partner'; context.user_data['trade_setup']={'sender_id':query.from_user.id}; await safe_edit_message(query, "Who to trade with? Reply @username.", InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data='menu_trade')]]))
async def handle_trade_partner_input(update:Update, context:ContextTypes.DEFAULT_TYPE): partner_username=update.message.text.strip().lstrip('@'); partner=player_manager.get_player_by_username(partner_username); if not partner: await update.message.reply_text("❌ Not found. Try again or /cancel."); return; if partner['user_id']==context.user_data['trade_setup']['sender_id']: await update.message.reply_text("❌ Cannot trade yourself. Try again or /cancel."); return; context.user_data['trade_setup']['receiver_id']=partner['user_id']; context.user_data['trade_setup']['receiver_username']=partner['username']; context.user_data['state']='awaiting_trade_offer_coins'; await update.message.reply_text(f"Trade with {partner['username']}.\nCoins to OFFER? (0 if none)")
async def handle_trade_offer_coins_input(update:Update, context:ContextTypes.DEFAULT_TYPE): try: coins=int(update.message.text.strip()); if coins<0: raise ValueError(); sender=player_manager.get_player(context.user_data['trade_setup']['sender_id']); if sender['coins']<coins: await update.message.reply_text(f"❌ Only have {sender['coins']}. Enter less or 0."); return; context.user_data['trade_setup']['offer_coins']=coins; context.user_data['state']='awaiting_trade_offer_items'; await update.message.reply_text(f"Offer {coins} coins.\nItems to OFFER? ('none' or IDs like 'skin_golden,emote_pack_1')") except ValueError: await update.message.reply_text("❌ Invalid number. Enter 0 or more.")
# ... (rest of trade implementation needed)
async def list_active_trades(query, context): await query.answer("Coming soon!", True)
async def accept_trade_offer(query, context, trade_id): user_id=query.from_user.id; success, msg=trading_system.accept_trade(trade_id, user_id); await query.answer(msg, True); if success: await show_trade_menu(query, context)
async def cancel_trade_offer(query, context, trade_id): user_id=query.from_user.id; success, msg=trading_system.cancel_trade(trade_id, user_id); await query.answer(msg, True); if success: await show_trade_menu(query, context)

# --- ADMIN AND ERROR HANDLERS ---
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Log Errors and notify user."""
    logger.error(msg="Exception while handling an update:", exc_info=context.error)
    try:
        if update and update.callback_query:
             await update.callback_query.answer("⚠️ Error occurred!", show_alert=True)
        # Add sending message to admin maybe?
    except Exception as e:
        logger.error(f"Exception in error handler itself: {e}")

async def get_logs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS: return await update.message.reply_text("❌ Unauthorized.")
    log_file = 'nohup.out'
    if os.path.exists(log_file):
        try: await context.bot.send_document(chat_id=user_id, document=InputFile(log_file, filename='bot_logs.txt'))
        except Exception as e: await update.message.reply_text(f"❌ Failed: {e}")
    else: await update.message.reply_text("❌ `nohup.out` not found.")

async def get_bot_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS: return await update.message.reply_text("❌ Unauthorized.")
    total_users = len(player_manager.players)
    active_games = sum(1 for g in game_manager.games.values() if g['status'] == 'in_progress')
    text = (f"📊 <b>STATS</b> 📊\n👥 Users: {total_users}\n🎮 Active Games: {active_games}")
    await update.message.reply_text(text, parse_mode='HTML')


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
    # application.add_handler(CommandHandler("broadcast", broadcast_message)) # Add back if needed

    # Callback Handler
    application.add_handler(CallbackQueryHandler(handle_callback_query))

    # Message Handler
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # --- FIX: Use add_error_handler ---
    application.add_error_handler(error_handler)
    # ----------------------------------

    logger.info("🎭 Mafia RPG Bot is starting (Inline Mode)...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
