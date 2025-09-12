import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional, Dict, Any, List
import logging
from datetime import datetime, timedelta, timezone
import asyncio
import uuid

from verselink_api import VerselinkAPI
from utils import *
from config import Config
from event_handlers import EventCreationHandler
from tournament_handlers import TournamentCreationHandler

logger = logging.getLogger(__name__)

class InteractiveSession:
    """Classe pour gérer une session de création interactive"""
    
    def __init__(self, user_id: str, session_type: str):
        self.user_id = user_id
        self.session_type = session_type  # 'event' ou 'tournament'
        self.session_id = str(uuid.uuid4())
        self.data = {}
        self.step = 0
        self.created_at = datetime.utcnow()
        self.last_activity = datetime.utcnow()
        self.is_active = True
        
    def update_activity(self):
        """Met à jour la dernière activité"""
        self.last_activity = datetime.utcnow()
        
    def is_expired(self, timeout_minutes: int = 30) -> bool:
        """Vérifie si la session a expiré"""
        return (datetime.utcnow() - self.last_activity).total_seconds() > (timeout_minutes * 60)

class SessionManager:
    """Gestionnaire des sessions interactives"""
    
    def __init__(self):
        self.sessions: Dict[str, InteractiveSession] = {}
        
    def create_session(self, user_id: str, session_type: str) -> InteractiveSession:
        """Crée une nouvelle session"""
        # Termine les sessions existantes pour cet utilisateur
        self.end_user_sessions(user_id)
        
        session = InteractiveSession(user_id, session_type)
        self.sessions[session.session_id] = session
        return session
        
    def get_session(self, user_id: str) -> Optional[InteractiveSession]:
        """Récupère la session active d'un utilisateur"""
        for session in self.sessions.values():
            if session.user_id == user_id and session.is_active:
                if session.is_expired():
                    session.is_active = False
                    continue
                return session
        return None
        
    def end_session(self, session_id: str):
        """Termine une session"""
        if session_id in self.sessions:
            self.sessions[session_id].is_active = False
            
    def end_user_sessions(self, user_id: str):
        """Termine toutes les sessions d'un utilisateur"""
        for session in self.sessions.values():
            if session.user_id == user_id:
                session.is_active = False
                
    def cleanup_expired(self):
        """Nettoie les sessions expirées"""
        expired = [sid for sid, session in self.sessions.items() if session.is_expired()]
        for sid in expired:
            self.sessions[sid].is_active = False

class EventCreationView(discord.ui.View):
    """Interface pour sélectionner le type d'événement"""
    
    def __init__(self, session_manager: SessionManager):
        super().__init__(timeout=300.0)
        self.session_manager = session_manager
        
    @discord.ui.select(
        placeholder="Choisissez le type d'événement...",
        min_values=1,
        max_values=1,
        options=[
            discord.SelectOption(label="🎯 Raid PvE", value="raid", description="Opération PvE contre l'IA"),
            discord.SelectOption(label="🏁 Course", value="course", description="Course de vaisseaux"),
            discord.SelectOption(label="⚔️ Combat PvP", value="pvp", description="Combat joueur contre joueur"),
            discord.SelectOption(label="🔫 FPS", value="fps", description="Combat au sol FPS"),
            discord.SelectOption(label="🔧 Salvaging", value="salvaging", description="Récupération et salvage"),
            discord.SelectOption(label="📦 Logistique", value="logistique", description="Transport et livraison"),
            discord.SelectOption(label="🌍 Exploration", value="exploration", description="Découverte de nouveaux systèmes"),
            discord.SelectOption(label="⛏️ Mining", value="mining", description="Extraction minière"),
            discord.SelectOption(label="💼 Trading", value="trading", description="Commerce et négoce"),
            discord.SelectOption(label="🎭 Roleplay", value="roleplay", description="Événement roleplay"),
            discord.SelectOption(label="📋 Autre", value="autre", description="Autre type d'événement")
        ]
    )
    async def select_event_type(self, interaction: discord.Interaction, select: discord.ui.Select):
        session = self.session_manager.get_session(str(interaction.user.id))
        if not session or session.session_type != 'event':
            await interaction.response.send_message("❌ Session expirée. Veuillez recommencer avec `/create-event`.", ephemeral=True)
            return
            
        session.data['type'] = select.values[0]
        session.update_activity()
        
        type_names = {
            'raid': 'Raid PvE', 'course': 'Course', 'pvp': 'Combat PvP', 'fps': 'Combat FPS',
            'salvaging': 'Salvaging', 'logistique': 'Logistique', 'exploration': 'Exploration',
            'mining': 'Mining', 'trading': 'Trading', 'roleplay': 'Roleplay', 'autre': 'Autre'
        }
        
        embed = create_success_embed(
            "✅ Type d'événement sélectionné",
            f"Vous avez choisi : **{type_names[select.values[0]]}**\n\n"
            f"Maintenant, envoyez-moi le **titre** de votre événement en message privé.\n"
            f"📝 *Exemple: \"Raid sur Jumptown - Opération Nettoyage\"*"
        )
        
        await interaction.response.edit_message(embed=embed, view=None)
        
        # Envoie un MP pour la suite
        try:
            dm_embed = create_info_embed(
                "📝 Titre de l'événement",
                f"Parfait ! Votre événement sera de type **{type_names[select.values[0]]}**.\n\n"
                f"Maintenant, envoyez-moi le **titre** de votre événement.\n\n"
                f"💡 **Conseils pour un bon titre :**\n"
                f"• Soyez précis et accrocheur\n"
                f"• Mentionnez le lieu si important\n"
                f"• Indiquez le niveau si nécessaire\n\n"
                f"📝 **Exemples :**\n"
                f"• \"Raid Jumptown - Opération Nettoyage\"\n"
                f"• \"Course Murray Cup - Qualification\"\n"
                f"• \"Exploration Pyro - Première Expédition\"\n\n"
                f"⏰ *Vous avez 10 minutes pour répondre*"
            )
            await interaction.user.send(embed=dm_embed)
        except discord.Forbidden:
            embed = create_error_embed(
                "❌ Impossible d'envoyer un MP",
                "Je ne peux pas vous envoyer de message privé. Veuillez activer les MPs ou continuer ici.\n\n"
                f"Envoyez votre titre d'événement dans ce canal."
            )
            await interaction.edit_original_response(embed=embed)

