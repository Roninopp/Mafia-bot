"""
Roles Manager - Handles role abilities and special powers
"""

from typing import Dict, List


class RoleManager:
    def __init__(self):
        self.roles = self._initialize_roles()
    
    def _initialize_roles(self) -> Dict[str, dict]:
        """Initialize all role definitions"""
        return {
            'mafia': {
                'name': 'Mafia',
                'team': 'mafia',
                'icon': '🔪',
                'description': 'Eliminate villagers during the night',
                'abilities': [
                    {
                        'id': 'eliminate',
                        'name': 'Eliminate',
                        'description': 'Choose one player to eliminate each night',
                        'cooldown': 0,
                        'uses': -1  # Unlimited
                    }
                ],
                'win_condition': 'Mafia members equal or outnumber villagers'
            },
            'detective': {
                'name': 'Detective',
                'team': 'villagers',
                'icon': '🔍',
                'description': 'Investigate players to find the Mafia',
                'abilities': [
                    {
                        'id': 'investigate',
                        'name': 'Investigate',
                        'description': 'Learn if a player is Mafia or Innocent',
                        'cooldown': 0,
                        'uses': -1
                    }
                ],
                'win_condition': 'Eliminate all Mafia members'
            },
            'doctor': {
                'name': 'Doctor',
                'team': 'villagers',
                'icon': '💉',
                'description': 'Protect players from elimination',
                'abilities': [
                    {
                        'id': 'protect',
                        'name': 'Protect',
                        'description': 'Save one player from elimination each night',
                        'cooldown': 1,
                        'uses': -1,
                        'restriction': 'Cannot protect same player twice in a row'
                    }
                ],
                'win_condition': 'Eliminate all Mafia members'
            },
            'villager': {
                'name': 'Villager',
                'team': 'villagers',
                'icon': '👥',
                'description': 'Vote and discuss to find the Mafia',
                'abilities': [
                    {
                        'id': 'vote',
                        'name': 'Vote',
                        'description': 'Vote to eliminate suspects during the day',
                        'cooldown': 0,
                        'uses': -1
                    }
                ],
                'win_condition': 'Eliminate all Mafia members'
            },
            'boss': {
                'name': 'Boss',
                'team': 'mafia',
                'icon': '👑',
                'description': 'Powerful Mafia leader with special abilities',
                'abilities': [
                    {
                        'id': 'eliminate',
                        'name': 'Eliminate',
                        'description': 'Eliminate one player each night',
                        'cooldown': 0,
                        'uses': -1
                    },
                    {
                        'id': 'intimidate',
                        'name': 'Intimidate',
                        'description': 'Cancel one player\'s vote (1 use per game)',
                        'cooldown': 0,
                        'uses': 1
                    },
                    {
                        'id': 'armor',
                        'name': 'Armor',
                        'description': 'Survive first elimination attempt',
                        'cooldown': 0,
                        'uses': 1,
                        'passive': True
                    }
                ],
                'win_condition': 'Eliminate all villagers'
            },
            'vigilante': {
                'name': 'Vigilante',
                'team': 'villagers',
                'icon': '🔫',
                'description': 'Take justice into your own hands',
                'abilities': [
                    {
                        'id': 'shoot',
                        'name': 'Shoot',
                        'description': 'Eliminate one player at night (limited uses)',
                        'cooldown': 2,
                        'uses': 2
                    }
                ],
                'win_condition': 'Eliminate all Mafia members'
            },
            'godfather': {
                'name': 'Godfather',
                'team': 'mafia',
                'icon': '🎩',
                'description': 'Mafia leader who appears innocent',
                'abilities': [
                    {
                        'id': 'eliminate',
                        'name': 'Eliminate',
                        'description': 'Choose elimination target',
                        'cooldown': 0,
                        'uses': -1
                    },
                    {
                        'id': 'disguise',
                        'name': 'Disguise',
                        'description': 'Appear innocent to Detective investigations',
                        'cooldown': 0,
                        'uses': -1,
                        'passive': True
                    }
                ],
                'win_condition': 'Mafia members equal or outnumber villagers'
            },
            'jester': {
                'name': 'Jester',
                'team': 'neutral',
                'icon': '🤡',
                'description': 'Get yourself eliminated to win',
                'abilities': [
                    {
                        'id': 'haunt',
                        'name': 'Haunt',
                        'description': 'If eliminated by vote, choose one player to eliminate',
                        'cooldown': 0,
                        'uses': 1
                    }
                ],
                'win_condition': 'Get eliminated by vote'
            }
        }
    
    def get_role_info(self, role: str) -> dict:
        """Get complete role information"""
        return self.roles.get(role, {})
    
    def get_role_abilities(self, role: str) -> List[dict]:
        """Get abilities for a role"""
        role_info = self.roles.get(role, {})
        return role_info.get('abilities', [])
    
    def get_role_description(self, role: str) -> str:
        """Get role description"""
        role_info = self.roles.get(role, {})
        return role_info.get('description', 'Unknown role')
    
    def get_role_icon(self, role: str) -> str:
        """Get role icon"""
        role_info = self.roles.get(role, {})
        return role_info.get('icon', '❓')
    
    def get_role_team(self, role: str) -> str:
        """Get role team"""
        role_info = self.roles.get(role, {})
        return role_info.get('team', 'unknown')
    
    def can_use_ability(self, role: str, ability_id: str, last_used: int, current_round: int) -> bool:
        """Check if ability can be used"""
        abilities = self.get_role_abilities(role)
        
        for ability in abilities:
            if ability['id'] == ability_id:
                # Check uses
                if ability['uses'] == 0:
                    return False
                
                # Check cooldown
                if ability['cooldown'] > 0:
                    if current_round - last_used < ability['cooldown']:
                        return False
                
                return True
        
        return False
    
    def get_ability_description(self, role: str, ability_id: str) -> str:
        """Get ability description"""
        abilities = self.get_role_abilities(role)
        
        for ability in abilities:
            if ability['id'] == ability_id:
                desc = f"<b>{ability['name']}</b>\n{ability['description']}"
                
                if ability.get('cooldown', 0) > 0:
                    desc += f"\n⏰ Cooldown: {ability['cooldown']} rounds"
                
                if ability.get('uses', -1) > 0:
                    desc += f"\n🔢 Uses: {ability['uses']}"
                
                if ability.get('restriction'):
                    desc += f"\n⚠️ {ability['restriction']}"
                
                return desc
        
        return "Unknown ability"
    
    def format_role_card(self, role: str) -> str:
        """Format complete role card for display"""
        role_info = self.get_role_info(role)
        
        if not role_info:
            return "❓ Unknown Role"
        
        text = (
            f"{role_info['icon']} <b>{role_info['name']}</b> {role_info['icon']}\n\n"
            f"👥 Team: <b>{role_info['team'].capitalize()}</b>\n"
            f"📝 {role_info['description']}\n\n"
            f"<b>Abilities:</b>\n"
        )
        
        for ability in role_info['abilities']:
            passive = " (Passive)" if ability.get('passive') else ""
            text += f"\n{role_info['icon']} <b>{ability['name']}</b>{passive}\n"
            text += f"   {ability['description']}\n"
            
            if ability.get('cooldown', 0) > 0:
                text += f"   ⏰ Cooldown: {ability['cooldown']} rounds\n"
            
            if ability.get('uses', -1) > 0:
                text += f"   🔢 Uses: {ability['uses']}\n"
        
        text += f"\n🎯 <b>Win Condition:</b>\n{role_info['win_condition']}"
        
        return text
    
    def get_available_roles(self, game_mode: str) -> List[str]:
        """Get roles available for a game mode"""
        mode_roles = {
            '5v5': ['mafia', 'detective', 'doctor', 'villager'],
            '1v1': ['mafia', 'detective'],
            '1vboss': ['boss', 'villager']
        }
        
        return mode_roles.get(game_mode, ['villager'])
    
    def get_role_count(self, game_mode: str, role: str) -> int:
        """Get how many of each role for a mode"""
        role_counts = {
            '5v5': {
                'mafia': 3,
                'detective': 1,
                'doctor': 1,
                'villager': 5
            },
            '1v1': {
                'mafia': 1,
                'detective': 1
            },
            '1vboss': {
                'boss': 1,
                'villager': 4
            }
        }
        
        mode_counts = role_counts.get(game_mode, {})
        return mode_counts.get(role, 0)
    
    def assign_roles(self, player_count: int, game_mode: str) -> List[str]:
        """Generate role list for assignment"""
        import random
        
        role_counts = {
            '5v5': {
                'mafia': 3,
                'detective': 1,
                'doctor': 1,
                'villager': 5
            },
            '1v1': {
                'mafia': 1,
                'detective': 1
            },
            '1vboss': {
                'boss': 1,
                'villager': 4
            }
        }
        
        counts = role_counts.get(game_mode, {'villager': player_count})
        
        roles = []
        for role, count in counts.items():
            roles.extend([role] * count)
        
        random.shuffle(roles)
        return roles
    
    def get_role_tips(self, role: str) -> List[str]:
        """Get gameplay tips for a role"""
        tips = {
            'mafia': [
                "🔪 Coordinate with other Mafia members",
                "🎭 Act innocent during the day",
                "🤫 Don't reveal your teammates",
                "🎯 Target powerful roles first"
            ],
            'detective': [
                "🔍 Investigate suspicious players",
                "🤔 Look for inconsistent behavior",
                "📊 Share information carefully",
                "🛡️ Stay hidden from Mafia"
            ],
            'doctor': [
                "💉 Protect key players",
                "🎯 Try to predict Mafia targets",
                "🔄 Vary your protection choices",
                "🤐 Keep your role secret"
            ],
            'villager': [
                "👥 Discuss and analyze behavior",
                "🗳️ Vote based on evidence",
                "🤝 Work with confirmed roles",
                "🧠 Use logic and deduction"
            ],
            'boss': [
                "👑 Use your abilities wisely",
                "🛡️ Your armor saves you once",
                "🎭 Play aggressively but smart",
                "💪 Intimidate strategically"
            ]
        }
        
        return tips.get(role, ["🎮 Play strategically!"])
    
    def get_role_weaknesses(self, role: str) -> List[str]:
        """Get role weaknesses"""
        weaknesses = {
            'mafia': ["Outnumbered by villagers", "Detective can expose you"],
            'detective': ["Mafia target", "No protection"],
            'doctor': ["Can't protect self", "Predictable patterns"],
            'villager': ["No special abilities", "Limited information"],
            'boss': ["Armor only works once", "Obvious target"]
        }
        
        return weaknesses.get(role, [])
    
    def get_role_strengths(self, role: str) -> List[str]:
        """Get role strengths"""
        strengths = {
            'mafia': ["Night elimination power", "Knows other Mafia", "Information advantage"],
            'detective': ["Investigation ability", "Can confirm innocents", "Lead villagers"],
            'doctor': ["Save lives", "Protect VIPs", "Swing votes"],
            'villager': ["Safety in numbers", "Voting power", "Can blend in"],
            'boss': ["Extra protection", "Intimidation power", "Strong abilities"]
        }
        
        return strengths.get(role, [])
    
    def is_evil_role(self, role: str) -> bool:
        """Check if role is on evil team"""
        role_info = self.get_role_info(role)
        return role_info.get('team') in ['mafia', 'neutral']
    
    def is_good_role(self, role: str) -> bool:
        """Check if role is on good team"""
        role_info = self.get_role_info(role)
        return role_info.get('team') == 'villagers'
    
    def get_compatible_roles(self, role: str) -> List[str]:
        """Get roles that work well together"""
        compatibility = {
            'mafia': ['mafia', 'godfather'],
            'detective': ['doctor', 'vigilante'],
            'doctor': ['detective', 'villager'],
            'villager': ['detective', 'doctor'],
            'boss': []
        }
        
        return compatibility.get(role, [])
    
    def get_role_priority(self, role: str) -> int:
        """Get elimination priority (higher = more important to eliminate)"""
        priorities = {
            'detective': 10,
            'doctor': 9,
            'vigilante': 8,
            'godfather': 7,
            'boss': 10,
            'mafia': 6,
            'villager': 3,
            'jester': 1
        }
        
        return priorities.get(role, 5)
