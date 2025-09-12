import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional, List
import logging
from datetime import datetime, timedelta

from verselink_api import VerselinkAPI
from utils import *
from config import Config

logger = logging.getLogger(__name__)

class EventManagement(commands.Cog):
    """Commandes de gestion des événements existants"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.api = VerselinkAPI()
    
    async def cog_load(self):
        """Initialize the cog"""
        logger.info("Event Management cog loaded")
        
    async def cog_unload(self):
        """Cleanup when cog is unloaded"""
        if self.api.session:
            await self.api.session.close()
    
    @app_commands.command(name="event-start", description="Démarrer un événement")
    @app_commands.describe(event_id="ID de l'événement à démarrer")
    @has_manage_guild()
    async def start_event(self, interaction: discord.Interaction, event_id: str):
        """Démarre un événement"""
        await interaction.response.defer()
        
        try:
            async with VerselinkAPI() as api:
                # Vérifier que l'événement existe
                event = await api.get_event(event_id)
                
                # Démarrer l'événement
                result = await api.start_event(event_id)
            
            embed = create_success_embed(
                "🚀 Événement démarré",
                f"L'événement **{event['title']}** a été démarré avec succès !\n\n"
                f"📅 **Début :** <t:{int(datetime.fromisoformat(event['start_at_utc']).timestamp())}:F>\n"
                f"👥 **Participants :** {event.get('confirmed_count', 0)}\n\n"
                f"Les participants ont été notifiés."
            )
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            embed = create_error_embed(
                "❌ Erreur",
                f"Impossible de démarrer l'événement :\n{str(e)}"
            )
            await interaction.followup.send(embed=embed)
    
    @app_commands.command(name="event-cancel", description="Annuler un événement")
    @app_commands.describe(
        event_id="ID de l'événement à annuler",
        reason="Raison de l'annulation (optionnel)"
    )
    @has_manage_guild()
    async def cancel_event(self, interaction: discord.Interaction, event_id: str, reason: Optional[str] = None):
        """Annule un événement"""
        await interaction.response.defer()
        
        try:
            async with VerselinkAPI() as api:
                # Vérifier que l'événement existe
                event = await api.get_event(event_id)
                
                # Annuler l'événement
                result = await api.cancel_event(event_id)
            
            embed = create_warning_embed(
                "🚫 Événement annulé",
                f"L'événement **{event['title']}** a été annulé.\n\n"
                f"📅 **Était prévu :** <t:{int(datetime.fromisoformat(event['start_at_utc']).timestamp())}:F>\n"
                f"👥 **Participants affectés :** {event.get('confirmed_count', 0)}\n"
                + (f"📝 **Raison :** {reason}\n" if reason else "") +
                f"\nTous les participants ont été notifiés de l'annulation."
            )
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            embed = create_error_embed(
                "❌ Erreur",
                f"Impossible d'annuler l'événement :\n{str(e)}"
            )
            await interaction.followup.send(embed=embed)
    
    @app_commands.command(name="event-edit", description="Modifier un événement existant")
    @app_commands.describe(event_id="ID de l'événement à modifier")
    @has_manage_guild()
    async def edit_event(self, interaction: discord.Interaction, event_id: str):
        """Lance l'édition interactive d'un événement"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            async with VerselinkAPI() as api:
                event = await api.get_event(event_id)
            
            embed = create_info_embed(
                "📝 Édition d'événement",
                f"Édition de **{event['title']}**\n\n"
                f"Je vais vous envoyer un message privé pour modifier cet événement.\n"
                f"Les participants seront notifiés des changements importants."
            )
            
            await interaction.followup.send(embed=embed)
            
            # Envoyer les options d'édition en MP
            try:
                dm_embed = create_embed(
                    "📝 Édition d'événement",
                    f"**Événement :** {event['title']}\n"
                    f"**Organisation :** {event.get('org_name', 'N/A')}\n"
                    f"**Date actuelle :** <t:{int(datetime.fromisoformat(event['start_at_utc']).timestamp())}:F>\n\n"
                    f"**Que voulez-vous modifier ?**\n"
                    f"• `titre` - Changer le titre\n"
                    f"• `description` - Modifier la description\n"
                    f"• `date` - Reprogrammer l'événement\n"
                    f"• `durée` - Changer la durée\n"
                    f"• `lieu` - Modifier le lieu\n"
                    f"• `participants` - Changer le nombre max\n"
                    f"• `visibilité` - Changer qui peut voir l'événement\n\n"
                    f"Tapez ce que vous voulez modifier, ou `annuler` pour arrêter."
                )
                await interaction.user.send(embed=dm_embed)
                
                # TODO: Implémenter la logique d'édition interactive
                # Pour l'instant, on indique que c'est en développement
                await interaction.user.send("🚧 **Fonction en développement**\nL'édition interactive sera disponible dans une prochaine mise à jour.\n\nEn attendant, vous pouvez recréer l'événement ou utiliser l'interface web.")
                
            except discord.Forbidden:
                embed = create_error_embed(
                    "❌ Impossible d'envoyer un MP",
                    "Je ne peux pas vous envoyer de message privé.\n\n"
                    "Utilisez l'interface web pour modifier l'événement :\n"
                    f"[Modifier l'événement](http://localhost:3000/events/{event_id}/edit)"
                )
                await interaction.edit_original_response(embed=embed)
        
        except Exception as e:
            embed = create_error_embed(
                "❌ Événement non trouvé",
                f"Impossible de trouver l'événement `{event_id}` :\n{str(e)}"
            )
            await interaction.followup.send(embed=embed)
    
    @app_commands.command(name="event-participants", description="Voir les participants d'un événement")
    @app_commands.describe(event_id="ID de l'événement")
    async def event_participants(self, interaction: discord.Interaction, event_id: str):
        """Affiche la liste des participants"""
        await interaction.response.defer()
        
        try:
            async with VerselinkAPI() as api:
                event = await api.get_event(event_id)
            
            if not event.get('signups'):
                embed = create_info_embed(
                    f"👥 Participants - {event['title']}",
                    "Aucun participant inscrit pour le moment."
                )
                await interaction.followup.send(embed=embed)
                return
            
            # Organiser les participants par statut
            confirmed = [s for s in event['signups'] if s['status'] == 'confirmed']
            waitlist = [s for s in event['signups'] if s['status'] == 'waitlist']
            checked_in = [s for s in event['signups'] if s['status'] == 'checked_in']
            
            embed = create_embed(
                f"👥 Participants - {event['title']}",
                f"**Total inscrit :** {len(event['signups'])}\n"
                f"**Confirmés :** {len(confirmed)}\n"
                f"**En attente :** {len(waitlist)}\n"
                f"**Présents :** {len(checked_in)}"
            )
            
            # Ajouter les participants confirmés
            if confirmed:
                confirmed_list = []
                for signup in confirmed[:10]:  # Limiter à 10 pour éviter de dépasser la limite
                    role_info = f" ({signup['role_name']})" if signup.get('role_name') else ""
                    confirmed_list.append(f"• {signup['user_handle']}{role_info}")
                
                embed.add_field(
                    name="✅ Confirmés",
                    value="\n".join(confirmed_list) + (f"\n... et {len(confirmed) - 10} autres" if len(confirmed) > 10 else ""),
                    inline=False
                )
            
            # Ajouter la liste d'attente si elle existe
            if waitlist:
                waitlist_list = []
                for signup in waitlist[:5]:
                    waitlist_list.append(f"• {signup['user_handle']}")
                
                embed.add_field(
                    name="⏳ Liste d'attente",
                    value="\n".join(waitlist_list) + (f"\n... et {len(waitlist) - 5} autres" if len(waitlist) > 5 else ""),
                    inline=False
                )
            
            embed.add_field(
                name="🔗 Voir tous les détails",
                value=f"[Page complète de l'événement](http://localhost:3000/events/{event_id})",
                inline=False
            )
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            embed = create_error_embed(
                "❌ Erreur",
                f"Impossible de récupérer les participants :\n{str(e)}"
            )
            await interaction.followup.send(embed=embed)
    
    @app_commands.command(name="join-event", description="S'inscrire à un événement")
    @app_commands.describe(
        event_id="ID de l'événement",
        role="Rôle souhaité (optionnel)",
        notes="Notes pour l'organisateur (optionnel)"
    )
    async def join_event(self, interaction: discord.Interaction, event_id: str, role: Optional[str] = None, notes: Optional[str] = None):
        """Inscription à un événement"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Données d'inscription
            signup_data = {}
            if role:
                signup_data['preferred_role'] = role
            if notes:
                signup_data['notes'] = notes
            
            async with VerselinkAPI() as api:
                # S'inscrire à l'événement
                result = await api.join_event(event_id, str(interaction.user.id))
                
                # Récupérer les détails de l'événement
                event = await api.get_event(event_id)
            
            embed = create_success_embed(
                "✅ Inscription confirmée",
                f"Vous êtes inscrit à **{event['title']}** !\n\n"
                f"📅 **Date :** <t:{int(datetime.fromisoformat(event['start_at_utc']).timestamp())}:F>\n"
                f"📍 **Lieu :** {event.get('location', 'Non spécifié')}\n"
                + (f"🎭 **Rôle :** {role}\n" if role else "") +
                f"\nVous recevrez des rappels avant l'événement."
            )
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            if "already" in str(e).lower():
                embed = create_warning_embed(
                    "⚠️ Déjà inscrit",
                    "Vous êtes déjà inscrit à cet événement."
                )
            elif "full" in str(e).lower():
                embed = create_warning_embed(
                    "⚠️ Événement complet",
                    "Cet événement est complet. Vous avez été ajouté à la liste d'attente."
                )
            else:
                embed = create_error_embed(
                    "❌ Erreur d'inscription",
                    f"Impossible de vous inscrire :\n{str(e)}"
                )
            await interaction.followup.send(embed=embed)
    
    @app_commands.command(name="leave-event", description="Se désinscrire d'un événement")
    @app_commands.describe(event_id="ID de l'événement")
    async def leave_event(self, interaction: discord.Interaction, event_id: str):
        """Désinscription d'un événement"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            async with VerselinkAPI() as api:
                # Se désinscrire
                result = await api.leave_event(event_id, str(interaction.user.id))
                
                # Récupérer les détails de l'événement
                event = await api.get_event(event_id)
            
            embed = create_success_embed(
                "✅ Désinscription confirmée",
                f"Vous êtes désinscrit de **{event['title']}**.\n\n"
                f"Vous ne recevrez plus de notifications pour cet événement."
            )
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            embed = create_error_embed(
                "❌ Erreur de désinscription",
                f"Impossible de vous désinscrire :\n{str(e)}"
            )
            await interaction.followup.send(embed=embed)
    
    @app_commands.command(name="my-events", description="Voir mes événements à venir")
    async def my_events(self, interaction: discord.Interaction):
        """Affiche les événements de l'utilisateur"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            async with VerselinkAPI() as api:
                # Récupérer les événements de l'utilisateur
                events = await api.get_user_events(str(interaction.user.id))
            
            if not events:
                embed = create_info_embed(
                    "📅 Mes événements",
                    "Vous n'êtes inscrit à aucun événement à venir.\n\n"
                    f"Découvrez les événements disponibles avec `/events`"
                )
                await interaction.followup.send(embed=embed)
                return
            
            embed = create_embed(
                f"📅 Mes événements ({len(events)})",
                f"Vos {len(events)} prochains événements :"
            )
            
            for event in events[:5]:  # Limiter à 5
                start_time = datetime.fromisoformat(event['start_at_utc'])
                status_emoji = {
                    'confirmed': '✅',
                    'waitlist': '⏳',
                    'checked_in': '🎯'
                }.get(event.get('my_status', 'confirmed'), '📅')
                
                embed.add_field(
                    name=f"{status_emoji} {event['title']}",
                    value=f"**Date :** <t:{int(start_time.timestamp())}:R>\n"
                          f"**Lieu :** {event.get('location', 'Non spécifié')}\n"
                          f"**Statut :** {event.get('my_status', 'Inscrit').title()}",
                    inline=False
                )
            
            if len(events) > 5:
                embed.add_field(
                    name="🔗 Voir tous mes événements",
                    value=f"[Interface web complète](http://localhost:3000/profile/events)",
                    inline=False
                )
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            embed = create_error_embed(
                "❌ Erreur",
                f"Impossible de récupérer vos événements :\n{str(e)}"
            )
            await interaction.followup.send(embed=embed)

async def setup(bot: commands.Bot):
    """Setup function for the cog"""
    await bot.add_cog(EventManagement(bot))