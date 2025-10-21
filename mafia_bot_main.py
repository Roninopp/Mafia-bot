"""
Mafia RPG Telegram Bot - Main Entry Point
Complete implementation with normal keyboards
"""

import logging
import asyncio  # Make sure asyncio is imported
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)
from game_manager import GameManager
from player_manager import PlayerManager
from config import BOT_TOKEN, FEATURES
from utils import *

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Global managers
game_manager = GameManager()
player_manager = PlayerManager()


# --- KEYBOARD HELPER FUNCTIONS (FIX) ---

def create_main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Creates the main menu keyboard."""
    keyboard = [
        ["🎮 Play Game", "👤 My Profile"],
        ["🏆 Leaderboard", "🎁 Daily Reward"],
        ["🏪 Shop", "❓ Help"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def create_game_mode_keyboard() -> ReplyKeyboardMarkup:
    """Creates the game mode selection keyboard."""
    keyboard = [
        ["⚔️ 5v5 Classic"],
        ["🎯 1v1 Duel"],
        ["👑 1vBoss Mission"],
        ["🔙 Back to Menu"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# -----------------------------------------


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Welcome message and main menu"""
    user = update.effective_user
    
    # Register player
    player_manager.register_player(user.id, user.username or user.first_name)
    
    welcome_frames = [
        f"🎭 <b>Welcome, {user.first_name}!</b> 🎭",
        "🔥 <b>Entering the world of Mafia RPG...</b> 🔥",
        "✨ <b>Your journey begins now!</b> ✨"
    ]
    
    msg = await update.message.reply_text(welcome_frames[0], parse_mode='HTML')
    
    for frame in welcome_frames[1:]:
        await asyncio.sleep(1)
        try:
            await msg.edit_text(frame, parse_mode='HTML')
        except:
            pass
    
    await asyncio.sleep(1)
    
    welcome_text = (
        f"🎭 <b>MAFIA RPG</b> 🎭\n\n"
        "🔥 <b>The Ultimate Strategy Game</b> 🔥\n\n"
        "Choose your destiny:\n"
        "🎮 <b>Game Modes:</b>\n"
        "• ⚔️ 5v5 Classic - Team battle\n"
        "• 🎯 1v1 Duel - Intense showdown\n"
        "• 👑 1vBoss - Defeat the kingpin\n\n"
        "🎯 Complete missions, level up, become a legend!\n\n"
        "👇 <b>Use the menu below to get started!</b>"
    )
    
    # --- FIX ---
    # Was: keyboard = create_game_keyboard()
    keyboard = create_main_menu_keyboard()
    
    await update.message.reply_text(
        welcome_text,
        parse_mode='HTML',
        reply_markup=keyboard
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all text messages"""
    text = update.message.text
    user_id = update.effective_user.id
    username = update.effective_user.username or update.effective_user.first_name
    
    # Register player if not exists
    player_manager.register_player(user_id, username)
    
    # Main menu options
    if text == "🎮 Play Game":
        await show_game_modes(update, context)
    
    elif text == "👤 My Profile":
        await show_profile(update, context)
    
    elif text == "🏆 Leaderboard":
        await show_leaderboard(update, context)
    
    elif text == "🎁 Daily Reward":
        await claim_daily_reward(update, context)
    
    elif text == "🏪 Shop":
        await show_shop(update, context)
    
    elif text == "❓ Help":
        await show_help(update, context)
    
    # Game mode selection
    elif text == "⚔️ 5v5 Classic":
        await create_game_lobby(update, context, '5v5')
    
    elif text == "🎯 1v1 Duel":
        await create_game_lobby(update, context, '1v1')
    
    elif text == "👑 1vBoss Mission":
        await create_game_lobby(update, context, '1vboss')
    
    elif text == "🔙 Back to Menu":
        # --- FIX ---
        # Was: keyboard = create_game_keyboard()
        keyboard = create_main_menu_keyboard()
        await update.message.reply_text(
            "📱 <b>Main Menu</b>",
            parse_mode='HTML',
            reply_markup=keyboard
        )
    
    # Game actions
    elif text.startswith("✅ Join Game:"):
        game_id = text.split(":")[-1].strip()
        await join_game_action(update, context, game_id)
    
    elif text.startswith("🚀 Start Game:"):
        game_id = text.split(":")[-1].strip()
        await start_game_action(update, context, game_id)
    
    elif text.startswith("❌ Cancel Game:"):
        game_id = text.split(":")[-1].strip()
        await cancel_game_action(update, context, game_id)
    
    # In-game actions
    elif any(emoji in text for emoji in ['🔪', '🔍', '💉']):
        await game_manager.handle_action(update, context)
    
    elif '🗳️' in text or 'Vote:' in text or '⏭️' in text:
        await game_manager.handle_vote(update, context)


async def show_game_modes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show game mode selection"""
    text = (
        "🎮 <b>SELECT GAME MODE</b> 🎮\n\n"
        "⚔️ <b>5v5 Classic</b>\n"
        "Team-based strategy with multiple roles\n"
        "Players: 10 | Duration: ~15 mins\n\n"
        "🎯 <b>1v1 Duel</b>\n"
        "Fast-paced showdown\n"
        "Players: 2 | Duration: ~5 mins\n\n"
        "👑 <b>1vBoss Mission</b>\n"
        "Team up to defeat the Boss!\n"
        "Players: 5 | Duration: ~10 mins\n\n"
        "Choose your mode:"
    )
    
    # --- FIX ---
    # Was calling a non-existent function
    keyboard = create_game_mode_keyboard()
    
    await update.message.reply_text(
        text,
        parse_mode='HTML',
        reply_markup=keyboard
    )


async def show_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show player profile"""
    user_id = update.effective_user.id
    player_data = player_manager.get_player(user_id)
    
    if not player_data:
        await update.message.reply_text("❌ Profile not found! Use /start first.")
        return
    
    # Animated profile loading
    msg = await update.message.reply_text("⏳ Loading profile...", parse_mode='HTML')
    await asyncio.sleep(0.5)
    
    profile_text = format_player_stats(player_data)
    
    # --- FIX ---
    # Was: keyboard = create_game_keyboard()
    keyboard = create_main_menu_keyboard()
    
    try:
        await msg.edit_text(profile_text, parse_mode='HTML')
    except:
        await update.message.reply_text(profile_text, parse_mode='HTML')
    
    await asyncio.sleep(0.5)
    await update.message.reply_text("📱 Main Menu", reply_markup=keyboard)


async def show_leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show top players"""
    top_players = player_manager.get_leaderboard(10)
    
    text = "🏆 <b>TOP PLAYERS</b> 🏆\n\n"
    
    if not top_players:
        text += "No players yet! Be the first!"
    else:
        for i, player in enumerate(top_players, 1):
            text += format_leaderboard_entry(i, player)
            text += "\n"
    
    # --- FIX ---
    # Was: keyboard = create_game_keyboard()
    keyboard = create_main_menu_keyboard()
    
    await update.message.reply_text(text, parse_mode='HTML', reply_markup=keyboard)


async def claim_daily_reward(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Claim daily reward"""
    user_id = update.effective_user.id
    success, reward = player_manager.claim_daily_reward(user_id)
    
    if success:
        frames = [
            "🎁 <b>Opening daily reward...</b>",
            "✨ <b>Revealing prizes...</b>",
            (
                f"🎉 <b>DAILY REWARD CLAIMED!</b> 🎉\n\n"
                f"You received:\n"
                f"💎 {reward['xp']} XP\n"
                f"🪙 {reward['coins']} Coins\n"
                f"🔥 Streak: {reward['streak']} days\n\n"
                f"Come back tomorrow for more!"
            )
        ]
        
        await send_animated_message(update.message, frames, delay=1.0)
    else:
        text = (
            "⏰ <b>Already Claimed!</b>\n\n"
            "You've already claimed your daily reward.\n"
            "Come back tomorrow for more goodies!"
        )
        await update.message.reply_text(text, parse_mode='HTML')
    
    # --- FIX ---
    # Was: keyboard = create_game_keyboard()
    keyboard = create_main_menu_keyboard()
    await update.message.reply_text("📱 Main Menu", reply_markup=keyboard)


async def show_shop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show shop items"""
    from config import SHOP_ITEMS
    
    user_id = update.effective_user.id
    player = player_manager.get_player(user_id)
    
    text = (
        f"🏪 <b>SHOP</b> 🏪\n\n"
        f"💰 Your Coins: <b>{player['coins']}</b>\n\n"
        "<b>Available Items:</b>\n\n"
    )
    
    for item in SHOP_ITEMS:
        owned = "✅" if player_manager.has_item(user_id, item['id']) else ""
        text += (
            f"{item['name']} {owned}\n"
            f"   {item['description']}\n"
            f"   💰 Price: {item['price']} coins\n\n"
        )
    
    text += "\n💡 Items coming soon! Stay tuned!"
    
    # --- FIX ---
    # Was: keyboard = create_game_keyboard()
    keyboard = create_main_menu_keyboard()
    await update.message.reply_text(text, parse_mode='HTML', reply_markup=keyboard)


async def show_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show help information"""
    text = (
        "❓ <b>HOW TO PLAY</b> ❓\n\n"
        "<b>🎭 GAME BASICS:</b>\n"
        "• Players are assigned secret roles\n"
        "• Mafia eliminates at night\n"
        "• Villagers vote during the day\n"
        "• Special roles have unique powers\n\n"
        "<b>⚔️ 5v5 CLASSIC:</b>\n"
        "• 3 Mafia vs 1 Detective, 1 Doctor, 5 Villagers\n"
        "• Mafia: Eliminate villagers\n"
        "• Detective: Investigate players\n"
        "• Doctor: Protect from attacks\n"
        "• Villager: Vote and discuss\n\n"
        "<b>🎯 1v1 DUEL:</b>\n"
        "• Quick match: Mafia vs Detective\n"
        "• Fast-paced strategic gameplay\n\n"
        "<b>👑 1vBOSS:</b>\n"
        "• Team up to defeat powerful Boss\n"
        "• Boss has special abilities\n\n"
        "<b>🎮 PROGRESSION:</b>\n"
        "• Earn XP and level up\n"
        "• Unlock achievements\n"
        "• Collect coins\n"
        "• Complete missions\n\n"
        "<b>⚡ COMMANDS:</b>\n"
        "/start - Begin your journey\n"
        "/profile - View your stats\n"
        "/help - Show this help\n\n"
        "👇 Use buttons below to navigate!"
    )
    
    # --- FIX ---
    # Was: keyboard = create_game_keyboard()
    keyboard = create_main_menu_keyboard()
    await update.message.reply_text(text, parse_mode='HTML', reply_markup=keyboard)


async def create_game_lobby(update: Update, context: ContextTypes.DEFAULT_TYPE, mode: str):
    """Create a new game lobby"""
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    # Create game
    game_id = game_manager.create_game(mode, user_id, chat_id)
    
    # Store game_id in context for this chat
    context.chat_data['active_game'] = game_id
    
    frames = [
        "🎮 <b>Creating game lobby...</b>",
        "✨ <b>Setting up battlefield...</b>",
        f"🎊 <b>Lobby Created!</b>"
    ]
    
    await send_animated_message(update.message, frames, delay=0.8)
    
    game = game_manager.get_game(game_id)
    required = game_manager.get_required_players(mode)
    
    text = (
        f"🎮 <b>GAME LOBBY</b> 🎮\n\n"
        f"🆔 Game ID: <code>{game_id}</code>\n"
        f"🎯 Mode: <b>{mode.upper()}</b>\n"
        f"👥 Players: {len(game['players'])}/{required}\n\n"
        f"<b>Waiting for players...</b>\n\n"
        f"Share this lobby with friends!"
    )
    
    # Create lobby keyboard
    keyboard = [
        [KeyboardButton(f"✅ Join Game: {game_id}")],
        [KeyboardButton(f"🚀 Start Game: {game_id}")],
        [KeyboardButton(f"❌ Cancel Game: {game_id}")],
        [KeyboardButton("🔙 Back to Menu")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(text, parse_mode='HTML', reply_markup=reply_markup)


async def join_game_action(update: Update, context: ContextTypes.DEFAULT_TYPE, game_id: str):
    """Join an existing game"""
    user_id = update.effective_user.id
    username = update.effective_user.username or update.effective_user.first_name
    
    success, message = game_manager.join_game(game_id, user_id, username)
    
    if success:
        game = game_manager.get_game(game_id)
        required = game_manager.get_required_players(game['mode'])
        
        text = (
            f"✅ <b>{username} joined the game!</b>\n\n"
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
        
        await update.message.reply_text(text, parse_mode='HTML')
    else:
        await update.message.reply_text(f"❌ {message}")


async def start_game_action(update: Update, context: ContextTypes.DEFAULT_TYPE, game_id: str):
    """Start the game"""
    user_id = update.effective_user.id
    
    success, message = game_manager.start_game(game_id, user_id)
    
    if not success:
        await update.message.reply_text(f"❌ {message}")
        return
    
    game = game_manager.get_game(game_id)
    
    # Animated start sequence
    from config import ANIMATION_SEQUENCES
    await send_animated_message(
        update.message,
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
    
    # Remove lobby keyboard
    await update.message.reply_text(
        "🎮 <b>Game Started!</b>\n\nCheck your private messages for your role!",
        parse_mode='HTML',
        reply_markup=ReplyKeyboardRemove()
    )
    
    await asyncio.sleep(2)
    
    # Start first round
    await game_manager.start_round(game_id, update.message, context)


async def cancel_game_action(update: Update, context: ContextTypes.DEFAULT_TYPE, game_id: str):
    """Cancel a game"""
    user_id = update.effective_user.id
    
    success, message = game_manager.cancel_game(game_id, user_id)
    
    if success:
        # --- FIX ---
        # Was: keyboard = create_game_keyboard()
        keyboard = create_main_menu_keyboard()
        await update.message.reply_text(
            f"✅ <b>Game cancelled!</b>",
            parse_mode='HTML',
            reply_markup=keyboard
        )
    else:
        await update.message.reply_text(f"❌ {message}")


async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show profile via command"""
    await show_profile(update, context)


async def leaderboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show leaderboard via command"""
    await show_leaderboard(update, context)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show help via command"""
    await show_help(update, context)


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Quick stats command"""
    user_id = update.effective_user.id
    player = player_manager.get_player(user_id)
    
    if not player:
        await update.message.reply_text("❌ Profile not found! Use /start first.")
        return
    
    win_rate = (player['wins'] / player['games_played'] * 100) if player['games_played'] > 0 else 0
    
    text = (
        f"📊 <b>Quick Stats</b>\n\n"
        f"⭐ Level: {player['level']}\n"
        f"💎 XP: {player['xp']}\n"
        f"🪙 Coins: {player['coins']}\n"
        f"🎮 Games: {player['games_played']}\n"
        f"🏆 Wins: {player['wins']}\n"
        f"📈 Win Rate: {win_rate:.1f}%"
    )
    
    await update.message.reply_text(text, parse_mode='HTML')


async def daily_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Quick daily reward claim"""
    await claim_daily_reward(update, context)


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors"""
    logger.error(f"Update {update} caused error {context.error}")
    
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "⚠️ <b>An error occurred!</b>\n\nPlease try again or contact support.",
            parse_mode='HTML'
        )


async def broadcast_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin command to broadcast messages"""
    from config import ADMIN_IDS
    
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


async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show bot statistics (admin only)"""
    from config import ADMIN_IDS
    
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ Unauthorized!")
        return
    
    total_players = len(player_manager.players)
    active_games = sum(1 for g in game_manager.games.values() if g['status'] == 'in_progress')
    total_games = len(game_manager.games)
    
    text = (
        "📊 <b>BOT STATISTICS</b>\n\n"
        f"👥 Total Players: {total_players}\n"
        f"🎮 Active Games: {active_games}\n"
        f"📈 Total Games: {total_games}\n"
    )
    
    await update.message.reply_text(text, parse_mode='HTML')


def main():
    """Start the bot"""
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("profile", profile_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("leaderboard", leaderboard_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("daily", daily_command))
    
    # Admin commands
    application.add_handler(CommandHandler("broadcast", broadcast_message))
    application.add_handler(CommandHandler("adminstats", admin_stats))
    
    # Message handler for buttons and text
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Error handler
    application.add_error_handler(error_handler)
    
    # Start bot
    logger.info("🎭 Mafia RPG Bot is starting...")
    logger.info("🚀 Bot is ready and running!")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
