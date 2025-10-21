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
                        'uses': -1
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
        return self.roles.get(role, {})
    
    def get_role_abilities(self, role: str) -> List[dict]:
        role_info = self.roles.get(role, {})
        return role_info.get('abilities', [])
    
    def get_role_description(self, role: str) -> str:
        role_info = self.roles.get(role, {})
        return role_info.get('description', 'Unknown role')
    
    def get_role_icon(self, role: str) -> str:
        role_info = self.roles.get(role, {})
        return role_info.get('icon', '❓')
    
    def get_role_team(self, role: str) -> str:
        role_info = self.roles.get(role, {})
        return role_info.get('team', 'unknown')
    
    def can_use_ability(self, role: str, ability_id: str, last_used: int, current_round: int) -> bool:
        abilities = self.get_role_abilities(role)
        for ability in abilities:
            if ability['id'] == ability_id:
                if ability['uses'] == 0: return False
                if ability['cooldown'] > 0:
                    if current_round - last_used < ability['cooldown']: return False
                return True
        return False
    
    def get_ability_description(self, role: str, ability_id: str) -> str:
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
        role_info = self.get_role_info(role)
        if not role_info: return "❓ Unknown Role"
        
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
        mode_roles = {
            '5v5': ['mafia', 'detective', 'doctor', 'villager'],
            '1v1': ['mafia', 'detective']
        }
        return mode_roles.get(game_mode, ['villager'])
    
    def get_role_count(self, game_mode: str, role: str) -> int:
        role_counts = {
            '5v5': {'mafia': 3, 'detective': 1, 'doctor': 1, 'villager': 5},
            '1v1': {'mafia': 1, 'detective': 1}
        }
        mode_counts = role_counts.get(game_mode, {})
        return mode_counts.get(role, 0)
    
    def assign_roles(self, player_count: int, game_mode: str) -> List[str]:
        import random
        
        role_counts = {
            '5v5': {'mafia': 3, 'detective': 1, 'doctor': 1, 'villager': 5},
            '1v1': {'mafia': 1, 'detective': 1}
        }
        counts = role_counts.get(game_mode, {'villager': player_count})
        
        roles = []
        for role, count in counts.items():
            roles.extend([role] * count)
        
        # Adjust for different player counts if needed, though 5v5 and 1v1 are fixed
        while len(roles) < player_count:
            roles.append('villager')
            
        random.shuffle(roles)
        return roles[:player_count] # Return correct number of roles
    
    def get_role_tips(self, role: str) -> List[str]:
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
            ]
        }
        return tips.get(role, ["🎮 Play strategically!"])
    
    def get_role_weaknesses(self, role: str) -> List[str]:
        weaknesses = {
            'mafia': ["Outnumbered by villagers", "Detective can expose you"],
            'detective': ["Mafia target", "No protection"],
            'doctor': ["Can't protect self", "Predictable patterns"],
            'villager': ["No special abilities", "Limited information"]
        }
        return weaknesses.get(role, [])
    
    def get_role_strengths(self, role: str) -> List[str]:
        strengths = {
            'mafia': ["Night elimination power", "Knows other Mafia", "Information advantage"],
            'detective': ["Investigation ability", "Can confirm innocents", "Lead villagers"],
            'doctor': ["Save lives", "Protect VIPs", "Swing votes"],
            'villager': ["Safety in numbers", "Voting power", "Can blend in"]
        }
        return strengths.get(role, [])
    
    def is_evil_role(self, role: str) -> bool:
        role_info = self.get_role_info(role)
        return role_info.get('team') in ['mafia', 'neutral']
    
    def is_good_role(self, role: str) -> bool:
        role_info = self.get_role_info(role)
        return role_info.get('team') == 'villagers'
    
    def get_compatible_roles(self, role: str) -> List[str]:
        compatibility = {
            'mafia': ['mafia', 'godfather'],
            'detective': ['doctor', 'vigilante'],
            'doctor': ['detective', 'villager'],
            'villager': ['detective', 'doctor']
        }
        return compatibility.get(role, [])
    
    def get_role_priority(self, role: str) -> int:
        priorities = {
            'detective': 10,
            'doctor': 9,
            'vigilante': 8,
            'godfather': 7,
            'mafia': 6,
            'villager': 3,
            'jester': 1
        }
        return priorities.get(role, 5)
