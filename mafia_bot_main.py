"""
Mafia RPG Telegram Bot - Main Entry Point
A highly engaging, animated Mafia game with multiple game modes
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters
)
from game_manager import GameManager
from player_manager import PlayerManager
from config import BOT_TOKEN, ADMIN_IDS
from utils import format_player_stats, create_game_keyboard, send_animated_message

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
        f"🎭 <b>Welcome to Mafia RPG, {user.first_name}!</b> 🎭\n\n"
        "🔥 <b>The Ultimate Strategy Game</b> 🔥\n\n"
        "Choose your destiny:\n"
        "🎮 <b>Game Modes:</b>\n"
        "• 5v5 - Classic team battle\n"
        "• 1v1 - Intense duel\n"
        "• 1vBoss - Take down the kingpin\n\n"
        "🎯 Complete missions, level up, and become a legend!\n\n"
        "Use /menu to see all commands"
    )
    
    keyboard = [
        [InlineKeyboardButton("🎮 Play Now", callback_data="menu_play")],
        [InlineKeyboardButton("👤 My Profile", callback_data="menu_profile")],
        [InlineKeyboardButton("🏆 Leaderboard", callback_data="menu_leaderboard")],
        [InlineKeyboardButton("❓ How to Play", callback_data="menu_help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        welcome_text,
        parse_mode='HTML',
        reply_markup=reply_markup
    )


async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show main menu"""
    keyboard = [
        [InlineKeyboardButton("🎮 Play Game", callback_data="menu_play")],
        [InlineKeyboardButton("👤 My Profile", callback_data="menu_profile")],
        [InlineKeyboardButton("🏆 Leaderboard", callback_data="menu_leaderboard")],
        [InlineKeyboardButton("🎁 Shop", callback_data="menu_shop")],
        [InlineKeyboardButton("❓ Help", callback_data="menu_help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = (
        "🎭 <b>Mafia RPG - Main Menu</b> 🎭\n\n"
        "Choose an option to continue your journey!"
    )
    
    if update.callback_query:
        await update.callback_query.message.edit_text(
            text,
            parse_mode='HTML',
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            text,
            parse_mode='HTML',
            reply_markup=reply_markup
        )


async def play_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show game mode selection"""
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("⚔️ 5v5 Classic", callback_data="mode_5v5")],
        [InlineKeyboardButton("🎯 1v1 Duel", callback_data="mode_1v1")],
        [InlineKeyboardButton("👑 1vBoss Mission", callback_data="mode_1vboss")],
        [InlineKeyboardButton("🔙 Back", callback_data="menu_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = (
        "🎮 <b>Select Game Mode</b> 🎮\n\n"
        "⚔️ <b>5v5 Classic</b>\n"
        "Team-based strategy game with Mafia, Detective, and Villagers\n\n"
        "🎯 <b>1v1 Duel</b>\n"
        "Fast-paced showdown between two players\n\n"
        "👑 <b>1vBoss Mission</b>\n"
        "Work together to take down the Boss!"
    )
    
    await query.message.edit_text(
        text,
        parse_mode='HTML',
        reply_markup=reply_markup
    )


async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show player profile"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    player_data = player_manager.get_player(user_id)
    
    text = format_player_stats(player_data)
    
    keyboard = [
        [InlineKeyboardButton("🎁 Claim Daily Reward", callback_data="claim_daily")],
        [InlineKeyboardButton("🔙 Back to Menu", callback_data="menu_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.edit_text(
        text,
        parse_mode='HTML',
        reply_markup=reply_markup
    )


async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show top players"""
    query = update.callback_query
    await query.answer()
    
    top_players = player_manager.get_leaderboard(10)
    
    text = "🏆 <b>TOP PLAYERS</b> 🏆\n\n"
    
    medals = ["🥇", "🥈", "🥉"]
    for i, player in enumerate(top_players, 1):
        medal = medals[i-1] if i <= 3 else f"{i}."
        text += f"{medal} <b>{player['username']}</b>\n"
        text += f"   Level {player['level']} • {player['wins']} Wins • {player['xp']} XP\n\n"
    
    keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="menu_main")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.edit_text(
        text,
        parse_mode='HTML',
        reply_markup=reply_markup
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show help information"""
    query = update.callback_query
    
    text = (
        "❓ <b>HOW TO PLAY</b> ❓\n\n"
        "<b>🎭 5v5 CLASSIC MODE:</b>\n"
        "• Players are assigned roles: Mafia, Detective, Villager\n"
        "• Mafia eliminates players at night\n"
        "• Detective investigates suspects\n"
        "• Villagers vote to eliminate Mafia during the day\n\n"
        "<b>🎯 1v1 DUEL:</b>\n"
        "• Quick match between two players\n"
        "• One Mafia vs one Detective/Villager\n"
        "• Complete missions to win\n\n"
        "<b>👑 1vBOSS MISSION:</b>\n"
        "• Team up against a powerful Boss\n"
        "• Complete objectives to weaken the Boss\n"
        "• Work together or face defeat!\n\n"
        "<b>📊 PROGRESSION:</b>\n"
        "• Earn XP from games and missions\n"
        "• Level up to unlock new roles and abilities\n"
        "• Collect achievements and items\n\n"
        "<b>⚡ COMMANDS:</b>\n"
        "/start - Begin your journey\n"
        "/menu - Main menu\n"
        "/play - Quick play\n"
        "/profile - View your stats\n"
        "/leaderboard - Top players"
    )
    
    keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="menu_main")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if query:
        await query.answer()
        await query.message.edit_text(
            text,
            parse_mode='HTML',
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            text,
            parse_mode='HTML',
            reply_markup=reply_markup
        )


async def create_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Create a new game lobby"""
    query = update.callback_query
    await query.answer()
    
    mode = query.data.split("_")[1]
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    game_id = game_manager.create_game(mode, user_id, chat_id)
    
    text = (
        f"🎮 <b>Game Lobby Created!</b> 🎮\n\n"
        f"📋 Game ID: <code>{game_id}</code>\n"
        f"🎯 Mode: <b>{mode.upper()}</b>\n"
        f"👥 Players: 1/{game_manager.get_required_players(mode)}\n\n"
        "⏳ Waiting for players to join...\n\n"
        "Share this message with friends to join!"
    )
    
    keyboard = [
        [InlineKeyboardButton("✅ Join Game", callback_data=f"join_{game_id}")],
        [InlineKeyboardButton("🚀 Start Game", callback_data=f"start_{game_id}")],
        [InlineKeyboardButton("❌ Cancel", callback_data=f"cancel_{game_id}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.edit_text(
        text,
        parse_mode='HTML',
        reply_markup=reply_markup
    )


async def join_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Join an existing game"""
    query = update.callback_query
    await query.answer()
    
    game_id = query.data.split("_")[1]
    user_id = update.effective_user.id
    username = update.effective_user.username or update.effective_user.first_name
    
    success, message = game_manager.join_game(game_id, user_id, username)
    
    if success:
        game = game_manager.get_game(game_id)
        text = (
            f"✅ <b>{username} joined the game!</b>\n\n"
            f"📋 Game ID: <code>{game_id}</code>\n"
            f"🎯 Mode: <b>{game['mode'].upper()}</b>\n"
            f"👥 Players: {len(game['players'])}/{game_manager.get_required_players(game['mode'])}\n\n"
        )
        
        text += "<b>Players:</b>\n"
        for player in game['players']:
            text += f"• {player['username']}\n"
        
        keyboard = [
            [InlineKeyboardButton("✅ Join Game", callback_data=f"join_{game_id}")],
            [InlineKeyboardButton("🚀 Start Game", callback_data=f"start_{game_id}")],
            [InlineKeyboardButton("❌ Cancel", callback_data=f"cancel_{game_id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.message.edit_text(
            text,
            parse_mode='HTML',
            reply_markup=reply_markup
        )
    else:
        await query.answer(message, show_alert=True)


async def start_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start the game"""
    query = update.callback_query
    await query.answer()
    
    game_id = query.data.split("_")[1]
    user_id = update.effective_user.id
    
    success, message = game_manager.start_game(game_id, user_id)
    
    if success:
        game = game_manager.get_game(game_id)
        
        # Animated start sequence
        await send_animated_message(
            query.message,
            [
                "🎬 <b>GAME STARTING...</b>",
                "🎭 <b>Assigning roles...</b>",
                "⚡ <b>Preparing the battlefield...</b>",
                "🔥 <b>LET THE GAME BEGIN!</b>"
            ]
        )
        
        # Send role information to each player privately
        for player in game['players']:
            try:
                role_text = (
                    f"🎭 <b>Your Role: {player['role'].upper()}</b> 🎭\n\n"
                    f"{game_manager.get_role_description(player['role'])}\n\n"
                    "Good luck! 🍀"
                )
                await context.bot.send_message(
                    chat_id=player['user_id'],
                    text=role_text,
                    parse_mode='HTML'
                )
            except:
                pass
        
        # Start first round
        await game_manager.start_round(game_id, query.message, context)
    else:
        await query.answer(message, show_alert=True)


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all button callbacks"""
    query = update.callback_query
    data = query.data
    
    if data == "menu_main":
        await menu(update, context)
    elif data == "menu_play":
        await play_menu(update, context)
    elif data == "menu_profile":
        await profile(update, context)
    elif data == "menu_leaderboard":
        await leaderboard(update, context)
    elif data == "menu_help":
        await help_command(update, context)
    elif data.startswith("mode_"):
        await create_game(update, context)
    elif data.startswith("join_"):
        await join_game(update, context)
    elif data.startswith("start_"):
        await start_game(update, context)
    elif data.startswith("vote_"):
        await game_manager.handle_vote(update, context)
    elif data.startswith("action_"):
        await game_manager.handle_action(update, context)
    elif data == "claim_daily":
        await claim_daily_reward(update, context)


async def claim_daily_reward(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Claim daily reward"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    success, reward = player_manager.claim_daily_reward(user_id)
    
    if success:
        text = (
            "🎁 <b>DAILY REWARD CLAIMED!</b> 🎁\n\n"
            f"You received:\n"
            f"💎 {reward['xp']} XP\n"
            f"🪙 {reward['coins']} Coins\n\n"
            "Come back tomorrow for more rewards!"
        )
    else:
        text = (
            "⏰ <b>Already Claimed!</b>\n\n"
            "You've already claimed your daily reward.\n"
            "Come back tomorrow!"
        )
    
    keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="menu_profile")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.edit_text(
        text,
        parse_mode='HTML',
        reply_markup=reply_markup
    )


async def quick_play(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Quick play command"""
    keyboard = [
        [InlineKeyboardButton("⚔️ 5v5", callback_data="mode_5v5")],
        [InlineKeyboardButton("🎯 1v1", callback_data="mode_1v1")],
        [InlineKeyboardButton("👑 1vBoss", callback_data="mode_1vboss")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🎮 Choose your game mode:",
        reply_markup=reply_markup
    )


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show player stats"""
    user_id = update.effective_user.id
    player_data = player_manager.get_player(user_id)
    
    text = format_player_stats(player_data)
    
    await update.message.reply_text(text, parse_mode='HTML')


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors"""
    logger.error(f"Update {update} caused error {context.error}")


def main():
    """Start the bot"""
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("menu", menu))
    application.add_handler(CommandHandler("play", quick_play))
    application.add_handler(CommandHandler("profile", stats))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("leaderboard", leaderboard))
    
    # Callback query handler
    application.add_handler(CallbackQueryHandler(button_handler))
    
    # Error handler
    application.add_error_handler(error_handler)
    
    # Start bot
    logger.info("🎭 Mafia RPG Bot is starting...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
