"""
Unit tests for MusicCommands Cog

Tests command validation, player management, and command execution.
"""

import pytest
import discord
from discord.ext import commands
from unittest.mock import Mock, AsyncMock, MagicMock, patch
from music_commands import MusicCommands
from music_player import MusicPlayer
from track import Track


@pytest.fixture
def bot():
    """Create a mock bot instance."""
    bot = Mock(spec=commands.Bot)
    bot.music_players = {}
    return bot


@pytest.fixture
def cog(bot):
    """Create a MusicCommands cog instance."""
    return MusicCommands(bot)


@pytest.fixture
def ctx():
    """Create a mock command context."""
    ctx = Mock(spec=commands.Context)
    ctx.guild = Mock()
    ctx.guild.id = 12345
    ctx.author = Mock()
    ctx.channel = Mock()
    ctx.send = AsyncMock()
    return ctx


@pytest.fixture
def voice_channel():
    """Create a mock voice channel."""
    channel = Mock(spec=discord.VoiceChannel)
    channel.id = 67890
    return channel


class TestMusicCommandsInit:
    """Test MusicCommands initialization."""
    
    def test_init(self, bot):
        """Test that MusicCommands initializes correctly."""
        cog = MusicCommands(bot)
        assert cog.bot == bot
        assert cog.audio_source_handler is not None


class TestValidateVoiceChannel:
    """Test voice channel validation."""
    
    def test_validate_voice_channel_user_in_channel(self, cog, ctx, voice_channel):
        """Test validation when user is in voice channel."""
        ctx.author.voice = Mock()
        ctx.author.voice.channel = voice_channel
        
        result = cog._validate_voice_channel(ctx)
        assert result == voice_channel
    
    def test_validate_voice_channel_user_not_in_channel(self, cog, ctx):
        """Test validation when user is not in voice channel."""
        ctx.author.voice = None
        
        result = cog._validate_voice_channel(ctx)
        assert result is None


class TestGetOrCreatePlayer:
    """Test player retrieval and creation."""
    
    def test_get_existing_player(self, cog, ctx):
        """Test getting an existing player."""
        # Create a mock player
        mock_player = Mock(spec=MusicPlayer)
        cog.bot.music_players[ctx.guild.id] = mock_player
        
        result = cog._get_or_create_player(ctx)
        assert result == mock_player
    
    def test_create_new_player(self, cog, ctx):
        """Test creating a new player when none exists."""
        result = cog._get_or_create_player(ctx)
        
        assert ctx.guild.id in cog.bot.music_players
        assert isinstance(cog.bot.music_players[ctx.guild.id], MusicPlayer)


class TestPauseCommand:
    """Test pause command."""
    
    @pytest.mark.asyncio
    async def test_pause_no_voice_channel(self, cog, ctx):
        """Test pause when user is not in voice channel."""
        ctx.author.voice = None
        
        await cog.pause(ctx)
        
        # Should send error message
        ctx.send.assert_called_once()
        call_args = ctx.send.call_args[0][0]
        assert "❌" in call_args
    
    @pytest.mark.asyncio
    async def test_pause_no_player(self, cog, ctx, voice_channel):
        """Test pause when no player exists."""
        ctx.author.voice = Mock()
        ctx.author.voice.channel = voice_channel
        
        await cog.pause(ctx)
        
        # Should send error message
        ctx.send.assert_called_once()
        call_args = ctx.send.call_args[0][0]
        assert "❌" in call_args
    
    @pytest.mark.asyncio
    async def test_pause_success(self, cog, ctx, voice_channel):
        """Test successful pause."""
        ctx.author.voice = Mock()
        ctx.author.voice.channel = voice_channel
        
        # Create mock player
        mock_player = Mock(spec=MusicPlayer)
        mock_player.pause = AsyncMock()
        cog.bot.music_players[ctx.guild.id] = mock_player
        
        await cog.pause(ctx)
        
        # Should call player.pause()
        mock_player.pause.assert_called_once()


