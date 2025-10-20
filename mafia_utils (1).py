"""
Utility Functions for Mafia RPG Bot
"""

import asyncio
from datetime import datetime, timedelta
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from config import EMOJIS, LOADING_FRAMES


def format_player_stats(player: dict) -> str:
    """Format player statistics for display"""
    if not player:
        return "❌ Player not found!"
    
    win_rate = (player['wins'] / player['games_played'] * 100) if player['games_played'] > 0 else 0
    
    # Calculate rank
    level = player['level']
    if level < 5:
        rank = "🌱 Rookie"
    elif level < 10:
        rank = "⚔️ Soldier"
    elif level < 20:
        rank = "🎖️ Warrior"
    elif level < 30:
        rank = "👑 Elite"
    elif level < 50:
        rank = "💎 Master"
    else:
        rank = "🏆 Legend"
    
    # Next level XP requirement
    next_level_xp = calculate_xp_for_level(level + 1)
    xp_progress = (player['xp'] / next_level_xp) * 100
    
    # Progress bar
    progress_bar = create_progress_bar(xp_progress)
    
    text = (
        f"👤 <b>{player['username']}</b>\n\n"
        f"🎖️ Rank: <b>{rank}</b>\n"
        f"⭐ Level: <b>{level}</b>\n"
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
    """Create a visual progress bar"""
    filled = int((percentage / 100) * length)
    empty = length - filled
    
    bar = "▰" * filled + "▱" * empty
    return f"[{bar}] {percentage:.0f}%"


def calculate_xp_for_level(level: int) -> int:
    """Calculate XP required for a specific level"""
    return int(100 * (level ** 1.5))


def format_time_remaining(seconds: int) -> str:
    """Format seconds into readable time"""
    if seconds >= 60:
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes}m {secs}s"
    return f"{seconds}s"


def create_game_keyboard(game_id: str, is_creator: bool = False) -> InlineKeyboardMarkup:
    """Create game lobby keyboard"""
    keyboard = [
        [InlineKeyboardButton("✅ Join Game", callback_data=f"join_{game_id}")]
    ]
    
    if is_creator:
        keyboard.append([
            InlineKeyboardButton("🚀 Start Game", callback_data=f"start_{game_id}"),
            InlineKeyboardButton("❌ Cancel", callback_data=f"cancel_{game_id}")
        ])
    
    return InlineKeyboardMarkup(keyboard)


async def send_animated_message(message, frames: list, delay: float = 1.0):
    """Send animated message with multiple frames"""
    sent_message = None
    for i, frame_text in enumerate(frames):
        if i == 0:
            sent_message = await message.reply_text(frame_text, parse_mode='HTML')
        else:
            await asyncio.sleep(delay)
            try:
                await sent_message.edit_text(frame_text, parse_mode='HTML')
            except:
                pass
    
    return sent_message


async def send_loading_animation(message, final_text: str):
    """Send loading animation"""
    loading_text = "⏳ Loading"
    
    for frame in LOADING_FRAMES:
        try:
            await message.edit_text(f"{loading_text} {frame}", parse_mode='HTML')
            await asyncio.sleep(0.3)
        except:
            pass
    
    try:
        await message.edit_text(final_text, parse_mode='HTML')
    except:
        pass


def format_game_summary(game: dict) -> str:
    """Format game summary"""
    alive_count = sum(1 for p in game['players'] if p['alive'])
    dead_count = len(game['players']) - alive_count
    
    text = (
        f"🎮 <b>GAME STATUS</b>\n\n"
        f"🆔 Game ID: <code>{game['id']}</code>\n"
        f"🎯 Mode: <b>{game['mode'].upper()}</b>\n"
        f"🔄 Round: <b>{game['round']}</b>\n"
        f"🌓 Phase: <b>{game['phase'].upper()}</b>\n\n"
        f"👥 Players:\n"
        f"   ✅ Alive: {alive_count}\n"
        f"   💀 Dead: {dead_count}\n\n"
    )
    
    return text


def format_role_list(game: dict, show_roles: bool = False) -> str:
    """Format list of players with optional roles"""
    text = "<b>Players:</b>\n"
    
    for i, player in enumerate(game['players'], 1):
        status = "✅" if player['alive'] else "💀"
        role_text = f" ({player['role'].upper()})" if show_roles and not player['alive'] else ""
        text += f"{i}. {status} {player['username']}{role_text}\n"
    
    return text


def get_role_emoji(role: str) -> str:
    """Get emoji for role"""
    return EMOJIS['roles'].get(role, '❓')


def get_action_emoji(action: str) -> str:
    """Get emoji for action"""
    return EMOJIS['actions'].get(action, '⚡')


def get_phase_emoji(phase: str) -> str:
    """Get emoji for game phase"""
    return EMOJIS['phases'].get(phase, '🎮')


def format_achievement(achievement: dict) -> str:
    """Format achievement for display"""
    text = (
        f"{achievement.get('icon', '🏆')} <b>{achievement['name']}</b>\n"
        f"   {achievement['description']}\n"
    )
    
    if 'reward' in achievement:
        text += f"   💰 Reward: {achievement['reward']} coins\n"
    
    return text


