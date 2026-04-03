"""
Unit tests for MusicPlayer class

Tests basic structure, initialization, connect, and disconnect functionality.
"""

import pytest
import asyncio
import discord
from unittest.mock import Mock, AsyncMock, MagicMock, patch
from music_player import MusicPlayer
from track_queue import TrackQueue


class TestMusicPlayerInitialization:
    """Test MusicPlayer initialization."""
    
    def test_init_creates_all_attributes(self):
        """Test that __init__ initializes all required attributes."""
        # Create mock context
        ctx = Mock()
        ctx.bot = Mock()
        ctx.guild = Mock()
        ctx.guild.id = 12345
        ctx.channel = Mock()
        
        # Create player
        player = MusicPlayer(ctx)
        
        # Verify all attributes are initialized
        assert player.bot == ctx.bot
        assert player.guild == ctx.guild
        assert player.channel == ctx.channel
        assert isinstance(player.queue, TrackQueue)
        assert player.current_track is None
        assert player.voice_client is None
        assert player.volume == 50
        assert player.is_playing is False
        assert player.is_paused is False
        assert player.disconnect_timer is None
    
    def test_init_default_volume_is_50(self):
        """Test that default volume is set to 50."""
        ctx = Mock()
        ctx.bot = Mock()
        ctx.guild = Mock()
        ctx.guild.id = 12345
        ctx.channel = Mock()
        
        player = MusicPlayer(ctx)
        
        assert player.volume == 50
    
    def test_init_creates_empty_queue(self):
        """Test that a new TrackQueue is created."""
        ctx = Mock()
        ctx.bot = Mock()
        ctx.guild = Mock()
        ctx.guild.id = 12345
        ctx.channel = Mock()
        
        player = MusicPlayer(ctx)
        
        assert isinstance(player.queue, TrackQueue)
        assert player.queue.is_empty()


class TestMusicPlayerConnect:
    """Test MusicPlayer connect functionality."""
    
    @pytest.mark.asyncio
    async def test_connect_to_voice_channel(self):
        """Test connecting to a voice channel."""
        # Create mock context
        ctx = Mock()
        ctx.bot = Mock()
        ctx.guild = Mock()
        ctx.guild.id = 12345
        ctx.channel = Mock()
        
        # Create mock voice channel
        voice_channel = AsyncMock()
        voice_channel.id = 67890
        mock_voice_client = Mock()
        voice_channel.connect = AsyncMock(return_value=mock_voice_client)
        
        # Create player
        player = MusicPlayer(ctx)
        
        # Connect to voice channel
        await player.connect(voice_channel)
        
        # Verify connection was established
        assert player.voice_client == mock_voice_client
        voice_channel.connect.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_connect_when_already_connected_to_same_channel(self):
        """Test connecting when already connected to the same channel."""
        ctx = Mock()
        ctx.bot = Mock()
        ctx.guild = Mock()
        ctx.guild.id = 12345
        ctx.channel = Mock()
        
        voice_channel = AsyncMock()
        voice_channel.id = 67890
        
        # Create player with existing voice client
        player = MusicPlayer(ctx)
        player.voice_client = Mock()
        player.voice_client.is_connected = Mock(return_value=True)
        player.voice_client.channel = voice_channel
        player.voice_client.move_to = AsyncMock()
        
        # Connect to same channel
        await player.connect(voice_channel)
        
        # Verify no move was attempted
        player.voice_client.move_to.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_connect_moves_to_different_channel(self):
        """Test moving to a different voice channel when already connected."""
        ctx = Mock()
        ctx.bot = Mock()
        ctx.guild = Mock()
        ctx.guild.id = 12345
        ctx.channel = Mock()
        
        old_channel = Mock()
        old_channel.id = 11111
        new_channel = AsyncMock()
        new_channel.id = 22222
        
        # Create player with existing voice client
        player = MusicPlayer(ctx)
        player.voice_client = Mock()
        player.voice_client.is_connected = Mock(return_value=True)
        player.voice_client.channel = old_channel
        player.voice_client.move_to = AsyncMock()
        
        # Connect to different channel
        await player.connect(new_channel)
        
        # Verify move was called
        player.voice_client.move_to.assert_called_once_with(new_channel)
    
    @pytest.mark.asyncio
    async def test_connect_raises_exception_on_failure(self):
        """Test that connect raises exception when connection fails."""
        ctx = Mock()
        ctx.bot = Mock()
        ctx.guild = Mock()
        ctx.guild.id = 12345
        ctx.channel = Mock()
        
        voice_channel = AsyncMock()
        voice_channel.id = 67890
        voice_channel.connect = AsyncMock(side_effect=Exception("Connection failed"))
        
        player = MusicPlayer(ctx)
        
        # Verify exception is raised
        with pytest.raises(Exception, match="Connection failed"):
            await player.connect(voice_channel)


