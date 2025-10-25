"""
Utility Functions for Mafia RPG Bot
"""
import asyncio
import logging
from datetime import datetime, timedelta
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from config import EMOJIS, ANIMATION_SEQUENCES, BOT_USERNAME, SHOP_ITEMS

logger = logging.getLogger(__name__)

# --- INLINE KEYBOARD FUNCTIONS ---
def create_main_menu_keyboard(is_private: bool = False) -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("🎮 Play", callback_data='menu_play'), InlineKeyboardButton("👤 My Profile", callback_data='menu_profile')],
        [InlineKeyboardButton("🏆 Leaderboard", callback_data='menu_leaderboard'), InlineKeyboardButton("🎁 Daily Reward", callback_data='menu_daily')],
        [InlineKeyboardButton("🏪 Shop", callback_data='menu_shop'), InlineKeyboardButton("❓ Help", callback_data='menu_help')],
        [InlineKeyboardButton("⚔️ Tournaments", callback_data='menu_tournament'), InlineKeyboardButton("📈 Trading Post", callback_data='menu_trade')]
    ]
    if is_private:
        keyboard.append([InlineKeyboardButton("➕ LET'S CREATE GANG ➕", url=f"https://t.me/{BOT_USERNAME}?startgroup=true")])
    return InlineKeyboardMarkup(keyboard)

def create_play_menu_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("⚔️ 5v5 Classic", callback_data='mode_5v5')],
        [InlineKeyboardButton("🎯 1v1 Duel", callback_data='mode_1v1')],
        [InlineKeyboardButton("🚀 Missions", callback_data='menu_missions')],
        [InlineKeyboardButton("🌟 Events (Soon)", callback_data="none")],
        [InlineKeyboardButton("🔙 Back", callback_data='menu_main')]
    ]
    return InlineKeyboardMarkup(keyboard)

def create_shop_keyboard(player_items: list) -> InlineKeyboardMarkup:
    keyboard = []
    player_item_ids = [item.get('id') for item in player_items if item and item.get('id')] if player_items else []
    for item in SHOP_ITEMS:
        item_id = item.get('id')
        if not item_id: continue
        if item_id not in player_item_ids:
            btn_text = f"💰 Buy: {item.get('name','?')} ({item.get('price',0)})"
            callback = f"buy_item_{item_id}"
            keyboard.append([InlineKeyboardButton(btn_text, callback_data=callback)])
        else:
            keyboard.append([InlineKeyboardButton(f"✅ {item.get('name','?')} (Owned)", callback_data="none")])
    keyboard.append([InlineKeyboardButton("🔙 Back to Menu", callback_data='menu_main')])
    return InlineKeyboardMarkup(keyboard)

# --- create_lobby_keyboard is now in mafia_bot_main.py ---

def create_missions_menu_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("🎯 Target Practice", callback_data='mission_target_practice')],
        [InlineKeyboardButton("🔍 Detective's Case", callback_data='mission_detectives_case')],
        [InlineKeyboardButton("💉 Doctor's Dilemma", callback_data='mission_doctors_dilemma')],
        [InlineKeyboardButton("💣 Timed Disarm", callback_data='mission_timed_disarm')],
        [InlineKeyboardButton("💰 Mafia Heist", callback_data='mission_mafia_heist')],
        [InlineKeyboardButton("🔙 Back to Play Menu", callback_data='menu_play')]
    ]
    return InlineKeyboardMarkup(keyboard)

def create_tournament_menu_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("🏆 View Tournaments", callback_data='tourn_list')],
        [InlineKeyboardButton("🔙 Back to Menu", callback_data='menu_main')]
    ]
    return InlineKeyboardMarkup(keyboard)

def create_trade_menu_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("➕ Create Trade Offer", callback_data='trade_create')],
        [InlineKeyboardButton("📬 View My Offers", callback_data='trade_list')],
        [InlineKeyboardButton("🔙 Back to Menu", callback_data='menu_main')]
    ]
    return InlineKeyboardMarkup(keyboard)

