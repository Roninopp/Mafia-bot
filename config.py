"""
Configuration file for Mafia RPG Bot
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Bot Token - Get from @BotFather on Telegram
# !!! IMPORTANT: PASTE YOUR NEW TOKEN FROM @BOTFATHER HERE !!!
BOT_TOKEN = "8180268399:AAEfEsmFMvrCsgfxMb5Q0kbPqajrTJbpD38" 

# --- FIX: Added Bot Username and Pic ---
BOT_USERNAME = "Mafia_Gang_Game_Bot" # Change this if your bot's username is different
MAFIA_PIC_URL = "https://i.imgur.com/X25sJtG.jpeg"


# Admin user IDs (can manage bot, kick players, etc.)
ADMIN_IDS = [6837532865]

# Game Settings
GAME_SETTINGS = {
    '5v5': {
        'min_players': 10,
        'max_players': 10,
        'roles': {
            'mafia': 3,
            'detective': 1,
            'doctor': 1,
            'villager': 5
        },
        'night_duration': 60,  # seconds
        'day_duration': 90,  # seconds
        'base_xp_reward': 150
    },
    '1v1': {
        'min_players': 2,
        'max_players': 2,
        'roles': {
            'mafia': 1,
            'detective': 1
        },
        'night_duration': 30,
        'day_duration': 45,
        'base_xp_reward': 75
    }
}

# --- FIX: This was missing from your GitHub version ---
MISSION_REWARDS = {
    'target_practice': {
        'xp': 50,
        'coins': 25
    },
    'detectives_case': {
        'xp': 75,
        'coins': 50
    },
    'doctors_dilemma': {
        'xp': 100,
        'coins': 75
    },
    'timed_disarm': {
        'xp': 30,
        'coins': 15
    },
    'mafia_heist_success': {
        'xp': 200,
        'coins': 150
    },
    'mafia_heist_fail': {
        'xp': 25,
        'coins': 10
    }
}
# -----------------------------------------------------

# XP and Level Settings
XP_SETTINGS = {
    'base_xp_per_level': 100,
    'level_multiplier': 1.5,
    'win_bonus': 100,
    'participation_bonus': 50,
    'survival_bonus': 25,
    'role_bonus': {
        'mafia': 10,
        'detective': 15,
        'doctor': 10,
        'villager': 5
    }
}

# Shop Items
SHOP_ITEMS = [
    {
        'id': 'skin_golden',
        'name': '🌟 Golden Skin',
        'description': 'Shine bright in the game!',
        'price': 500,
        'type': 'cosmetic'
    },
    {
        'id': 'ability_double_vote',
        'name': '🗳️ Double Vote',
        'description': 'Your vote counts twice (1 use)',
        'price': 200,
        'type': 'ability'
    },
    {
        'id': 'ability_immunity',
        'name': '🛡️ Immunity Shield',
        'description': 'Survive one night attack (1 use)',
        'price': 300,
        'type': 'ability'
    },
    {
        'id': 'emote_pack_1',
        'name': '😎 Emote Pack 1',
        'description': 'Express yourself!',
        'price': 150,
        'type': 'cosmetic'
    },
    {
        'id': 'role_reroll',
        'name': '🎲 Role Reroll',
        'description': 'Reroll your role once per game',
        'price': 400,
        'type': 'ability'
    }
]

# Achievements
ACHIEVEMENTS = [
    {'id': 'first_win', 'name': 'First Blood', 'description': 'Win your first game', 'icon': '🏆', 'reward': 50},
]

# Missions
MISSION_TEMPLATES = {
    '5v5': [
        {'id': 'identify_mafia', 'name': 'Find the Culprit', 'description': 'Correctly identify a Mafia member', 'reward_xp': 50, 'reward_coins': 25},
        {'id': 'survive_night', 'name': 'Night Owl', 'description': 'Survive 3 nights in a row', 'reward_xp': 75, 'reward_coins': 35}
    ],
    '1v1': [
        {'id': 'quick_win', 'name': 'Speed Demon', 'description': 'Win in under 2 minutes', 'reward_xp': 100, 'reward_coins': 50}
    ]
}

# Emojis and Animations
EMOJIS = {
    'roles': {
        'mafia': '🔪',
        'detective': '🔍',
        'doctor': '💉',
        'villager': '👥',
        'godfather': '🎩',
        'vigilante': '🔫',
        'jester': '🤡'
    },
    'actions': {'kill': '☠️', 'investigate': '🔎', 'protect': '🛡️', 'vote': '🗳️'},
    'status': {'alive': '✅', 'dead': '💀', 'winner': '🏆', 'loser': '💔'},
    'phases': {'night': '🌙', 'day': '☀️', 'voting': '⚖️'}
}

# Animation frames for loading
LOADING_FRAMES = ["⚡", "⚡⚡", "⚡⚡⚡", "⚡⚡⚡⚡", "✨"]

# Enhanced animation sequences
ANIMATION_SEQUENCES = {
    'game_start': [
        "🎬 <b>GAME STARTING</b> 🎬",
        "🎭 <b>Shuffling roles...</b> 🎭",
        "⚡ <b>Preparing battlefield...</b> ⚡",
        "🔥 <b>LET THE GAME BEGIN!</b> 🔥"
    ],
    'night_phase': ["🌙 <b>Night falls...</b>", "🌑 <b>The town sleeps...</b>", "👻 <b>But evil lurks in shadows...</b>"],
    'day_phase': ["☀️ <b>Morning breaks...</b>", "🌅 <b>The town awakens...</b>", "👥 <b>Time to discuss and vote!</b>"],
    'elimination': ["⚡ <b>Processing actions...</b>", "🎭 <b>The night reveals its secrets...</b>", "💀 <b>Someone has fallen!</b>"],
    'victory': ["🎆 <b>GAME OVER!</b>", "🏆 <b>VICTORY!</b>", "🎉 <b>CONGRATULATIONS!</b>"]
}

# Database settings
DATABASE_CONFIG = {'enabled': False, 'type': 'sqlite', 'path': 'mafia_game.db'}

# Rate limiting
RATE_LIMITS = {'create_game': 5, 'join_game': 20, 'vote': 100}

# Feature flags
FEATURES = {
    'missions_enabled': True,
    'shop_enabled': True,
    'achievements_enabled': True,
    'daily_rewards_enabled': True,
    'leaderboard_enabled': True,
    'statistics_enabled': True,
    'tournaments_enabled': True,
    'clans_enabled': False,
    'trading_enabled': True
}

# Random events
RANDOM_EVENTS = [
    {'id': 'full_moon', 'name': '🌕 Full Moon', 'description': 'Mafia power increased!', 'effect': 'mafia_boost', 'probability': 0.1},
    {'id': 'blackout', 'name': '⚡ Blackout', 'description': 'Detective investigation fails!', 'effect': 'detective_fail', 'probability': 0.05},
    {'id': 'guardian_angel', 'name': '👼 Guardian Angel', 'description': 'Random player protected!', 'effect': 'random_protect', 'probability': 0.08}
]
