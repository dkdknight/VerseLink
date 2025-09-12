import discord
from discord.ext import commands
import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
import json

from verselink_api import VerselinkAPI
from utils import *
from config import Config

logger = logging.getLogger(__name__)

class AutoPublisher:
    """Système de publication automatique des événements sur Discord"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.api = VerselinkAPI()
        # Mapping des emojis pour les rôles
        self.role_emojis = [
            "1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", 
            "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"
        ]
        self.default_join_emoji = "✅"
        self.reserve_emoji = "🟡"
        
    async def publish_event(self, event_data: Dict[str, Any], org_config: Dict[str, Any]):
        """Publie un événement sur Discord avec système de réactions"""
        try:
            guild_id = org_config.get('discord_guild_id')
            channel_id = org_config.get('events_channel_id')
            
            if not guild_id or not channel_id:
                logger.warning(f"Configuration Discord manquante pour l'organisation {event_data.get('org_name')}")
                return None
            
            guild = self.bot.get_guild(int(guild_id))
            if not guild:
                logger.error(f"Guild {guild_id} introuvable")
                return None
                
            channel = guild.get_channel(int(channel_id))
            if not channel:
                logger.error(f"Channel {channel_id} introuvable dans {guild.name}")
                return None
            
            # Créer l'embed de l'événement
            embed = await self.create_event_embed(event_data)
            
            # Publier le message
            message = await channel.send(embed=embed)
            
            # Ajouter les réactions pour l'inscription
            await self.add_event_reactions(message, event_data)
            
            # Sauvegarder l'ID du message pour la gestion des inscriptions
            await self.save_message_mapping(event_data['id'], message.id, channel.id, guild.id)
            
            logger.info(f"Événement {event_data['title']} publié sur {guild.name}#{channel.name}")
            return message
            
        except Exception as e:
            logger.error(f"Erreur lors de la publication de l'événement: {e}")
            return None
    
    async def create_event_embed(self, event_data: Dict[str, Any]) -> discord.Embed:
        """Crée l'embed pour l'événement"""
        
        # Couleurs par type d'événement
        type_colors = {
            'raid': 0xFF6B6B,
            'course': 0x4ECDC4,
            'pvp': 0xFF8E53,
            'fps': 0x95E1D3,
            'salvaging': 0xFFD93D,
            'logistique': 0x6C5CE7,
            'exploration': 0x00B894,
            'mining': 0xFDCB6E,
            'trading': 0x0984E3,
            'roleplay': 0xE17055,
            'autre': 0x74B9FF
        }
        
        event_type = event_data.get('type', 'autre')
        color = type_colors.get(event_type, 0x3B82F6)
        
        # Icônes par type
        type_icons = {
            'raid': '🎯',
            'course': '🏁',
            'pvp': '⚔️',
            'fps': '🔫',
            'salvaging': '🔧',
            'logistique': '📦',
            'exploration': '🌍',
            'mining': '⛏️',
            'trading': '💼',
            'roleplay': '🎭',
            'autre': '📋'
        }
        
        icon = type_icons.get(event_type, '📋')
        type_name = event_type.replace('_', ' ').title()
        
        # Créer l'embed
        embed = discord.Embed(
            title=f"{icon} {event_data['title']}",
            description=event_data.get('description', 'Aucune description'),
            color=color,
            timestamp=datetime.fromisoformat(event_data['start_at_utc'].replace('Z', '+00:00'))
        )
        
        # Informations de base
        embed.add_field(
            name="📅 Date et Heure",
            value=f"<t:{int(datetime.fromisoformat(event_data['start_at_utc'].replace('Z', '+00:00')).timestamp())}:F>",
            inline=True
        )
        
        embed.add_field(
            name="⏱️ Durée",
            value=f"{event_data.get('duration_minutes', 60)} minutes",
            inline=True
        )
        
        embed.add_field(
            name="🏷️ Type",
            value=type_name,
            inline=True
        )
        
        # Lieu si spécifié
        if event_data.get('location'):
            embed.add_field(
                name="📍 Lieu",
                value=event_data['location'],
                inline=True
            )
        
        # Participants
        max_participants = event_data.get('max_participants')
        current_count = len(event_data.get('signups', []))
        
        if max_participants:
            embed.add_field(
                name="👥 Participants",
                value=f"{current_count}/{max_participants}",
                inline=True
            )
        else:
            embed.add_field(
                name="👥 Participants",
                value=f"{current_count} (illimité)",
                inline=True
            )
        
        # Rôles si définis
        roles = event_data.get('roles', [])
        if roles:
            role_text = ""
            for i, role in enumerate(roles[:10]):  # Max 10 rôles
                emoji = self.role_emojis[i]
                role_text += f"{emoji} **{role['name']}** ({role['capacity']} places)\n"
                if role.get('description'):
                    role_text += f"   ↳ {role['description']}\n"
            
            embed.add_field(
                name="🎭 Rôles Disponibles",
                value=role_text,
                inline=False
            )
            
            # Instructions d'inscription avec rôles
            instructions = f"**Comment s'inscrire :**\n"
            for i, role in enumerate(roles[:10]):
                emoji = self.role_emojis[i]
                instructions += f"{emoji} Pour le rôle **{role['name']}**\n"
            instructions += f"{self.reserve_emoji} Pour la liste d'attente\n"
            instructions += f"❌ Pour se désinscrire\n\n"
            instructions += f"*Cliquez sur la réaction correspondante ci-dessous*"
            
        else:
            # Instructions d'inscription simple
            instructions = f"**Comment s'inscrire :**\n"
            instructions += f"{self.default_join_emoji} Pour participer\n"
            instructions += f"❌ Pour se désinscrire\n\n"
            instructions += f"*Cliquez sur la réaction correspondante ci-dessous*"
        
        embed.add_field(
            name="📝 Inscription",
            value=instructions,
            inline=False
        )
        
        # Footer avec organisation
        embed.set_footer(
            text=f"Organisé par {event_data.get('org_name', 'Organisation')} • ID: {event_data['id'][:8]}",
            icon_url=self.bot.user.avatar.url if self.bot.user.avatar else None
        )
        
        return embed
    
    async def add_event_reactions(self, message: discord.Message, event_data: Dict[str, Any]):
        """Ajoute les réactions d'inscription à un message d'événement"""
        try:
            roles = event_data.get('roles', [])
            
            if roles:
                # Ajouter une réaction pour chaque rôle
                for i, role in enumerate(roles[:10]):  # Max 10 rôles
                    await message.add_reaction(self.role_emojis[i])
                
                # Ajouter la réaction pour liste d'attente
                await message.add_reaction(self.reserve_emoji)
            else:
                # Inscription simple
                await message.add_reaction(self.default_join_emoji)
            
            # Toujours ajouter la réaction de désinscription
            await message.add_reaction("❌")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'ajout des réactions: {e}")
    
    async def save_message_mapping(self, event_id: str, message_id: int, channel_id: int, guild_id: int):
        """Sauvegarde le mapping message Discord <-> événement"""
        try:
            async with self.api as api:
                mapping_data = {
                    'event_id': event_id,
                    'message_id': str(message_id),
                    'channel_id': str(channel_id),
                    'guild_id': str(guild_id),
                    'created_at': datetime.now(timezone.utc).isoformat()
                }
                # Sauvegarder dans la base de données via API
                await api.save_discord_message_mapping(mapping_data)
                
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde du mapping: {e}")
    
    async def handle_reaction_add(self, payload: discord.RawReactionActionEvent):
        """Gère l'ajout de réactions pour les inscriptions"""
        try:
            # Ignorer les réactions du bot
            if payload.user_id == self.bot.user.id:
                return
            
            # Récupérer les informations du message
            guild = self.bot.get_guild(payload.guild_id)
            if not guild:
                return
                
            channel = guild.get_channel(payload.channel_id)
            if not channel:
                return
                
            message = await channel.fetch_message(payload.message_id)
            user = guild.get_member(payload.user_id)
            
            if not user or user.bot:
                return
            
            # Vérifier si c'est un message d'événement
            event_data = await self.get_event_from_message(payload.message_id)
            if not event_data:
                return
            
            # Traiter l'inscription selon l'emoji
            await self.process_event_signup(event_data, user, str(payload.emoji), message)
            
        except Exception as e:
            logger.error(f"Erreur lors du traitement de la réaction: {e}")
    
    async def handle_reaction_remove(self, payload: discord.RawReactionActionEvent):
        """Gère la suppression de réactions pour les désinscriptions"""
        try:
            # Ignorer les réactions du bot
            if payload.user_id == self.bot.user.id:
                return
            
            # Si c'est la réaction de désinscription ❌, ne rien faire 
            # (la désinscription se fait sur l'ajout de ❌)
            if str(payload.emoji) == "❌":
                return
            
            # Pour les autres réactions, on peut gérer la désinscription automatique
            event_data = await self.get_event_from_message(payload.message_id)
            if not event_data:
                return
            
            guild = self.bot.get_guild(payload.guild_id)
            if not guild:
                return
                
            user = guild.get_member(payload.user_id)
            if not user or user.bot:
                return
            
            # Désinscrire l'utilisateur
            await self.process_event_leave(event_data, user)
            
        except Exception as e:
            logger.error(f"Erreur lors du traitement de la suppression de réaction: {e}")
    
    async def get_event_from_message(self, message_id: int) -> Optional[Dict[str, Any]]:
        """Récupère les données d'événement depuis un message ID"""
        try:
            async with self.api as api:
                mapping = await api.get_discord_message_mapping(str(message_id))
                if mapping:
                    event = await api.get_event(mapping['event_id'])
                    return event
                return None
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de l'événement: {e}")
            return None
    
    async def process_event_signup(self, event_data: Dict[str, Any], user: discord.Member, emoji: str, message: discord.Message):
        """Traite l'inscription à un événement"""
        try:
            # Si c'est ❌, désinscrire
            if emoji == "❌":
                await self.process_event_leave(event_data, user)
                return
            
            # Déterminer le rôle selon l'emoji
            role_name = None
            roles = event_data.get('roles', [])
            
            if roles:
                # Événement avec rôles
                if emoji in self.role_emojis:
                    role_index = self.role_emojis.index(emoji)
                    if role_index < len(roles):
                        role_name = roles[role_index]['name']
                elif emoji == self.reserve_emoji:
                    role_name = "Liste d'attente"
            else:
                # Événement sans rôles spécifiques
                if emoji == self.default_join_emoji:
                    role_name = None  # Inscription générale
            
            if role_name is not None or (not roles and emoji == self.default_join_emoji):
                # Inscrire l'utilisateur
                async with self.api as api:
                    signup_data = {
                        'role_name': role_name,
                        'notes': f'Inscription via Discord (réaction {emoji})'
                    }
                    
                    result = await api.join_event(event_data['id'], str(user.id), signup_data)
                    
                    # Envoyer confirmation en MP
                    try:
                        role_text = f" pour le rôle **{role_name}**" if role_name else ""
                        embed = create_success_embed(
                            "✅ Inscription confirmée",
                            f"Vous êtes inscrit à **{event_data['title']}**{role_text} !\n\n"
                            f"📅 **Date :** <t:{int(datetime.fromisoformat(event_data['start_at_utc'].replace('Z', '+00:00')).timestamp())}:F>\n"
                            f"📍 **Lieu :** {event_data.get('location', 'Non spécifié')}\n\n"
                            f"Vous recevrez des rappels avant l'événement."
                        )
                        await user.send(embed=embed)
                    except discord.Forbidden:
                        pass  # L'utilisateur n'accepte pas les MPs
                    
                    # Mettre à jour le message (optionnel)
                    await self.update_event_message(message, event_data['id'])
                    
        except Exception as e:
            logger.error(f"Erreur lors de l'inscription: {e}")
            # Envoyer erreur en MP si possible
            try:
                embed = create_error_embed(
                    "❌ Erreur d'inscription",
                    f"Impossible de vous inscrire à {event_data['title']}.\n\n"
                    f"Raison possible: Événement complet ou vous êtes déjà inscrit."
                )
                await user.send(embed=embed)
            except discord.Forbidden:
                pass
    
    async def process_event_leave(self, event_data: Dict[str, Any], user: discord.Member):
        """Traite la désinscription d'un événement"""
        try:
            async with self.api as api:
                await api.leave_event(event_data['id'], str(user.id))
                
                # Confirmation en MP
                try:
                    embed = create_success_embed(
                        "✅ Désinscription confirmée",
                        f"Vous êtes désinscrit de **{event_data['title']}**.\n\n"
                        f"Vous ne recevrez plus de notifications pour cet événement."
                    )
                    await user.send(embed=embed)
                except discord.Forbidden:
                    pass
                    
        except Exception as e:
            logger.error(f"Erreur lors de la désinscription: {e}")
    
    async def update_event_message(self, message: discord.Message, event_id: str):
        """Met à jour le message d'événement avec les nouvelles données"""
        try:
            async with self.api as api:
                # Récupérer les données mises à jour
                event_data = await api.get_event(event_id)
                if event_data:
                    # Recréer l'embed
                    embed = await self.create_event_embed(event_data)
                    await message.edit(embed=embed)
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour du message: {e}")
    
    async def publish_tournament(self, tournament_data: Dict[str, Any], org_config: Dict[str, Any]):
        """Publie un tournoi sur Discord"""
        try:
            guild_id = org_config.get('discord_guild_id')
            channel_id = org_config.get('tournaments_channel_id', org_config.get('events_channel_id'))
            
            if not guild_id or not channel_id:
                logger.warning(f"Configuration Discord manquante pour l'organisation {tournament_data.get('org_name')}")
                return None
            
            guild = self.bot.get_guild(int(guild_id))
            if not guild:
                return None
                
            channel = guild.get_channel(int(channel_id))
            if not channel:
                return None
            
            # Créer l'embed du tournoi
            embed = await self.create_tournament_embed(tournament_data)
            
            # Publier le message
            message = await channel.send(embed=embed)
            
            # Ajouter les réactions pour l'inscription (simple pour les tournois)
            await message.add_reaction("🏆")  # S'inscrire
            await message.add_reaction("❌")   # Se désinscrire
            
            # Sauvegarder le mapping
            await self.save_tournament_message_mapping(tournament_data['id'], message.id, channel.id, guild.id)
            
            logger.info(f"Tournoi {tournament_data['name']} publié sur {guild.name}#{channel.name}")
            return message
            
        except Exception as e:
            logger.error(f"Erreur lors de la publication du tournoi: {e}")
            return None
    
    async def create_tournament_embed(self, tournament_data: Dict[str, Any]) -> discord.Embed:
        """Crée l'embed pour le tournoi"""
        embed = discord.Embed(
            title=f"🏆 {tournament_data['name']}",
            description=tournament_data.get('description', 'Aucune description'),
            color=0xF59E0B,
            timestamp=datetime.fromisoformat(tournament_data['start_date'].replace('Z', '+00:00'))
        )
        
        # Informations de base
        embed.add_field(
            name="📅 Date de début",
            value=f"<t:{int(datetime.fromisoformat(tournament_data['start_date'].replace('Z', '+00:00')).timestamp())}:F>",
            inline=True
        )
        
        embed.add_field(
            name="🎮 Jeu",
            value=tournament_data.get('game', 'Star Citizen'),
            inline=True
        )
        
        embed.add_field(
            name="🏁 Format",
            value=tournament_data.get('format', 'Best of 3'),
            inline=True
        )
        
        embed.add_field(
            name="👥 Participants",
            value=f"{len(tournament_data.get('participants', []))}/{tournament_data.get('max_participants', 'N/A')}",
            inline=True
        )
        
        embed.add_field(
            name="🏆 Type",
            value=tournament_data.get('tournament_type', 'elimination').replace('_', ' ').title(),
            inline=True
        )
        
        # Prix si définis
        if tournament_data.get('prize_pool'):
            embed.add_field(
                name="💰 Prix",
                value=tournament_data['prize_pool'],
                inline=True
            )
        
        # Règles
        if tournament_data.get('rules'):
            rules_text = tournament_data['rules']
            if len(rules_text) > 1000:
                rules_text = rules_text[:1000] + "..."
            embed.add_field(
                name="📋 Règles",
                value=rules_text,
                inline=False
            )
        
        # Instructions d'inscription
        instructions = f"**Comment s'inscrire :**\n"
        instructions += f"🏆 Pour participer au tournoi\n"
        instructions += f"❌ Pour se désinscrire\n\n"
        instructions += f"*Cliquez sur la réaction correspondante ci-dessous*"
        
        embed.add_field(
            name="📝 Inscription",
            value=instructions,
            inline=False
        )
        
        # Footer
        embed.set_footer(
            text=f"Organisé par {tournament_data.get('org_name', 'Organisation')} • ID: {tournament_data['id'][:8]}",
            icon_url=self.bot.user.avatar.url if self.bot.user.avatar else None
        )
        
        return embed
    
    async def save_tournament_message_mapping(self, tournament_id: str, message_id: int, channel_id: int, guild_id: int):
        """Sauvegarde le mapping message Discord <-> tournoi"""
        try:
            async with self.api as api:
                mapping_data = {
                    'tournament_id': tournament_id,
                    'message_id': str(message_id),
                    'channel_id': str(channel_id),
                    'guild_id': str(guild_id),
                    'created_at': datetime.now(timezone.utc).isoformat()
                }
                await api.save_discord_tournament_mapping(mapping_data)
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde du mapping tournoi: {e}")

async def setup(bot: commands.Bot):
    """Setup function for the auto publisher system"""
    publisher = AutoPublisher(bot)
    
    @bot.event
    async def on_raw_reaction_add(payload: discord.RawReactionActionEvent):
        await publisher.handle_reaction_add(payload)
    
    @bot.event  
    async def on_raw_reaction_remove(payload: discord.RawReactionActionEvent):
        await publisher.handle_reaction_remove(payload)
    
    return publisher