# --- REPLY KEYBOARD FUNCTIONS (FOR IN-GAME ACTIONS) ---
def create_voting_keyboard(players: list) -> ReplyKeyboardMarkup:
    keyboard = []
    row = []
    for player in players:
        if player and player.get('alive'):
            username = player.get('username', 'Unknown')
            row.append(KeyboardButton(f"🗳️ Vote: {username}"))
            if len(row) == 2: keyboard.append(row); row = []
    if row: keyboard.append(row)
    keyboard.append([KeyboardButton("⏭️ Skip Vote")])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

def create_player_action_keyboard(action: str, players: list) -> ReplyKeyboardMarkup:
    keyboard = []
    action_emoji = {'kill': '🔪', 'investigate': '🔍', 'protect': '💉'}
    emoji = action_emoji.get(action, '⚡')
    row = []
    for player in players:
         if player and player.get('alive'):
            username = player.get('username', 'Unknown')
            row.append(KeyboardButton(f"{emoji} {username}"))
            if len(row) == 2: keyboard.append(row); row = []
    if row: keyboard.append(row)
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)


# --- FORMATTING AND ANIMATION FUNCTIONS ---
def format_player_stats(player: dict) -> str:
    if not player: return "❌ Player not found!"
    win_rate = (player.get('wins', 0) / player.get('games_played', 1)) * 100 if player.get('games_played', 0) > 0 else 0
    level = player.get('level', 1)
    rank = get_rank_title(level)
    next_level_xp = calculate_xp_for_level(level + 1)
    xp_progress = (player.get('xp', 0) / next_level_xp) * 100 if next_level_xp > 0 else 0
    progress_bar = create_progress_bar(xp_progress)
    text = (f"👤 <b>{player.get('username','Unknown')}</b>\n\n🎖️ Rank: <b>{rank}</b>\n⭐ Level: <b>{level}</b>\n"
            f"💎 XP: {player.get('xp', 0)}/{next_level_xp}\n{progress_bar}\n\n"
            f"🪙 Coins: <b>{player.get('coins', 0)}</b>\n🎮 Games Played: <b>{player.get('games_played', 0)}</b>\n"
            f"🏆 Wins: <b>{player.get('wins', 0)}</b>\n💔 Losses: <b>{player.get('losses', 0)}</b>\n📊 Win Rate: <b>{win_rate:.1f}%</b>\n")
    if player.get('favorite_role'): text += f"🎭 Favorite Role: <b>{player['favorite_role'].upper()}</b>\n"
    if player.get('streak', 0) > 0: text += f"🔥 Daily Streak: <b>{player['streak']} days</b>\n"
    if player.get('achievements'): text += f"\n🏅 Achievements: <b>{len(player['achievements'])}</b>"
    return text

def create_progress_bar(percentage: float, length: int = 10) -> str:
    filled = int((percentage / 100) * length); empty = length - filled
    bar = "▰" * filled + "▱" * empty; return f"[{bar}] {percentage:.0f}%"

def calculate_xp_for_level(level: int) -> int:
    if level <= 1: return 100 # XP needed for level 2
    return int(100 * (level ** 1.5))

async def send_animated_message(message, frames: list, delay: float = 1.0):
    sent_message = None
    try:
        for i, frame_text in enumerate(frames):
            if i == 0: sent_message = await message.reply_text(frame_text, parse_mode='HTML')
            elif sent_message: await asyncio.sleep(delay); await sent_message.edit_text(frame_text, parse_mode='HTML')
        return sent_message
    except Exception as e: logger.warning(f"Animation failed: {e}"); return sent_message