class TestResumeCommand:
    """Test resume command."""
    
    @pytest.mark.asyncio
    async def test_resume_no_voice_channel(self, cog, ctx):
        """Test resume when user is not in voice channel."""
        ctx.author.voice = None
        
        await cog.resume(ctx)
        
        # Should send error message
        ctx.send.assert_called_once()
        call_args = ctx.send.call_args[0][0]
        assert "❌" in call_args
    
    @pytest.mark.asyncio
    async def test_resume_success(self, cog, ctx, voice_channel):
        """Test successful resume."""
        ctx.author.voice = Mock()
        ctx.author.voice.channel = voice_channel
        
        # Create mock player
        mock_player = Mock(spec=MusicPlayer)
        mock_player.resume = AsyncMock()
        cog.bot.music_players[ctx.guild.id] = mock_player
        
        await cog.resume(ctx)
        
        # Should call player.resume()
        mock_player.resume.assert_called_once()


class TestSkipCommand:
    """Test skip command."""
    
    @pytest.mark.asyncio
    async def test_skip_success(self, cog, ctx, voice_channel):
        """Test successful skip."""
        ctx.author.voice = Mock()
        ctx.author.voice.channel = voice_channel
        
        # Create mock player
        mock_player = Mock(spec=MusicPlayer)
        mock_player.skip = AsyncMock()
        cog.bot.music_players[ctx.guild.id] = mock_player
        
        await cog.skip(ctx)
        
        # Should call player.skip()
        mock_player.skip.assert_called_once()


class TestStopCommand:
    """Test stop command."""
    
    @pytest.mark.asyncio
    async def test_stop_success(self, cog, ctx, voice_channel):
        """Test successful stop."""
        ctx.author.voice = Mock()
        ctx.author.voice.channel = voice_channel
        
        # Create mock player
        mock_player = Mock(spec=MusicPlayer)
        mock_player.stop = AsyncMock()
        cog.bot.music_players[ctx.guild.id] = mock_player
        
        await cog.stop(ctx)
        
        # Should call player.stop()
        mock_player.stop.assert_called_once()


class TestQueueCommand:
    """Test queue command."""
    
    @pytest.mark.asyncio
    async def test_queue_no_player(self, cog, ctx):
        """Test queue when no player exists."""
        await cog.queue(ctx)
        
        # Should send error message
        ctx.send.assert_called_once()
        call_args = ctx.send.call_args[0][0]
        assert "❌" in call_args
    
    @pytest.mark.asyncio
    async def test_queue_empty(self, cog, ctx):
        """Test queue when queue is empty."""
        # Create mock player with empty queue
        mock_player = Mock(spec=MusicPlayer)
        mock_player.queue = Mock()
        mock_player.queue.get_all = Mock(return_value=[])
        cog.bot.music_players[ctx.guild.id] = mock_player
        
        await cog.queue(ctx)
        
        # Should send empty queue message
        ctx.send.assert_called_once()
        call_args = ctx.send.call_args[0][0]
        assert "empty" in call_args.lower()
    
    @pytest.mark.asyncio
    async def test_queue_with_tracks(self, cog, ctx):
        """Test queue with tracks."""
        # Create mock tracks
        track1 = Track({'title': 'Track 1', 'url': 'http://example.com/1', 'duration': 180})
        track2 = Track({'title': 'Track 2', 'url': 'http://example.com/2', 'duration': 240})
        
        # Create mock player with tracks
        mock_player = Mock(spec=MusicPlayer)
        mock_player.queue = Mock()
        mock_player.queue.get_all = Mock(return_value=[track1, track2])
        cog.bot.music_players[ctx.guild.id] = mock_player
        
        await cog.queue(ctx)
        
        # Should send embed with queue
        ctx.send.assert_called_once()
        call_args = ctx.send.call_args
        assert 'embed' in call_args[1]


