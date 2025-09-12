import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional
import logging
import psutil
import platform
from datetime import datetime, timedelta

from verselink_api import VerselinkAPI
from utils import *
from config import Config

logger = logging.getLogger(__name__)

class AdminCommands(commands.Cog):
    """Administrative and help commands"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @app_commands.command(name="help", description="Afficher l'aide des commandes VerseLink")
    async def help_command(self, interaction: discord.Interaction):
        """Display help for VerseLink commands"""
        embed = create_embed(
            "🤖 VerseLink Bot - Aide",
            "Bot officiel pour la plateforme VerseLink Star Citizen",
            color=0x3B82F6
        )
        
        # Basic commands
        embed.add_field(
            name="📋 Commandes de Base",
            value="`/help` - Afficher cette aide\n"
                  "`/status` - Statut du système VerseLink\n"
                  "`/events` - Lister les événements\n"
                  "`/tournaments` - Lister les tournois\n"
                  "`/event-info <id>` - Détails d'un événement\n"
                  "`/tournament-bracket <id>` - Bracket d'un tournoi",
            inline=False
        )
        
        # Interactive creation commands
        embed.add_field(
            name="🎯 Création Interactive",
            value="`/create-event` - Créer un événement (guide interactif)\n"
                  "`/create-tournament` - Créer un tournoi (guide interactif)\n"
                  "💡 *Ces commandes vous guident étape par étape*",
            inline=False
        )
        
        # Event management commands
        embed.add_field(
            name="📅 Gestion d'Événements",
            value="`/join-event <id>` - S'inscrire à un événement\n"
                  "`/leave-event <id>` - Se désinscrire d'un événement\n"
                  "`/my-events` - Voir mes événements\n"
                  "`/event-participants <id>` - Voir les participants",
            inline=False
        )
        
        # Admin commands
        if interaction.user.guild_permissions.manage_guild:
            embed.add_field(
                name="⚙️ Commandes Admin",
                value="`/setup` - Configurer ce serveur\n"
                      "`/config` - Voir la configuration\n"
                      "`/set-channel` - Définir les canaux\n"
                      "`/toggle` - Activer/désactiver des fonctions\n"
                      "`/event-start <id>` - Démarrer un événement\n"
                      "`/event-cancel <id>` - Annuler un événement\n"
                      "`/event-edit <id>` - Modifier un événement",
                inline=False
            )
        
        # User commands
        embed.add_field(
            name="👤 Commandes Utilisateur",
            value="`/join-event <id>` - S'inscrire à un événement\n"
                  "`/join-tournament <id>` - S'inscrire à un tournoi\n"
                  "`/leave-event <id>` - Se désinscrire d'un événement\n"
                  "`/leave-tournament <id>` - Se désinscrire d'un tournoi\n"
                  "`/profile` - Afficher votre profil\n"
                  "`/link-account` - Lier votre compte Discord",
            inline=False
        )
        
        # Links
        embed.add_field(
            name="🔗 Liens Utiles",
            value="[Site VerseLink](http://89.88.206.99:3000)\n"
                  "[Gestion Discord](http://89.88.206.99:3000/discord)\n"
                  "[Événements](http://89.88.206.99:3000/events)\n"
                  "[Tournois](http://89.88.206.99:3000/tournaments)",
            inline=False
        )
        
        embed.set_footer(text="VerseLink - Plateforme Star Citizen")
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="bot-info", description="Informations techniques du bot")
    @is_bot_admin()
    async def info_command(self, interaction: discord.Interaction):
        """Display bot technical information"""
        await interaction.response.defer()
        
        try:
            # System info
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            uptime = datetime.utcnow() - self.bot.start_time
            uptime_str = str(uptime).split('.')[0]
            
            embed = create_info_embed(
                "🤖 VerseLink Bot - Informations Techniques",
                f"Informations sur le bot et le système"
            )
            
            # Bot stats
            embed.add_field(
                name="📊 Statistiques Bot",
                value=f"**Serveurs**: {len(self.bot.guilds)}\n"
                      f"**Utilisateurs**: {sum(g.member_count for g in self.bot.guilds)}\n"
                      f"**Commandes**: {len(self.bot.tree.get_commands())}\n"
                      f"**Uptime**: {uptime_str}",
                inline=True
            )
            
            # System stats
            embed.add_field(
                name="💻 Système",
                value=f"**OS**: {platform.system()} {platform.release()}\n"
                      f"**Python**: {platform.python_version()}\n"
                      f"**Discord.py**: {discord.__version__}\n"
                      f"**CPU**: {psutil.cpu_percent()}%",
                inline=True
            )
            
            # Memory and disk
            embed.add_field(
                name="🔧 Ressources",
                value=f"**RAM**: {memory.percent}% ({memory.used // 1024 // 1024}MB)\n"
                      f"**Disque**: {disk.percent}% ({disk.used // 1024 // 1024 // 1024}GB)\n"
                      f"**Latence**: {round(self.bot.latency * 1000)}ms",
                inline=True
            )
            
            # Configuration
            embed.add_field(
                name="⚙️ Configuration",
                value=f"**Environment**: {Config.ENVIRONMENT}\n"
                      f"**Debug**: {Config.DEBUG_MODE}\n"
                      f"**Prefix**: {Config.BOT_PREFIX}\n"
                      f"**Log Level**: {Config.LOG_LEVEL}",
                inline=True
            )
            
            # API Status
            try:
                async with VerselinkAPI() as api:
                    health = await api.get_health()
                
                api_status = "✅ Connecté" if health.get('status') == 'healthy' else "❌ Problème"
                embed.add_field(
                    name="🔗 API VerseLink",
                    value=f"**Statut**: {api_status}\n"
                          f"**URL**: {Config.VERSELINK_API_BASE}\n"
                          f"**Guildes**: {health.get('guilds_registered', 0)} enregistrées\n"
                          f"**Jobs**: {health.get('pending_jobs', 0)} en attente",
                    inline=True
                )
            except Exception as e:
                embed.add_field(
                    name="🔗 API VerseLink",
                    value=f"**Statut**: ❌ Erreur\n**Erreur**: {str(e)[:50]}...",
                    inline=True
                )
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            embed = create_error_embed(
                "❌ Erreur",
                f"Impossible de récupérer les informations : {str(e)}"
            )
            await interaction.followup.send(embed=embed)
    
    @app_commands.command(name="toggle", description="Activer/désactiver des fonctionnalités")
    @app_commands.describe(
        feature="Fonctionnalité à basculer",
        enabled="Activer (true) ou désactiver (false)"
    )
    @app_commands.choices(feature=[
        app_commands.Choice(name="Annonces automatiques", value="auto_announcements"),
        app_commands.Choice(name="Synchronisation de messages", value="message_sync"),
        app_commands.Choice(name="Rappels automatiques", value="auto_reminders"),
    ])
    @has_manage_guild()
    async def toggle_feature(
        self, 
        interaction: discord.Interaction,
        feature: str,
        enabled: bool
    ):
        """Toggle guild features"""
        await interaction.response.defer()
        
        try:
            update_data = {feature: enabled}
            
            async with VerselinkAPI() as api:
                await api.update_guild_config(str(interaction.guild.id), update_data)
            
            feature_names = {
                'auto_announcements': 'Annonces automatiques',
                'message_sync': 'Synchronisation de messages',
                'auto_reminders': 'Rappels automatiques'
            }
            
            status = "activée" if enabled else "désactivée"
            embed = create_success_embed(
                f"✅ Fonctionnalité {status.title()}",
                f"**{feature_names[feature]}** a été {status} pour ce serveur."
            )
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            embed = create_error_embed(
                "❌ Erreur de Configuration",
                f"Impossible de modifier la fonctionnalité : {str(e)}"
            )
            await interaction.followup.send(embed=embed)
    
    @app_commands.command(name="sync-message", description="Synchroniser un message avec d'autres serveurs")
    @app_commands.describe(
        message_id="ID du message à synchroniser",
        target_guilds="IDs des serveurs cibles (séparés par des virgules)"
    )
    @has_manage_guild()
    async def sync_message(
        self, 
        interaction: discord.Interaction,
        message_id: str,
        target_guilds: Optional[str] = None
    ):
        """Sync a message across guilds"""
        await interaction.response.defer()
        
        try:
            # Find the message
            message = None
            for channel in interaction.guild.text_channels:
                try:
                    message = await channel.fetch_message(int(message_id))
                    break
                except (discord.NotFound, discord.Forbidden, ValueError):
                    continue
            
            if not message:
                embed = create_error_embed(
                    "❌ Message Introuvable",
                    f"Impossible de trouver le message avec l'ID `{message_id}`"
                )
                await interaction.followup.send(embed=embed)
                return
            
            # Prepare sync data
            sync_data = {
                'guild_id': str(interaction.guild.id),
                'channel_id': str(message.channel.id),
                'message_id': message_id,
                'content': message.content,
                'author_name': message.author.display_name,
                'author_avatar': str(message.author.display_avatar.url),
                'embeds': [embed.to_dict() for embed in message.embeds] if message.embeds else [],
                'target_guilds': target_guilds.split(',') if target_guilds else None
            }
            
            async with VerselinkAPI() as api:
                result = await api.sync_message(sync_data)
            
            synced_count = result.get('synced_guilds', 0)
            embed = create_success_embed(
                "✅ Message Synchronisé",
                f"Le message a été synchronisé avec {synced_count} serveur(s)."
            )
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            embed = create_error_embed(
                "❌ Erreur de Synchronisation",
                f"Impossible de synchroniser le message : {str(e)}"
            )
            await interaction.followup.send(embed=embed)
    
    @app_commands.command(name="remind", description="Programmer un rappel")
    @app_commands.describe(
        message="Message du rappel",
        delay_hours="Délai en heures",
        channel="Canal où envoyer le rappel (optionnel)"
    )
    @has_manage_guild()
    async def schedule_reminder(
        self, 
        interaction: discord.Interaction,
        message: str,
        delay_hours: int,
        channel: Optional[discord.TextChannel] = None
    ):
        """Schedule a reminder"""
        await interaction.response.defer()
        
        if delay_hours < 1 or delay_hours > 168:  # Max 1 week
            embed = create_error_embed(
                "❌ Délai Invalide",
                "Le délai doit être entre 1 et 168 heures (1 semaine)."
            )
            await interaction.followup.send(embed=embed)
            return
        
        try:
            target_channel = channel or interaction.channel
            
            reminder_data = {
                'guild_id': str(interaction.guild.id),
                'channel_id': str(target_channel.id),
                'message': message,
                'scheduled_for': (datetime.utcnow() + timedelta(hours=delay_hours)).isoformat(),
                'created_by_user_id': str(interaction.user.id),
                'created_by_user_name': interaction.user.display_name
            }
            
            async with VerselinkAPI() as api:
                result = await api.schedule_reminder(reminder_data)
            
            remind_time = format_datetime(reminder_data['scheduled_for'])
            embed = create_success_embed(
                "⏰ Rappel Programmé",
                f"Rappel programmé pour {remind_time}\n\n"
                f"**Message**: {message}\n"
                f"**Canal**: {target_channel.mention}\n"
                f"**ID**: `{result.get('reminder_id', 'N/A')}`"
            )
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            embed = create_error_embed(
                "❌ Erreur de Rappel",
                f"Impossible de programmer le rappel : {str(e)}"
            )
            await interaction.followup.send(embed=embed)
    
    @app_commands.command(name="reload-config", description="Recharger la configuration du bot")
    @is_bot_admin()
    async def reload_config(self, interaction: discord.Interaction):
        """Reload bot configuration"""
        await interaction.response.defer()
        
        try:
            # Test API connection
            async with VerselinkAPI() as api:
                health = await api.get_health()
            
            embed = create_success_embed(
                "✅ Configuration Rechargée",
                f"Configuration rechargée avec succès !\n\n"
                f"**Statut API**: {health.get('status', 'Unknown')}\n"
                f"**Guildes**: {health.get('guilds_registered', 0)} enregistrées"
            )
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            embed = create_error_embed(
                "❌ Erreur de Rechargement",
                f"Impossible de recharger la configuration : {str(e)}"
            )
            await interaction.followup.send(embed=embed)

async def setup(bot: commands.Bot):
    """Setup function for the cog"""
    await bot.add_cog(AdminCommands(bot))