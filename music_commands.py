"""
Music Commands module for Discord Music Bot

Implements all user-facing commands for music playback control.
"""

import logging
import discord
from discord import app_commands
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
    
    def _validate_voice_channel(self, interaction: discord.Interaction):
        """
        Validate that the user is in a voice channel.
        
        Args:
            interaction: Discord interaction
        
        Returns:
            discord.VoiceChannel or None: The voice channel if user is connected, None otherwise
        
        Validates Requirements: 4.2, 10.1-10.10
        """
        if not interaction.user.voice:
            return None
        return interaction.user.voice.channel
    
    def _get_or_create_player(self, interaction: discord.Interaction):
        """
        Get existing MusicPlayer for guild or create a new one.
        
        Args:
            interaction: Discord interaction
        
        Returns:
            MusicPlayer: The music player for this guild
        
        Validates Requirements: 4.1, 4.3
        """
        guild_id = interaction.guild.id
        
        if guild_id not in self.bot.music_players:
            logger.info(f"Creating new MusicPlayer for guild {guild_id}")
            # Create a fake context object for MusicPlayer
            class FakeContext:
                def __init__(self, interaction):
                    self.guild = interaction.guild
                    self.channel = interaction.channel
                    self.send = interaction.channel.send
            
            self.bot.music_players[guild_id] = MusicPlayer(FakeContext(interaction))
        
        return self.bot.music_players[guild_id]
    
    @app_commands.command(name='play', description='Включить музыку по названию или ссылке')
    @app_commands.describe(query='Название трека или URL (YouTube, SoundCloud)')
    async def play(self, interaction: discord.Interaction, query: str):
        """
        Play a track from search query or URL.
        
        Supports:
        - YouTube URLs (videos and playlists)
        - SoundCloud URLs
        - Direct audio file URLs
        - Search queries (searches YouTube)
        
        Args:
            interaction: Discord interaction
            query: Search query or URL
        
        Validates Requirements: 10.1, 1.1-1.5, 2.1-2.5, 4.1, 4.2
        """
        try:
            # Validate user is in voice channel
            voice_channel = self._validate_voice_channel(interaction)
            if not voice_channel:
                await interaction.response.send_message("❌ Ты должен быть в голосовом канале!", ephemeral=True)
                return
            
            # Defer response as this might take a while
            await interaction.response.defer()
            
            # Get or create music player
            player = self._get_or_create_player(interaction)
            
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
                        await interaction.followup.send(f"✅ Добавлено {len(result)} треков из плейлиста")
                        logger.info(f"Added {len(result)} tracks from playlist in guild {interaction.guild.id}")
                    else:
                        # Single track
                        player.queue.add(result)
                        embed = result.get_embed()
                        embed.title = f"✅ Добавлено в очередь: {result.title}"
                        await interaction.followup.send(embed=embed)
                        logger.info(f"Added track '{result.title}' to queue in guild {interaction.guild.id}")
                else:
                    # Search for tracks
                    logger.info(f"Searching for: {query}")
                    results = await self.audio_source_handler.search(query, max_results=1)
                    
                    if not results:
                        await interaction.followup.send("❌ Ничего не найдено")
                        return
                    
                    # Add first result to queue
                    track = results[0]
                    player.queue.add(track)
                    embed = track.get_embed()
                    embed.title = f"✅ Добавлено в очередь: {track.title}"
                    await interaction.followup.send(embed=embed)
                    logger.info(f"Added track '{track.title}' from search to queue in guild {interaction.guild.id}")
            
            except Exception as e:
                logger.error(f"Error processing query '{query}': {e}", exc_info=True)
                await interaction.followup.send(f"❌ Ошибка: {str(e)}")
                return
            
            # Connect to voice channel if not already connected
            if not player.voice_client or not player.voice_client.is_connected():
                await player.connect(voice_channel)
                logger.info(f"Connected to voice channel in guild {interaction.guild.id}")
            
            # Start playback if not already playing
            if not player.is_playing and not player.is_paused:
                await player.play_next()
                logger.info(f"Started playback in guild {interaction.guild.id}")
        
        except Exception as e:
            logger.error(f"Error in play command: {e}", exc_info=True)
            if not interaction.response.is_done():
                await interaction.response.send_message(f"❌ Произошла ошибка: {str(e)}", ephemeral=True)
            else:
                await interaction.followup.send(f"❌ Произошла ошибка: {str(e)}")
    
    @app_commands.command(name='pause', description='Поставить на паузу')
    async def pause(self, interaction: discord.Interaction):
        """
        Pause the current track.
        
        Args:
            interaction: Discord interaction
        
        Validates Requirements: 10.2, 7.1
        """
        try:
            # Validate user is in voice channel
            voice_channel = self._validate_voice_channel(interaction)
            if not voice_channel:
                await interaction.response.send_message("❌ Ты должен быть в голосовом канале!", ephemeral=True)
                return
            
            # Get player for this guild
            guild_id = interaction.guild.id
            if guild_id not in self.bot.music_players:
                await interaction.response.send_message("❌ Нет активного плеера", ephemeral=True)
                return
            
            player = self.bot.music_players[guild_id]
            await interaction.response.defer()
            await player.pause()
            await interaction.followup.send("⏸️ Пауза")
        
        except Exception as e:
            logger.error(f"Error in pause command: {e}", exc_info=True)
            if not interaction.response.is_done():
                await interaction.response.send_message(f"❌ Ошибка: {str(e)}", ephemeral=True)
    
    @app_commands.command(name='resume', description='Продолжить воспроизведение')
    async def resume(self, interaction: discord.Interaction):
        """
        Resume playback from pause.
        
        Args:
            interaction: Discord interaction
        
        Validates Requirements: 10.3, 7.2
        """
        try:
            # Validate user is in voice channel
            voice_channel = self._validate_voice_channel(interaction)
            if not voice_channel:
                await interaction.response.send_message("❌ Ты должен быть в голосовом канале!", ephemeral=True)
                return
            
            # Get player for this guild
            guild_id = interaction.guild.id
            if guild_id not in self.bot.music_players:
                await interaction.response.send_message("❌ Нет активного плеера", ephemeral=True)
                return
            
            player = self.bot.music_players[guild_id]
            await interaction.response.defer()
            await player.resume()
            await interaction.followup.send("▶️ Продолжаем")
        
        except Exception as e:
            logger.error(f"Error in resume command: {e}", exc_info=True)
            if not interaction.response.is_done():
                await interaction.response.send_message(f"❌ Ошибка: {str(e)}", ephemeral=True)
    
    @app_commands.command(name='skip', description='Пропустить трек')
    async def skip(self, interaction: discord.Interaction):
        """
        Skip the current track and play the next one.
        
        Args:
            interaction: Discord interaction
        
        Validates Requirements: 10.4, 7.3
        """
        try:
            # Validate user is in voice channel
            voice_channel = self._validate_voice_channel(interaction)
            if not voice_channel:
                await interaction.response.send_message("❌ Ты должен быть в голосовом канале!", ephemeral=True)
                return
            
            # Get player for this guild
            guild_id = interaction.guild.id
            if guild_id not in self.bot.music_players:
                await interaction.response.send_message("❌ Нет активного плеера", ephemeral=True)
                return
            
            player = self.bot.music_players[guild_id]
            await interaction.response.defer()
            await player.skip()
            await interaction.followup.send("⏭️ Пропущено")
        
        except Exception as e:
            logger.error(f"Error in skip command: {e}", exc_info=True)
            if not interaction.response.is_done():
                await interaction.response.send_message(f"❌ Ошибка: {str(e)}", ephemeral=True)
    
    @app_commands.command(name='stop', description='Остановить воспроизведение')
    async def stop(self, interaction: discord.Interaction):
        """
        Stop playback and clear the queue.
        
        Args:
            interaction: Discord interaction
        
        Validates Requirements: 10.5, 7.3
        """
        try:
            # Validate user is in voice channel
            voice_channel = self._validate_voice_channel(interaction)
            if not voice_channel:
                await interaction.response.send_message("❌ Ты должен быть в голосовом канале!", ephemeral=True)
                return
            
            # Get player for this guild
            guild_id = interaction.guild.id
            if guild_id not in self.bot.music_players:
                await interaction.response.send_message("❌ Нет активного плеера", ephemeral=True)
                return
            
            player = self.bot.music_players[guild_id]
            await interaction.response.defer()
            await player.stop()
            await interaction.followup.send("⏹️ Остановлено")
        
        except Exception as e:
            logger.error(f"Error in stop command: {e}", exc_info=True)
            if not interaction.response.is_done():
                await interaction.response.send_message(f"❌ Ошибка: {str(e)}", ephemeral=True)

    @app_commands.command(name='queue', description='Показать очередь треков')
    async def queue(self, interaction: discord.Interaction):
        """
        Display the current queue of tracks.
        
        Args:
            interaction: Discord interaction
        
        Validates Requirements: 10.6, 5.3, 3.2, 3.3
        """
        try:
            # Get player for this guild
            guild_id = interaction.guild.id
            if guild_id not in self.bot.music_players:
                await interaction.response.send_message("❌ Нет активного плеера", ephemeral=True)
                return
            
            player = self.bot.music_players[guild_id]
            
            # Get all tracks in queue
            queue_tracks = player.queue.get_all()
            
            if not queue_tracks:
                await interaction.response.send_message("📜 Очередь пуста", ephemeral=True)
                return
            
            # Build embed with queue information
            embed = discord.Embed(
                title="📜 Очередь треков",
                description=f"**{len(queue_tracks)} трек(ов) в очереди**",
                color=discord.Color.blue()
            )
            
            # Add up to 10 tracks to the embed
            for i, track in enumerate(queue_tracks[:10], 1):
                embed.add_field(
                    name=f"{i}. {track.title}",
                    value=f"Длительность: {track.format_duration()} | Автор: {track.uploader}",
                    inline=False
                )
            
            # Add note if there are more tracks
            if len(queue_tracks) > 10:
                embed.set_footer(text=f"... и ещё {len(queue_tracks) - 10} трек(ов)")
            
            await interaction.response.send_message(embed=embed)
            logger.info(f"Displayed queue with {len(queue_tracks)} tracks in guild {interaction.guild.id}")
        
        except Exception as e:
            logger.error(f"Error in queue command: {e}", exc_info=True)
            if not interaction.response.is_done():
                await interaction.response.send_message(f"❌ Ошибка: {str(e)}", ephemeral=True)
    
    @app_commands.command(name='nowplaying', description='Что сейчас играет')
    async def nowplaying(self, interaction: discord.Interaction):
        """
        Display information about the currently playing track.
        
        Args:
            interaction: Discord interaction
        
        Validates Requirements: 10.7, 3.2, 3.3
        """
        try:
            # Get player for this guild
            guild_id = interaction.guild.id
            if guild_id not in self.bot.music_players:
                await interaction.response.send_message("❌ Нет активного плеера", ephemeral=True)
                return
            
            player = self.bot.music_players[guild_id]
            
            # Check if there's a current track
            if not player.current_track:
                await interaction.response.send_message("❌ Ничего не играет", ephemeral=True)
                return
            
            # Get current track embed
            embed = player.current_track.get_embed()
            embed.title = f"🎵 Сейчас играет: {player.current_track.title}"
            embed.color = discord.Color.green()
            
            # Add playback status
            if player.is_paused:
                embed.add_field(name="Статус", value="⏸️ Пауза", inline=True)
            else:
                embed.add_field(name="Статус", value="▶️ Играет", inline=True)
            
            # Add volume
            embed.add_field(name="Громкость", value=f"🔊 {player.volume}%", inline=True)
            
            # Add queue info
            queue_size = len(player.queue.get_all())
            embed.add_field(name="Очередь", value=f"📜 {queue_size} трек(ов)", inline=True)
            
            await interaction.response.send_message(embed=embed)
            logger.info(f"Displayed now playing info in guild {interaction.guild.id}")
        
        except Exception as e:
            logger.error(f"Error in nowplaying command: {e}", exc_info=True)
            if not interaction.response.is_done():
                await interaction.response.send_message(f"❌ Ошибка: {str(e)}", ephemeral=True)
    
    @app_commands.command(name='volume', description='Установить громкость')
    @app_commands.describe(level='Уровень громкости (0-100)')
    async def volume(self, interaction: discord.Interaction, level: int):
        """
        Set the playback volume.
        
        Args:
            interaction: Discord interaction
            level: Volume level (0-100)
        
        Validates Requirements: 10.8, 7.4
        """
        try:
            # Validate user is in voice channel
            voice_channel = self._validate_voice_channel(interaction)
            if not voice_channel:
                await interaction.response.send_message("❌ Ты должен быть в голосовом канале!", ephemeral=True)
                return
            
            # Get player for this guild
            guild_id = interaction.guild.id
            if guild_id not in self.bot.music_players:
                await interaction.response.send_message("❌ Нет активного плеера", ephemeral=True)
                return
            
            player = self.bot.music_players[guild_id]
            await interaction.response.defer()
            await player.set_volume(level)
            await interaction.followup.send(f"🔊 Громкость установлена на {level}%")
        
        except Exception as e:
            logger.error(f"Error in volume command: {e}", exc_info=True)
            if not interaction.response.is_done():
                await interaction.response.send_message(f"❌ Ошибка: {str(e)}", ephemeral=True)
    
    @app_commands.command(name='clear', description='Очистить очередь')
    async def clear(self, interaction: discord.Interaction):
        """
        Clear all tracks from the queue except the currently playing track.
        
        Args:
            interaction: Discord interaction
        
        Validates Requirements: 10.9, 5.4
        """
        try:
            # Validate user is in voice channel
            voice_channel = self._validate_voice_channel(interaction)
            if not voice_channel:
                await interaction.response.send_message("❌ Ты должен быть в голосовом канале!", ephemeral=True)
                return
            
            # Get player for this guild
            guild_id = interaction.guild.id
            if guild_id not in self.bot.music_players:
                await interaction.response.send_message("❌ Нет активного плеера", ephemeral=True)
                return
            
            player = self.bot.music_players[guild_id]
            
            # Get queue size before clearing
            queue_size = len(player.queue.get_all())
            
            if queue_size == 0:
                await interaction.response.send_message("❌ Очередь уже пуста", ephemeral=True)
                return
            
            # Clear the queue
            player.queue.clear()
            
            await interaction.response.send_message(f"✅ Очищено {queue_size} трек(ов)")
            logger.info(f"Cleared {queue_size} tracks from queue in guild {interaction.guild.id}")
        
        except Exception as e:
            logger.error(f"Error in clear command: {e}", exc_info=True)
            if not interaction.response.is_done():
                await interaction.response.send_message(f"❌ Ошибка: {str(e)}", ephemeral=True)
    
    @app_commands.command(name='commands', description='Показать все команды')
    async def commands_list(self, interaction: discord.Interaction):
        """
        Display list of all available commands.
        
        Args:
            interaction: Discord interaction
        
        Validates Requirements: 10.10
        """
        try:
            embed = discord.Embed(
                title="🎵 Discord Music Bot - Команды",
                description="Список всех доступных команд",
                color=discord.Color.purple()
            )
            
            # Playback commands
            embed.add_field(
                name="▶️ Управление воспроизведением",
                value=(
                    "`/play <запрос или URL>` - Включить трек\n"
                    "`/pause` - Пауза\n"
                    "`/resume` - Продолжить\n"
                    "`/skip` - Пропустить трек\n"
                    "`/stop` - Остановить"
                ),
                inline=False
            )
            
            # Queue commands
            embed.add_field(
                name="📜 Управление очередью",
                value=(
                    "`/queue` - Показать очередь\n"
                    "`/clear` - Очистить очередь\n"
                    "`/nowplaying` - Что сейчас играет"
                ),
                inline=False
            )
            
            # Settings commands
            embed.add_field(
                name="⚙️ Настройки",
                value=(
                    "`/volume <0-100>` - Установить громкость\n"
                    "`/commands` - Показать команды"
                ),
                inline=False
            )
            
            # Additional info
            embed.set_footer(text="Поддержка YouTube, SoundCloud и прямых ссылок")
            
            await interaction.response.send_message(embed=embed)
            logger.info(f"Displayed help message in guild {interaction.guild.id}")
        
        except Exception as e:
            logger.error(f"Error in help command: {e}", exc_info=True)
            if not interaction.response.is_done():
                await interaction.response.send_message(f"❌ Ошибка: {str(e)}", ephemeral=True)


async def setup(bot):
    """
    Setup function to add the cog to the bot.
    
    Args:
        bot: The MusicBot instance
    """
    await bot.add_cog(MusicCommands(bot))
    logger.info("MusicCommands Cog loaded")