def format_mission(mission: dict) -> str:
    """Format mission for display"""
    status = "✅" if mission.get('completed') else "⏳"
    
    text = (
        f"{status} <b>{mission['name']}</b>\n"
        f"   {mission['description']}\n"
        f"   💎 Reward: {mission['reward_xp']} XP, {mission['reward_coins']} coins\n"
    )
    
    return text


def calculate_game_rewards(game: dict, player: dict) -> dict:
    """Calculate rewards for a player based on game results"""
    base_xp = 100
    base_coins = 50
    
    rewards = {
        'xp': base_xp,
        'coins': base_coins,
        'achievements': []
    }
    
    # Survival bonus
    if player['alive']:
        rewards['xp'] += 50
        rewards['coins'] += 25
    
    # Win bonus
    winner = game.get('winner')
    if winner:
        if (winner == 'villagers' and player['role'] != 'mafia') or \
           (winner == 'mafia' and player['role'] == 'mafia'):
            rewards['xp'] += 100
            rewards['coins'] += 50
    
    # Role bonus
    role_bonuses = {
        'mafia': 10,
        'detective': 15,
        'doctor': 10,
        'boss': 20,
        'villager': 5
    }
    
    rewards['xp'] += role_bonuses.get(player['role'], 0)
    
    # Round bonus
    rewards['xp'] += game['round'] * 5
    
    return rewards


def validate_username(username: str) -> bool:
    """Validate username"""
    if not username or len(username) < 3:
        return False
    if len(username) > 32:
        return False
    return True


def format_leaderboard_entry(rank: int, player: dict) -> str:
    """Format single leaderboard entry"""
    medals = {1: "🥇", 2: "🥈", 3: "🥉"}
    rank_str = medals.get(rank, f"{rank}.")
    
    return (
        f"{rank_str} <b>{player['username']}</b>\n"
        f"   Level {player['level']} • {player['wins']} wins • {player['xp']} XP\n"
    )


def get_time_until_daily_reset(last_claim: str) -> str:
    """Calculate time until daily reset"""
    if not last_claim:
        return "Available now!"
    
    last_claim_date = datetime.fromisoformat(last_claim)
    next_claim = last_claim_date + timedelta(days=1)
    now = datetime.now()
    
    if now >= next_claim:
        return "Available now!"
    
    time_diff = next_claim - now
    hours = time_diff.seconds // 3600
    minutes = (time_diff.seconds % 3600) // 60
    
    return f"{hours}h {minutes}m"


def create_voting_keyboard(game: dict) -> InlineKeyboardMarkup:
    """Create voting keyboard for day phase"""
    keyboard = []
    
    for player in game['players']:
        if player['alive']:
            keyboard.append([
                InlineKeyboardButton(
                    f"🗳️ Vote {player['username']}",
                    callback_data=f"vote_{game['id']}_{player['user_id']}"
                )
            ])
    
    keyboard.append([
        InlineKeyboardButton("⏭️ Skip Vote", callback_data=f"vote_{game['id']}_skip")
    ])
    
    return InlineKeyboardMarkup(keyboard)


def format_vote_results(game: dict, vote_counts: dict) -> str:
    """Format voting results"""
    text = "📊 <b>VOTING RESULTS</b>\n\n"
    
    if not vote_counts:
        text += "No votes were cast!\n"
        return text
    
    sorted_votes = sorted(vote_counts.items(), key=lambda x: x[1], reverse=True)
    
    for user_id, votes in sorted_votes:
        # Find player name
        for player in game['players']:
            if player['user_id'] == user_id:
                text += f"• {player['username']}: {votes} vote(s)\n"
                break
    
    return text


def generate_game_id() -> str:
    """Generate unique game ID"""
    import random
    import string
    
    timestamp = int(datetime.now().timestamp())
    random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    
    return f"GAME_{random_str}_{timestamp}"


def sanitize_input(text: str) -> str:
    """Sanitize user input"""
    # Remove HTML tags
    import re
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text)


def format_game_history(player: dict) -> str:
    """Format player's game history"""
    text = "📊 <b>GAME HISTORY</b>\n\n"
    
    if not player.get('roles_played'):
        text += "No games played yet!\n"
        return text
    
    text += "<b>Roles Played:</b>\n"
    for role, count in player['roles_played'].items():
        emoji = get_role_emoji(role)
        text += f"{emoji} {role.capitalize()}: {count} time(s)\n"
    
    return text


async def send_countdown(message, seconds: int, prefix: str = "Starting in"):
    """Send countdown animation"""
    for i in range(seconds, 0, -1):
        try:
            await message.edit_text(
                f"⏰ <b>{prefix} {i}...</b>",
                parse_mode='HTML'
            )
            await asyncio.sleep(1)
        except:
            pass


