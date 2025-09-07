import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional, List
import logging
from datetime import datetime, timedelta, timezone

from api import VerselinkAPI
from utils import *
from config import Config

logger = logging.getLogger(__name__)

class VerselinkCommands(commands.Cog):
    """Main VerseLink bot commands"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.api = VerselinkAPI()
    
    async def cog_load(self):
        """Initialize the cog"""
        logger.info("VerseLink commands cog loaded")
    
    async def cog_unload(self):
        """Cleanup when cog is unloaded"""
        if self.api.session:
            await self.api.session.close()
    
    # Setup Commands
    @app_commands.command(name="setup", description="Configurer ce serveur Discord avec VerseLink")
    @has_manage_guild()
    async def setup_guild(self, interaction: discord.Interaction):
        """Setup this Discord guild with VerseLink"""
        await interaction.response.defer()
        
        try:
            guild_data = {
                'guild_id': str(interaction.guild.id),
                'guild_name': interaction.guild.name,
                'guild_icon': str(interaction.guild.icon) if interaction.guild.icon else None,
                'owner_id': str(interaction.guild.owner_id),
                'member_count': interaction.guild.member_count,
                'setup_by_user_id': str(interaction.user.id),
                'setup_by_user_name': f"{interaction.user.name}#{interaction.user.discriminator}"
            }
            
            async with VerselinkAPI() as api:
                result = await api.register_guild(str(interaction.guild.id), guild_data)
            
            embed = create_success_embed(
                "✅ Serveur Configuré",
                f"Le serveur **{interaction.guild.name}** a été configuré avec succès !\n\n"
                f"🔗 [Gérer les intégrations](http://89.88.206.99:3000/discord)\n\n"
                f"Utilisez `/config` pour voir les options de configuration."
            )
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            embed = create_error_embed(
                "❌ Erreur de Configuration",
                f"Impossible de configurer le serveur : {str(e)}"
            )
            await interaction.followup.send(embed=embed)
    
    @app_commands.command(name="config", description="Afficher ou modifier la configuration du serveur")
    @has_manage_guild()
    async def guild_config(self, interaction: discord.Interaction):
        """Show guild configuration"""
        await interaction.response.defer()
        
        try:
            async with VerselinkAPI() as api:
                config = await api.get_guild_config(str(interaction.guild.id))
            
            embed = create_info_embed(
                f"⚙️ Configuration - {interaction.guild.name}",
                "Configuration actuelle du serveur :"
            )
            
            # Basic info
            embed.add_field(
                name="📋 Informations",
                value=f"**Nom**: {config.get('guild_name', 'Non défini')}\n"
                      f"**ID**: {config.get('guild_id')}\n"
                      f"**Statut**: {'✅ Actif' if config.get('is_active') else '❌ Inactif'}",
                inline=False
            )
            
            # Channels
            channels_info = []
            if config.get('events_channel_id'):
                channels_info.append(f"📅 Événements: <#{config['events_channel_id']}>")
            if config.get('tournaments_channel_id'):
                channels_info.append(f"🏆 Tournois: <#{config['tournaments_channel_id']}>")
            if config.get('announcements_channel_id'):
                channels_info.append(f"📢 Annonces: <#{config['announcements_channel_id']}>")
            
            if channels_info:
                embed.add_field(
                    name="📺 Canaux Configurés",
                    value="\n".join(channels_info),
                    inline=False
                )
            else:
                embed.add_field(
                    name="📺 Canaux",
                    value="Aucun canal configuré\nUtilisez `/set-channel` pour configurer",
                    inline=False
                )
            
            # Settings
            settings = []
            if config.get('auto_announcements'):
                settings.append("✅ Annonces automatiques")
            if config.get('message_sync'):
                settings.append("✅ Synchronisation des messages")
            if config.get('auto_reminders'):
                settings.append("✅ Rappels automatiques")
            
            if settings:
                embed.add_field(
                    name="⚙️ Paramètres Actifs",
                    value="\n".join(settings),
                    inline=False
                )
            
            embed.add_field(
                name="🔗 Gestion Web",
                value="[Configurer en ligne](http://89.88.206.99:3000/discord)",
                inline=False
            )
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            if "404" in str(e):
                embed = create_warning_embed(
                    "⚠️ Serveur Non Configuré",
                    "Ce serveur n'est pas encore configuré avec VerseLink.\n"
                    "Utilisez `/setup` pour le configurer."
                )
            else:
                embed = create_error_embed(
                    "❌ Erreur",
                    f"Impossible de récupérer la configuration : {str(e)}"
                )
            await interaction.followup.send(embed=embed)
    
    # Channel Configuration
    @app_commands.command(name="set-channel", description="Définir un canal pour un type de contenu")
    @app_commands.describe(
        channel_type="Type de canal à configurer",
        channel="Canal Discord à utiliser"
    )
    @app_commands.choices(channel_type=[
        app_commands.Choice(name="Événements", value="events"),
        app_commands.Choice(name="Tournois", value="tournaments"),
        app_commands.Choice(name="Annonces", value="announcements"),
    ])
    @has_manage_guild()
    async def set_channel(
        self, 
        interaction: discord.Interaction,
        channel_type: str,
        channel: discord.TextChannel
    ):
        """Set a channel for specific content type"""
        await interaction.response.defer()
        
        try:
            config_field = f"{channel_type}_channel_id"
            update_data = {config_field: str(channel.id)}
            
            async with VerselinkAPI() as api:
                await api.update_guild_config(str(interaction.guild.id), update_data)
            
            type_names = {
                'events': 'Événements',
                'tournaments': 'Tournois',
                'announcements': 'Annonces'
            }
            
            embed = create_success_embed(
                "✅ Canal Configuré",
                f"Le canal {channel.mention} a été configuré pour **{type_names[channel_type]}**."
            )
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            embed = create_error_embed(
                "❌ Erreur de Configuration",
                f"Impossible de configurer le canal : {str(e)}"
            )
            await interaction.followup.send(embed=embed)
    
    # Status Commands
    @app_commands.command(name="status", description="Afficher le statut de VerseLink")
    async def status(self, interaction: discord.Interaction):
        """Show VerseLink system status"""
        await interaction.response.defer()
        
        try:
            async with VerselinkAPI() as api:
                health = await api.get_health()
                stats = await api.get_stats()
            
            # Health status
            status_emoji = "✅" if health.get('status') == 'healthy' else "❌"
            embed = create_embed(
                f"{status_emoji} Statut VerseLink",
                f"Système : **{health.get('status', 'Inconnu').title()}**",
                color=0x10B981 if health.get('status') == 'healthy' else 0xEF4444
            )
            
            # System info
            embed.add_field(
                name="🔧 Configuration",
                value=f"Webhook: {'✅' if health.get('webhook_secret_configured') else '❌'}\n"
                      f"Bot API: {'✅' if health.get('bot_api_configured') else '❌'}",
                inline=True
            )
            
            embed.add_field(
                name="🌐 Serveurs",
                value=f"Enregistrés: {health.get('guilds_registered', 0)}\n"
                      f"Actifs: {health.get('active_guilds', 0)}",
                inline=True
            )
            
            embed.add_field(
                name="⏳ Tâches",
                value=f"En attente: {health.get('pending_jobs', 0)}",
                inline=True
            )
            
            # Additional stats if available
            if stats:
                embed.add_field(
                    name="📊 Statistiques",
                    value=f"Événements: {stats.get('total_events', 0)}\n"
                          f"Tournois: {stats.get('total_tournaments', 0)}\n"
                          f"Utilisateurs: {stats.get('total_users', 0)}",
                    inline=True
                )
            
            embed.add_field(
                name="🔗 Accès Web",
                value="[Interface VerseLink](http://89.88.206.99:3000)",
                inline=False
            )
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            embed = create_error_embed(
                "❌ Erreur de Statut",
                f"Impossible de récupérer le statut : {str(e)}"
            )
            await interaction.followup.send(embed=embed)
    
    # Event Commands
    @app_commands.command(name="events", description="Afficher les prochains événements")
    @app_commands.describe(limit="Nombre d'événements à afficher (max 10)")
    async def list_events(self, interaction: discord.Interaction, limit: Optional[int] = 5):
        """List upcoming events"""
        await interaction.response.defer()
        
        limit = max(1, min(limit or 5, 10))
        
        try:
            async with VerselinkAPI() as api:
                events = await api.get_events(limit=limit)
            
            if not events:
                embed = create_info_embed(
                    "📅 Événements",
                    "Aucun événement prévu pour le moment."
                )
                await interaction.followup.send(embed=embed)
                return
            
            embed = create_embed(
                f"📅 Prochains Événements ({len(events)})",
                f"Les {len(events)} prochains événements :"
            )
            
            for event in events[:5]:  # Limit to 5 to avoid embed limits
                date_str = format_datetime(event.get('date', ''))
                participants = f"{event.get('current_participants', 0)}/{event.get('max_participants', '∞')}"
                
                embed.add_field(
                    name=f"📅 {event.get('title', 'Événement sans titre')}",
                    value=f"**Date**: {date_str}\n"
                          f"**Participants**: {participants}\n"
                          f"**Lieu**: {event.get('location', 'Non spécifié')}\n"
                          f"[Plus d'infos](http://89.88.206.99:3000/events/{event.get('id', '')})",
                    inline=False
                )
            
            if len(events) > 5:
                embed.add_field(
                    name="🔗 Voir Tous les Événements",
                    value=f"[{len(events) - 5} événements supplémentaires](http://89.88.206.99:3000/events)",
                    inline=False
                )
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            embed = create_error_embed(
                "❌ Erreur Événements",
                f"Impossible de récupérer les événements : {str(e)}"
            )
            await interaction.followup.send(embed=embed)
    
    @app_commands.command(name="event-info", description="Afficher les détails d'un événement")
    @app_commands.describe(event_id="ID de l'événement")
    async def event_info(self, interaction: discord.Interaction, event_id: str):
        """Get detailed event information"""
        await interaction.response.defer()
        
        try:
            async with VerselinkAPI() as api:
                event = await api.get_event(event_id)
            
            embed = create_event_embed(event)
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            embed = create_error_embed(
                "❌ Événement Introuvable",
                f"Impossible de trouver l'événement `{event_id}` : {str(e)}"
            )
            await interaction.followup.send(embed=embed)
    
    @app_commands.command(name="event-create", description="Créer un nouvel événement")
    @app_commands.describe(
        org_id="ID de l'organisation",
        title="Titre de l'événement",
        date="Date/heure de début (ISO 8601)",
        duration="Durée en minutes",
        description="Description de l'événement",
        location="Lieu de l'événement"
    )
    @has_manage_guild()
    async def event_create(
        self,
        interaction: discord.Interaction,
        org_id: str,
        title: str,
        date: str,
        duration: int,
        description: str,
        location: Optional[str] = None,
    ):
        """Create a new event for an organization"""
        await interaction.response.defer()

        try:
            start_dt = datetime.fromisoformat(date)
            if start_dt.tzinfo is None:
                start_dt = start_dt.replace(tzinfo=timezone.utc)

            event_data = {
                'title': title,
                'description': description,
                'type': 'autre',
                'start_at_utc': start_dt.isoformat(),
                'duration_minutes': duration,
            }
            if location:
                event_data['location'] = location

            async with VerselinkAPI() as api:
                event = await api.create_event(org_id, event_data)
                config = await api.get_guild_config(str(interaction.guild.id))

            embed = create_success_embed(
                "✅ Événement Créé",
                f"L'événement **{title}** a été créé avec succès",
            )
            await interaction.followup.send(embed=embed)

            channel_id = config.get('events_channel_id')
            if channel_id:
                channel = interaction.guild.get_channel(int(channel_id))
                if channel:
                    event_embed = create_event_embed(event)
                    await safe_send(channel, embed=event_embed)

        except Exception as e:
            if '401' in str(e) or '403' in str(e):
                embed = create_error_embed(
                    "❌ Accès Refusé",
                    "Vous n'avez pas les droits pour créer un événement.",
                )
            else:
                embed = create_error_embed(
                    "❌ Erreur",
                    f"Impossible de créer l'événement : {str(e)}",
                )
            await interaction.followup.send(embed=embed)

    # Tournament Commands
    @app_commands.command(name="tournaments", description="Afficher les tournois actifs")
    @app_commands.describe(limit="Nombre de tournois à afficher (max 10)")
    async def list_tournaments(self, interaction: discord.Interaction, limit: Optional[int] = 5):
        """List active tournaments"""
        await interaction.response.defer()
        
        limit = max(1, min(limit or 5, 10))
        
        try:
            async with VerselinkAPI() as api:
                tournaments = await api.get_tournaments(limit=limit)
            
            if not tournaments:
                embed = create_info_embed(
                    "🏆 Tournois",
                    "Aucun tournoi actif pour le moment."
                )
                await interaction.followup.send(embed=embed)
                return
            
            embed = create_embed(
                f"🏆 Tournois Actifs ({len(tournaments)})",
                f"Les {len(tournaments)} tournois en cours :"
            )
            
            for tournament in tournaments[:5]:
                status_emoji = {
                    'open': '🟢',
                    'full': '🟡',
                    'active': '🔴',
                    'finished': '⚫'
                }.get(tournament.get('status', 'open'), '🟢')
                
                participants = f"{tournament.get('current_participants', 0)}/{tournament.get('max_participants', '∞')}"
                
                embed.add_field(
                    name=f"{status_emoji} {tournament.get('name', 'Tournoi sans nom')}",
                    value=f"**Type**: {tournament.get('tournament_type', 'N/A').replace('_', ' ').title()}\n"
                          f"**Participants**: {participants}\n"
                          f"**Jeu**: {tournament.get('game', 'Non spécifié')}\n"
                          f"[Plus d'infos](http://89.88.206.99:3000/tournaments/{tournament.get('id', '')})",
                    inline=False
                )
            
            if len(tournaments) > 5:
                embed.add_field(
                    name="🔗 Voir Tous les Tournois",
                    value=f"[{len(tournaments) - 5} tournois supplémentaires](http://89.88.206.99:3000/tournaments)",
                    inline=False
                )
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            embed = create_error_embed(
                "❌ Erreur Tournois",
                f"Impossible de récupérer les tournois : {str(e)}"
            )
            await interaction.followup.send(embed=embed)
    
    @app_commands.command(name="tournament-bracket", description="Afficher le bracket d'un tournoi")
    @app_commands.describe(tournament_id="ID du tournoi")
    async def tournament_bracket(self, interaction: discord.Interaction, tournament_id: str):
        """Show tournament bracket"""
        await interaction.response.defer()
        
        try:
            async with VerselinkAPI() as api:
                tournament = await api.get_tournament(tournament_id)
                bracket = await api.get_tournament_bracket(tournament_id)
            
            embed = create_bracket_embed(tournament, bracket)
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            embed = create_error_embed(
                "❌ Bracket Introuvable",
                f"Impossible de récupérer le bracket du tournoi `{tournament_id}` : {str(e)}"
            )
            await interaction.followup.send(embed=embed)

async def setup(bot: commands.Bot):
    """Setup function for the cog"""
    await bot.add_cog(VerselinkCommands(bot))