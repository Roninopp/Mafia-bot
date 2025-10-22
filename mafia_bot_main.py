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
            "This city runs on deals & danger. Ready to play?\n\n"
            "👥 <b>Games:</b> 5v5 & 1v1 battles.\n"
            "🚀 <b>Missions:</b> Solo challenges.\n"
            "🏆 <b>Rep:</b> Level up & get rich.\n"
            "⚔️ <b>Tournaments:</b> Compete!\n"
            "📈 <b>Trade:</b> Exchange loot."
        )
        keyboard = create_main_menu_keyboard(is_private=True)
        try:
            await context.bot.send_photo(chat_id=chat.id, photo=MAFIA_PIC_URL)
        except Exception as e:
            logger.error(f"Failed start photo: {e}.")
        await context.bot.send_message(chat_id=chat.id, text=welcome_text, parse_mode='HTML', reply_markup=keyboard)
    else:
        welcome_text = (f"🎭 <b>MAFIA RPG</b> 🎭\n\n🔥 Welcome, {user.first_name}! Use /play to start.")
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🎮 Play (in PM)", url=f"https://t.me/{BOT_USERNAME}?start=play")]])
        await update.message.reply_text(welcome_text, parse_mode='HTML', reply_markup=keyboard)


# --- COMMAND HANDLERS ---
async def play_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎮 Choose Mode:", reply_markup=create_play_menu_keyboard())

async def shop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    player = player_manager.get_player(update.effective_user.id)
    if not player: await update.message.reply_text("/start first."); return
    text = f"🏪 SHOP | 💰 Coins: <b>{player['coins']}</b>"
    keyboard = create_shop_keyboard(player['items'])
    await update.message.reply_text(text, parse_mode='HTML', reply_markup=keyboard)

async def profile_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    player = player_manager.get_player(update.effective_user.id)
    if not player: await update.message.reply_text("/start first."); return
    await update.message.reply_text(format_player_stats(player), parse_mode='HTML')

async def leaderboard_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    top = player_manager.get_leaderboard(10); text = "🏆 TOP PLAYERS 🏆\n\n"
    if not top: text += "None yet!"
    else: text += "\n".join(format_leaderboard_entry(i, p) for i, p in enumerate(top, 1))
    await update.message.reply_text(text, parse_mode='HTML')

async def daily_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    success, reward = player_manager.claim_daily_reward(update.effective_user.id)
    if success: text = f"🎉 DAILY REWARD! 🎉\n💎{reward['xp']} XP\n🪙{reward['coins']} Coins\n🔥Streak: {reward['streak']}"
    else: text = "⏰ Already Claimed!"
    await update.message.reply_text(text, parse_mode='HTML')

async def tournament_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not FEATURES['tournaments_enabled']: await update.message.reply_text("Tournaments off."); return
    await update.message.reply_text("🏆 TOURNAMENTS 🏆", reply_markup=create_tournament_menu_keyboard())

async def trade_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not FEATURES['trading_enabled']: await update.message.reply_text("Trading off."); return
    await update.message.reply_text("📈 TRADING POST 📈", reply_markup=create_trade_menu_keyboard())

async def help_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = ("❓ HELP ❓\n\nBasic Mafia rules apply.\n\n"
            "⚡ COMMANDS:\n/start /play /shop /profile\n/leaderboard /daily\n/tournament /trade\n"
            "/logs (Admin) /botstats (Admin)")
    await update.message.reply_text(text, parse_mode='HTML')


# --- Message Handler ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text, user_id = update.message.text, update.effective_user.id
    username = update.effective_user.username or update.effective_user.first_name
    player_manager.register_player(user_id, username)
    if context.user_data.get('state') == 'awaiting_trade_partner': await handle_trade_partner_input(update, context); return
    if context.user_data.get('state') == 'awaiting_trade_offer_coins': await handle_trade_offer_coins_input(update, context); return
    if any(e in text for e in ['🔪','🔍','💉']): await game_manager.handle_action(update, context); return
    if any(e in text for e in ['🗳️','Vote:','⏭️']): await game_manager.handle_vote(update, context); return
    if update.effective_chat.type == 'private': await update.message.reply_text("Use commands or buttons.")


