import discord
from discord.ext import commands
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import logging
import asyncio

logger = logging.getLogger(__name__)

def format_datetime(dt_str: str) -> str:
    """Format datetime string for Discord display"""
    try:
        dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        return f"<t:{int(dt.timestamp())}:F>"
    except:
        return dt_str

def format_date(dt_str: str) -> str:
    """Format date for Discord display"""
    try:
        dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        return f"<t:{int(dt.timestamp())}:D>"
    except:
        return dt_str

def format_time(dt_str: str) -> str:
    """Format time for Discord display"""
    try:
        dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        return f"<t:{int(dt.timestamp())}:t>"
    except:
        return dt_str

def create_embed(title: str, description: str = None, color: int = 0x3B82F6) -> discord.Embed:
    """Create a standard VerseLink embed"""
    embed = discord.Embed(title=title, description=description, color=color)
    embed.set_footer(text="VerseLink", icon_url="https://i.imgur.com/placeholder.png")
    embed.timestamp = datetime.now(timezone.utc)
    return embed

def create_error_embed(title: str, description: str) -> discord.Embed:
    """Create an error embed"""
    return create_embed(title, description, color=0xEF4444)

def create_success_embed(title: str, description: str) -> discord.Embed:
    """Create a success embed"""
    return create_embed(title, description, color=0x10B981)

def create_warning_embed(title: str, description: str) -> discord.Embed:
    """Create a warning embed"""
    return create_embed(title, description, color=0xF59E0B)

def create_info_embed(title: str, description: str) -> discord.Embed:
    """Create an info embed"""
    return create_embed(title, description, color=0x6B7280)

def create_event_embed(event: Dict[str, Any]) -> discord.Embed:
    """Create embed for event announcement"""
    embed = create_embed(
        title=f"📅 {event['title']}",
        description=event.get('description', 'Aucune description'),
        color=0x3B82F6
    )
    
    if event.get('date'):
        embed.add_field(
            name="📆 Date",
            value=format_datetime(event['date']),
            inline=True
        )
    
    if event.get('location'):
        embed.add_field(
            name="📍 Lieu",
            value=event['location'],
            inline=True
        )
    
    if event.get('max_participants'):
        participants = event.get('current_participants', 0)
        embed.add_field(
            name="👥 Participants",
            value=f"{participants}/{event['max_participants']}",
            inline=True
        )
    
    if event.get('organization_name'):
        embed.add_field(
            name="🏢 Organisation",
            value=event['organization_name'],
            inline=True
        )
    
    embed.add_field(
        name="🔗 Lien",
        value=f"[Voir sur VerseLink](http://89.88.206.99:3000/events/{event.get('id', '')})",
        inline=False
    )
    
    return embed

def create_tournament_embed(tournament: Dict[str, Any]) -> discord.Embed:
    """Create embed for tournament announcement"""
    embed = create_embed(
        title=f"🏆 {tournament['name']}",
        description=tournament.get('description', 'Aucune description'),
        color=0xF59E0B
    )
    
    if tournament.get('start_date'):
        embed.add_field(
            name="🚀 Début",
            value=format_datetime(tournament['start_date']),
            inline=True
        )
    
    if tournament.get('tournament_type'):
        embed.add_field(
            name="🎯 Type",
            value=tournament['tournament_type'].replace('_', ' ').title(),
            inline=True
        )
    
    if tournament.get('max_participants'):
        participants = tournament.get('current_participants', 0)
        embed.add_field(
            name="👥 Participants",
            value=f"{participants}/{tournament['max_participants']}",
            inline=True
        )
    
    if tournament.get('game'):
        embed.add_field(
            name="🎮 Jeu",
            value=tournament['game'],
            inline=True
        )
    
    if tournament.get('prize_pool'):
        embed.add_field(
            name="💰 Prix",
            value=tournament['prize_pool'],
            inline=True
        )
    
    status_color = {
        'open': '🟢 Ouvert',
        'full': '🟡 Complet',
        'active': '🔴 En cours',
        'finished': '⚫ Terminé'
    }
    
    embed.add_field(
        name="📊 Statut",
        value=status_color.get(tournament.get('status', 'open'), '🟢 Ouvert'),
        inline=True
    )
    
    embed.add_field(
        name="🔗 Lien",
        value=f"[Voir sur VerseLink](http://89.88.206.99:3000/tournaments/{tournament.get('id', '')})",
        inline=False
    )
    
    return embed