class TestMusicPlayerDisconnect:
    """Test MusicPlayer disconnect functionality."""
    
    @pytest.mark.asyncio
    async def test_disconnect_from_voice_channel(self):
        """Test disconnecting from voice channel."""
        ctx = Mock()
        ctx.bot = Mock()
        ctx.guild = Mock()
        ctx.guild.id = 12345
        ctx.channel = Mock()
        
        # Create player with connected voice client
        player = MusicPlayer(ctx)
        mock_voice_client = Mock()
        mock_voice_client.is_connected = Mock(return_value=True)
        mock_voice_client.is_playing = Mock(return_value=False)
        mock_voice_client.disconnect = AsyncMock()
        player.voice_client = mock_voice_client
        
        # Disconnect
        await player.disconnect()
        
        # Verify disconnect was called
        mock_voice_client.disconnect.assert_called_once()
        
        # Verify state was reset
        assert player.voice_client is None
        assert player.current_track is None
        assert player.is_playing is False
        assert player.is_paused is False
    
    @pytest.mark.asyncio
    async def test_disconnect_stops_playback(self):
        """Test that disconnect stops active playback."""
        ctx = Mock()
        ctx.bot = Mock()
        ctx.guild = Mock()
        ctx.guild.id = 12345
        ctx.channel = Mock()
        
        # Create player with playing voice client
        player = MusicPlayer(ctx)
        mock_voice_client = Mock()
        mock_voice_client.is_connected = Mock(return_value=True)
        mock_voice_client.is_playing = Mock(return_value=True)
        mock_voice_client.stop = Mock()
        mock_voice_client.disconnect = AsyncMock()
        player.voice_client = mock_voice_client
        
        # Disconnect
        await player.disconnect()
        
        # Verify stop was called before disconnect
        mock_voice_client.stop.assert_called_once()
        mock_voice_client.disconnect.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_disconnect_cancels_timer(self):
        """Test that disconnect cancels the disconnect timer."""
        ctx = Mock()
        ctx.bot = Mock()
        ctx.guild = Mock()
        ctx.guild.id = 12345
        ctx.channel = Mock()
        
        # Create player with disconnect timer
        player = MusicPlayer(ctx)
        mock_timer = Mock()
        mock_timer.cancel = Mock()
        player.disconnect_timer = mock_timer
        
        mock_voice_client = Mock()
        mock_voice_client.is_connected = Mock(return_value=True)
        mock_voice_client.is_playing = Mock(return_value=False)
        mock_voice_client.disconnect = AsyncMock()
        player.voice_client = mock_voice_client
        
        # Disconnect
        await player.disconnect()
        
        # Verify timer was cancelled
        mock_timer.cancel.assert_called_once()
        assert player.disconnect_timer is None
    
    @pytest.mark.asyncio
    async def test_disconnect_when_not_connected(self):
        """Test disconnect when not connected (should not raise error)."""
        ctx = Mock()
        ctx.bot = Mock()
        ctx.guild = Mock()
        ctx.guild.id = 12345
        ctx.channel = Mock()
        
        # Create player without voice client
        player = MusicPlayer(ctx)
        player.voice_client = None
        
        # Disconnect should not raise error
        await player.disconnect()
        
        # Verify state is clean
        assert player.voice_client is None
        assert player.current_track is None
        assert player.is_playing is False
        assert player.is_paused is False
    
    @pytest.mark.asyncio
    async def test_disconnect_resets_state_on_error(self):
        """Test that state is reset even if disconnect fails."""
        ctx = Mock()
        ctx.bot = Mock()
        ctx.guild = Mock()
        ctx.guild.id = 12345
        ctx.channel = Mock()
        
        # Create player with voice client that fails to disconnect
        player = MusicPlayer(ctx)
        player.voice_client = Mock()
        player.voice_client.is_connected = Mock(return_value=True)
        player.voice_client.is_playing = Mock(return_value=False)
        player.voice_client.disconnect = AsyncMock(side_effect=Exception("Disconnect failed"))
        player.current_track = Mock()
        player.is_playing = True
        player.is_paused = True
        
        # Disconnect (should not raise exception)
        await player.disconnect()
        
        # Verify state was reset despite error
        assert player.voice_client is None
        assert player.current_track is None
        assert player.is_playing is False
        assert player.is_paused is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