# --- Callback Query Handler ---
async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query or not query.message: return
    try: await query.answer()
    except BadRequest as e:
        if "query is too old" in str(e).lower(): return
        logger.error(f"Err answering query: {e}"); return

    data, user_id = query.data, query.from_user.id
    username = query.from_user.username or query.from_user.first_name
    logger.info(f"Callback: data='{data}', user={user_id}")

    if not data.startswith(('mission_','shoot_','case_','dilemma_','disarm_','heist_','trade_','tourn_')):
        context.user_data.pop('mission_state', None); context.user_data.pop('trade_setup', None); context.user_data.pop('state', None)

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
        elif data == 'mode_5v5': await create_game_lobby(query, context, '5v5')
        elif data == 'mode_1v1': await create_game_lobby(query, context, '1v1')
        elif data == 'menu_missions': await show_missions_menu(query, context)
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
        else: logger.warning(f"Unhandled callback: {data}"); await query.answer("?", True)
    except Exception as e:
        logger.error(f"Err handling '{data}' for {user_id}: {e}", exc_info=True)
        await query.answer("⚠️ Error! Check logs.", True)


# --- MENU DISPLAY FUNCTIONS ---
async def safe_edit_message(query, text, keyboard):
    if not query or not query.message: logger.warning("safe_edit: invalid query."); return
    try: await query.edit_message_text(text, parse_mode='HTML', reply_markup=keyboard)
    except BadRequest as e:
        if "message is not modified" not in str(e).lower(): logger.error(f"Edit fail (BadRequest): {e}")
    except Exception as e: logger.error(f"Edit fail: {e}")

async def show_main_menu_callback(query, context):
    user = query.from_user; text = f"🚬 Welcome back, {user.first_name}.\n\nWhat's the move?"
    keyboard = create_main_menu_keyboard(is_private=True)
    await safe_edit_message(query, text, keyboard)

async def show_play_menu(query, context):
    await safe_edit_message(query, "🎮 Choose Mode:", create_play_menu_keyboard())

async def show_profile(query, context):
    player = player_manager.get_player(query.from_user.id)
    if not player: await safe_edit_message(query, "❌ /start first.", None); return
    text = format_player_stats(player)
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Menu", callback_data='menu_main')]])
    await safe_edit_message(query, text, keyboard)

# --- FIX: Use safe_edit_message for leaderboard ---
async def show_leaderboard(query, context):
    top = player_manager.get_leaderboard(10); text = "🏆 TOP PLAYERS 🏆\n\n"
    if not top: text += "None yet!"
    else: text += "\n".join(format_leaderboard_entry(i, p) for i, p in enumerate(top, 1))
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Menu", callback_data='menu_main')]])
    await safe_edit_message(query, text, keyboard) # Use safe edit here
# -----------------------------------------------

async def claim_daily_reward(query, context):
    success, reward = player_manager.claim_daily_reward(query.from_user.id)
    if success: text = f"🎉 DAILY! 🎉\n💎{reward['xp']} XP\n🪙{reward['coins']} Coins\n🔥Streak: {reward['streak']}"
    else: text = "⏰ Claimed!"
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Menu", callback_data='menu_main')]])
    await safe_edit_message(query, text, keyboard)

async def show_shop(query, context):
    player = player_manager.get_player(query.from_user.id)
    text = f"🏪 SHOP | 💰 Coins: <b>{player['coins']}</b>"
    keyboard = create_shop_keyboard(player['items'])
    await safe_edit_message(query, text, keyboard)

async def show_help_callback(query, context):
    text = ("❓ HELP ❓\n\nBasics: Mafia kill night, Town votes day.\n\n"
            "⚡ COMMANDS:\n/start /play /shop /profile\n/leaderboard /daily\n/tournament /trade\n"
            "/logs (A) /botstats (A)")
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Menu", callback_data='menu_main')]])
    await safe_edit_message(query, text, keyboard)

async def show_tournament_menu(query, context):
    if not FEATURES['tournaments_enabled']: await query.answer("Off.", True); return
    await safe_edit_message(query, "🏆 TOURNAMENTS 🏆", create_tournament_menu_keyboard())