class TestNowPlayingCommand:
    """Test nowplaying command."""
    
    @pytest.mark.asyncio
    async def test_nowplaying_no_player(self, cog, ctx):
        """Test nowplaying when no player exists."""
        await cog.nowplaying(ctx)
        
        # Should send error message
        ctx.send.assert_called_once()
        call_args = ctx.send.call_args[0][0]
        assert "❌" in call_args
    
    @pytest.mark.asyncio
    async def test_nowplaying_no_track(self, cog, ctx):
        """Test nowplaying when no track is playing."""
        # Create mock player with no current track
        mock_player = Mock(spec=MusicPlayer)
        mock_player.current_track = None
        cog.bot.music_players[ctx.guild.id] = mock_player
        
        await cog.nowplaying(ctx)
        
        # Should send error message
        ctx.send.assert_called_once()
        call_args = ctx.send.call_args[0][0]
        assert "❌" in call_args
    
    @pytest.mark.asyncio
    async def test_nowplaying_with_track(self, cog, ctx):
        """Test nowplaying with active track."""
        # Create mock track
        track = Track({'title': 'Current Track', 'url': 'http://example.com/1', 'duration': 180})
        
        # Create mock player with current track
        mock_player = Mock(spec=MusicPlayer)
        mock_player.current_track = track
        mock_player.is_paused = False
        mock_player.volume = 50
        mock_player.queue = Mock()
        mock_player.queue.get_all = Mock(return_value=[])
        cog.bot.music_players[ctx.guild.id] = mock_player
        
        await cog.nowplaying(ctx)
        
        # Should send embed with track info
        ctx.send.assert_called_once()
        call_args = ctx.send.call_args
        assert 'embed' in call_args[1]


class TestVolumeCommand:
    """Test volume command."""
    
    @pytest.mark.asyncio
    async def test_volume_success(self, cog, ctx, voice_channel):
        """Test successful volume change."""
        ctx.author.voice = Mock()
        ctx.author.voice.channel = voice_channel
        
        # Create mock player
        mock_player = Mock(spec=MusicPlayer)
        mock_player.set_volume = AsyncMock()
        cog.bot.music_players[ctx.guild.id] = mock_player
        
        await cog.volume(ctx, 75)
        
        # Should call player.set_volume() with correct value
        mock_player.set_volume.assert_called_once_with(75)


class TestClearCommand:
    """Test clear command."""
    
    @pytest.mark.asyncio
    async def test_clear_empty_queue(self, cog, ctx, voice_channel):
        """Test clear when queue is already empty."""
        ctx.author.voice = Mock()
        ctx.author.voice.channel = voice_channel
        
        # Create mock player with empty queue
        mock_player = Mock(spec=MusicPlayer)
        mock_player.queue = Mock()
        mock_player.queue.get_all = Mock(return_value=[])
        cog.bot.music_players[ctx.guild.id] = mock_player
        
        await cog.clear(ctx)
        
        # Should send already empty message
        ctx.send.assert_called_once()
        call_args = ctx.send.call_args[0][0]
        assert "already empty" in call_args.lower()
    
    @pytest.mark.asyncio
    async def test_clear_success(self, cog, ctx, voice_channel):
        """Test successful clear."""
        ctx.author.voice = Mock()
        ctx.author.voice.channel = voice_channel
        
        # Create mock tracks
        track1 = Track({'title': 'Track 1', 'url': 'http://example.com/1', 'duration': 180})
        track2 = Track({'title': 'Track 2', 'url': 'http://example.com/2', 'duration': 240})
        
        # Create mock player with tracks
        mock_player = Mock(spec=MusicPlayer)
        mock_player.queue = Mock()
        mock_player.queue.get_all = Mock(return_value=[track1, track2])
        mock_player.queue.clear = Mock()
        cog.bot.music_players[ctx.guild.id] = mock_player
        
        await cog.clear(ctx)
        
        # Should call queue.clear()
        mock_player.queue.clear.assert_called_once()
        
        # Should send success message
        ctx.send.assert_called_once()
        call_args = ctx.send.call_args[0][0]
        assert "✅" in call_args


class TestHelpCommand:
    """Test help command."""
    
    @pytest.mark.asyncio
    async def test_help(self, cog, ctx):
        """Test help command displays all commands."""
        await cog.help(ctx)
        
        # Should send embed with help info
        ctx.send.assert_called_once()
        call_args = ctx.send.call_args
        assert 'embed' in call_args[1]