class TestMusicPlayerPlayNext:
    """Test MusicPlayer play_next functionality."""
    
    @pytest.mark.asyncio
    async def test_play_next_with_track_in_queue(self):
        """Test playing next track when queue has tracks."""
        ctx = Mock()
        ctx.bot = Mock()
        ctx.bot.loop = asyncio.get_event_loop()
        ctx.guild = Mock()
        ctx.guild.id = 12345
        ctx.channel = AsyncMock()
        
        # Create player with connected voice client
        player = MusicPlayer(ctx)
        mock_voice_client = Mock()
        mock_voice_client.is_connected = Mock(return_value=True)
        mock_voice_client.play = Mock()
        player.voice_client = mock_voice_client
        
        # Add track to queue
        mock_track = Mock()
        mock_track.title = "Test Track"
        mock_track.url = "https://example.com/track"
        mock_track.get_embed = Mock(return_value=Mock(title="Test Track"))
        player.queue.add(mock_track)
        
        # Mock audio source handler and PCMVolumeTransformer
        with patch.object(player.audio_source_handler, 'get_audio_source', new_callable=AsyncMock) as mock_get_audio:
            with patch('music_player.discord.PCMVolumeTransformer') as mock_transformer:
                mock_audio_source = Mock()
                mock_get_audio.return_value = mock_audio_source
                mock_transformed = Mock()
                mock_transformer.return_value = mock_transformed
                
                # Play next track
                await player.play_next()
                
                # Verify track was retrieved and playback started
                assert player.current_track == mock_track
                assert player.is_playing is True
                assert player.is_paused is False
                mock_voice_client.play.assert_called_once()
                ctx.channel.send.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_play_next_with_empty_queue(self):
        """Test play_next when queue is empty."""
        ctx = Mock()
        ctx.bot = Mock()
        ctx.guild = Mock()
        ctx.guild.id = 12345
        ctx.channel = AsyncMock()
        
        # Create player with empty queue
        player = MusicPlayer(ctx)
        player.voice_client = Mock()
        player.voice_client.is_connected = Mock(return_value=True)
        
        # Mock schedule_disconnect
        player.schedule_disconnect = AsyncMock()
        
        # Play next (queue is empty)
        await player.play_next()
        
        # Verify playback stopped and disconnect scheduled
        assert player.is_playing is False
        assert player.current_track is None
        ctx.channel.send.assert_called_once()
        player.schedule_disconnect.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_play_next_not_connected(self):
        """Test play_next when not connected to voice channel."""
        ctx = Mock()
        ctx.bot = Mock()
        ctx.guild = Mock()
        ctx.guild.id = 12345
        ctx.channel = AsyncMock()
        
        # Create player without voice client
        player = MusicPlayer(ctx)
        player.voice_client = None
        
        # Add track to queue
        mock_track = Mock()
        player.queue.add(mock_track)
        
        # Play next
        await player.play_next()
        
        # Verify error message sent and playback not started
        assert player.is_playing is False
        ctx.channel.send.assert_called_once()
        assert "Not connected" in str(ctx.channel.send.call_args)
    
    @pytest.mark.asyncio
    async def test_play_next_source_error_skips_track(self):
        """Test that source errors cause track to be skipped."""
        ctx = Mock()
        ctx.bot = Mock()
        ctx.bot.loop = asyncio.get_event_loop()
        ctx.guild = Mock()
        ctx.guild.id = 12345
        ctx.channel = AsyncMock()
        
        # Create player
        player = MusicPlayer(ctx)
        mock_voice_client = Mock()
        mock_voice_client.is_connected = Mock(return_value=True)
        mock_voice_client.play = Mock()
        player.voice_client = mock_voice_client
        
        # Add two tracks to queue
        mock_track1 = Mock()
        mock_track1.title = "Bad Track"
        mock_track2 = Mock()
        mock_track2.title = "Good Track"
        mock_track2.get_embed = Mock(return_value=Mock(title="Good Track"))
        player.queue.add(mock_track1)
        player.queue.add(mock_track2)
        
        # Mock audio source handler - first fails, second succeeds
        call_count = 0
        async def mock_get_audio(track):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("Source unavailable")
            return Mock()
        
        with patch.object(player.audio_source_handler, 'get_audio_source', side_effect=mock_get_audio):
            with patch('music_player.discord.PCMVolumeTransformer') as mock_transformer:
                mock_transformer.return_value = Mock()
                
                # Play next - should skip bad track and play good track
                await player.play_next()
                
                # Verify bad track was skipped and good track is playing
                assert player.current_track == mock_track2
                assert call_count == 2
                mock_voice_client.play.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_play_next_retry_on_max_retries(self):
        """Test that max retries causes track to be skipped."""
        ctx = Mock()
        ctx.bot = Mock()
        ctx.bot.loop = asyncio.get_event_loop()
        ctx.guild = Mock()
        ctx.guild.id = 12345
        ctx.channel = AsyncMock()
        
        # Create player
        player = MusicPlayer(ctx)
        player.voice_client = Mock()
        player.voice_client.is_connected = Mock(return_value=True)
        
        # Add track to queue
        mock_track = Mock()
        mock_track.title = "Test Track"
        player.queue.add(mock_track)
        player.current_track = mock_track
        
        # Mock schedule_disconnect for empty queue after skip
        player.schedule_disconnect = AsyncMock()
        
        # Call with retry_count = 3 (max retries reached)
        await player.play_next(retry_count=3)
        
        # Verify track was skipped (current_track reset and play_next called recursively)
        ctx.channel.send.assert_called()
    
    @pytest.mark.asyncio
    async def test_play_next_retry_same_track(self):
        """Test that retry attempts use the same track."""
        ctx = Mock()
        ctx.bot = Mock()
        ctx.bot.loop = asyncio.get_event_loop()
        ctx.guild = Mock()
        ctx.guild.id = 12345
        ctx.channel = AsyncMock()
        
        # Create player
        player = MusicPlayer(ctx)
        mock_voice_client = Mock()
        mock_voice_client.is_connected = Mock(return_value=True)
        mock_voice_client.play = Mock()
        player.voice_client = mock_voice_client
        
        # Set current track (simulating retry scenario)
        mock_track = Mock()
        mock_track.title = "Test Track"
        mock_track.get_embed = Mock(return_value=Mock(title="Test Track"))
        player.current_track = mock_track
        
        # Mock audio source handler and PCMVolumeTransformer
        with patch.object(player.audio_source_handler, 'get_audio_source', new_callable=AsyncMock) as mock_get_audio:
            with patch('music_player.discord.PCMVolumeTransformer') as mock_transformer:
                mock_audio_source = Mock()
                mock_get_audio.return_value = mock_audio_source
                mock_transformed = Mock()
                mock_transformer.return_value = mock_transformed
                
                # Play next with retry_count = 1
                await player.play_next(retry_count=1)
                
                # Verify same track is used (not fetched from queue)
                assert player.current_track == mock_track
                mock_voice_client.play.assert_called_once()
                # Should not send "now playing" message on retry
                ctx.channel.send.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_play_next_applies_volume(self):
        """Test that volume is applied to audio source."""
        ctx = Mock()
        ctx.bot = Mock()
        ctx.bot.loop = asyncio.get_event_loop()
        ctx.guild = Mock()
        ctx.guild.id = 12345
        ctx.channel = AsyncMock()
        
        # Create player with custom volume
        player = MusicPlayer(ctx)
        player.volume = 75
        mock_voice_client = Mock()
        mock_voice_client.is_connected = Mock(return_value=True)
        mock_voice_client.play = Mock()
        player.voice_client = mock_voice_client
        
        # Add track to queue
        mock_track = Mock()
        mock_track.title = "Test Track"
        mock_track.get_embed = Mock(return_value=Mock(title="Test Track"))
        player.queue.add(mock_track)
        
        # Mock audio source handler
        with patch.object(player.audio_source_handler, 'get_audio_source', new_callable=AsyncMock) as mock_get_audio:
            mock_audio_source = Mock()
            mock_get_audio.return_value = mock_audio_source
            
            with patch('music_player.discord.PCMVolumeTransformer') as mock_transformer:
                # Play next track
                await player.play_next()
                
                # Verify volume transformer was created with correct volume
                mock_transformer.assert_called_once()
                args = mock_transformer.call_args
                assert args[1]['volume'] == 0.75  # 75 / 100


