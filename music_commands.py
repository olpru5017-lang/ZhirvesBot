"""
Music Commands module for Discord Music Bot

Implements all user-facing commands for music playback control.
"""

import logging
import discord
from discord.ext import commands
from music_player import MusicPlayer
from audio_source_handler import AudioSourceHandler
from error_handler import ErrorHandler


logger = logging.getLogger(__name__)


class MusicCommands(commands.Cog):
    """Command handler for music playback commands."""
    
    def __init__(self, bot):
        """
        Initialize MusicCommands Cog.
        
        Args:
            bot: The MusicBot instance
        
        Validates Requirements: 10.1-10.10
        """
        self.bot = bot
        self.audio_source_handler = AudioSourceHandler()
        logger.info("MusicCommands Cog initialized")
    
    def _validate_voice_channel(self, ctx):
        """
        Validate that the user is in a voice channel.
        
        Args:
            ctx: Discord command context
        
        Returns:
            discord.VoiceChannel or None: The voice channel if user is connected, None otherwise
        
        Validates Requirements: 4.2, 10.1-10.10
        """
        if not ctx.author.voice:
            return None
        return ctx.author.voice.channel
    
    def _get_or_create_player(self, ctx):
        """
        Get existing MusicPlayer for guild or create a new one.
        
        Args:
            ctx: Discord command context
        
        Returns:
            MusicPlayer: The music player for this guild
        
        Validates Requirements: 4.1, 4.3
        """
        guild_id = ctx.guild.id
        
        if guild_id not in self.bot.music_players:
            logger.info(f"Creating new MusicPlayer for guild {guild_id}")
            self.bot.music_players[guild_id] = MusicPlayer(ctx)
        
        return self.bot.music_players[guild_id]
    
    @commands.command(name='play')
    async def play(self, ctx, *, query: str):
        """
        Play a track from search query or URL.
        
        Supports:
        - YouTube URLs (videos and playlists)
        - SoundCloud URLs
        - Direct audio file URLs
        - Search queries (searches YouTube)
        
        Args:
            ctx: Discord command context
            query: Search query or URL
        
        Validates Requirements: 10.1, 1.1-1.5, 2.1-2.5, 4.1, 4.2
        """
        try:
            # Validate user is in voice channel
            voice_channel = self._validate_voice_channel(ctx)
            if not voice_channel:
                await ErrorHandler.handle_user_error(ctx, "You must be in a voice channel to use this command")
                return
            
            # Get or create music player
            player = self._get_or_create_player(ctx)
            
            # Send processing message
            processing_msg = await ctx.send("🔍 Processing your request...")
            
            # Determine if query is URL or search query
            is_url = query.startswith('http://') or query.startswith('https://')
            
            try:
                if is_url:
                    # Extract from URL
                    logger.info(f"Extracting from URL: {query}")
                    result = await self.audio_source_handler.extract_from_url(query)
                    
                    # Check if result is a playlist (list) or single track
                    if isinstance(result, list):
                        # Playlist
                        player.queue.add_multiple(result)
                        await processing_msg.edit(content=f"✅ Added {len(result)} tracks from playlist to queue")
                        logger.info(f"Added {len(result)} tracks from playlist in guild {ctx.guild.id}")
                    else:
                        # Single track
                        player.queue.add(result)
                        embed = result.get_embed()
                        embed.title = f"✅ Added to queue: {result.title}"
                        await processing_msg.edit(content=None, embed=embed)
                        logger.info(f"Added track '{result.title}' to queue in guild {ctx.guild.id}")
                else:
                    # Search for tracks
                    logger.info(f"Searching for: {query}")
                    results = await self.audio_source_handler.search(query, max_results=1)
                    
                    if not results:
                        await processing_msg.edit(content="❌ No results found for your search")
                        return
                    
                    # Add first result to queue
                    track = results[0]
                    player.queue.add(track)
                    embed = track.get_embed()
                    embed.title = f"✅ Added to queue: {track.title}"
                    await processing_msg.edit(content=None, embed=embed)
                    logger.info(f"Added track '{track.title}' from search to queue in guild {ctx.guild.id}")
            
            except Exception as e:
                logger.error(f"Error processing query '{query}': {e}", exc_info=True)
                await processing_msg.edit(content=f"❌ Error: {str(e)}")
                return
            
            # Connect to voice channel if not already connected
            if not player.voice_client or not player.voice_client.is_connected():
                await player.connect(voice_channel)
                logger.info(f"Connected to voice channel in guild {ctx.guild.id}")
            
            # Start playback if not already playing
            if not player.is_playing and not player.is_paused:
                await player.play_next()
                logger.info(f"Started playback in guild {ctx.guild.id}")
        
        except Exception as e:
            logger.error(f"Error in play command: {e}", exc_info=True)
            await ctx.send(f"❌ An error occurred: {str(e)}")
    
    @commands.command(name='pause')
    async def pause(self, ctx):
        """
        Pause the current track.
        
        Args:
            ctx: Discord command context
        
        Validates Requirements: 10.2, 7.1
        """
        try:
            # Validate user is in voice channel
            voice_channel = self._validate_voice_channel(ctx)
            if not voice_channel:
                await ErrorHandler.handle_user_error(ctx, "You must be in a voice channel to use this command")
                return
            
            # Get player for this guild
            guild_id = ctx.guild.id
            if guild_id not in self.bot.music_players:
                await ErrorHandler.handle_user_error(ctx, "No active music player")
                return
            
            player = self.bot.music_players[guild_id]
            await player.pause()
        
        except Exception as e:
            logger.error(f"Error in pause command: {e}", exc_info=True)
            await ctx.send(f"❌ An error occurred: {str(e)}")
    
    @commands.command(name='resume')
    async def resume(self, ctx):
        """
        Resume playback from pause.
        
        Args:
            ctx: Discord command context
        
        Validates Requirements: 10.3, 7.2
        """
        try:
            # Validate user is in voice channel
            voice_channel = self._validate_voice_channel(ctx)
            if not voice_channel:
                await ErrorHandler.handle_user_error(ctx, "You must be in a voice channel to use this command")
                return
            
            # Get player for this guild
            guild_id = ctx.guild.id
            if guild_id not in self.bot.music_players:
                await ErrorHandler.handle_user_error(ctx, "No active music player")
                return
            
            player = self.bot.music_players[guild_id]
            await player.resume()
        
        except Exception as e:
            logger.error(f"Error in resume command: {e}", exc_info=True)
            await ctx.send(f"❌ An error occurred: {str(e)}")
    
    @commands.command(name='skip')
    async def skip(self, ctx):
        """
        Skip the current track and play the next one.
        
        Args:
            ctx: Discord command context
        
        Validates Requirements: 10.4, 7.3
        """
        try:
            # Validate user is in voice channel
            voice_channel = self._validate_voice_channel(ctx)
            if not voice_channel:
                await ErrorHandler.handle_user_error(ctx, "You must be in a voice channel to use this command")
                return
            
            # Get player for this guild
            guild_id = ctx.guild.id
            if guild_id not in self.bot.music_players:
                await ErrorHandler.handle_user_error(ctx, "No active music player")
                return
            
            player = self.bot.music_players[guild_id]
            await player.skip()
        
        except Exception as e:
            logger.error(f"Error in skip command: {e}", exc_info=True)
            await ctx.send(f"❌ An error occurred: {str(e)}")
    
    @commands.command(name='stop')
    async def stop(self, ctx):
        """
        Stop playback and clear the queue.
        
        Args:
            ctx: Discord command context
        
        Validates Requirements: 10.5, 7.3
        """
        try:
            # Validate user is in voice channel
            voice_channel = self._validate_voice_channel(ctx)
            if not voice_channel:
                await ErrorHandler.handle_user_error(ctx, "You must be in a voice channel to use this command")
                return
            
            # Get player for this guild
            guild_id = ctx.guild.id
            if guild_id not in self.bot.music_players:
                await ErrorHandler.handle_user_error(ctx, "No active music player")
                return
            
            player = self.bot.music_players[guild_id]
            await player.stop()
        
        except Exception as e:
            logger.error(f"Error in stop command: {e}", exc_info=True)
            await ctx.send(f"❌ An error occurred: {str(e)}")

    @commands.command(name='queue')
    async def queue(self, ctx):
        """
        Display the current queue of tracks.
        
        Args:
            ctx: Discord command context
        
        Validates Requirements: 10.6, 5.3, 3.2, 3.3
        """
        try:
            # Get player for this guild
            guild_id = ctx.guild.id
            if guild_id not in self.bot.music_players:
                await ctx.send("❌ No active music player")
                return
            
            player = self.bot.music_players[guild_id]
            
            # Get all tracks in queue
            queue_tracks = player.queue.get_all()
            
            if not queue_tracks:
                await ctx.send("📜 Queue is empty")
                return
            
            # Build embed with queue information
            embed = discord.Embed(
                title="📜 Music Queue",
                description=f"**{len(queue_tracks)} track(s) in queue**",
                color=discord.Color.blue()
            )
            
            # Add up to 10 tracks to the embed
            for i, track in enumerate(queue_tracks[:10], 1):
                embed.add_field(
                    name=f"{i}. {track.title}",
                    value=f"Duration: {track.format_duration()} | Uploader: {track.uploader}",
                    inline=False
                )
            
            # Add note if there are more tracks
            if len(queue_tracks) > 10:
                embed.set_footer(text=f"... and {len(queue_tracks) - 10} more track(s)")
            
            await ctx.send(embed=embed)
            logger.info(f"Displayed queue with {len(queue_tracks)} tracks in guild {ctx.guild.id}")
        
        except Exception as e:
            logger.error(f"Error in queue command: {e}", exc_info=True)
            await ctx.send(f"❌ An error occurred: {str(e)}")
    
    @commands.command(name='nowplaying')
    async def nowplaying(self, ctx):
        """
        Display information about the currently playing track.
        
        Args:
            ctx: Discord command context
        
        Validates Requirements: 10.7, 3.2, 3.3
        """
        try:
            # Get player for this guild
            guild_id = ctx.guild.id
            if guild_id not in self.bot.music_players:
                await ctx.send("❌ No active music player")
                return
            
            player = self.bot.music_players[guild_id]
            
            # Check if there's a current track
            if not player.current_track:
                await ctx.send("❌ Nothing is currently playing")
                return
            
            # Get current track embed
            embed = player.current_track.get_embed()
            embed.title = f"🎵 Now Playing: {player.current_track.title}"
            embed.color = discord.Color.green()
            
            # Add playback status
            if player.is_paused:
                embed.add_field(name="Status", value="⏸️ Paused", inline=True)
            else:
                embed.add_field(name="Status", value="▶️ Playing", inline=True)
            
            # Add volume
            embed.add_field(name="Volume", value=f"🔊 {player.volume}%", inline=True)
            
            # Add queue info
            queue_size = len(player.queue.get_all())
            embed.add_field(name="Queue", value=f"📜 {queue_size} track(s)", inline=True)
            
            await ctx.send(embed=embed)
            logger.info(f"Displayed now playing info in guild {ctx.guild.id}")
        
        except Exception as e:
            logger.error(f"Error in nowplaying command: {e}", exc_info=True)
            await ctx.send(f"❌ An error occurred: {str(e)}")
    
    @commands.command(name='volume')
    async def volume(self, ctx, volume: int):
        """
        Set the playback volume.
        
        Args:
            ctx: Discord command context
            volume: Volume level (0-100)
        
        Validates Requirements: 10.8, 7.4
        """
        try:
            # Validate user is in voice channel
            voice_channel = self._validate_voice_channel(ctx)
            if not voice_channel:
                await ErrorHandler.handle_user_error(ctx, "You must be in a voice channel to use this command")
                return
            
            # Get player for this guild
            guild_id = ctx.guild.id
            if guild_id not in self.bot.music_players:
                await ErrorHandler.handle_user_error(ctx, "No active music player")
                return
            
            player = self.bot.music_players[guild_id]
            await player.set_volume(volume)
        
        except Exception as e:
            logger.error(f"Error in volume command: {e}", exc_info=True)
            await ctx.send(f"❌ An error occurred: {str(e)}")
    
    @commands.command(name='clear')
    async def clear(self, ctx):
        """
        Clear all tracks from the queue except the currently playing track.
        
        Args:
            ctx: Discord command context
        
        Validates Requirements: 10.9, 5.4
        """
        try:
            # Validate user is in voice channel
            voice_channel = self._validate_voice_channel(ctx)
            if not voice_channel:
                await ErrorHandler.handle_user_error(ctx, "You must be in a voice channel to use this command")
                return
            
            # Get player for this guild
            guild_id = ctx.guild.id
            if guild_id not in self.bot.music_players:
                await ErrorHandler.handle_user_error(ctx, "No active music player")
                return
            
            player = self.bot.music_players[guild_id]
            
            # Get queue size before clearing
            queue_size = len(player.queue.get_all())
            
            if queue_size == 0:
                await ctx.send("❌ Queue is already empty")
                return
            
            # Clear the queue
            player.queue.clear()
            
            await ctx.send(f"✅ Cleared {queue_size} track(s) from queue")
            logger.info(f"Cleared {queue_size} tracks from queue in guild {ctx.guild.id}")
        
        except Exception as e:
            logger.error(f"Error in clear command: {e}", exc_info=True)
            await ctx.send(f"❌ An error occurred: {str(e)}")
    
    @commands.command(name='help')
    async def help(self, ctx):
        """
        Display list of all available commands.
        
        Args:
            ctx: Discord command context
        
        Validates Requirements: 10.10
        """
        try:
            embed = discord.Embed(
                title="🎵 Discord Music Bot - Commands",
                description="List of all available commands",
                color=discord.Color.purple()
            )
            
            # Playback commands
            embed.add_field(
                name="▶️ Playback Commands",
                value=(
                    "`/play <query or URL>` - Play a track from search or URL\n"
                    "`/pause` - Pause the current track\n"
                    "`/resume` - Resume playback\n"
                    "`/skip` - Skip the current track\n"
                    "`/stop` - Stop playback and clear queue"
                ),
                inline=False
            )
            
            # Queue commands
            embed.add_field(
                name="📜 Queue Commands",
                value=(
                    "`/queue` - Display the current queue\n"
                    "`/clear` - Clear all tracks from queue\n"
                    "`/nowplaying` - Show currently playing track"
                ),
                inline=False
            )
            
            # Settings commands
            embed.add_field(
                name="⚙️ Settings Commands",
                value=(
                    "`/volume <0-100>` - Set playback volume\n"
                    "`/help` - Show this help message"
                ),
                inline=False
            )
            
            # Additional info
            embed.set_footer(text="Supports YouTube, SoundCloud, and direct audio links")
            
            await ctx.send(embed=embed)
            logger.info(f"Displayed help message in guild {ctx.guild.id}")
        
        except Exception as e:
            logger.error(f"Error in help command: {e}", exc_info=True)
            await ctx.send(f"❌ An error occurred: {str(e)}")


async def setup(bot):
    """
    Setup function to add the cog to the bot.
    
    Args:
        bot: The MusicBot instance
    """
    await bot.add_cog(MusicCommands(bot))
    logger.info("MusicCommands Cog loaded")