class InteractiveEvents(commands.Cog):
    """Système interactif de création d'événements et tournois"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.api = VerselinkAPI()
        self.session_manager = SessionManager()
        
        # Gestionnaires spécialisés
        self.event_handler = EventCreationHandler(self.api, self.bot)
        self.tournament_handler = TournamentCreationHandler(self.api)
        
    async def cog_load(self):
        """Initialize the cog"""
        logger.info("Interactive Events cog loaded")
        # Démarrer le nettoyage périodique des sessions
        self.cleanup_task = asyncio.create_task(self.cleanup_expired_sessions())
        
    async def cog_unload(self):
        """Cleanup when cog is unloaded"""
        if hasattr(self, 'cleanup_task'):
            self.cleanup_task.cancel()
        if self.api.session:
            await self.api.session.close()
            
    async def cleanup_expired_sessions(self):
        """Nettoie périodiquement les sessions expirées"""
        while True:
            try:
                await asyncio.sleep(300)  # Toutes les 5 minutes
                self.session_manager.cleanup_expired()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error cleaning up sessions: {e}")
    
    @app_commands.command(name="create-event", description="Créer un événement de manière interactive")
    async def create_event_interactive(self, interaction: discord.Interaction):
        """Commande pour créer un événement de manière interactive"""
        await interaction.response.defer(ephemeral=True)
        
        # Vérifier si l'utilisateur a déjà une session active
        existing_session = self.session_manager.get_session(str(interaction.user.id))
        if existing_session:
            embed = create_warning_embed(
                "⚠️ Session active",
                f"Vous avez déjà une session de création **{existing_session.session_type}** en cours.\n\n"
                f"Tapez `annuler` dans nos MPs pour l'annuler, ou continuez votre création actuelle."
            )
            await interaction.followup.send(embed=embed)
            return
        
        # Créer une nouvelle session
        session = self.session_manager.create_session(str(interaction.user.id), 'event')
        
        embed = create_embed(
            "🎯 Création d'Événement Interactive",
            "Bienvenue dans l'assistant de création d'événements !\n\n"
            "Je vais vous guider étape par étape pour créer votre événement parfait.\n"
            "Commençons par choisir le type d'événement :",
            color=0x3B82F6
        )
        
        view = EventCreationView(self.session_manager)
        await interaction.followup.send(embed=embed, view=view)
        
    @app_commands.command(name="create-tournament", description="Créer un tournoi de manière interactive")
    async def create_tournament_interactive(self, interaction: discord.Interaction):
        """Commande pour créer un tournoi de manière interactive"""
        await interaction.response.defer(ephemeral=True)
        
        # Vérifier si l'utilisateur a déjà une session active
        existing_session = self.session_manager.get_session(str(interaction.user.id))
        if existing_session:
            embed = create_warning_embed(
                "⚠️ Session active",
                f"Vous avez déjà une session de création **{existing_session.session_type}** en cours.\n\n"
                f"Tapez `annuler` dans nos MPs pour l'annuler, ou continuez votre création actuelle."
            )
            await interaction.followup.send(embed=embed)
            return
        
        # Créer une nouvelle session pour tournoi
        session = self.session_manager.create_session(str(interaction.user.id), 'tournament')
        
        embed = create_embed(
            "🏆 Création de Tournoi Interactive",
            "Bienvenue dans l'assistant de création de tournois !\n\n"
            "Je vais vous guider pour créer votre tournoi compétitif.\n"
            "Commençons par me dire le **nom** de votre tournoi en message privé.",
            color=0xF59E0B
        )
        
        await interaction.followup.send(embed=embed)
        
        # Envoyer le premier MP
        try:
            dm_embed = create_info_embed(
                "🏆 Nom du tournoi",
                "Parfait ! Commençons par le nom de votre tournoi.\n\n"
                "💡 **Conseils pour un bon nom :**\n"
                "• Soyez créatif et mémorable\n"
                "• Mentionnez le jeu/mode si nécessaire\n"
                "• Indiquez la période ou saison\n\n"
                "📝 **Exemples :**\n"
                "• \"Championnat Star Citizen 2025\"\n"
                "• \"Tournoi Racing Murray Cup\"\n"
                "• \"Arena Commander Masters\"\n\n"
                "⏰ *Vous avez 10 minutes pour répondre*"
            )
            await interaction.user.send(embed=dm_embed)
        except discord.Forbidden:
            embed = create_error_embed(
                "❌ Impossible d'envoyer un MP",
                "Je ne peux pas vous envoyer de message privé. Veuillez activer les MPs."
            )
            await interaction.edit_original_response(embed=embed)
            self.session_manager.end_session(session.session_id)
    
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Écoute les messages pour les sessions interactives"""
        # Ignorer les messages du bot
        if message.author.bot:
            return
            
        # Vérifier si c'est un MP et si l'utilisateur a une session active
        if isinstance(message.channel, discord.DMChannel):
            session = self.session_manager.get_session(str(message.author.id))
            if session and session.is_active:
                await self.handle_session_message(message, session)
    
    async def handle_session_message(self, message: discord.Message, session: InteractiveSession):
        """Gère les messages dans le contexte d'une session"""
        session.update_activity()
        
        # Commandes spéciales
        content = message.content.lower().strip()
        if content in ['annuler', 'cancel', 'stop', 'quit']:
            await self.cancel_session(message, session)
            return
        elif content in ['aide', 'help', '?']:
            await self.send_help(message, session)
            return
        elif content in ['status', 'statut', 'état']:
            await self.send_status(message, session)
            return
            
        # Traiter selon le type de session
        if session.session_type == 'event':
            await self.event_handler.handle_event_message(message, session)
        elif session.session_type == 'tournament':
            await self.tournament_handler.handle_tournament_message(message, session)
    
    async def cancel_session(self, message: discord.Message, session: InteractiveSession):
        """Annule une session"""
        self.session_manager.end_session(session.session_id)
        
        embed = create_success_embed(
            "✅ Session annulée",
            f"Votre session de création de **{session.session_type}** a été annulée.\n\n"
            f"Vous pouvez recommencer à tout moment avec `/create-{session.session_type}`."
        )
        await message.channel.send(embed=embed)
    
    async def send_help(self, message: discord.Message, session: InteractiveSession):
        """Envoie l'aide pour une session"""
        embed = create_info_embed(
            "🤖 Aide - Session Interactive",
            f"Vous êtes en train de créer un **{session.session_type}**.\n\n"
            f"**Commandes disponibles :**\n"
            f"• `annuler` - Annuler la création\n"
            f"• `status` - Voir l'état actuel\n"
            f"• `aide` - Voir cette aide\n\n"
            f"**Progression :** {len(session.data)}/10 étapes complétées\n\n"
            f"Continuez en répondant à la dernière question posée."
        )
        await message.channel.send(embed=embed)
    
    async def send_status(self, message: discord.Message, session: InteractiveSession):
        """Envoie le statut d'une session"""
        steps_completed = len(session.data)
        total_steps = len(self.event_steps) if session.session_type == 'event' else len(self.tournament_steps)
        
        embed = create_info_embed(
            f"📊 Statut - Création de {session.session_type.title()}",
            f"**Progression :** {steps_completed}/{total_steps} étapes\n\n"
            f"**Données collectées :**\n"
        )
        
        for key, value in session.data.items():
            if key == 'description' and len(str(value)) > 100:
                value = str(value)[:100] + "..."
            embed.description += f"• **{key.title()}**: {value}\n"
        
        await message.channel.send(embed=embed)

async def setup(bot: commands.Bot):
    """Setup function for the cog"""
    await bot.add_cog(InteractiveEvents(bot))