class TestMusicPlayerScheduleDisconnect:
    """Test MusicPlayer schedule_disconnect functionality."""
    
    @pytest.mark.asyncio
    async def test_schedule_disconnect_creates_timer(self):
        """Test that schedule_disconnect creates a timer task."""
        ctx = Mock()
        ctx.bot = Mock()
        ctx.guild = Mock()
        ctx.guild.id = 12345
        ctx.channel = AsyncMock()
        
        player = MusicPlayer(ctx)
        
        # Schedule disconnect
        await player.schedule_disconnect()
        
        # Verify timer was created
        assert player.disconnect_timer is not None
        assert isinstance(player.disconnect_timer, asyncio.Task)
        
        # Cancel timer to clean up
        player.disconnect_timer.cancel()
    
    @pytest.mark.asyncio
    async def test_schedule_disconnect_cancels_existing_timer(self):
        """Test that scheduling disconnect cancels existing timer."""
        ctx = Mock()
        ctx.bot = Mock()
        ctx.guild = Mock()
        ctx.guild.id = 12345
        ctx.channel = AsyncMock()
        
        player = MusicPlayer(ctx)
        
        # Create first timer
        await player.schedule_disconnect()
        first_timer = player.disconnect_timer
        
        # Create second timer
        await player.schedule_disconnect()
        second_timer = player.disconnect_timer
        
        # Give a moment for cancellation to process
        await asyncio.sleep(0.01)
        
        # Verify first timer was cancelled and new timer created
        assert first_timer.cancelled()
        assert second_timer is not first_timer
        assert not second_timer.cancelled()
        
        # Clean up
        second_timer.cancel()