async def show_trade_menu(query, context):
    if not FEATURES['trading_enabled']: await query.answer("Off.", True); return
    await safe_edit_message(query, "📈 TRADING POST 📈", create_trade_menu_keyboard())

# --- LOBBY/GAME ---
async def create_game_lobby(query, context, mode: str):
    user_id, chat_id = query.from_user.id, query.message.chat_id
    game_id = game_manager.create_game(mode, user_id, chat_id)
    context.chat_data['active_game'] = game_id
    game = game_manager.get_game(game_id)
    req = game_manager.get_required_players(mode)
    text = (f"🎮 LOBBY <code>{game_id}</code> | <b>{mode.upper()}</b>\n"
            f"👥 {len(game['players'])}/{req} | 👑 {query.from_user.username or query.from_user.first_name}\nWaiting...")
    keyboard = create_lobby_keyboard(game_id, is_creator=True)
    await safe_edit_message(query, text, keyboard)

async def join_game_action(query, context, game_id: str, user_id: int, username: str):
    success, msg = game_manager.join_game(game_id, user_id, username)
    if success:
        await query.answer("✅ Joined!")
        game = game_manager.get_game(game_id); req = game_manager.get_required_players(game['mode'])
        text = f"🎮 LOBBY <code>{game_id}</code> | <b>{game['mode'].upper()}</b>\n👥 {len(game['players'])}/{req}\n\nPlayers:\n"
        text += "\n".join(f"{'👑' if p['user_id']==game['creator_id'] else '•'} {p['username']}" for p in game['players'])
        if len(game['players'])>=req: text+="\n🎉 Full!"
        keyboard = create_lobby_keyboard(game_id, is_creator=(user_id==game['creator_id']))
        await safe_edit_message(query, text, keyboard)
    else: await query.answer(f"❌ {msg}", True)

async def start_game_action(query, context, game_id: str, user_id: int):
    success, msg = game_manager.start_game(game_id, user_id)
    if not success: await query.answer(f"❌ {msg}", True); return
    await query.answer("🚀 Starting!")
    game = game_manager.get_game(game_id)
    await send_animated_message(query.message, ANIMATION_SEQUENCES['game_start'], 1.5)
    for p in game['players']:
        desc = game_manager.get_role_description(p['role'])
        await send_role_reveal_animation(context, p['user_id'], p['role'], desc)
    await query.edit_message_text("🎮 Game Started! Check PMs!", reply_markup=None, parse_mode='HTML') # Ensure HTML parse mode
    await asyncio.sleep(2); await game_manager.start_round(game_id, query.message, context)

async def cancel_game_action(query, context, game_id: str, user_id: int):
    success, msg = game_manager.cancel_game(game_id, user_id)
    if success: await query.answer("✅ Cancelled!"); await show_main_menu_callback(query, context)
    else: await query.answer(f"❌ {msg}", True)

# --- SHOP ---
async def handle_purchase(query, context, item_id, user_id):
    player = player_manager.get_player(user_id)
    item = next((i for i in SHOP_ITEMS if i['id'] == item_id), None)
    if not item: await query.answer("❌ Not found!", True); return
    if player_manager.has_item(user_id, item_id): await query.answer("✅ Owned!", True); return
    if player['coins'] < item['price']: await query.answer(f"❌ Need {item['price']} coins.", True); return
    if player_manager.spend_coins(user_id, item['price']):
        player_manager.add_item(user_id, item)
        await query.answer(f"🎉 Bought: {item['name']}", True); await show_shop(query, context)
    else: await query.answer("❌ Failed!", True)


# --- MISSIONS (Corrected Syntax) ---
async def show_missions_menu(query, context):
    text = "🚀 SINGLE-PLAYER MISSIONS 🚀\n\nChoose challenge:"
    keyboard = create_missions_menu_keyboard()
    await safe_edit_message(query, text, keyboard)

async def start_target_practice(query, context):
    context.user_data['mission_state'] = {'score': 0, 'round': 0}
    await safe_edit_message(query, "🎯 Target Practice\nGet ready...", None)
    await asyncio.sleep(2)
    await send_target_practice_round(query, context)

