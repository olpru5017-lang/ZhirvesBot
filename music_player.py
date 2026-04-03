"""
Music Player module for Discord Music Bot

Manages audio playback in voice channels.
"""

import asyncio
import logging
import discord
from track_queue import TrackQueue
from audio_source_handler import AudioSourceHandler
from error_handler import ErrorHandler


logger = logging.getLogger(__name__)


class MusicPlayer:
    """Manages music playback in a Discord voice channel."""
    
    def __init__(self, ctx):
        """
        Initialize MusicPlayer for a guild.
        
        Args:
            ctx: Discord command context containing bot, guild, and channel info
        
        Validates Requirements: 4.1, 4.3
        """
        self.bot = ctx.bot
        self.guild = ctx.guild
        self.channel = ctx.channel
        self.queue = TrackQueue()
        self.current_track = None
        self.voice_client = None
        self.volume = 50
        self.is_playing = False
        self.is_paused = False
        self.disconnect_timer = None
        self.audio_source_handler = AudioSourceHandler()
        self.ctx = ctx
        
        logger.info(f"MusicPlayer initialized for guild {self.guild.id}")
    
    async def connect(self, voice_channel):
        """
        Connect to a voice channel.
        
        Args:
            voice_channel: Discord VoiceChannel to connect to
        
        Raises:
            Exception: If connection fails
        
        Validates Requirements: 4.1, 4.3
        """
        try:
            # If already connected to a different channel, move to new channel
            if self.voice_client and self.voice_client.is_connected():
                if self.voice_client.channel != voice_channel:
                    logger.info(f"Moving from channel {self.voice_client.channel.id} to {voice_channel.id}")
                    await self.voice_client.move_to(voice_channel)
                else:
                    logger.info(f"Already connected to channel {voice_channel.id}")
                    return
            else:
                # Connect to the voice channel
                logger.info(f"Connecting to voice channel {voice_channel.id} in guild {self.guild.id}")
                self.voice_client = await voice_channel.connect()
            
            logger.info(f"Successfully connected to voice channel {voice_channel.id}")
            
        except Exception as e:
            logger.error(f"Failed to connect to voice channel {voice_channel.id}: {e}", exc_info=True)
            raise
    
    async def disconnect(self):
        """
        Disconnect from the voice channel and cleanup resources.
        
        Validates Requirements: 4.4
        """
        try:
            # Cancel disconnect timer if active
            if self.disconnect_timer:
                self.disconnect_timer.cancel()
                self.disconnect_timer = None
                logger.info("Cancelled disconnect timer")
            
            # Stop playback if active
            if self.voice_client and self.voice_client.is_playing():
                self.voice_client.stop()
                logger.info("Stopped playback before disconnect")
            
            # Disconnect from voice channel
            if self.voice_client and self.voice_client.is_connected():
                logger.info(f"Disconnecting from voice channel in guild {self.guild.id}")
                await self.voice_client.disconnect()
                logger.info("Successfully disconnected from voice channel")
            
            # Reset state
            self.voice_client = None
            self.current_track = None
            self.is_playing = False
            self.is_paused = False
            
            logger.info(f"MusicPlayer cleanup completed for guild {self.guild.id}")
            
        except Exception as e:
            logger.error(f"Error during disconnect in guild {self.guild.id}: {e}", exc_info=True)
            # Reset state even if disconnect fails
            self.voice_client = None
            self.current_track = None
            self.is_playing = False
            self.is_paused = False
    
    async def play_next(self, retry_count: int = 0):
        """
        Play the next track from the queue.
        
        Handles automatic progression through the queue, empty queue scenarios,
        and retry logic for stream interruptions.
        
        Args:
            retry_count (int): Current retry attempt (0-indexed, max 3 attempts)
        
        Validates Requirements: 6.1, 6.2, 6.3, 6.4, 6.5
        """
        try:
            # If this is a retry, check if we've exceeded max attempts
            if retry_count >= 3:
                logger.error(f"Max retries (3) reached for track in guild {self.guild.id}")
                await ErrorHandler.handle_audio_error(self.ctx, Exception("Max retries reached"), retry_count)
                # Skip to next track after max retries
                self.current_track = None
                await self.play_next(retry_count=0)
                return
            
            # If retrying the same track, don't get a new one from queue
            if retry_count == 0:
                # Get next track from queue
                next_track = self.queue.next()
                
                # Handle empty queue
                if next_track is None:
                    logger.info(f"Queue is empty in guild {self.guild.id}, stopping playback")
                    self.is_playing = False
                    self.current_track = None
                    await self.channel.send("✅ Queue finished. Disconnecting in 5 minutes if no new tracks are added.")
                    # Schedule disconnect after 5 minutes of inactivity
                    await self.schedule_disconnect()
                    return
                
                self.current_track = next_track
                logger.info(f"Playing next track: {self.current_track.title} in guild {self.guild.id}")
            else:
                # Retrying the same track
                logger.info(f"Retrying track: {self.current_track.title} (attempt {retry_count + 1}/3)")
            
            # Check if we're connected to voice channel
            if not self.voice_client or not self.voice_client.is_connected():
                logger.error(f"Not connected to voice channel in guild {self.guild.id}")
                await self.channel.send("❌ Not connected to voice channel")
                self.is_playing = False
                return
            
            # Get audio source for the track
            try:
                audio_source = await self.audio_source_handler.get_audio_source(self.current_track)
            except Exception as e:
                logger.error(f"Failed to get audio source for track '{self.current_track.title}': {e}")
                await ErrorHandler.handle_source_error(self.ctx, e)
                # Skip to next track on source error
                self.current_track = None
                await self.play_next(retry_count=0)
                return
            
            # Apply volume transformation
            audio_source = discord.PCMVolumeTransformer(audio_source, volume=self.volume / 100)
            
            # Define callback for when track finishes
            def after_playing(error):
                if error:
                    logger.error(f"Error during playback in guild {self.guild.id}: {error}")
                    # Schedule retry with exponential backoff
                    coro = self._handle_playback_error(error, retry_count)
                    asyncio.run_coroutine_threadsafe(coro, self.bot.loop)
                else:
                    # Track finished successfully, play next
                    logger.info(f"Track finished successfully in guild {self.guild.id}")
                    coro = self.play_next(retry_count=0)
                    asyncio.run_coroutine_threadsafe(coro, self.bot.loop)
            
            # Start playback
            self.voice_client.play(audio_source, after=after_playing)
            self.is_playing = True
            self.is_paused = False
            
            # Send now playing message (only on first attempt, not retries)
            if retry_count == 0:
                embed = self.current_track.get_embed()
                embed.title = f"🎵 Now Playing: {self.current_track.title}"
                await self.channel.send(embed=embed)
            
            logger.info(f"Started playback of track: {self.current_track.title} in guild {self.guild.id}")
            
        except Exception as e:
            logger.error(f"Error in play_next for guild {self.guild.id}: {e}", exc_info=True)
            await ErrorHandler.handle_audio_error(self.ctx, e, retry_count)
            # Try to continue with next track
            self.current_track = None
            await self.play_next(retry_count=0)
    
    async def _handle_playback_error(self, error: Exception, retry_count: int):
        """
        Handle playback errors with retry logic.
        
        Args:
            error (Exception): The error that occurred during playback
            retry_count (int): Current retry attempt
        
        Validates Requirements: 6.4, 6.5, 8.4
        """
        logger.error(f"Playback error in guild {self.guild.id}: {error}", exc_info=True)
        
        # Check if we should retry
        should_retry = await ErrorHandler.handle_audio_error(self.ctx, error, retry_count)
        
        if should_retry:
            # Retry the same track
            await self.play_next(retry_count=retry_count + 1)
        else:
            # Max retries reached, skip to next track
            self.current_track = None
            await self.play_next(retry_count=0)
    
    async def schedule_disconnect(self):
        """
        Schedule automatic disconnect after 5 minutes of inactivity.
        
        Validates Requirements: 4.4
        """
        # Cancel existing timer if any
        if self.disconnect_timer:
            self.disconnect_timer.cancel()
        
        # Schedule disconnect after 5 minutes (300 seconds)
        async def disconnect_after_timeout():
            await asyncio.sleep(300)
            if not self.is_playing and self.queue.is_empty():
                logger.info(f"Disconnecting due to inactivity in guild {self.guild.id}")
                await self.channel.send("👋 Disconnecting due to inactivity")
                await self.disconnect()
        
        self.disconnect_timer = asyncio.create_task(disconnect_after_timeout())

    async def pause(self):
        """
        Pause the current track.

        Validates Requirements: 7.1
        """
        try:
            if not self.voice_client or not self.voice_client.is_connected():
                logger.warning(f"Cannot pause: not connected to voice channel in guild {self.guild.id}")
                await self.channel.send("❌ Not connected to voice channel")
                return

            if not self.is_playing:
                logger.warning(f"Cannot pause: nothing is playing in guild {self.guild.id}")
                await self.channel.send("❌ Nothing is currently playing")
                return

            if self.is_paused:
                logger.warning(f"Cannot pause: already paused in guild {self.guild.id}")
                await self.channel.send("❌ Playback is already paused")
                return

            if self.voice_client.is_playing():
                self.voice_client.pause()
                self.is_paused = True
                logger.info(f"Paused playback in guild {self.guild.id}")
                await self.channel.send("⏸️ Paused playback")

                # Schedule disconnect after 10 minutes of pause
                async def disconnect_after_pause():
                    await asyncio.sleep(600)  # 10 minutes
                    if self.is_paused:
                        logger.info(f"Disconnecting due to prolonged pause in guild {self.guild.id}")
                        await self.channel.send("👋 Disconnecting due to prolonged pause (10 minutes)")
                        await self.stop()
                        await self.disconnect()

                # Cancel existing timer and create new one
                if self.disconnect_timer:
                    self.disconnect_timer.cancel()
                self.disconnect_timer = asyncio.create_task(disconnect_after_pause())
            else:
                logger.warning(f"Cannot pause: voice client not playing in guild {self.guild.id}")
                await self.channel.send("❌ Nothing is currently playing")

        except Exception as e:
            logger.error(f"Error pausing playback in guild {self.guild.id}: {e}", exc_info=True)
            await self.channel.send(f"❌ Error pausing playback: {str(e)}")

    async def resume(self):
        """
        Resume playback from pause.

        Validates Requirements: 7.2
        """
        try:
            if not self.voice_client or not self.voice_client.is_connected():
                logger.warning(f"Cannot resume: not connected to voice channel in guild {self.guild.id}")
                await self.channel.send("❌ Not connected to voice channel")
                return

            if not self.is_paused:
                logger.warning(f"Cannot resume: playback is not paused in guild {self.guild.id}")
                await self.channel.send("❌ Playback is not paused")
                return

            if self.voice_client.is_paused():
                self.voice_client.resume()
                self.is_paused = False
                logger.info(f"Resumed playback in guild {self.guild.id}")
                await self.channel.send("▶️ Resumed playback")

                # Cancel pause disconnect timer
                if self.disconnect_timer:
                    self.disconnect_timer.cancel()
                    self.disconnect_timer = None
            else:
                logger.warning(f"Cannot resume: voice client not paused in guild {self.guild.id}")
                await self.channel.send("❌ Playback is not paused")

        except Exception as e:
            logger.error(f"Error resuming playback in guild {self.guild.id}: {e}", exc_info=True)
            await self.channel.send(f"❌ Error resuming playback: {str(e)}")

    async def skip(self):
        """
        Skip the current track and play the next one.

        Validates Requirements: 7.3
        """
        try:
            if not self.voice_client or not self.voice_client.is_connected():
                logger.warning(f"Cannot skip: not connected to voice channel in guild {self.guild.id}")
                await self.channel.send("❌ Not connected to voice channel")
                return

            if not self.is_playing and not self.is_paused:
                logger.warning(f"Cannot skip: nothing is playing in guild {self.guild.id}")
                await self.channel.send("❌ Nothing is currently playing")
                return

            logger.info(f"Skipping track in guild {self.guild.id}")

            # Stop current playback (this will trigger the after callback)
            if self.voice_client.is_playing() or self.voice_client.is_paused():
                self.voice_client.stop()

            # Reset pause state
            self.is_paused = False

            await self.channel.send("⏭️ Skipped track")

        except Exception as e:
            logger.error(f"Error skipping track in guild {self.guild.id}: {e}", exc_info=True)
            await self.channel.send(f"❌ Error skipping track: {str(e)}")

    async def stop(self):
        """
        Stop playback and clear the queue.

        Validates Requirements: 7.3
        """
        try:
            if not self.voice_client or not self.voice_client.is_connected():
                logger.warning(f"Cannot stop: not connected to voice channel in guild {self.guild.id}")
                await self.channel.send("❌ Not connected to voice channel")
                return

            logger.info(f"Stopping playback and clearing queue in guild {self.guild.id}")

            # Stop playback
            if self.voice_client.is_playing() or self.voice_client.is_paused():
                self.voice_client.stop()

            # Clear queue
            self.queue.clear()

            # Reset state
            self.current_track = None
            self.is_playing = False
            self.is_paused = False

            # Cancel disconnect timer if active
            if self.disconnect_timer:
                self.disconnect_timer.cancel()
                self.disconnect_timer = None

            await self.channel.send("⏹️ Stopped playback and cleared queue")

        except Exception as e:
            logger.error(f"Error stopping playback in guild {self.guild.id}: {e}", exc_info=True)
            await self.channel.send(f"❌ Error stopping playback: {str(e)}")

    async def set_volume(self, volume: int):
        """
        Set the playback volume.

        Args:
            volume (int): Volume level (0-100)

        Validates Requirements: 7.4
        """
        try:
            # Clamp volume to 0-100 range
            if volume < 0:
                volume = 0
                logger.info(f"Volume clamped to 0 in guild {self.guild.id}")
            elif volume > 100:
                volume = 100
                logger.info(f"Volume clamped to 100 in guild {self.guild.id}")

            self.volume = volume
            logger.info(f"Set volume to {volume} in guild {self.guild.id}")

            # Apply volume to current playback if active
            if self.voice_client and self.voice_client.source:
                if isinstance(self.voice_client.source, discord.PCMVolumeTransformer):
                    self.voice_client.source.volume = volume / 100
                    logger.info(f"Applied volume {volume} to current playback in guild {self.guild.id}")

            await self.channel.send(f"🔊 Volume set to {volume}%")

        except Exception as e:
            logger.error(f"Error setting volume in guild {self.guild.id}: {e}", exc_info=True)
            await self.channel.send(f"❌ Error setting volume: {str(e)}")