class TestMusicPlayerPause:
    """Test MusicPlayer pause functionality."""
    
    @pytest.mark.asyncio
    async def test_pause_playing_track(self):
        """Test pausing a playing track."""
        ctx = Mock()
        ctx.bot = Mock()
        ctx.guild = Mock()
        ctx.guild.id = 12345
        ctx.channel = AsyncMock()
        
        # Create player with playing voice client
        player = MusicPlayer(ctx)
        mock_voice_client = Mock()
        mock_voice_client.is_connected = Mock(return_value=True)
        mock_voice_client.is_playing = Mock(return_value=True)
        mock_voice_client.pause = Mock()
        player.voice_client = mock_voice_client
        player.is_playing = True
        player.is_paused = False
        
        # Pause playback
        await player.pause()
        
        # Verify pause was called and state updated
        mock_voice_client.pause.assert_called_once()
        assert player.is_paused is True
        ctx.channel.send.assert_called_once()
        assert "Paused" in str(ctx.channel.send.call_args)
    
    @pytest.mark.asyncio
    async def test_pause_not_connected(self):
        """Test pause when not connected to voice channel."""
        ctx = Mock()
        ctx.bot = Mock()
        ctx.guild = Mock()
        ctx.guild.id = 12345
        ctx.channel = AsyncMock()
        
        player = MusicPlayer(ctx)
        player.voice_client = None
        
        # Attempt to pause
        await player.pause()
        
        # Verify error message sent
        ctx.channel.send.assert_called_once()
        assert "Not connected" in str(ctx.channel.send.call_args)
    
    @pytest.mark.asyncio
    async def test_pause_nothing_playing(self):
        """Test pause when nothing is playing."""
        ctx = Mock()
        ctx.bot = Mock()
        ctx.guild = Mock()
        ctx.guild.id = 12345
        ctx.channel = AsyncMock()
        
        player = MusicPlayer(ctx)
        mock_voice_client = Mock()
        mock_voice_client.is_connected = Mock(return_value=True)
        player.voice_client = mock_voice_client
        player.is_playing = False
        
        # Attempt to pause
        await player.pause()
        
        # Verify error message sent
        ctx.channel.send.assert_called_once()
        assert "Nothing is currently playing" in str(ctx.channel.send.call_args)
    
    @pytest.mark.asyncio
    async def test_pause_already_paused(self):
        """Test pause when already paused."""
        ctx = Mock()
        ctx.bot = Mock()
        ctx.guild = Mock()
        ctx.guild.id = 12345
        ctx.channel = AsyncMock()
        
        player = MusicPlayer(ctx)
        mock_voice_client = Mock()
        mock_voice_client.is_connected = Mock(return_value=True)
        player.voice_client = mock_voice_client
        player.is_playing = True
        player.is_paused = True
        
        # Attempt to pause
        await player.pause()
        
        # Verify error message sent
        ctx.channel.send.assert_called_once()
        assert "already paused" in str(ctx.channel.send.call_args)
    
    @pytest.mark.asyncio
    async def test_pause_schedules_disconnect_timer(self):
        """Test that pause schedules disconnect after 10 minutes."""
        ctx = Mock()
        ctx.bot = Mock()
        ctx.guild = Mock()
        ctx.guild.id = 12345
        ctx.channel = AsyncMock()
        
        player = MusicPlayer(ctx)
        mock_voice_client = Mock()
        mock_voice_client.is_connected = Mock(return_value=True)
        mock_voice_client.is_playing = Mock(return_value=True)
        mock_voice_client.pause = Mock()
        player.voice_client = mock_voice_client
        player.is_playing = True
        player.is_paused = False
        
        # Pause playback
        await player.pause()
        
        # Verify disconnect timer was created
        assert player.disconnect_timer is not None
        assert isinstance(player.disconnect_timer, asyncio.Task)
        
        # Clean up
        player.disconnect_timer.cancel()