# --- FIX: Corrected SyntaxError Here ---
async def send_target_practice_round(query, context):
    state = context.user_data.get('mission_state')
    if not state: logger.warning("Target practice state missing!"); return

    score = state.get('score', 0)
    round_num = state.get('round', 0)

    if round_num >= 7:
        await end_target_practice(query, context)
        return

    target = random.choice(['👥 Villager','👥 Villager','🔪 Mafia','💉 Doctor'])
    emoji = get_role_emoji(target.split(' ')[-1].lower())
    state['current_target'] = target.split(' ')[-1]
    state['round'] = round_num + 1
    text = f"<b>SCORE:{score}</b>|R:{state['round']}/7\n{emoji}<b>{target}</b>{emoji}\nSHOOT?"
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("💥", callback_data="shoot_Shoot"),
        InlineKeyboardButton("✋", callback_data="shoot_Hold")
    ]])
    await safe_edit_message(query, text, keyboard)
# --------------------------------------

# --- FIX: Corrected SyntaxError Here ---
async def handle_target_practice(query, context, data):
    state = context.user_data.get('mission_state')
    if not state or 'current_target' not in state:
        await safe_edit_message(query, "Mission expired.", InlineKeyboardMarkup([[InlineKeyboardButton("🔙", callback_data='menu_missions')]])); return

    target = state.get('current_target')
    action = data.split('_')[-1]
    feedback = ""

    if action == 'Shoot':
        if target == 'Mafia':
            state['score'] = state.get('score', 0) + 100
            feedback = "💥 Hit!"
        else:
            state['score'] = state.get('score', 0) - 75
            feedback = "❌ Civilian!"
    elif action == 'Hold': # Ensure this is elif
        if target != 'Mafia':
            state['score'] = state.get('score', 0) + 20
            feedback = "✅ Good!"
        else:
            state['score'] = state.get('score', 0) - 50
            feedback = "❌ Missed!"

    await safe_edit_message(query, f"<b>{feedback}</b>\nNext...", None)
    await asyncio.sleep(1.5)
    await send_target_practice_round(query, context)
# --------------------------------------


# ... (rest of mission functions unchanged) ...
async def end_target_practice(query, context):
    state = context.user_data.pop('mission_state', None)
    if not state: return
    user_id, score = query.from_user.id, state.get('score', 0)
    rewards = MISSION_REWARDS['target_practice']
    xp, coin = rewards.get('xp', 0) + (score // 10), rewards.get('coins', 0) + (score // 5)
    if xp > 0: player_manager.add_xp(user_id, xp)
    if coin > 0: player_manager.add_coins(user_id, coin)
    text = f"🎯 DONE! Score:<b>{score}</b>\n💎{xp} XP\n🪙{coin} Coins"
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data='menu_missions')]])
    await safe_edit_message(query, text, keyboard)

async def start_detectives_case(query, context):
    await safe_edit_message(query, "🔍 Memorize...", None)
    await asyncio.sleep(2)
    roles = ['mafia','detective','doctor','villager']
    sequence = [get_role_emoji(random.choice(roles)) for _ in range(4)]
    seq_str = " ".join(sequence)
    context.user_data['mission_state'] = {'correct_answer': seq_str}
    await query.edit_message_text(f"Memorize:\n<b>{seq_str}</b>\n(5s!)", parse_mode='HTML')
    await asyncio.sleep(5)
    options = [seq_str]
    for _ in range(3):
        fake = " ".join([get_role_emoji(random.choice(roles)) for _ in range(4)])
        while fake in options: fake = " ".join([get_role_emoji(random.choice(roles)) for _ in range(4)])
        options.append(fake)
    random.shuffle(options)
    buttons = [[InlineKeyboardButton(opt, callback_data=f"case_answer_{i}")] for i,opt in enumerate(options)]
    context.user_data['mission_state']['options'] = options
    await safe_edit_message(query, "Sequence?", InlineKeyboardMarkup(buttons))