def create_bracket_embed(tournament: Dict[str, Any], bracket: Dict[str, Any]) -> discord.Embed:
    """Create embed for tournament bracket"""
    embed = create_embed(
        title=f"🏆 Bracket - {tournament['name']}",
        color=0xF59E0B
    )
    
    if bracket.get('rounds'):
        rounds_info = []
        for round_data in bracket['rounds']:
            round_name = round_data.get('name', f"Round {round_data.get('round_number', '?')}")
            matches = round_data.get('matches', [])
            completed = len([m for m in matches if m.get('status') == 'completed'])
            total = len(matches)
            rounds_info.append(f"**{round_name}**: {completed}/{total} matchs")
        
        embed.add_field(
            name="📊 Progression",
            value="\n".join(rounds_info[:5]),  # Limit to 5 rounds
            inline=False
        )
    
    embed.add_field(
        name="🔗 Bracket Complet",
        value=f"[Voir sur VerseLink](http://89.88.206.99:3000/tournaments/{tournament.get('id', '')}/bracket)",
        inline=False
    )
    
    return embed

class ConfirmationView(discord.ui.View):
    """View for confirmation dialogs"""
    def __init__(self, timeout: float = 30.0):
        super().__init__(timeout=timeout)
        self.value = None
    
    @discord.ui.button(label='Confirmer', style=discord.ButtonStyle.green, emoji='✅')
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        self.value = True
        self.stop()
    
    @discord.ui.button(label='Annuler', style=discord.ButtonStyle.red, emoji='❌')
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        self.value = False
        self.stop()

async def send_confirmation(
    interaction: discord.Interaction, 
    message: str, 
    timeout: float = 30.0
) -> Optional[bool]:
    """Send a confirmation dialog and return the result"""
    embed = create_warning_embed("Confirmation", message)
    view = ConfirmationView(timeout=timeout)
    
    await interaction.followup.send(embed=embed, view=view, ephemeral=True)
    
    await view.wait()
    return view.value

def has_manage_guild():
    """Check if user has manage guild permissions"""
    def predicate(interaction: discord.Interaction):
        return interaction.user.guild_permissions.manage_guild
    return discord.app_commands.check(predicate)

def is_bot_admin():
    """Check if user is a bot admin (server owner or has admin perms)"""
    def predicate(interaction: discord.Interaction):
        return (
            interaction.user.guild_permissions.administrator or
            interaction.user.id == interaction.guild.owner_id
        )
    return discord.app_commands.check(predicate)

async def safe_send(channel, content=None, **kwargs):
    """Safely send a message to a channel"""
    try:
        return await channel.send(content, **kwargs)
    except discord.Forbidden:
        logger.warning(f"Missing permissions to send message in {channel}")
        return None
    except discord.HTTPException as e:
        logger.error(f"HTTP error sending message: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error sending message: {e}")
        return None

def chunk_text(text: str, max_length: int = 2000) -> List[str]:
    """Split text into chunks that fit Discord message limits"""
    if len(text) <= max_length:
        return [text]
    
    chunks = []
    current_chunk = ""
    
    for line in text.split('\n'):
        if len(current_chunk) + len(line) + 1 > max_length:
            if current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = ""
        
        if len(line) > max_length:
            # Split long lines
            while line:
                chunk_size = max_length - len(current_chunk) - 1
                if chunk_size <= 0:
                    chunks.append(current_chunk.strip())
                    current_chunk = ""
                    chunk_size = max_length
                
                chunks.append(line[:chunk_size])
                line = line[chunk_size:]
        else:
            if current_chunk:
                current_chunk += "\n"
            current_chunk += line
    
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks