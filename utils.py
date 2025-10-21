"""
Utility Functions for Mafia RPG Bot
"""

import asyncio
import logging
from datetime import datetime, timedelta
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from config import EMOJIS, LOADING_FRAMES, ANIMATION_SEQUENCES, SHOP_ITEMS

logger = logging.getLogger(__name__)

# --- INLINE KEYBOARD FUNCTIONS ---

def create_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Creates the main menu inline keyboard."""
    keyboard = [
        [
            InlineKeyboardButton("🎮 Play", callback_data='menu_play'),
            InlineKeyboardButton("👤 My Profile", callback_data='menu_profile')
        ],
        [
            InlineKeyboardButton("🏆 Leaderboard", callback_data='menu_leaderboard'),
            InlineKeyboardButton("🎁 Daily Reward", callback_data='menu_daily')
        ],
        [
            InlineKeyboardButton("🏪 Shop", callback_data='menu_shop'),
            InlineKeyboardButton("❓ Help", callback_data='menu_help')
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def create_game_mode_keyboard() -> InlineKeyboardMarkup:
    """Creates the game mode selection inline keyboard."""
    keyboard = [
        [InlineKeyboardButton("⚔️ 5v5 Classic", callback_data='mode_5v5')],
        [InlineKeyboardButton("🎯 1v1 Duel", callback_data='mode_1v1')],
        [InlineKeyboardButton("🚀 Missions (Single Player)", callback_data='mode_missions')],
        [InlineKeyboardButton("🔙 Back to Menu", callback_data='menu_main')]
    ]
    return InlineKeyboardMarkup(keyboard)

def create_shop_keyboard(player_items: list) -> InlineKeyboardMarkup:
    """Creates the inline shop keyboard."""
    keyboard = []
    player_item_ids = [item['id'] for item in player_items]
    
    for item in SHOP_ITEMS:
        if item['id'] not in player_item_ids:
            # Player doesn't own it, show buy button
            btn_text = f"💰 Buy: {item['name']} ({item['price']})"
            callback = f"buy_item_{item['id']}"
            keyboard.append([InlineKeyboardButton(btn_text, callback_data=callback)])
        else:
            # Player owns it
            keyboard.append([InlineKeyboardButton(f"✅ {item['name']} (Owned)", callback_data="none")])
        
    keyboard.append([InlineKeyboardButton("🔙 Back to Menu", callback_data='menu_main')])
    return InlineKeyboardMarkup(keyboard)

def create_lobby_keyboard(game_id: str, is_creator: bool = False) -> InlineKeyboardMarkup:
    """Create game lobby inline keyboard"""
    keyboard = [
        [InlineKeyboardButton("✅ Join Game", callback_data=f"join_game_{game_id}")]
    ]
    
    if is_creator:
        keyboard.append(
            [InlineKeyboardButton("🚀 Start Game", callback_data=f"start_game_{game_id}")]
        )
    
    keyboard.append(
        [InlineKeyboardButton("❌ Cancel Game", callback_data=f"cancel_game_{game_id}")]
    )
    return InlineKeyboardMarkup(keyboard)

def create_missions_menu_keyboard() -> InlineKeyboardMarkup:
    """Creates the missions menu inline keyboard."""
    keyboard = [
        [InlineKeyboardButton("🎯 Target Practice", callback_data='mission_target')],
        [InlineKeyboardButton("🔍 Detective's Case", callback_data='mission_case')],
        [InlineKeyboardButton("💉 Doctor's Dilemma", callback_data='mission_dilemma')],
        [InlineKeyboardButton("💣 Timed Disarm", callback_data='mission_disarm')],
        [InlineKeyboardButton("💰 Mafia Heist", callback_data='mission_heist')],
        [InlineKeyboardButton("🔙 Back to Play Menu", callback_data='menu_play')]
    ]
    return InlineKeyboardMarkup(keyboard)

# --- REPLY KEYBOARD FUNCTIONS (FOR IN-GAME ACTIONS) ---

def create_voting_keyboard(players: list) -> ReplyKeyboardMarkup:
    """Create voting keyboard for day phase (REPLY KEYBOARD)"""
    keyboard = []
    row = []
    for player in players:
        if player['alive']:
            row.append(KeyboardButton(f"🗳️ Vote: {player['username']}"))
            if len(row) == 2:
                keyboard.append(row)
                row = []
    if row:
        keyboard.append(row)
    
    keyboard.append([KeyboardButton("⏭️ Skip Vote")])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

def create_player_action_keyboard(action: str, players: list) -> ReplyKeyboardMarkup:
    """Create keyboard for player actions (kill, investigate, protect) (REPLY KEYBOARD)"""
    keyboard = []
    
    action_emoji = {
        'kill': '🔪',
        'investigate': '🔍',
        'protect': '💉'
    }
    emoji = action_emoji.get(action, '⚡')
    
    row = []
    for player in players:
        if player['alive']:
            row.append(KeyboardButton(f"{emoji} {player['username']}"))
            if len(row) == 2:
                keyboard.append(row)
                row = []
    if row:
        keyboard.append(row)
    
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)


# --- FORMATTING AND ANIMATION FUNCTIONS (Unchanged) ---

def format_player_stats(player: dict) -> str:
    if not player:
        return "❌ Player not found!"
    
    win_rate = (player['wins'] / player['games_played'] * 100) if player['games_played'] > 0 else 0
    rank = get_rank_title(player['level'])
    next_level_xp = calculate_xp_for_level(player['level'] + 1)
    xp_progress = (player['xp'] / next_level_xp) * 100 if next_level_xp > 0 else 0
    progress_bar = create_progress_bar(xp_progress)
    
    text = (
        f"👤 <b>{player['username']}</b>\n\n"
        f"🎖️ Rank: <b>{rank}</b>\n"
        f"⭐ Level: <b>{player['level']}</b>\n"
        f"💎 XP: {player['xp']}/{next_level_xp}\n"
        f"{progress_bar}\n\n"
        f"🪙 Coins: <b>{player['coins']}</b>\n"
        f"🎮 Games Played: <b>{player['games_played']}</b>\n"
        f"🏆 Wins: <b>{player['wins']}</b>\n"
        f"💔 Losses: <b>{player['losses']}</b>\n"
        f"📊 Win Rate: <b>{win_rate:.1f}%</b>\n"
    )
    
    if player.get('favorite_role'):
        text += f"🎭 Favorite Role: <b>{player['favorite_role'].upper()}</b>\n"
    if player.get('streak', 0) > 0:
        text += f"🔥 Daily Streak: <b>{player['streak']} days</b>\n"
    if player.get('achievements'):
        text += f"\n🏅 Achievements: <b>{len(player['achievements'])}</b>"
    
    return text


def create_progress_bar(percentage: float, length: int = 10) -> str:
    filled = int((percentage / 100) * length)
    empty = length - filled
    bar = "▰" * filled + "▱" * empty
    return f"[{bar}] {percentage:.0f}%"


def calculate_xp_for_level(level: int) -> int:
    return int(100 * (level ** 1.5))


async def send_animated_message(message, frames: list, delay: float = 1.0):
    sent_message = None
    try:
        for i, frame_text in enumerate(frames):
            if i == 0:
                sent_message = await message.reply_text(frame_text, parse_mode='HTML')
            else:
                await asyncio.sleep(delay)
                if sent_message:
                    await sent_message.edit_text(frame_text, parse_mode='HTML')
        return sent_message
    except Exception as e:
        logger.warning(f"Animation failed: {e}")
        return sent_message


def format_leaderboard_entry(rank: int, player: dict) -> str:
    medals = {1: "🥇", 2: "🥈", 3: "🥉"}
    rank_str = medals.get(rank, f"{rank}.")
    
    return (
        f"{rank_str} <b>{player['username']}</b>\n"
        f"   Level {player['level']} • {player['wins']} wins • {player['xp']} XP\n"
    )


def generate_game_id() -> str:
    import random
    import string
    timestamp = int(datetime.now().timestamp()) % 100000
    random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"G-{random_str}{timestamp}"


def check_game_end_condition(game: dict) -> tuple:
    from roles import RoleManager # Local import to avoid circular dependency
    role_manager = RoleManager()
    
    alive_players = [p for p in game['players'] if p['alive']]
    
    mafia_alive = sum(1 for p in alive_players if role_manager.get_role_team(p['role']) == 'mafia')
    villagers_alive = sum(1 for p in alive_players if role_manager.get_role_team(p['role']) == 'villagers')
    
    # --- REMOVED 1vBOSS LOGIC ---
    
    if mafia_alive == 0:
        return True, 'villagers'
    elif mafia_alive >= villagers_alive:
        return True, 'mafia'
    
    return False, None


def get_role_emoji(role: str) -> str:
    return EMOJIS['roles'].get(role, '❓')


def format_night_summary(eliminated: dict, protected_info: dict, investigated: dict = None) -> str:
    text = "🌙 <b>NIGHT SUMMARY</b> 🌙\n\n"
    
    if eliminated:
        text += f"☠️ {eliminated['username']} was eliminated!\n"
        text += f"They were a <b>{eliminated['role'].upper()}</b>\n\n"
    elif protected_info.get('protected'):
        text += "🛡️ Someone was attacked, but the Doctor saved them!\n\n"
    else:
        text += "🌟 A peaceful night. No casualties.\n\n"
    
    if investigated:
        text += f"🔍 Investigation complete (results sent privately)\n"
    
    return text


def format_day_summary(eliminated: dict, vote_count: int) -> str:
    text = "☀️ <b>DAY SUMMARY</b> ☀️\n\n"
    
    if eliminated:
        text += f"⚖️ The town has voted!\n\n"
        text += f"💀 {eliminated['username']} was eliminated!\n"
        text += f"They were a <b>{eliminated['role'].upper()}</b>\n"
        text += f"Votes received: {vote_count}\n"
    else:
        text += "🤝 No consensus reached. No one was eliminated.\n"
    
    return text


def get_rank_title(level: int) -> str:
    if level < 5: return "🌱 Rookie"
    elif level < 10: return "⚔️ Soldier"
    elif level < 20: return "🎖️ Warrior"
    elif level < 30: return "👑 Elite"
    elif level < 50: return "💎 Master"
    else: return "🏆 Legend"

def format_vote_results(game: dict, vote_counts: dict) -> str:
    """Format voting results"""
    text = "📊 <b>VOTING RESULTS</b>\n\n"
    
    if not vote_counts:
        text += "No votes were cast!\n"
        return text
    
    sorted_votes = sorted(vote_counts.items(), key=lambda x: x[1], reverse=True)
    
    for user_id, votes in sorted_votes:
        player_name = "Unknown"
        for player in game['players']:
            if player['user_id'] == user_id:
                player_name = player['username']
                break
        text += f"• {player_name}: {votes} vote(s)\n"
    
    return text

async def send_role_reveal_animation(context, user_id: int, role: str, description: str):
    frames = [
        "🤫 <b>Assigning your role...</b>",
        "🎭 <b>You are...</b>",
        f"<b>{get_role_emoji(role)} {role.upper()} {get_role_emoji(role)}</b>"
    ]
    try:
        msg = await context.bot.send_message(user_id, frames[0], parse_mode='HTML')
        for frame in frames[1:]:
            await asyncio.sleep(1.5)
            await msg.edit_text(frame, parse_mode='HTML')
        
        await asyncio.sleep(1)
        await msg.edit_text(description, parse_mode='HTML')
    except Exception as e:
        logger.warning(f"Failed to send role reveal to {user_id}: {e}")

async def send_elimination_animation(message, username: str, role: str):
    frames = [
        "⚖️ <b>The town has made its decision...</b>",
        f"🚶 <b>{username} steps forward...</b>",
        f"💀 <b>{username} has been eliminated!</b> 💀\n\nThey were a <b>{role.upper()}</b>!"
    ]
    await send_animated_message(message, frames, delay=1.5)

async def send_phase_transition(message, phase: str):
    if phase == 'night':
        frames = ANIMATION_SEQUENCES['night_phase']
    else:
        frames = ANIMATION_SEQUENCES['day_phase']
    await send_animated_message(message, frames, delay=1.2)

async def send_victory_animation(message, winner: str, winners: list):
    frames = ANIMATION_SEQUENCES['victory']
    winner_text = f"🏆 <b>THE {winner.upper()} TEAM WINS!</b> 🏆\n\n"
    winner_text += "<b>Victorious Players:</b>\n"
    for player in winners:
        winner_text += f"• {player['username']} ({player['role'].upper()})\n"
    
    frames.append(winner_text)
    await send_animated_message(message, frames, delay=1.5)