async def handle_detectives_case(query, context, data):
    state = context.user_data.pop('mission_state', None)
    if not state: await safe_edit_message(query, "Expired.", InlineKeyboardMarkup([[InlineKeyboardButton("🔙", callback_data='menu_missions')]])); return
    correct, options = state.get('correct_answer'), state.get('options')
    try: chosen = options[int(data.split('_')[-1])]
    except: await safe_edit_message(query, "Invalid.", InlineKeyboardMarkup([[InlineKeyboardButton("🔙", callback_data='menu_missions')]])); return
    rewards, user_id = MISSION_REWARDS['detectives_case'], query.from_user.id
    if chosen == correct:
        player_manager.add_xp(user_id, rewards['xp']); player_manager.add_coins(user_id, rewards['coins'])
        text = f"✅ Solved!\n💎{rewards['xp']} XP\n🪙{rewards['coins']} Coins"
    else: text = f"❌ Wrong!\nCorrect:\n{correct}"
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data='menu_missions')]])
    await safe_edit_message(query, text, keyboard)

async def start_doctors_dilemma(query, context):
    puzzles = [{"q":"P A:\"Villager\", P B:\"A lies\". Mafia lies. Who?", "a":"dilemma_answer_A", "options":[("A","dilemma_answer_A"),("B","dilemma_answer_B")]},
               {"q":"P1:Innocent, P2:Innocent. One is GF(lies). P1:\"Villager\", P2:\"One true\". Who GF?", "a":"dilemma_answer_B", "options":[("P1","dilemma_answer_A"),("P2","dilemma_answer_B")]}]
    puzzle = random.choice(puzzles)
    context.user_data['mission_state'] = {'correct_answer': puzzle['a']}
    buttons = [[InlineKeyboardButton(t,cb) for t,cb in puzzle['options']]]
    await safe_edit_message(query, f"💉 Dilemma:\n{puzzle['q']}", InlineKeyboardMarkup(buttons))

async def handle_doctors_dilemma(query, context, data):
    state = context.user_data.pop('mission_state', None)
    if not state: await safe_edit_message(query, "Expired.", InlineKeyboardMarkup([[InlineKeyboardButton("🔙", callback_data='menu_missions')]])); return
    correct, user_id, rewards = state.get('correct_answer'), query.from_user.id, MISSION_REWARDS['doctors_dilemma']
    if data == correct:
        player_manager.add_xp(user_id, rewards['xp']); player_manager.add_coins(user_id, rewards['coins'])
        text = f"✅ Correct!\n💎{rewards['xp']} XP\n🪙{rewards['coins']} Coins"
    else: text = "❌ Wrong!"
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data='menu_missions')]])
    await safe_edit_message(query, text, keyboard)

async def start_timed_disarm(query, context):
    context.user_data['mission_state'] = {'clicks':0, 'end_time':asyncio.get_event_loop().time()+10.0}
    text = "💣 DISARM! (10s)"
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("CLICK!", callback_data="disarm_click_0")]])
    await safe_edit_message(query, text, keyboard)

async def handle_timed_disarm(query, context, data):
    state = context.user_data.get('mission_state')
    if not state: await query.answer(); return
    time_left = state['end_time'] - asyncio.get_event_loop().time()
    if time_left <= 0:
        await query.answer("Time!")
        user_id, clicks = query.from_user.id, state.get('clicks', 0)
        context.user_data.pop('mission_state', None)
        rewards = MISSION_REWARDS['timed_disarm']
        xp = rewards.get('xp', 0) + (clicks * 2)
        coin = rewards.get('coins', 0) + clicks
        if xp > 0: player_manager.add_xp(user_id,xp)
        if coin > 0: player_manager.add_coins(user_id,coin)
        text = f"🎉 DISARMED! Clicks:<b>{clicks}</b>\n💎{xp} XP\n🪙{coin} Coins"
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data='menu_missions')]])
        await safe_edit_message(query, text, keyboard)
        return
    state['clicks'] += 1; await query.answer(f"{state['clicks']}")
    if state['clicks'] % 5 == 0:
        new_text = f"💣 DISARM! ({time_left:.1f}s)\nClicks:<b>{state['clicks']}</b>"
        new_kb = InlineKeyboardMarkup([[InlineKeyboardButton(f"CLICK! [{state['clicks']}]", callback_data=f"disarm_click_{state['clicks']}")]])
        try: await query.edit_message_text(new_text, reply_markup=new_kb)
        except: pass

