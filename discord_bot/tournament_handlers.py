import discord
from typing import Optional, Dict, Any, List
import logging
from datetime import datetime, timedelta, timezone
import re

from verselink_api import VerselinkAPI
from utils import *
from config import Config

logger = logging.getLogger(__name__)

class TournamentCreationHandler:
    """Gestionnaire pour la création de tournois"""
    
    def __init__(self, api: VerselinkAPI):
        self.api = api
        
    async def handle_tournament_message(self, message: discord.Message, session):
        """Gère les messages pour la création de tournois"""
        current_step = self.get_current_step(session)
        
        if current_step == 'name':
            await self.handle_name(message, session)
        elif current_step == 'description':
            await self.handle_description(message, session)
        elif current_step == 'organization':
            await self.handle_organization(message, session)
        elif current_step == 'game':
            await self.handle_game(message, session)
        elif current_step == 'tournament_type':
            await self.handle_tournament_type(message, session)
        elif current_step == 'start_date':
            await self.handle_start_date(message, session)
        elif current_step == 'max_participants':
            await self.handle_max_participants(message, session)
        elif current_step == 'format':
            await self.handle_format(message, session)
        elif current_step == 'rules':
            await self.handle_rules(message, session)
        elif current_step == 'prizes':
            await self.handle_prizes(message, session)
        elif current_step == 'confirmation':
            await self.handle_confirmation(message, session)
    
    def get_current_step(self, session) -> str:
        """Détermine l'étape actuelle basée sur les données collectées"""
        steps = ['name', 'description', 'organization', 'game', 'tournament_type',
                'start_date', 'max_participants', 'format', 'rules', 'prizes', 'confirmation']
        
        for step in steps:
            if step not in session.data:
                return step
        return 'confirmation'
    
    async def handle_name(self, message: discord.Message, session):
        """Gère la saisie du nom du tournoi"""
        name = message.content.strip()
        
        if len(name) < 3:
            embed = create_error_embed(
                "❌ Nom trop court",
                "Le nom doit contenir au moins 3 caractères.\n\n"
                "Exemples de bons noms :\n"
                "• \"Championnat Star Citizen 2025\"\n"
                "• \"Murray Cup Racing Championship\"\n"
                "• \"Arena Commander Masters\""
            )
            await message.channel.send(embed=embed)
            return
            
        if len(name) > 100:
            embed = create_error_embed(
                "❌ Nom trop long",
                "Le nom ne peut pas dépasser 100 caractères.\n\n"
                "Essayez de le raccourcir tout en gardant l'essentiel."
            )
            await message.channel.send(embed=embed)
            return
        
        session.data['name'] = name
        
        embed = create_success_embed(
            "✅ Nom enregistré",
            f"**Nom du tournoi :** {name}\n\n"
            f"Maintenant, décrivez votre tournoi.\n\n"
            f"💡 **Une bonne description contient :**\n"
            f"• Le format de compétition\n"
            f"• Les règles principales\n"
            f"• Les prix ou récompenses\n"
            f"• Prérequis pour participer\n\n"
            f"📝 **Exemple :**\n"
            f"*\"Tournoi de course dans l'univers Star Citizen. Format éliminatoire simple. "
            f"Ouvert à tous les pilotes. Prix : 100k aUEC pour le vainqueur, 50k pour le second.\"*"
        )
        await message.channel.send(embed=embed)
    
    async def handle_description(self, message: discord.Message, session):
        """Gère la saisie de la description"""
        description = message.content.strip()
        
        if len(description) < 20:
            embed = create_error_embed(
                "❌ Description trop courte",
                "La description doit contenir au moins 20 caractères.\n\n"
                "Donnez plus de détails sur votre tournoi !"
            )
            await message.channel.send(embed=embed)
            return
            
        if len(description) > 2000:
            embed = create_error_embed(
                "❌ Description trop longue",
                "La description ne peut pas dépasser 2000 caractères.\n\n"
                "Essayez de résumer les points essentiels."
            )
            await message.channel.send(embed=embed)
            return
        
        session.data['description'] = description
        
        embed = create_success_embed(
            "✅ Description enregistrée",
            f"**Description :** {description[:200]}{'...' if len(description) > 200 else ''}\n\n"
            f"Maintenant, choisissez l'organisation qui héberge ce tournoi.\n\n"
            f"Envoyez-moi :\n"
            f"• Le **nom** de l'organisation\n"
            f"• Ou son **tag** (ex: TEST, CORP)\n"
            f"• Ou son **ID** si vous le connaissez"
        )
        await message.channel.send(embed=embed)
    
    async def handle_organization(self, message: discord.Message, session):
        """Gère la sélection de l'organisation"""
        org_input = message.content.strip()
        
        try:
            # Essayer de trouver l'organisation
            async with self.api as api:
                # Si c'est un UUID, essayer directement
                if len(org_input) > 30 and '-' in org_input:
                    try:
                        org = await api.get_organization(org_input)
                        session.data['org_id'] = org['id']
                        session.data['org_name'] = org['name']
                    except:
                        raise Exception("Organisation non trouvée avec cet ID")
                else:
                    # Chercher par nom ou tag
                    orgs = await api.get_organizations(limit=50)
                    found_org = None
                    
                    for org in orgs:
                        if (org.get('name', '').lower() == org_input.lower() or 
                            org.get('tag', '').lower() == org_input.lower()):
                            found_org = org
                            break
                    
                    if not found_org:
                        raise Exception("Organisation non trouvée")
                    
                    session.data['org_id'] = found_org['id']
                    session.data['org_name'] = found_org['name']
            
            embed = create_success_embed(
                "✅ Organisation sélectionnée",
                f"**Organisation :** {session.data['org_name']}\n\n"
                f"Dans quel jeu se déroule ce tournoi ?\n\n"
                f"🎮 **Jeux supportés :**\n"
                f"• `Star Citizen` - Univers persistant\n"
                f"• `Arena Commander` - Combat spatial\n"
                f"• `Star Marine` - Combat FPS\n"
                f"• `Squadron 42` - Mode solo (pour les speedruns)\n"
                f"• `Racing` - Courses de vaisseaux\n"
                f"• `Autre` - Spécifiez le jeu"
            )
            await message.channel.send(embed=embed)
            
        except Exception as e:
            embed = create_error_embed(
                "❌ Organisation non trouvée",
                f"Impossible de trouver l'organisation \"{org_input}\".\n\n"
                f"Vérifiez :\n"
                f"• L'orthographe du nom\n"
                f"• Que vous êtes bien membre\n"
                f"• Que l'organisation existe\n\n"
                f"Essayez avec le nom complet ou le tag."
            )
            await message.channel.send(embed=embed)
    
    async def handle_game(self, message: discord.Message, session):
        """Gère la sélection du jeu"""
        game_input = message.content.strip().lower()
        
        game_mapping = {
            'star citizen': 'Star Citizen',
            'starcitizen': 'Star Citizen',
            'sc': 'Star Citizen',
            'arena commander': 'Arena Commander',
            'ac': 'Arena Commander',
            'star marine': 'Star Marine',
            'sm': 'Star Marine',
            'squadron 42': 'Squadron 42',
            's42': 'Squadron 42',
            'racing': 'Racing',
            'course': 'Racing'
        }
        
        if game_input in game_mapping:
            game = game_mapping[game_input]
        elif game_input == 'autre':
            embed = create_info_embed(
                "🎮 Jeu personnalisé",
                "Précisez le nom du jeu pour ce tournoi :"
            )
            await message.channel.send(embed=embed)
            return
        else:
            # Jeu personnalisé
            if len(game_input) > 50:
                embed = create_error_embed(
                    "❌ Nom de jeu trop long",
                    "Le nom du jeu ne peut pas dépasser 50 caractères."
                )
                await message.channel.send(embed=embed)
                return
            game = game_input.title()
        
        session.data['game'] = game
        
        embed = create_success_embed(
            "✅ Jeu sélectionné",
            f"**Jeu :** {game}\n\n"
            f"Quel est le type de tournoi ?\n\n"
            f"🏆 **Types disponibles :**\n"
            f"• `elimination` - Élimination simple\n"
            f"• `double_elimination` - Double élimination\n"
            f"• `round_robin` - Tournoi à la ronde\n"
            f"• `swiss` - Système suisse\n"
            f"• `league` - Format championnat\n"
            f"• `custom` - Format personnalisé"
        )
        await message.channel.send(embed=embed)
    
    async def handle_tournament_type(self, message: discord.Message, session):
        """Gère la sélection du type de tournoi"""
        tournament_type = message.content.strip().lower()
        
        valid_types = ['elimination', 'double_elimination', 'round_robin', 'swiss', 'league', 'custom']
        
        if tournament_type not in valid_types:
            embed = create_error_embed(
                "❌ Type de tournoi invalide",
                "Choisissez parmi :\n"
                "• `elimination` - Élimination simple\n"
                "• `double_elimination` - Double élimination\n"
                "• `round_robin` - Tournoi à la ronde\n"
                "• `swiss` - Système suisse\n"
                "• `league` - Format championnat\n"
                "• `custom` - Format personnalisé"
            )
            await message.channel.send(embed=embed)
            return
        
        session.data['tournament_type'] = tournament_type
        
        type_names = {
            'elimination': 'Élimination simple',
            'double_elimination': 'Double élimination',
            'round_robin': 'Tournoi à la ronde',
            'swiss': 'Système suisse',
            'league': 'Format championnat',
            'custom': 'Format personnalisé'
        }
        
        embed = create_success_embed(
            "✅ Type de tournoi sélectionné",
            f"**Type :** {type_names[tournament_type]}\n\n"
            f"Quand commence le tournoi ?\n\n"
            f"📅 **Formats acceptés :**\n"
            f"• `25/12/2025 20:30` (JJ/MM/AAAA HH:MM)\n"
            f"• `2025-12-25 20:30` (AAAA-MM-JJ HH:MM)\n"
            f"• `demain 20h` ou `demain 20:30`\n"
            f"• `dans 1 semaine 19h`\n\n"
            f"⏰ **Important :** L'heure est en UTC (temps universel)"
        )
        await message.channel.send(embed=embed)
    
    async def handle_start_date(self, message: discord.Message, session):
        """Gère la saisie de la date de début"""
        date_input = message.content.strip()
        
        try:
            parsed_date = self.parse_date(date_input)
            
            # Vérifier que la date est dans le futur
            if parsed_date <= datetime.utcnow():
                embed = create_error_embed(
                    "❌ Date invalide",
                    "La date doit être dans le futur.\n\n"
                    f"Date saisie : {parsed_date.strftime('%d/%m/%Y à %H:%M UTC')}\n"
                    f"Maintenant : {datetime.utcnow().strftime('%d/%m/%Y à %H:%M UTC')}"
                )
                await message.channel.send(embed=embed)
                return
            
            # Vérifier que ce n'est pas trop loin dans le futur (6 mois max pour tournois)
            if parsed_date > datetime.utcnow() + timedelta(days=180):
                embed = create_error_embed(
                    "❌ Date trop éloignée",
                    "Le tournoi ne peut pas être programmé à plus de 6 mois.\n\n"
                    "Choisissez une date plus proche."
                )
                await message.channel.send(embed=embed)
                return
            
            session.data['start_date'] = parsed_date.isoformat()
            
            embed = create_success_embed(
                "✅ Date enregistrée",
                f"**Début du tournoi :** {parsed_date.strftime('%d/%m/%Y à %H:%M UTC')}\n"
                f"**Discord :** <t:{int(parsed_date.timestamp())}:F>\n\n"
                f"Combien de participants maximum ?\n\n"
                f"👥 **Suggestions selon le type :**\n"
                f"• Élimination simple : 8, 16, 32, 64\n"
                f"• Double élimination : 8, 16, 32\n"
                f"• Round Robin : 6-12 participants\n"
                f"• Système suisse : 8-64 participants\n\n"
                f"💡 *Choisissez un nombre pair de préférence*"
            )
            await message.channel.send(embed=embed)
            
        except ValueError as e:
            embed = create_error_embed(
                "❌ Format de date invalide",
                f"Je n'ai pas pu comprendre cette date : \"{date_input}\"\n\n"
                f"📅 **Formats acceptés :**\n"
                f"• `25/12/2025 20:30`\n"
                f"• `2025-12-25 20:30`\n"
                f"• `demain 20h`\n"
                f"• `dans 1 semaine 19:30`\n\n"
                f"Réessayez avec un de ces formats."
            )
            await message.channel.send(embed=embed)
    
    def parse_date(self, date_input: str) -> datetime:
        """Parse une date en format naturel (même logique que pour les événements)"""
        date_input = date_input.lower().strip()
        
        # Format relatif : "demain 20h", "dans 1 semaine 19:30"
        if "demain" in date_input:
            time_match = re.search(r'(\d{1,2})h?:?(\d{0,2})', date_input)
            if time_match:
                hour = int(time_match.group(1))
                minute = int(time_match.group(2)) if time_match.group(2) else 0
                tomorrow = datetime.utcnow() + timedelta(days=1)
                return tomorrow.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        if "dans" in date_input and ("jour" in date_input or "semaine" in date_input):
            if "semaine" in date_input:
                weeks_match = re.search(r'dans\s+(\d+)\s+semaines?', date_input)
                time_match = re.search(r'(\d{1,2})h?:?(\d{0,2})', date_input)
                if weeks_match and time_match:
                    weeks = int(weeks_match.group(1))
                    hour = int(time_match.group(1))
                    minute = int(time_match.group(2)) if time_match.group(2) else 0
                    future_date = datetime.utcnow() + timedelta(weeks=weeks)
                    return future_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
            else:
                days_match = re.search(r'dans\s+(\d+)\s+jours?', date_input)
                time_match = re.search(r'(\d{1,2})h?:?(\d{0,2})', date_input)
                if days_match and time_match:
                    days = int(days_match.group(1))
                    hour = int(time_match.group(1))
                    minute = int(time_match.group(2)) if time_match.group(2) else 0
                    future_date = datetime.utcnow() + timedelta(days=days)
                    return future_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        # Format standard : DD/MM/YYYY HH:MM ou YYYY-MM-DD HH:MM
        try:
            # Essayer DD/MM/YYYY HH:MM
            if '/' in date_input:
                return datetime.strptime(date_input, '%d/%m/%Y %H:%M')
            # Essayer YYYY-MM-DD HH:MM
            elif '-' in date_input:
                return datetime.strptime(date_input, '%Y-%m-%d %H:%M')
        except ValueError:
            pass
        
        raise ValueError(f"Format de date non reconnu : {date_input}")
    
    async def handle_max_participants(self, message: discord.Message, session):
        """Gère la saisie du nombre maximum de participants"""
        try:
            max_participants = int(message.content.strip())
            
            if max_participants < 2:
                embed = create_error_embed(
                    "❌ Nombre insuffisant",
                    "Un tournoi doit avoir au moins 2 participants."
                )
                await message.channel.send(embed=embed)
                return
            
            if max_participants > 256:
                embed = create_error_embed(
                    "❌ Nombre trop élevé",
                    "Le maximum est de 256 participants pour un tournoi.\n\n"
                    "Pour plus de participants, divisez en plusieurs tournois."
                )
                await message.channel.send(embed=embed)
                return
            
            session.data['max_participants'] = max_participants
            
            embed = create_success_embed(
                "✅ Participants enregistrés",
                f"**Maximum :** {max_participants} participants\n\n"
                f"Quel sera le format des matchs ?\n\n"
                f"⚔️ **Formats courants :**\n"
                f"• `Best of 1` (Bo1) - Un seul match\n"
                f"• `Best of 3` (Bo3) - Premier à 2 victoires\n"
                f"• `Best of 5` (Bo5) - Premier à 3 victoires\n"
                f"• `Best of 7` (Bo7) - Premier à 4 victoires\n\n"
                f"📝 **Ou décrivez votre format personnalisé**"
            )
            await message.channel.send(embed=embed)
            
        except ValueError:
            embed = create_error_embed(
                "❌ Format invalide",
                "Veuillez saisir un nombre entier.\n\n"
                f"Exemple : `16`, `32`, `64`"
            )
            await message.channel.send(embed=embed)
    
    async def handle_format(self, message: discord.Message, session):
        """Gère la saisie du format"""
        format_input = message.content.strip().lower()
        
        # Formats standards
        format_mapping = {
            'best of 1': 'Best of 1',
            'bo1': 'Best of 1',
            'best of 3': 'Best of 3',
            'bo3': 'Best of 3',
            'best of 5': 'Best of 5',
            'bo5': 'Best of 5',
            'best of 7': 'Best of 7',
            'bo7': 'Best of 7'
        }
        
        if format_input in format_mapping:
            match_format = format_mapping[format_input]
        else:
            # Format personnalisé
            if len(format_input) > 100:
                embed = create_error_embed(
                    "❌ Format trop long",
                    "La description du format ne peut pas dépasser 100 caractères."
                )
                await message.channel.send(embed=embed)
                return
            match_format = message.content.strip()
        
        session.data['format'] = match_format
        
        embed = create_success_embed(
            "✅ Format enregistré",
            f"**Format des matchs :** {match_format}\n\n"
            f"Maintenant, précisez les règles du tournoi.\n\n"
            f"📋 **Incluez :**\n"
            f"• Règles de gameplay spécifiques\n"
            f"• Restrictions d'équipement\n"
            f"• Comportement attendu\n"
            f"• Sanctions possibles\n\n"
            f"💡 *Tapez \"skip\" pour des règles standards*"
        )
        await message.channel.send(embed=embed)
    
    async def handle_rules(self, message: discord.Message, session):
        """Gère la saisie des règles"""
        rules_input = message.content.strip()
        
        if rules_input.lower() in ['skip', 'ignorer', 'passer', 'standard']:
            rules = "Règles standards de Star Citizen. Fair-play requis. Pas de triche ou d'exploitation de bugs."
        else:
            if len(rules_input) > 2000:
                embed = create_error_embed(
                    "❌ Règles trop longues",
                    "Les règles ne peuvent pas dépasser 2000 caractères.\n\n"
                    "Essayez de résumer les points essentiels."
                )
                await message.channel.send(embed=embed)
                return
            rules = rules_input
        
        session.data['rules'] = rules
        
        embed = create_success_embed(
            "✅ Règles enregistrées",
            f"**Règles :** {rules[:200]}{'...' if len(rules) > 200 else ''}\n\n"
            f"Enfin, quels sont les prix/récompenses ?\n\n"
            f"🏆 **Exemples :**\n"
            f"• `1er: 100k aUEC, 2e: 50k aUEC, 3e: 25k aUEC`\n"
            f"• `Vainqueur: Titre + Badge Discord`\n"
            f"• `Équipe gagnante: Ship pack`\n\n"
            f"💡 *Tapez \"aucun\" s'il n'y a pas de prix*"
        )
        await message.channel.send(embed=embed)
    
    async def handle_prizes(self, message: discord.Message, session):
        """Gère la saisie des prix"""
        prizes_input = message.content.strip()
        
        if prizes_input.lower() in ['aucun', 'aucune', 'none', 'pas de prix', 'skip']:
            prizes = None
        else:
            if len(prizes_input) > 500:
                embed = create_error_embed(
                    "❌ Description des prix trop longue",
                    "La description des prix ne peut pas dépasser 500 caractères."
                )
                await message.channel.send(embed=embed)
                return
            prizes = prizes_input
        
        session.data['prizes'] = prizes
        
        # Générer le résumé final
        await self.send_confirmation(message, session)
    
    async def send_confirmation(self, message: discord.Message, session):
        """Envoie la confirmation finale"""
        data = session.data
        start_time = datetime.fromisoformat(data['start_date'])
        
        embed = create_embed(
            "📋 Confirmation - Récapitulatif du tournoi",
            "Voici le récapitulatif de votre tournoi. Vérifiez tous les détails :",
            color=0xF59E0B
        )
        
        embed.add_field(
            name="🏆 Informations Générales",
            value=f"**Nom :** {data['name']}\n"
                  f"**Jeu :** {data['game']}\n"
                  f"**Organisation :** {data['org_name']}",
            inline=False
        )
        
        embed.add_field(
            name="📅 Planning & Format",
            value=f"**Début :** <t:{int(start_time.timestamp())}:F>\n"
                  f"**Type :** {data['tournament_type'].replace('_', ' ').title()}\n"
                  f"**Format :** {data['format']}",
            inline=False
        )
        
        embed.add_field(
            name="👥 Participants & Prix",
            value=f"**Maximum :** {data['max_participants']} participants\n"
                  f"**Prix :** {data.get('prizes', 'Aucun prix')}\n",
            inline=False
        )
        
        if len(data['rules']) <= 200:
            embed.add_field(name="📋 Règles", value=data['rules'], inline=False)
        else:
            embed.add_field(name="📋 Règles", value=data['rules'][:200] + "...", inline=False)
        
        embed.add_field(
            name="✅ Validation",
            value="Tapez `confirmer` pour créer le tournoi\n"
                  "Tapez `modifier` pour changer des éléments\n"
                  "Tapez `annuler` pour tout annuler",
            inline=False
        )
        
        await message.channel.send(embed=embed)
    
    async def handle_confirmation(self, message: discord.Message, session):
        """Gère la confirmation finale"""
        response = message.content.strip().lower()
        
        if response in ['confirmer', 'confirm', 'oui', 'yes', 'valider']:
            await self.create_tournament(message, session)
        elif response in ['modifier', 'edit', 'changer']:
            await self.handle_modification(message, session)
        elif response in ['annuler', 'cancel', 'non', 'no']:
            await self.cancel_creation(message, session)
        else:
            embed = create_warning_embed(
                "❓ Réponse non reconnue",
                "Veuillez répondre :\n"
                "• `confirmer` pour créer le tournoi\n"
                "• `modifier` pour changer des éléments\n"
                "• `annuler` pour tout annuler"
            )
            await message.channel.send(embed=embed)
    
    async def create_tournament(self, message: discord.Message, session):
        """Crée le tournoi final"""
        try:
            # Préparer les données pour l'API
            tournament_data = {
                'name': session.data['name'],
                'description': session.data['description'],
                'game': session.data['game'],
                'tournament_type': session.data['tournament_type'],
                'start_date': session.data['start_date'],
                'max_participants': session.data['max_participants'],
                'format': session.data['format'],
                'rules': session.data['rules'],
                'prize_pool': session.data.get('prizes'),
                'discord_integration_enabled': True,
                'status': 'draft'  # Commence en brouillon
            }
            
            # Créer le tournoi via l'API
            async with self.api as api:
                # Note: Adapter selon l'API réelle
                result = await api.create_tournament(session.data['org_id'], tournament_data)
            
            embed = create_success_embed(
                "🎉 Tournoi créé avec succès !",
                f"**{session.data['name']}** a été créé !\n\n"
                f"🔗 **Lien :** [Voir le tournoi](http://localhost:3000/tournaments/{result['tournament_id']})\n"
                f"📅 **Début :** <t:{int(datetime.fromisoformat(session.data['start_date']).timestamp())}:F>\n"
                f"👥 **Organisation :** {session.data['org_name']}\n"
                f"🏆 **Max participants :** {session.data['max_participants']}\n\n"
                f"Le tournoi sera automatiquement annoncé sur les serveurs Discord configurés !"
            )
            
            await message.channel.send(embed=embed)
            
            # Terminer la session
            from interactive_events import SessionManager
            session_manager = SessionManager()
            session_manager.end_session(session.session_id)
            
        except Exception as e:
            embed = create_error_embed(
                "❌ Erreur lors de la création",
                f"Impossible de créer le tournoi :\n{str(e)}\n\n"
                f"Vérifiez vos permissions et réessayez."
            )
            await message.channel.send(embed=embed)
    
    async def handle_modification(self, message: discord.Message, session):
        """Gère la modification d'éléments"""
        embed = create_info_embed(
            "🔧 Modification",
            "Quelle information voulez-vous modifier ?\n\n"
            "**Disponible :**\n"
            "• `nom` - Changer le nom\n"
            "• `description` - Changer la description\n"
            "• `jeu` - Changer le jeu\n"
            "• `type` - Changer le type de tournoi\n"
            "• `date` - Changer la date/heure\n"
            "• `participants` - Changer le nombre max\n"
            "• `format` - Changer le format des matchs\n"
            "• `règles` - Changer les règles\n"
            "• `prix` - Changer les prix\n\n"
            "Tapez le nom de ce que vous voulez modifier."
        )
        await message.channel.send(embed=embed)
        
        # Marquer pour modification dans la prochaine étape
        session.data['_modifying'] = True
    
    async def cancel_creation(self, message: discord.Message, session):
        """Annule la création"""
        embed = create_success_embed(
            "✅ Création annulée",
            "La création du tournoi a été annulée.\n\n"
            "Toutes les données ont été supprimées.\n"
            "Vous pouvez recommencer avec `/create-tournament`."
        )
        await message.channel.send(embed=embed)
        
        # Terminer la session
        from interactive_events import SessionManager
        session_manager = SessionManager()
        session_manager.end_session(session.session_id)