class TestMusicPlayerResume:
    """Test MusicPlayer resume functionality."""
    
    @pytest.mark.asyncio
    async def test_resume_paused_track(self):
        """Test resuming a paused track."""
        ctx = Mock()
        ctx.bot = Mock()
        ctx.guild = Mock()
        ctx.guild.id = 12345
        ctx.channel = AsyncMock()
        
        # Create player with paused voice client
        player = MusicPlayer(ctx)
        mock_voice_client = Mock()
        mock_voice_client.is_connected = Mock(return_value=True)
        mock_voice_client.is_paused = Mock(return_value=True)
        mock_voice_client.resume = Mock()
        player.voice_client = mock_voice_client
        player.is_paused = True
        
        # Resume playback
        await player.resume()
        
        # Verify resume was called and state updated
        mock_voice_client.resume.assert_called_once()
        assert player.is_paused is False
        ctx.channel.send.assert_called_once()
        assert "Resumed" in str(ctx.channel.send.call_args)
    
    @pytest.mark.asyncio
    async def test_resume_not_connected(self):
        """Test resume when not connected to voice channel."""
        ctx = Mock()
        ctx.bot = Mock()
        ctx.guild = Mock()
        ctx.guild.id = 12345
        ctx.channel = AsyncMock()
        
        player = MusicPlayer(ctx)
        player.voice_client = None
        
        # Attempt to resume
        await player.resume()
        
        # Verify error message sent
        ctx.channel.send.assert_called_once()
        assert "Not connected" in str(ctx.channel.send.call_args)
    
    @pytest.mark.asyncio
    async def test_resume_not_paused(self):
        """Test resume when not paused."""
        ctx = Mock()
        ctx.bot = Mock()
        ctx.guild = Mock()
        ctx.guild.id = 12345
        ctx.channel = AsyncMock()
        
        player = MusicPlayer(ctx)
        mock_voice_client = Mock()
        mock_voice_client.is_connected = Mock(return_value=True)
        player.voice_client = mock_voice_client
        player.is_paused = False
        
        # Attempt to resume
        await player.resume()
        
        # Verify error message sent
        ctx.channel.send.assert_called_once()
        assert "not paused" in str(ctx.channel.send.call_args)
    
    @pytest.mark.asyncio
    async def test_resume_cancels_disconnect_timer(self):
        """Test that resume cancels the pause disconnect timer."""
        ctx = Mock()
        ctx.bot = Mock()
        ctx.guild = Mock()
        ctx.guild.id = 12345
        ctx.channel = AsyncMock()
        
        player = MusicPlayer(ctx)
        mock_voice_client = Mock()
        mock_voice_client.is_connected = Mock(return_value=True)
        mock_voice_client.is_paused = Mock(return_value=True)
        mock_voice_client.resume = Mock()
        player.voice_client = mock_voice_client
        player.is_paused = True
        
        # Create a mock timer
        mock_timer = Mock()
        mock_timer.cancel = Mock()
        player.disconnect_timer = mock_timer
        
        # Resume playback
        await player.resume()
        
        # Verify timer was cancelled
        mock_timer.cancel.assert_called_once()
        assert player.disconnect_timer is None