async def start_mafia_heist(query, context):
    text = "💰 HEIST: Bank entrance. Guard away."
    buttons = [[InlineKeyboardButton("🚪 Sneak", callback_data="heist_sneak")],[InlineKeyboardButton("🥊 Distract", callback_data="heist_distract")]]
    await safe_edit_message(query, text, InlineKeyboardMarkup(buttons))

async def handle_mafia_heist(query, context, data):
    user_id = query.from_user.id
    if data in ['heist_sneak','heist_distract']:
        text = "At vault. Code or drill?"
        buttons = [[InlineKeyboardButton("💻 Hack", callback_data="heist_hack")],[InlineKeyboardButton("🛠️ Drill", callback_data="heist_drill")]]
        await safe_edit_message(query, text, InlineKeyboardMarkup(buttons))
    elif data == 'heist_hack':
        text = "In! Loot! ...Click. Gun. Boss! Set up!"
        rewards = MISSION_REWARDS['mafia_heist_fail']
        player_manager.add_xp(user_id,rewards.get('xp',0)); player_manager.add_coins(user_id,rewards.get('coins',0))
        end_text = f"{text}\n💔 FAILED\n💎{rewards.get('xp',0)} XP\n🪙{rewards.get('coins',0)} Coins"
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙", callback_data='menu_missions')]])
        await safe_edit_message(query, end_text, keyboard)
    elif data == 'heist_drill':
        text = "Loud! Open! Loot! Alarms! Escape!"
        rewards = MISSION_REWARDS['mafia_heist_success']
        player_manager.add_xp(user_id,rewards.get('xp',0)); player_manager.add_coins(user_id,rewards.get('coins',0))
        end_text = f"{text}\n🎉 SUCCESS!\n💎{rewards.get('xp',0)} XP\n🪙{rewards.get('coins',0)} Coins"
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙", callback_data='menu_missions')]])
        await safe_edit_message(query, end_text, keyboard)


# --- TOURNAMENT/TRADE FUNCTIONS ---
# ... (Placeholders unchanged)
async def create_new_tournament(query, context): await query.answer("Coming soon!", True)
async def list_tournaments(query, context): await safe_edit_message(query, "No tournaments open.", InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data='menu_tournament')]]))
async def show_tournament_details(query, context, tournament_id): pass
async def register_for_tournament(query, context, tournament_id): pass
async def start_tournament_handler(query, context, tournament_id): pass
async def show_tournament_brackets(query, context, tournament_id): pass
async def start_create_trade(query, context): await safe_edit_message(query, "Trade creation coming soon.", InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data='menu_trade')]]))
async def handle_trade_partner_input(update: Update, context: ContextTypes.DEFAULT_TYPE): pass
async def handle_trade_offer_coins_input(update: Update, context: ContextTypes.DEFAULT_TYPE): pass
async def list_active_trades(query, context): await query.answer("Coming soon!", True)
async def accept_trade_offer(query, context, trade_id): pass
async def cancel_trade_offer(query, context, trade_id): pass


# --- ADMIN AND ERROR HANDLERS ---
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Log Errors and notify user."""
    logger.error(msg="Exception while handling an update:", exc_info=context.error)
    try:
        if update and update.callback_query: await update.callback_query.answer("⚠️ Error occurred!", show_alert=True)
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
    application.add_handler(CommandHandler("help", help_command_handler))
    application.add_handler(CommandHandler("tournament", tournament_command))
    application.add_handler(CommandHandler("trade", trade_command))

    # Admin Commands
    application.add_handler(CommandHandler("logs", get_logs))
    application.add_handler(CommandHandler("botstats", get_bot_stats))

    # Callback Handler
    application.add_handler(CallbackQueryHandler(handle_callback_query))

    # Message Handler
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # --- FIX: Correct method to add the error handler ---
    application.add_error_handler(error_handler)
    # ----------------------------------------------------

    logger.info("🎭 Mafia RPG Bot is starting (Inline Mode)...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


# --- FIX: Corrected duplicate main() call ---
if __name__ == '__main__':
    main()
# ------------------------------------------