def format_leaderboard_entry(rank: int, player: dict) -> str:
    medals = {1: "🥇", 2: "🥈", 3: "🥉"}; rank_str = medals.get(rank, f"{rank}.")
    return f"{rank_str} <b>{player.get('username','Unknown')}</b>\n   Level {player.get('level', 1)} • {player.get('wins', 0)} wins • {player.get('xp', 0)} XP\n"

def generate_game_id() -> str:
    import random, string
    timestamp = int(datetime.now().timestamp()) % 100000
    random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"G-{random_str}{timestamp}"

def get_role_emoji(role: str) -> str: return EMOJIS.get('roles', {}).get(role, '❓')

def format_night_summary(eliminated: dict, protected_info: dict, investigated: dict = None) -> str:
    text = "🌙 <b>NIGHT SUMMARY</b> 🌙\n\n"
    if eliminated: text += f"☠️ {eliminated.get('username','?')} was eliminated! ({eliminated.get('role','?').upper()})\n\n"
    elif protected_info.get('protected'): text += "🛡️ Someone was attacked, but saved!\n\n"
    else: text += "🌟 A peaceful night. No casualties.\n\n"
    return text

def format_day_summary(eliminated: dict, vote_count: int) -> str:
    text = "☀️ <b>DAY SUMMARY</b> ☀️\n\n"
    if eliminated:
        text = f"⚖️ The town voted!\n\n💀 {eliminated.get('username','?')} was eliminated! ({eliminated.get('role','?').upper()})\nVotes: {vote_count}\n"
    else: text += "🤝 No consensus. No one was eliminated.\n"
    return text

def get_rank_title(level: int) -> str:
    if level < 5: return "🌱 Rookie"
    elif level < 10: return "⚔️ Soldier"
    elif level < 20: return "🎖️ Warrior"
    elif level < 30: return "👑 Elite"
    elif level < 50: return "💎 Master"
    else: return "🏆 Legend"

def format_vote_results(game: dict, vote_counts: dict) -> str:
    text = "📊 <b>VOTING RESULTS</b>\n\n";
    if not vote_counts: return text + "No votes cast!\n"
    sorted_votes = sorted(vote_counts.items(), key=lambda x: x[1], reverse=True)
    for user_id, votes in sorted_votes:
        player_name = next((p['username'] for p in game.get('players',[]) if p.get('user_id') == user_id), "Unknown")
        text += f"• {player_name}: {votes} vote(s)\n"
    return text

async def send_role_reveal_animation(context, user_id: int, role: str, description: str):
    frames = ["🤫 Assigning role...", "🎭 You are...", f"<b>{get_role_emoji(role)} {role.upper()} {get_role_emoji(role)}</b>"]
    try:
        msg = await context.bot.send_message(user_id, frames[0], parse_mode='HTML')
        for frame in frames[1:]: await asyncio.sleep(1.5); await msg.edit_text(frame, parse_mode='HTML')
        await asyncio.sleep(1); await msg.edit_text(description, parse_mode='HTML')
    except Exception as e: logger.warning(f"Failed role reveal to {user_id}: {e}")

async def send_elimination_animation(message, username: str, role: str):
    frames = ["⚖️ Decision made...", f"🚶 {username} steps forward...", f"💀 <b>{username}</b> eliminated! (<b>{role.upper()}</b>)"]
    await send_animated_message(message, frames, delay=1.5)

async def send_phase_transition(message, phase: str):
    frames = ANIMATION_SEQUENCES.get('night_phase' if phase == 'night' else 'day_phase', [])
    await send_animated_message(message, frames, delay=1.2)

async def send_victory_animation(message, winner: str, winners: list):
    frames = ANIMATION_SEQUENCES.get('victory', [])
    winner_text = f"🏆 <b>THE {winner.upper()} TEAM WINS!</b> 🏆\n\nVictorious:\n"
    winner_text += "\n".join(f"• {p.get('username','?')} ({p.get('role', '??').upper()})" for p in winners)
    frames.append(winner_text)
    await send_animated_message(message, frames, delay=1.5)