class TestMusicPlayerSkip:
    """Test MusicPlayer skip functionality."""
    
    @pytest.mark.asyncio
    async def test_skip_playing_track(self):
        """Test skipping a playing track."""
        ctx = Mock()
        ctx.bot = Mock()
        ctx.guild = Mock()
        ctx.guild.id = 12345
        ctx.channel = AsyncMock()
        
        # Create player with playing voice client
        player = MusicPlayer(ctx)
        mock_voice_client = Mock()
        mock_voice_client.is_connected = Mock(return_value=True)
        mock_voice_client.is_playing = Mock(return_value=True)
        mock_voice_client.is_paused = Mock(return_value=False)
        mock_voice_client.stop = Mock()
        player.voice_client = mock_voice_client
        player.is_playing = True
        player.is_paused = False
        
        # Skip track
        await player.skip()
        
        # Verify stop was called
        mock_voice_client.stop.assert_called_once()
        assert player.is_paused is False
        ctx.channel.send.assert_called_once()
        assert "Skipped" in str(ctx.channel.send.call_args)
    
    @pytest.mark.asyncio
    async def test_skip_paused_track(self):
        """Test skipping a paused track."""
        ctx = Mock()
        ctx.bot = Mock()
        ctx.guild = Mock()
        ctx.guild.id = 12345
        ctx.channel = AsyncMock()
        
        # Create player with paused voice client
        player = MusicPlayer(ctx)
        mock_voice_client = Mock()
        mock_voice_client.is_connected = Mock(return_value=True)
        mock_voice_client.is_playing = Mock(return_value=False)
        mock_voice_client.is_paused = Mock(return_value=True)
        mock_voice_client.stop = Mock()
        player.voice_client = mock_voice_client
        player.is_playing = True
        player.is_paused = True
        
        # Skip track
        await player.skip()
        
        # Verify stop was called and pause state reset
        mock_voice_client.stop.assert_called_once()
        assert player.is_paused is False
    
    @pytest.mark.asyncio
    async def test_skip_not_connected(self):
        """Test skip when not connected to voice channel."""
        ctx = Mock()
        ctx.bot = Mock()
        ctx.guild = Mock()
        ctx.guild.id = 12345
        ctx.channel = AsyncMock()
        
        player = MusicPlayer(ctx)
        player.voice_client = None
        
        # Attempt to skip
        await player.skip()
        
        # Verify error message sent
        ctx.channel.send.assert_called_once()
        assert "Not connected" in str(ctx.channel.send.call_args)
    
    @pytest.mark.asyncio
    async def test_skip_nothing_playing(self):
        """Test skip when nothing is playing."""
        ctx = Mock()
        ctx.bot = Mock()
        ctx.guild = Mock()
        ctx.guild.id = 12345
        ctx.channel = AsyncMock()
        
        player = MusicPlayer(ctx)
        mock_voice_client = Mock()
        mock_voice_client.is_connected = Mock(return_value=True)
        player.voice_client = mock_voice_client
        player.is_playing = False
        player.is_paused = False
        
        # Attempt to skip
        await player.skip()
        
        # Verify error message sent
        ctx.channel.send.assert_called_once()
        assert "Nothing is currently playing" in str(ctx.channel.send.call_args)


class TestMusicPlayerStop:
    """Test MusicPlayer stop functionality."""
    
    @pytest.mark.asyncio
    async def test_stop_playing_track(self):
        """Test stopping playback and clearing queue."""
        ctx = Mock()
        ctx.bot = Mock()
        ctx.guild = Mock()
        ctx.guild.id = 12345
        ctx.channel = AsyncMock()
        
        # Create player with playing voice client and tracks in queue
        player = MusicPlayer(ctx)
        mock_voice_client = Mock()
        mock_voice_client.is_connected = Mock(return_value=True)
        mock_voice_client.is_playing = Mock(return_value=True)
        mock_voice_client.is_paused = Mock(return_value=False)
        mock_voice_client.stop = Mock()
        player.voice_client = mock_voice_client
        player.is_playing = True
        player.current_track = Mock()
        
        # Add tracks to queue
        player.queue.add(Mock())
        player.queue.add(Mock())
        
        # Stop playback
        await player.stop()
        
        # Verify stop was called and state reset
        mock_voice_client.stop.assert_called_once()
        assert player.current_track is None
        assert player.is_playing is False
        assert player.is_paused is False
        ctx.channel.send.assert_called_once()
        assert "Stopped" in str(ctx.channel.send.call_args)
    
    @pytest.mark.asyncio
    async def test_stop_clears_queue(self):
        """Test that stop clears the queue."""
        ctx = Mock()
        ctx.bot = Mock()
        ctx.guild = Mock()
        ctx.guild.id = 12345
        ctx.channel = AsyncMock()
        
        player = MusicPlayer(ctx)
        mock_voice_client = Mock()
        mock_voice_client.is_connected = Mock(return_value=True)
        mock_voice_client.is_playing = Mock(return_value=True)
        mock_voice_client.is_paused = Mock(return_value=False)
        mock_voice_client.stop = Mock()
        player.voice_client = mock_voice_client
        player.is_playing = True
        
        # Add tracks to queue
        player.queue.add(Mock())
        player.queue.add(Mock())
        player.queue.add(Mock())
        
        # Stop playback
        await player.stop()
        
        # Verify queue is empty (only current track preserved by clear())
        assert len(player.queue.get_all()) == 0
    
    @pytest.mark.asyncio
    async def test_stop_not_connected(self):
        """Test stop when not connected to voice channel."""
        ctx = Mock()
        ctx.bot = Mock()
        ctx.guild = Mock()
        ctx.guild.id = 12345
        ctx.channel = AsyncMock()
        
        player = MusicPlayer(ctx)
        player.voice_client = None
        
        # Attempt to stop
        await player.stop()
        
        # Verify error message sent
        ctx.channel.send.assert_called_once()
        assert "Not connected" in str(ctx.channel.send.call_args)
    
    @pytest.mark.asyncio
    async def test_stop_cancels_disconnect_timer(self):
        """Test that stop cancels the disconnect timer."""
        ctx = Mock()
        ctx.bot = Mock()
        ctx.guild = Mock()
        ctx.guild.id = 12345
        ctx.channel = AsyncMock()
        
        player = MusicPlayer(ctx)
        mock_voice_client = Mock()
        mock_voice_client.is_connected = Mock(return_value=True)
        mock_voice_client.is_playing = Mock(return_value=True)
        mock_voice_client.is_paused = Mock(return_value=False)
        mock_voice_client.stop = Mock()
        player.voice_client = mock_voice_client
        player.is_playing = True
        
        # Create a mock timer
        mock_timer = Mock()
        mock_timer.cancel = Mock()
        player.disconnect_timer = mock_timer
        
        # Stop playback
        await player.stop()
        
        # Verify timer was cancelled
        mock_timer.cancel.assert_called_once()
        assert player.disconnect_timer is None