def check_game_end_condition(game: dict) -> tuple:
    """Check if game should end and return winner"""
    alive_players = [p for p in game['players'] if p['alive']]
    
    mafia_alive = sum(1 for p in alive_players if p['role'] == 'mafia')
    villagers_alive = sum(1 for p in alive_players if p['role'] not in ['mafia', 'boss'])
    
    if mafia_alive == 0:
        return True, 'villagers'
    elif mafia_alive >= villagers_alive:
        return True, 'mafia'
    elif game['mode'] == '1vboss':
        boss_alive = any(p['alive'] and p['role'] == 'boss' for p in game['players'])
        if not boss_alive:
            return True, 'villagers'
    
    return False, None


def format_error_message(error: str) -> str:
    """Format error message"""
    return f"❌ <b>Error:</b> {error}"


def format_success_message(message: str) -> str:
    """Format success message"""
    return f"✅ <b>Success:</b> {message}"


def create_player_action_keyboard(game_id: str, players: list, action: str) -> InlineKeyboardMarkup:
    """Create keyboard for player actions (kill, investigate, protect)"""
    keyboard = []
    
    action_text = {
        'kill': '🔪 Eliminate',
        'investigate': '🔍 Investigate',
        'protect': '💉 Protect'
    }
    
    for player in players:
        if player['alive']:
            keyboard.append([
                InlineKeyboardButton(
                    f"{action_text.get(action, '⚡')} {player['username']}",
                    callback_data=f"action_{action}_{game_id}_{player['user_id']}"
                )
            ])
    
    return InlineKeyboardMarkup(keyboard)


def format_night_summary(eliminated: dict, protected: dict, investigated: dict) -> str:
    """Format night phase summary"""
    text = "🌙 <b>NIGHT SUMMARY</b> 🌙\n\n"
    
    if eliminated and not protected:
        text += f"☠️ {eliminated['username']} was eliminated!\n"
        text += f"They were a <b>{eliminated['role'].upper()}</b>\n\n"
    elif protected:
        text += "🛡️ Someone was protected! No one died.\n\n"
    else:
        text += "🌟 A peaceful night. No casualties.\n\n"
    
    if investigated:
        text += f"🔍 Investigation complete (results sent privately)\n"
    
    return text


def format_day_summary(eliminated: dict, vote_count: int) -> str:
    """Format day phase summary"""
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
    """Get rank title based on level"""
    if level < 5:
        return "🌱 Rookie"
    elif level < 10:
        return "⚔️ Soldier"
    elif level < 20:
        return "🎖️ Warrior"
    elif level < 30:
        return "👑 Elite"
    elif level < 50:
        return "💎 Master"
    else:
        return "🏆 Legend"


def calculate_level_from_xp(total_xp: int) -> tuple:
    """Calculate level and remaining XP from total XP"""
    level = 1
    xp = total_xp
    
    while True:
        xp_needed = calculate_xp_for_level(level + 1)
        if xp < xp_needed:
            break
        xp -= xp_needed
        level += 1
    
    return level, xp


def format_ability_description(ability: dict) -> str:
    """Format ability description with details"""
    text = f"⚡ <b>{ability['name']}</b>\n"
    text += f"{ability['description']}\n\n"
    
    if ability.get('cooldown', 0) > 0:
        text += f"⏰ Cooldown: {ability['cooldown']} rounds\n"
    
    if ability.get('uses', -1) > 0:
        text += f"🔢 Limited uses: {ability['uses']}\n"
    
    if ability.get('restriction'):
        text += f"⚠️ {ability['restriction']}\n"
    
    return text


def is_game_balanced(players: list) -> tuple:
    """Check if game teams are balanced"""
    mafia_count = sum(1 for p in players if p['role'] in ['mafia', 'boss', 'godfather'])
    villager_count = len(players) - mafia_count
    
    # Mafia should be roughly 30-40% of players
    ideal_ratio = 0.35
    actual_ratio = mafia_count / len(players) if players else 0
    
    balanced = 0.25 <= actual_ratio <= 0.45
    
    return balanced, actual_ratio


def generate_game_tips(role: str) -> list:
    """Generate helpful tips for a role"""
    tips = {
        'mafia': [
            "💡 Coordinate with your Mafia team",
            "💡 Act innocent during the day",
            "💡 Target power roles first",
            "💡 Create alibis and stories"
        ],
        'detective': [
            "💡 Investigate suspicious players",
            "💡 Keep your role secret",
            "💡 Share info carefully",
            "💡 Look for behavioral patterns"
        ],
        'doctor': [
            "💡 Protect key players",
            "💡 Vary your protection",
            "💡 Try to predict Mafia targets",
            "💡 Stay hidden from Mafia"
        ],
        'villager': [
            "💡 Observe player behavior",
            "💡 Vote based on evidence",
            "💡 Trust confirmed roles",
            "💡 Discuss strategies with others"
        ],
        'boss': [
            "💡 Use abilities strategically",
            "💡 Your armor saves you once",
            "💡 Intimidate wisely",
            "💡 Lead your team to victory"
        ]
    }
    
    return tips.get(role, ["💡 Play smart and have fun!"])
