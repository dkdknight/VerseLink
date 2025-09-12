import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional, Dict, Any
import logging

from verselink_api import VerselinkAPI
from utils import *
from config import Config

logger = logging.getLogger(__name__)

class OrganizationConfig(commands.Cog):
    """Configuration Discord pour les organisations"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.api = VerselinkAPI()
    
    async def cog_load(self):
        """Initialize the cog"""
        logger.info("Organization Config cog loaded")
    
    async def cog_unload(self):
        """Cleanup when cog is unloaded"""
        if self.api.session:
            await self.api.session.close()
    
    @app_commands.command(name="setup-org", description="Configurer Discord pour votre organisation")
    @app_commands.describe(
        org_name="Nom de votre organisation",
        events_channel="Canal pour les événements",
        tournaments_channel="Canal pour les tournois (optionnel)"
    )
    @has_manage_guild()
    async def setup_organization(
        self, 
        interaction: discord.Interaction, 
        org_name: str,
        events_channel: discord.TextChannel,
        tournaments_channel: Optional[discord.TextChannel] = None
    ):
        """Configure Discord pour une organisation"""
        await interaction.response.defer()
        
        try:
            # Vérifier que l'organisation existe
            async with self.api as api:
                orgs = await api.get_organizations(limit=100)
                found_org = None
                
                for org in orgs:
                    if (org.get('name', '').lower() == org_name.lower() or 
                        org.get('tag', '').lower() == org_name.lower()):
                        found_org = org
                        break
                
                if not found_org:
                    embed = create_error_embed(
                        "❌ Organisation non trouvée",
                        f"L'organisation \"{org_name}\" n'existe pas.\n\n"
                        f"Vérifiez le nom ou créez l'organisation sur [VerseLink](http://localhost:3000)."
                    )
                    await interaction.followup.send(embed=embed)
                    return
                
                # Configuration Discord
                discord_config = {
                    'discord_guild_id': str(interaction.guild.id),
                    'discord_guild_name': interaction.guild.name,
                    'events_channel_id': str(events_channel.id),
                    'events_channel_name': events_channel.name,
                    'auto_publish_events': True,
                    'auto_publish_tournaments': True
                }
                
                if tournaments_channel:
                    discord_config['tournaments_channel_id'] = str(tournaments_channel.id)
                    discord_config['tournaments_channel_name'] = tournaments_channel.name
                else:
                    # Utiliser le même canal pour tournois et événements
                    discord_config['tournaments_channel_id'] = str(events_channel.id)
                    discord_config['tournaments_channel_name'] = events_channel.name
                
                # Sauvegarder la configuration
                await api.update_organization_discord_config(found_org['id'], discord_config)
            
            # Confirmation
            embed = create_success_embed(
                "✅ Configuration Discord mise à jour",
                f"**Organisation :** {found_org['name']}\n"
                f"**Serveur :** {interaction.guild.name}\n"
                f"**Canal événements :** {events_channel.mention}\n"
                f"**Canal tournois :** {tournaments_channel.mention if tournaments_channel else events_channel.mention}\n\n"
                f"📢 **Fonctionnalités activées :**\n"
                f"• Publication automatique des événements\n"
                f"• Publication automatique des tournois\n"
                f"• Inscriptions via réactions Discord\n"
                f"• Notifications automatiques\n\n"
                f"Utilisez `/test-publish` pour tester la publication."
            )
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            embed = create_error_embed(
                "❌ Erreur de configuration",
                f"Impossible de configurer l'organisation :\n{str(e)}"
            )
            await interaction.followup.send(embed=embed)
    
    @app_commands.command(name="test-publish", description="Tester la publication d'événements")
    @app_commands.describe(org_name="Nom de votre organisation")
    @has_manage_guild()
    async def test_publish(self, interaction: discord.Interaction, org_name: str):
        """Teste la publication d'un événement fictif"""
        await interaction.response.defer()
        
        try:
            # Vérifier que l'organisation existe et a une config Discord
            async with self.api as api:
                orgs = await api.get_organizations(limit=100)
                found_org = None
                
                for org in orgs:
                    if (org.get('name', '').lower() == org_name.lower() or 
                        org.get('tag', '').lower() == org_name.lower()):
                        found_org = org
                        break
                
                if not found_org:
                    embed = create_error_embed(
                        "❌ Organisation non trouvée",
                        f"L'organisation \"{org_name}\" n'existe pas."
                    )
                    await interaction.followup.send(embed=embed)
                    return
                
                # Récupérer la config Discord
                discord_config = await api.get_organization_discord_config(found_org['id'])
                
                if not discord_config or not discord_config.get('events_channel_id'):
                    embed = create_error_embed(
                        "❌ Configuration manquante",
                        f"L'organisation {found_org['name']} n'a pas de configuration Discord.\n\n"
                        f"Utilisez `/setup-org` pour la configurer."
                    )
                    await interaction.followup.send(embed=embed)
                    return
            
            # Créer un événement de test
            from auto_publisher import AutoPublisher
            from datetime import datetime, timezone, timedelta
            
            publisher = AutoPublisher(self.bot)
            
            test_event = {
                'id': 'test-event-' + str(interaction.id),
                'title': '🧪 Test de Publication Discord',
                'description': 'Ceci est un événement de test pour valider la configuration Discord.\n\nSi vous voyez ce message, la publication automatique fonctionne parfaitement !',
                'type': 'autre',
                'start_at_utc': (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat(),
                'duration_minutes': 60,
                'location': 'Serveur Discord',
                'max_participants': 10,
                'org_name': found_org['name'],
                'signups': [],
                'roles': [
                    {
                        'name': 'Testeur Principal',
                        'capacity': 1,
                        'description': 'Responsable des tests'
                    },
                    {
                        'name': 'Observateur',
                        'capacity': 5,
                        'description': 'Observe le test'
                    }
                ]
            }
            
            # Publier l'événement de test
            message = await publisher.publish_event(test_event, discord_config)
            
            if message:
                embed = create_success_embed(
                    "✅ Test de publication réussi !",
                    f"L'événement de test a été publié avec succès !\n\n"
                    f"📍 **Canal :** <#{discord_config['events_channel_id']}>\n"
                    f"💬 **Message :** [Voir l'événement](https://discord.com/channels/{interaction.guild.id}/{message.channel.id}/{message.id})\n\n"
                    f"🎯 **Fonctionnalités testées :**\n"
                    f"• ✅ Publication automatique\n"
                    f"• ✅ Embed personnalisé\n"
                    f"• ✅ Réactions d'inscription\n"
                    f"• ✅ Rôles multiples\n\n"
                    f"Vous pouvez maintenant créer de vrais événements qui seront automatiquement publiés !"
                )
                
                # Ajouter un bouton pour supprimer le test
                view = discord.ui.View(timeout=300)
                
                async def delete_test(button_interaction):
                    try:
                        await message.delete()
                        await button_interaction.response.send_message("🗑️ Événement de test supprimé.", ephemeral=True)
                    except:
                        await button_interaction.response.send_message("❌ Impossible de supprimer le message.", ephemeral=True)
                
                delete_button = discord.ui.Button(label="🗑️ Supprimer le test", style=discord.ButtonStyle.secondary)
                delete_button.callback = delete_test
                view.add_item(delete_button)
                
                await interaction.followup.send(embed=embed, view=view)
            else:
                embed = create_error_embed(
                    "❌ Échec du test",
                    f"Impossible de publier l'événement de test.\n\n"
                    f"Vérifiez :\n"
                    f"• Les permissions du bot dans <#{discord_config['events_channel_id']}>\n"
                    f"• Que le canal existe toujours\n"
                    f"• La configuration de l'organisation"
                )
                await interaction.followup.send(embed=embed)
                
        except Exception as e:
            embed = create_error_embed(
                "❌ Erreur de test",
                f"Erreur lors du test de publication :\n{str(e)}"
            )
            await interaction.followup.send(embed=embed)
    
    @app_commands.command(name="org-config", description="Voir la configuration Discord de votre organisation")
    @app_commands.describe(org_name="Nom de votre organisation")
    @has_manage_guild()
    async def view_org_config(self, interaction: discord.Interaction, org_name: str):
        """Affiche la configuration Discord d'une organisation"""
        await interaction.response.defer()
        
        try:
            async with self.api as api:
                # Trouver l'organisation
                orgs = await api.get_organizations(limit=100)
                found_org = None
                
                for org in orgs:
                    if (org.get('name', '').lower() == org_name.lower() or 
                        org.get('tag', '').lower() == org_name.lower()):
                        found_org = org
                        break
                
                if not found_org:
                    embed = create_error_embed(
                        "❌ Organisation non trouvée",
                        f"L'organisation \"{org_name}\" n'existe pas."
                    )
                    await interaction.followup.send(embed=embed)
                    return
                
                # Récupérer la configuration
                discord_config = await api.get_organization_discord_config(found_org['id'])
                
                if not discord_config:
                    embed = create_warning_embed(
                        "⚠️ Aucune configuration",
                        f"L'organisation **{found_org['name']}** n'a pas de configuration Discord.\n\n"
                        f"Utilisez `/setup-org` pour la configurer."
                    )
                    await interaction.followup.send(embed=embed)
                    return
                
                # Afficher la configuration
                embed = create_info_embed(
                    f"⚙️ Configuration Discord - {found_org['name']}",
                    f"Configuration actuelle pour cette organisation"
                )
                
                embed.add_field(
                    name="🌐 Serveur Discord",
                    value=f"**Nom :** {discord_config.get('discord_guild_name', 'N/A')}\n"
                          f"**ID :** {discord_config.get('discord_guild_id', 'N/A')}",
                    inline=False
                )
                
                embed.add_field(
                    name="📢 Canaux",
                    value=f"**Événements :** <#{discord_config.get('events_channel_id', '0')}>\n"
                          f"**Tournois :** <#{discord_config.get('tournaments_channel_id', '0')}>",
                    inline=False
                )
                
                embed.add_field(
                    name="🔧 Fonctionnalités",
                    value=f"**Publication auto événements :** {'✅' if discord_config.get('auto_publish_events') else '❌'}\n"
                          f"**Publication auto tournois :** {'✅' if discord_config.get('auto_publish_tournaments') else '❌'}\n"
                          f"**Inscriptions par réactions :** ✅",
                    inline=False
                )
                
                # Vérifier les permissions
                events_channel = self.bot.get_channel(int(discord_config.get('events_channel_id', 0)))
                if events_channel:
                    perms = events_channel.permissions_for(interaction.guild.me)
                    permissions_status = "✅ Complètes" if all([
                        perms.send_messages,
                        perms.embed_links,
                        perms.add_reactions,
                        perms.read_message_history
                    ]) else "⚠️ Incomplètes"
                else:
                    permissions_status = "❌ Canal introuvable"
                
                embed.add_field(
                    name="🔐 Permissions Bot",
                    value=f"**Statut :** {permissions_status}\n"
                          f"**Requises :** Envoyer messages, Embed links, Ajouter réactions",
                    inline=False
                )
                
                await interaction.followup.send(embed=embed)
                
        except Exception as e:
            embed = create_error_embed(
                "❌ Erreur",
                f"Impossible de récupérer la configuration :\n{str(e)}"
            )
            await interaction.followup.send(embed=embed)

async def setup(bot: commands.Bot):
    """Setup function for the cog"""
    await bot.add_cog(OrganizationConfig(bot))