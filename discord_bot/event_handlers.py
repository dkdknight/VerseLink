import discord
from typing import Optional, Dict, Any, List
import logging
from datetime import datetime, timedelta, timezone
import re

from verselink_api import VerselinkAPI
from utils import *
from config import Config

logger = logging.getLogger(__name__)

class EventCreationHandler:
    """Gestionnaire pour la création d'événements"""
    
    def __init__(self, api: VerselinkAPI):
        self.api = api
        
    async def handle_event_message(self, message: discord.Message, session):
        """Gère les messages pour la création d'événements"""
        current_step = self.get_current_step(session)
        
        if current_step == 'title':
            await self.handle_title(message, session)
        elif current_step == 'description':
            await self.handle_description(message, session)
        elif current_step == 'organization':
            await self.handle_organization(message, session)
        elif current_step == 'date':
            await self.handle_date(message, session)
        elif current_step == 'duration':
            await self.handle_duration(message, session)
        elif current_step == 'location':
            await self.handle_location(message, session)
        elif current_step == 'max_participants':
            await self.handle_max_participants(message, session)
        elif current_step == 'roles':
            await self.handle_roles(message, session)
        elif current_step == 'visibility':
            await self.handle_visibility(message, session)
        elif current_step == 'confirmation':
            await self.handle_confirmation(message, session)
    
    def get_current_step(self, session) -> str:
        """Détermine l'étape actuelle basée sur les données collectées"""
        steps = ['title', 'description', 'organization', 'date', 'duration', 
                'location', 'max_participants', 'roles', 'visibility', 'confirmation']
        
        for step in steps:
            if step not in session.data:
                return step
        return 'confirmation'
    
    async def handle_title(self, message: discord.Message, session):
        """Gère la saisie du titre"""
        title = message.content.strip()
        
        if len(title) < 3:
            embed = create_error_embed(
                "❌ Titre trop court",
                "Le titre doit contenir au moins 3 caractères.\n\n"
                "Essayez quelque chose de plus descriptif comme :\n"
                "• \"Raid sur Jumptown\"\n"
                "• \"Course Murray Cup\"\n"
                "• \"Exploration Pyro\""
            )
            await message.channel.send(embed=embed)
            return
            
        if len(title) > 100:
            embed = create_error_embed(
                "❌ Titre trop long",
                "Le titre ne peut pas dépasser 100 caractères.\n\n"
                "Essayez de le raccourcir tout en gardant l'essentiel."
            )
            await message.channel.send(embed=embed)
            return
        
        session.data['title'] = title
        
        embed = create_success_embed(
            "✅ Titre enregistré",
            f"**Titre :** {title}\n\n"
            f"Maintenant, décrivez votre événement en quelques phrases.\n\n"
            f"💡 **Une bonne description contient :**\n"
            f"• L'objectif de l'événement\n"
            f"• Ce qui va se passer\n"
            f"• Prérequis éventuels\n"
            f"• Récompenses ou butin\n\n"
            f"📝 **Exemple :**\n"
            f"*\"Opération de nettoyage sur Jumptown. Nous allons sécuriser la zone et éliminer les hostiles. "
            f"Apportez vos meilleurs vaisseaux de combat ! Butin partagé entre tous les participants.\"*"
        )
        await message.channel.send(embed=embed)
    
    async def handle_description(self, message: discord.Message, session):
        """Gère la saisie de la description"""
        description = message.content.strip()
        
        if len(description) < 10:
            embed = create_error_embed(
                "❌ Description trop courte",
                "La description doit contenir au moins 10 caractères.\n\n"
                "Donnez plus de détails sur votre événement !"
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
        
        # Récupérer les organisations de l'utilisateur
        embed = create_success_embed(
            "✅ Description enregistrée",
            f"**Description :** {description[:200]}{'...' if len(description) > 200 else ''}\n\n"
            f"Maintenant, choisissez l'organisation qui héberge cet événement.\n\n"
            f"Envoyez-moi :\n"
            f"• Le **nom** de l'organisation\n"
            f"• Ou son **tag** (ex: TEST, CORP)\n"
            f"• Ou son **ID** si vous le connaissez\n\n"
            f"💡 *Si vous n'êtes membre d'aucune organisation, tapez \"aucune\"*"
        )
        await message.channel.send(embed=embed)
    
    async def handle_organization(self, message: discord.Message, session):
        """Gère la sélection de l'organisation"""
        org_input = message.content.strip()
        
        if org_input.lower() in ['aucune', 'none', 'pas', 'non']:
            embed = create_error_embed(
                "❌ Organisation requise",
                "Vous devez être membre d'une organisation pour créer un événement.\n\n"
                "Créez d'abord une organisation sur [VerseLink](http://localhost:3000/organizations/create) "
                "ou rejoignez-en une existante."
            )
            await message.channel.send(embed=embed)
            return
        
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
                f"Maintenant, définissons la date et l'heure de l'événement.\n\n"
                f"📅 **Formats acceptés :**\n"
                f"• `25/12/2025 20:30` (JJ/MM/AAAA HH:MM)\n"
                f"• `2025-12-25 20:30` (AAAA-MM-JJ HH:MM)\n"
                f"• `demain 20h` ou `demain 20:30`\n"
                f"• `dans 2 jours 19h`\n\n"
                f"⏰ **Important :** L'heure est en UTC (temps universel)"
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
    
    async def handle_date(self, message: discord.Message, session):
        """Gère la saisie de la date"""
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
            
            # Vérifier que ce n'est pas trop loin dans le futur (1 an max)
            if parsed_date > datetime.utcnow() + timedelta(days=365):
                embed = create_error_embed(
                    "❌ Date trop éloignée",
                    "L'événement ne peut pas être programmé à plus d'un an.\n\n"
                    "Choisissez une date plus proche."
                )
                await message.channel.send(embed=embed)
                return
            
            session.data['start_at_utc'] = parsed_date.isoformat()
            
            embed = create_success_embed(
                "✅ Date enregistrée",
                f"**Date et heure :** {parsed_date.strftime('%d/%m/%Y à %H:%M UTC')}\n"
                f"**Discord :** <t:{int(parsed_date.timestamp())}:F>\n\n"
                f"Maintenant, indiquez la durée de l'événement en minutes.\n\n"
                f"⏱️ **Exemples :**\n"
                f"• `60` pour 1 heure\n"
                f"• `120` pour 2 heures\n"
                f"• `90` pour 1h30\n"
                f"• `240` pour 4 heures"
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
                f"• `dans 3 jours 19:30`\n\n"
                f"Réessayez avec un de ces formats."
            )
            await message.channel.send(embed=embed)
    
    def parse_date(self, date_input: str) -> datetime:
        """Parse une date en format naturel"""
        date_input = date_input.lower().strip()
        
        # Format relatif : "demain 20h", "dans 2 jours 19:30"
        if "demain" in date_input:
            time_match = re.search(r'(\d{1,2})h?:?(\d{0,2})', date_input)
            if time_match:
                hour = int(time_match.group(1))
                minute = int(time_match.group(2)) if time_match.group(2) else 0
                tomorrow = datetime.utcnow() + timedelta(days=1)
                return tomorrow.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        if "dans" in date_input and "jour" in date_input:
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
    
    async def handle_duration(self, message: discord.Message, session):
        """Gère la saisie de la durée"""
        try:
            duration = int(message.content.strip())
            
            if duration < 15:
                embed = create_error_embed(
                    "❌ Durée trop courte",
                    "La durée minimum est de 15 minutes.\n\n"
                    "Pour un événement si court, utilisez plutôt le chat vocal !"
                )
                await message.channel.send(embed=embed)
                return
            
            if duration > 1440:  # 24 heures
                embed = create_error_embed(
                    "❌ Durée trop longue",
                    "La durée maximum est de 24 heures (1440 minutes).\n\n"
                    "Pour des événements plus longs, créez plusieurs sessions."
                )
                await message.channel.send(embed=embed)
                return
            
            session.data['duration_minutes'] = duration
            
            # Calculer l'heure de fin
            start_time = datetime.fromisoformat(session.data['start_at_utc'])
            end_time = start_time + timedelta(minutes=duration)
            
            hours = duration // 60
            minutes = duration % 60
            duration_str = f"{hours}h{minutes:02d}" if hours > 0 else f"{minutes}min"
            
            embed = create_success_embed(
                "✅ Durée enregistrée",
                f"**Durée :** {duration_str} ({duration} minutes)\n"
                f"**Fin prévue :** <t:{int(end_time.timestamp())}:F>\n\n"
                f"Maintenant, indiquez le lieu de l'événement.\n\n"
                f"🌍 **Exemples :**\n"
                f"• `Jumptown, Yela`\n"
                f"• `Station Port Olisar`\n"
                f"• `Système Pyro`\n"
                f"• `Arena Commander`\n\n"
                f"💡 *Ou tapez \"skip\" pour ignorer cette étape*"
            )
            await message.channel.send(embed=embed)
            
        except ValueError:
            embed = create_error_embed(
                "❌ Durée invalide",
                "Veuillez saisir un nombre entier de minutes.\n\n"
                f"Exemples : `60`, `120`, `90`"
            )
            await message.channel.send(embed=embed)
    
    async def handle_location(self, message: discord.Message, session):
        """Gère la saisie du lieu"""
        location = message.content.strip()
        
        if location.lower() in ['skip', 'ignorer', 'passer', '']:
            session.data['location'] = None
        else:
            if len(location) > 200:
                embed = create_error_embed(
                    "❌ Lieu trop long",
                    "Le lieu ne peut pas dépasser 200 caractères."
                )
                await message.channel.send(embed=embed)
                return
            session.data['location'] = location
        
        embed = create_success_embed(
            "✅ Lieu enregistré",
            f"**Lieu :** {session.data.get('location', 'Non spécifié')}\n\n"
            f"Combien de participants maximum voulez-vous ?\n\n"
            f"👥 **Options :**\n"
            f"• Un nombre (ex: `20`, `50`)\n"
            f"• `illimité` pour aucune limite\n\n"
            f"💡 *Conseil : Limitez selon la capacité de votre organisation*"
        )
        await message.channel.send(embed=embed)
    
    async def handle_max_participants(self, message: discord.Message, session):
        """Gère la saisie du nombre maximum de participants"""
        input_text = message.content.strip().lower()
        
        if input_text in ['illimité', 'illimite', 'unlimited', 'infini', 'aucune', 'skip']:
            session.data['max_participants'] = None
            max_text = "Illimité"
        else:
            try:
                max_participants = int(input_text)
                if max_participants < 1:
                    embed = create_error_embed(
                        "❌ Nombre invalide",
                        "Le nombre de participants doit être au moins 1.\n\n"
                        "Ou tapez `illimité` pour aucune limite."
                    )
                    await message.channel.send(embed=embed)
                    return
                
                if max_participants > 1000:
                    embed = create_error_embed(
                        "❌ Nombre trop élevé",
                        "Le maximum est de 1000 participants.\n\n"
                        "Pour plus, utilisez `illimité`."
                    )
                    await message.channel.send(embed=embed)
                    return
                
                session.data['max_participants'] = max_participants
                max_text = f"{max_participants} participants"
                
            except ValueError:
                embed = create_error_embed(
                    "❌ Format invalide",
                    "Veuillez saisir :\n"
                    "• Un nombre (ex: `20`)\n"
                    "• Ou `illimité`"
                )
                await message.channel.send(embed=embed)
                return
        
        embed = create_success_embed(
            "✅ Participants enregistrés",
            f"**Maximum :** {max_text}\n\n"
            f"Voulez-vous créer des rôles spécifiques pour cet événement ?\n\n"
            f"🎭 **Exemples de rôles :**\n"
            f"• Pilote (10 places)\n"
            f"• Support (5 places)\n"
            f"• Commandant (1 place)\n\n"
            f"📝 **Format :** `Nom du rôle : Nombre de places : Description`\n"
            f"📝 **Exemple :** `Pilote : 10 : Pilotes principaux pour l'assaut`\n\n"
            f"💡 *Tapez \"skip\" pour ignorer ou créer plusieurs rôles séparés par des retours à la ligne*"
        )
        await message.channel.send(embed=embed)
    
    async def handle_roles(self, message: discord.Message, session):
        """Gère la création des rôles"""
        roles_text = message.content.strip()
        
        if roles_text.lower() in ['skip', 'ignorer', 'passer', 'non', 'aucun']:
            session.data['roles'] = []
        else:
            try:
                roles = []
                lines = roles_text.split('\n')
                
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    
                    parts = line.split(':')
                    if len(parts) < 2:
                        raise ValueError(f"Format invalide pour : {line}")
                    
                    name = parts[0].strip()
                    capacity = int(parts[1].strip())
                    description = parts[2].strip() if len(parts) > 2 else ""
                    
                    if capacity < 1:
                        raise ValueError("La capacité doit être au moins 1")
                    
                    roles.append({
                        'name': name,
                        'capacity': capacity,
                        'description': description
                    })
                
                if len(roles) > 10:
                    embed = create_error_embed(
                        "❌ Trop de rôles",
                        "Maximum 10 rôles par événement.\n\n"
                        "Essayez de regrouper certains rôles similaires."
                    )
                    await message.channel.send(embed=embed)
                    return
                
                session.data['roles'] = roles
                
            except (ValueError, IndexError) as e:
                embed = create_error_embed(
                    "❌ Format des rôles invalide",
                    f"Erreur : {str(e)}\n\n"
                    f"**Format attendu :**\n"
                    f"`Nom : Capacité : Description`\n\n"
                    f"**Exemple :**\n"
                    f"`Pilote : 10 : Pilotes principaux`\n"
                    f"`Support : 5 : Équipe de soutien`"
                )
                await message.channel.send(embed=embed)
                return
        
        roles_summary = "Aucun rôle spécifique"
        if session.data['roles']:
            roles_summary = "\n".join([f"• {r['name']} ({r['capacity']} places)" for r in session.data['roles']])
        
        embed = create_success_embed(
            "✅ Rôles enregistrés",
            f"**Rôles :**\n{roles_summary}\n\n"
            f"Enfin, choisissez la visibilité de votre événement :\n\n"
            f"👁️ **Options :**\n"
            f"• `public` - Visible par tous\n"
            f"• `unlisted` - Visible avec le lien uniquement\n"
            f"• `private` - Visible par les membres de l'organisation seulement"
        )
        await message.channel.send(embed=embed)
    
    async def handle_visibility(self, message: discord.Message, session):
        """Gère la sélection de la visibilité"""
        visibility = message.content.strip().lower()
        
        if visibility not in ['public', 'unlisted', 'private']:
            embed = create_error_embed(
                "❌ Visibilité invalide",
                "Choisissez parmi :\n"
                "• `public` - Visible par tous\n"
                "• `unlisted` - Visible avec le lien uniquement\n"
                "• `private` - Visible par les membres de l'organisation seulement"
            )
            await message.channel.send(embed=embed)
            return
        
        session.data['visibility'] = visibility
        
        # Générer le résumé final
        await self.send_confirmation(message, session)
    
    async def send_confirmation(self, message: discord.Message, session):
        """Envoie la confirmation finale"""
        data = session.data
        start_time = datetime.fromisoformat(data['start_at_utc'])
        
        embed = create_embed(
            "📋 Confirmation - Récapitulatif de l'événement",
            "Voici le récapitulatif de votre événement. Vérifiez tous les détails :",
            color=0xF59E0B
        )
        
        embed.add_field(
            name="📝 Informations Générales",
            value=f"**Titre :** {data['title']}\n"
                  f"**Type :** {data['type'].title()}\n"
                  f"**Organisation :** {data['org_name']}",
            inline=False
        )
        
        embed.add_field(
            name="📅 Planning",
            value=f"**Début :** <t:{int(start_time.timestamp())}:F>\n"
                  f"**Durée :** {data['duration_minutes']} minutes\n"
                  f"**Lieu :** {data.get('location', 'Non spécifié')}",
            inline=False
        )
        
        embed.add_field(
            name="👥 Participants",
            value=f"**Maximum :** {data.get('max_participants', 'Illimité')}\n"
                  f"**Rôles :** {len(data.get('roles', []))} rôle(s) défini(s)\n"
                  f"**Visibilité :** {data['visibility'].title()}",
            inline=False
        )
        
        if data.get('roles'):
            roles_text = "\n".join([f"• {r['name']} ({r['capacity']})" for r in data['roles']])
            embed.add_field(name="🎭 Rôles Définis", value=roles_text, inline=False)
        
        embed.add_field(
            name="✅ Validation",
            value="Tapez `confirmer` pour créer l'événement\n"
                  "Tapez `modifier` pour changer des éléments\n"
                  "Tapez `annuler` pour tout annuler",
            inline=False
        )
        
        await message.channel.send(embed=embed)
    
    async def handle_confirmation(self, message: discord.Message, session):
        """Gère la confirmation finale"""
        response = message.content.strip().lower()
        
        if response in ['confirmer', 'confirm', 'oui', 'yes', 'valider']:
            await self.create_event(message, session)
        elif response in ['modifier', 'edit', 'changer']:
            await self.handle_modification(message, session)
        elif response in ['annuler', 'cancel', 'non', 'no']:
            await self.cancel_creation(message, session)
        else:
            embed = create_warning_embed(
                "❓ Réponse non reconnue",
                "Veuillez répondre :\n"
                "• `confirmer` pour créer l'événement\n"
                "• `modifier` pour changer des éléments\n"
                "• `annuler` pour tout annuler"
            )
            await message.channel.send(embed=embed)
    
    async def create_event(self, message: discord.Message, session):
        """Crée l'événement final"""
        try:
            # Préparer les données pour l'API
            event_data = {
                'title': session.data['title'],
                'description': session.data['description'],  
                'type': session.data['type'],
                'start_at_utc': session.data['start_at_utc'],
                'duration_minutes': session.data['duration_minutes'],
                'location': session.data.get('location'),
                'max_participants': session.data.get('max_participants'),
                'visibility': session.data['visibility'],
                'discord_integration_enabled': True,
                'roles': session.data.get('roles', []),
                'allowed_org_ids': []
            }
            
            # Créer l'événement
            async with self.api as api:
                result = await api.create_event(session.data['org_id'], event_data)
            
            embed = create_success_embed(
                "🎉 Événement créé avec succès !",
                f"**{session.data['title']}** a été créé !\n\n"
                f"🔗 **Lien :** [Voir l'événement](http://localhost:3000/events/{result['event_id']})\n"
                f"📅 **Début :** <t:{int(datetime.fromisoformat(session.data['start_at_utc']).timestamp())}:F>\n"
                f"👥 **Organisation :** {session.data['org_name']}\n\n"
                f"L'événement sera automatiquement annoncé sur les serveurs Discord configurés !"
            )
            
            await message.channel.send(embed=embed)
            
            # Terminer la session
            from interactive_events import SessionManager
            session_manager = SessionManager()
            session_manager.end_session(session.session_id)
            
        except Exception as e:
            embed = create_error_embed(
                "❌ Erreur lors de la création",
                f"Impossible de créer l'événement :\n{str(e)}\n\n"
                f"Vérifiez vos permissions et réessayez."
            )
            await message.channel.send(embed=embed)
    
    async def handle_modification(self, message: discord.Message, session):
        """Gère la modification d'éléments"""
        embed = create_info_embed(
            "🔧 Modification",
            "Quelle information voulez-vous modifier ?\n\n"
            "**Disponible :**\n"
            "• `titre` - Changer le titre\n"
            "• `description` - Changer la description\n"
            "• `date` - Changer la date/heure\n"
            "• `durée` - Changer la durée\n"
            "• `lieu` - Changer le lieu\n"
            "• `participants` - Changer le nombre max\n"
            "• `rôles` - Redéfinir les rôles\n"
            "• `visibilité` - Changer la visibilité\n\n"
            "Tapez le nom de ce que vous voulez modifier."
        )
        await message.channel.send(embed=embed)
        
        # Marquer pour modification dans la prochaine étape
        session.data['_modifying'] = True
    
    async def cancel_creation(self, message: discord.Message, session):
        """Annule la création"""
        embed = create_success_embed(
            "✅ Création annulée",
            "La création de l'événement a été annulée.\n\n"
            "Toutes les données ont été supprimées.\n"
            "Vous pouvez recommencer avec `/create-event`."
        )
        await message.channel.send(embed=embed)
        
        # Terminer la session
        from interactive_events import SessionManager
        session_manager = SessionManager()
        session_manager.end_session(session.session_id)