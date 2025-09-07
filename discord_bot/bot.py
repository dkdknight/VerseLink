import discord
from discord.ext import commands
import asyncio
import logging
import sys
import traceback
from datetime import datetime

from config import Config
from verselink_api import VerselinkAPI
from utils import create_embed, create_error_embed, create_success_embed

# Setup logging
import sys
import os

# Force UTF-8 encoding for Windows compatibility
if sys.platform.startswith('win'):
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Set environment encoding
os.environ['PYTHONIOENCODING'] = 'utf-8'

logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class VerselinkBot(commands.Bot):
    """Main VerseLink Discord Bot"""
    
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        intents.guild_messages = True
        intents.members = True
        
        super().__init__(
            command_prefix=Config.BOT_PREFIX,
            intents=intents,
            help_command=None,
            description="Bot officiel VerseLink pour Star Citizen"
        )
        
        self.api = VerselinkAPI()
        self.start_time = datetime.utcnow()
        
    async def setup_hook(self):
        """Setup hook called when bot is starting"""
        logger.info("Setting up VerseLink bot...")
        
        try:
            # Verify configuration
            Config.validate()
            logger.info("Configuration validated")
            
            # Test API connection
            async with VerselinkAPI() as api:
                health = await api.verify_bot()
                logger.info(f"API connection verified: {health}")
            
            # Load extensions
            await self.load_extension('commands')
            logger.info("Commands loaded")
            
            # Sync commands
            synced = await self.tree.sync()
            logger.info(f"Synced {len(synced)} command(s)")
            
        except Exception as e:
            logger.error(f"Setup failed: {e}")
            raise
    
    async def on_ready(self):
        """Called when bot is ready"""
        logger.info(f"Bot {self.user} is now online!")
        logger.info(f"Connected to {len(self.guilds)} guild(s)")
        logger.info(f"Serving {sum(g.member_count for g in self.guilds)} users")
        
        # Set bot status
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name="VerseLink | /help"
        )
        await self.change_presence(activity=activity)
        
        # Register all connected guilds
        await self.register_all_guilds()
    
    async def on_guild_join(self, guild: discord.Guild):
        """Called when bot joins a new guild"""
        logger.info(f"Joined guild: {guild.name} ({guild.id})")
        
        # Try to find a general channel to send welcome message
        welcome_channel = None
        for channel in guild.text_channels:
            if channel.permissions_for(guild.me).send_messages:
                if any(name in channel.name.lower() for name in ['general', 'accueil', 'welcome', 'bot']):
                    welcome_channel = channel
                    break
        
        if not welcome_channel:
            # Find any channel we can send to
            for channel in guild.text_channels:
                if channel.permissions_for(guild.me).send_messages:
                    welcome_channel = channel
                    break
        
        if welcome_channel:
            embed = create_success_embed(
                "VerseLink Bot - Bienvenue !",
                f"Merci d'avoir ajoute le bot VerseLink a **{guild.name}** !\n\n"
                f"Configuration requise :\n"
                f"Utilisez `/setup` pour configurer votre serveur\n\n"
                f"Commandes principales :\n"
                f"• `/setup` - Configurer le serveur\n"
                f"• `/config` - Voir la configuration\n"
                f"• `/events` - Lister les evenements\n"
                f"• `/tournaments` - Lister les tournois\n"
                f"• `/status` - Statut du systeme\n\n"
                f"Liens utiles :\n"
                f"[Site VerseLink](http://89.88.206.99:3000) | "
                f"[Gestion Discord](http://89.88.206.99:3000/discord)\n\n"
                f"Besoin d'aide ? Utilisez `/help` ou contactez un administrateur."
            )
            
            try:
                await welcome_channel.send(embed=embed)
            except discord.Forbidden:
                logger.warning(f"Cannot send welcome message in {guild.name}")
    
    async def on_guild_remove(self, guild: discord.Guild):
        """Called when bot leaves a guild"""
        logger.info(f"📤 Left guild: {guild.name} ({guild.id})")
        
        # Disconnect guild from VerseLink
        try:
            async with VerselinkAPI() as api:
                # We'll just log this for now since disconnect endpoint is optional
                logger.info(f"Guild {guild.name} disconnected from VerseLink")
        except Exception as e:
            logger.error(f"Failed to disconnect guild {guild.name}: {e}")
    
    async def on_message(self, message: discord.Message):
        """Called for every message"""
        # Ignore bot messages
        if message.author.bot:
            return
        
        # Process commands
        await self.process_commands(message)
        
        # Auto-moderation check (if enabled)
        if message.guild:
            try:
                await self.check_message_moderation(message)
            except Exception as e:
                logger.error(f"Auto-moderation error: {e}")
    
    async def check_message_moderation(self, message: discord.Message):
        """Check message for auto-moderation"""
        try:
            async with VerselinkAPI() as api:
                result = await api.check_message_content(
                    content=message.content,
                    user_id=str(message.author.id)
                )
            
            if result.get('violations_detected'):
                violations = result.get('violations', [])
                logger.info(f"Auto-moderation triggered for user {message.author} in {message.guild.name}")
                
                # Take action based on violations
                for violation in violations:
                    action = violation.get('action', 'warning')
                    
                    if action == 'warning':
                        # Send warning message
                        embed = create_error_embed(
                            "⚠️ Avertissement Auto-Modération",
                            f"{message.author.mention}, votre message a été signalé par l'auto-modération.\n"
                            f"**Raison**: {violation.get('details', 'Violation détectée')}\n\n"
                            f"Veuillez respecter les règles de la communauté."
                        )
                        
                        try:
                            await message.channel.send(embed=embed, delete_after=30)
                        except discord.Forbidden:
                            pass
                    
                    elif action in ['strike', 'temporary_ban']:
                        # More serious actions - just log for now
                        logger.warning(f"Serious auto-moderation action required: {action} for {message.author}")
        
        except Exception as e:
            # Don't spam logs for API errors
            if "404" not in str(e):
                logger.debug(f"Auto-moderation check failed: {e}")
    
    async def register_all_guilds(self):
        """Register all connected guilds with VerseLink"""
        for guild in self.guilds:
            try:
                guild_data = {
                    'guild_id': str(guild.id),
                    'guild_name': guild.name,
                    'guild_icon': str(guild.icon) if guild.icon else None,
                    'owner_id': str(guild.owner_id),
                    'member_count': guild.member_count,
                    'bot_auto_registered': True
                }
                
                async with VerselinkAPI() as api:
                    await api.register_guild(str(guild.id), guild_data)
                
                logger.info(f"Registered guild: {guild.name}")
                
            except Exception as e:
                if "already registered" in str(e).lower():
                    logger.debug(f"Guild {guild.name} already registered")
                else:
                    logger.error(f"Failed to register guild {guild.name}: {e}")
    
    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError):
        """Handle command errors"""
        if isinstance(error, commands.CommandNotFound):
            return
        
        logger.error(f"Command error in {ctx.command}: {error}")
        
        embed = create_error_embed(
            "❌ Erreur de Commande",
            f"Une erreur s'est produite : {str(error)}"
        )
        
        try:
            await ctx.send(embed=embed, delete_after=30)
        except discord.Forbidden:
            pass
    
    async def on_app_command_error(self, interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
        """Handle application command errors"""
        logger.error(f"App command error: {error}")
        
        if isinstance(error, discord.app_commands.MissingPermissions):
            embed = create_error_embed(
                "❌ Permissions Insuffisantes",
                "Vous n'avez pas les permissions nécessaires pour utiliser cette commande."
            )
        elif isinstance(error, discord.app_commands.CommandOnCooldown):
            embed = create_error_embed(
                "⏰ Délai d'Attente",
                f"Cette commande est en délai d'attente. Réessayez dans {error.retry_after:.1f} secondes."
            )
        else:
            embed = create_error_embed(
                "❌ Erreur",
                f"Une erreur s'est produite : {str(error)}"
            )
        
        try:
            if interaction.response.is_done():
                await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                await interaction.response.send_message(embed=embed, ephemeral=True)
        except discord.Forbidden:
            pass
    
    async def close(self):
        """Cleanup when bot is shutting down"""
        logger.info("🛑 Shutting down VerseLink bot...")
        
        # Close API session
        if self.api.session:
            await self.api.session.close()
        
        await super().close()

def main():
    """Main function to run the bot"""
    try:
        # Validate configuration
        Config.validate()
        
        # Create and run bot
        bot = VerselinkBot()
        bot.run(Config.DISCORD_BOT_TOKEN, log_handler=None)
        
    except ValueError as e:
        logger.error(f"❌ Configuration error: {e}")
        logger.error("Please check your .env file and ensure all required variables are set.")
        sys.exit(1)
    except discord.LoginFailure:
        logger.error("❌ Invalid Discord bot token!")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("👋 Bot stopped by user")
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()