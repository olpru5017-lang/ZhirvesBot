"""
Discord Music Bot - Main Entry Point

A Discord bot that plays music in voice channels with support for
YouTube, SoundCloud, and direct audio links.
"""

import os
import logging
from dotenv import load_dotenv
import discord
from discord.ext import commands


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MusicBot(commands.Bot):
    """Main bot client for Discord Music Bot."""
    
    def __init__(self):
        """Initialize the bot with required intents and settings."""
        intents = discord.Intents.default()
        intents.message_content = True
        intents.voice_states = True
        
        super().__init__(command_prefix='/', intents=intents)
        
        # Dictionary to store MusicPlayer instances per guild
        self.music_players = {}
    
    async def setup_hook(self):
        """Initialize bot components after connection."""
        logger.info("Bot setup hook called")
        # Load MusicCommands cog
        await self.load_extension('music_commands')
        logger.info("MusicCommands cog loaded")
    
    async def on_ready(self):
        """Called when the bot is ready and connected to Discord."""
        logger.info(f"Bot logged in as {self.user.name} (ID: {self.user.id})")
        logger.info(f"Connected to {len(self.guilds)} guilds")
        await self.change_presence(activity=discord.Game(name="🎵 Ready to play music"))


async def main():
    """Main entry point for the bot."""
    # Load environment variables
    load_dotenv()
    
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        logger.error("DISCORD_TOKEN not found in environment variables")
        logger.error("Please create a .env file with your bot token")
        return
    
    # Create and start the bot
    bot = MusicBot()
    
    try:
        logger.info("Starting Discord Music Bot...")
        await bot.start(token)
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    except Exception as e:
        logger.error(f"Error starting bot: {e}", exc_info=True)
    finally:
        await bot.close()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