class TestMusicPlayerSetVolume:
    """Test MusicPlayer set_volume functionality."""
    
    @pytest.mark.asyncio
    async def test_set_volume_valid_range(self):
        """Test setting volume within valid range (0-100)."""
        ctx = Mock()
        ctx.bot = Mock()
        ctx.guild = Mock()
        ctx.guild.id = 12345
        ctx.channel = AsyncMock()
        
        player = MusicPlayer(ctx)
        
        # Set volume to 75
        await player.set_volume(75)
        
        # Verify volume was set
        assert player.volume == 75
        ctx.channel.send.assert_called_once()
        assert "75" in str(ctx.channel.send.call_args)
    
    @pytest.mark.asyncio
    async def test_set_volume_clamps_below_zero(self):
        """Test that volume below 0 is clamped to 0."""
        ctx = Mock()
        ctx.bot = Mock()
        ctx.guild = Mock()
        ctx.guild.id = 12345
        ctx.channel = AsyncMock()
        
        player = MusicPlayer(ctx)
        
        # Set volume to -10
        await player.set_volume(-10)
        
        # Verify volume was clamped to 0
        assert player.volume == 0
        ctx.channel.send.assert_called_once()
        assert "0" in str(ctx.channel.send.call_args)
    
    @pytest.mark.asyncio
    async def test_set_volume_clamps_above_100(self):
        """Test that volume above 100 is clamped to 100."""
        ctx = Mock()
        ctx.bot = Mock()
        ctx.guild = Mock()
        ctx.guild.id = 12345
        ctx.channel = AsyncMock()
        
        player = MusicPlayer(ctx)
        
        # Set volume to 150
        await player.set_volume(150)
        
        # Verify volume was clamped to 100
        assert player.volume == 100
        ctx.channel.send.assert_called_once()
        assert "100" in str(ctx.channel.send.call_args)
    
    @pytest.mark.asyncio
    async def test_set_volume_applies_to_current_playback(self):
        """Test that volume is applied to current playback."""
        ctx = Mock()
        ctx.bot = Mock()
        ctx.guild = Mock()
        ctx.guild.id = 12345
        ctx.channel = AsyncMock()
        
        # Create player with active playback
        player = MusicPlayer(ctx)
        mock_source = Mock(spec=discord.PCMVolumeTransformer)
        mock_source.volume = 0.5
        mock_voice_client = Mock()
        mock_voice_client.source = mock_source
        player.voice_client = mock_voice_client
        
        # Set volume to 80
        await player.set_volume(80)
        
        # Verify volume was applied to source
        assert player.volume == 80
        assert mock_source.volume == 0.8
    
    @pytest.mark.asyncio
    async def test_set_volume_boundary_values(self):
        """Test setting volume to boundary values 0 and 100."""
        ctx = Mock()
        ctx.bot = Mock()
        ctx.guild = Mock()
        ctx.guild.id = 12345
        ctx.channel = AsyncMock()
        
        player = MusicPlayer(ctx)
        
        # Test volume 0
        await player.set_volume(0)
        assert player.volume == 0
        
        # Test volume 100
        await player.set_volume(100)
        assert player.volume == 100
