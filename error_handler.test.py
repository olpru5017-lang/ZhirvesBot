"""
Unit tests for ErrorHandler class

Tests error handling, retry logic with exponential backoff, and error messages.
"""

import unittest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from error_handler import ErrorHandler


class TestErrorHandler(unittest.TestCase):
    """Test cases for ErrorHandler class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create mock context
        self.ctx = MagicMock()
        self.ctx.send = AsyncMock()
        self.ctx.guild = MagicMock()
        self.ctx.guild.id = 12345
    
    def test_handle_user_error_sends_message(self):
        """Test handle_user_error sends formatted error message."""
        async def run_test():
            await ErrorHandler.handle_user_error(self.ctx, "You must be in a voice channel")
            
            # Verify message was sent with correct format
            self.ctx.send.assert_called_once_with("❌ You must be in a voice channel")
        
        asyncio.run(run_test())
    
    def test_handle_user_error_with_different_messages(self):
        """Test handle_user_error with various error messages."""
        async def run_test():
            messages = [
                "Invalid volume level",
                "Queue is empty",
                "Not connected to voice channel"
            ]
            
            for message in messages:
                self.ctx.send.reset_mock()
                await ErrorHandler.handle_user_error(self.ctx, message)
                self.ctx.send.assert_called_once_with(f"❌ {message}")
        
        asyncio.run(run_test())
    
    def test_handle_network_error_retry_on_first_attempt(self):
        """Test handle_network_error returns True to retry on first attempt."""
        async def run_test():
            error = Exception("Connection timeout")
            
            # First attempt (retry_count=0) should return True
            result = await ErrorHandler.handle_network_error(self.ctx, error, retry_count=0)
            
            self.assertTrue(result)
            # Should not send error message yet
            self.ctx.send.assert_not_called()
        
        asyncio.run(run_test())
    
    def test_handle_network_error_retry_on_second_attempt(self):
        """Test handle_network_error returns True to retry on second attempt."""
        async def run_test():
            error = Exception("Connection timeout")
            
            # Second attempt (retry_count=1) should return True
            result = await ErrorHandler.handle_network_error(self.ctx, error, retry_count=1)
            
            self.assertTrue(result)
            # Should not send error message yet
            self.ctx.send.assert_not_called()
        
        asyncio.run(run_test())
    
    def test_handle_network_error_retry_on_third_attempt(self):
        """Test handle_network_error returns True to retry on third attempt."""
        async def run_test():
            error = Exception("Connection timeout")
            
            # Third attempt (retry_count=2) should return True
            result = await ErrorHandler.handle_network_error(self.ctx, error, retry_count=2)
            
            self.assertTrue(result)
            # Should not send error message yet
            self.ctx.send.assert_not_called()
        
        asyncio.run(run_test())
    
    def test_handle_network_error_max_retries_reached(self):
        """Test handle_network_error returns False after 3 attempts."""
        async def run_test():
            error = Exception("Connection timeout")
            
            # Fourth attempt (retry_count=3) should return False
            result = await ErrorHandler.handle_network_error(self.ctx, error, retry_count=3)
            
            self.assertFalse(result)
            # Should send error message
            self.ctx.send.assert_called_once_with(
                "❌ Network error: Unable to connect after 3 attempts"
            )
        
        asyncio.run(run_test())
    
    def test_handle_network_error_exponential_backoff_timing(self):
        """Test handle_network_error uses exponential backoff delays."""
        async def run_test():
            error = Exception("Connection timeout")
            
            # Test delay for retry_count=0 (should be 2^0 = 1 second)
            start_time = asyncio.get_event_loop().time()
            await ErrorHandler.handle_network_error(self.ctx, error, retry_count=0)
            elapsed = asyncio.get_event_loop().time() - start_time
            self.assertGreaterEqual(elapsed, 1.0)
            self.assertLess(elapsed, 1.5)
            
            # Test delay for retry_count=1 (should be 2^1 = 2 seconds)
            start_time = asyncio.get_event_loop().time()
            await ErrorHandler.handle_network_error(self.ctx, error, retry_count=1)
            elapsed = asyncio.get_event_loop().time() - start_time
            self.assertGreaterEqual(elapsed, 2.0)
            self.assertLess(elapsed, 2.5)
            
            # Test delay for retry_count=2 (should be 2^2 = 4 seconds)
            start_time = asyncio.get_event_loop().time()
            await ErrorHandler.handle_network_error(self.ctx, error, retry_count=2)
            elapsed = asyncio.get_event_loop().time() - start_time
            self.assertGreaterEqual(elapsed, 4.0)
            self.assertLess(elapsed, 4.5)
        
        asyncio.run(run_test())
    
    def test_handle_source_error_sends_message(self):
        """Test handle_source_error sends formatted error message."""
        async def run_test():
            error = Exception("Video unavailable")
            
            await ErrorHandler.handle_source_error(self.ctx, error)
            
            # Verify message was sent with error details
            self.ctx.send.assert_called_once_with("❌ Source error: Video unavailable")
        
        asyncio.run(run_test())
    
    def test_handle_source_error_with_different_errors(self):
        """Test handle_source_error with various source errors."""
        async def run_test():
            errors = [
                Exception("Video unavailable"),
                Exception("Content blocked in your country"),
                Exception("Invalid URL format")
            ]
            
            for error in errors:
                self.ctx.send.reset_mock()
                await ErrorHandler.handle_source_error(self.ctx, error)
                self.ctx.send.assert_called_once_with(f"❌ Source error: {str(error)}")
        
        asyncio.run(run_test())
    
    def test_handle_audio_error_retry_on_first_attempt(self):
        """Test handle_audio_error returns True to retry on first attempt."""
        async def run_test():
            error = Exception("Stream interrupted")
            
            # First attempt (retry_count=0) should return True
            result = await ErrorHandler.handle_audio_error(self.ctx, error, retry_count=0)
            
            self.assertTrue(result)
            # Should not send error message yet
            self.ctx.send.assert_not_called()
        
        asyncio.run(run_test())
    
    def test_handle_audio_error_retry_on_second_attempt(self):
        """Test handle_audio_error returns True to retry on second attempt."""
        async def run_test():
            error = Exception("Stream interrupted")
            
            # Second attempt (retry_count=1) should return True
            result = await ErrorHandler.handle_audio_error(self.ctx, error, retry_count=1)
            
            self.assertTrue(result)
            # Should not send error message yet
            self.ctx.send.assert_not_called()
        
        asyncio.run(run_test())
    
    def test_handle_audio_error_retry_on_third_attempt(self):
        """Test handle_audio_error returns True to retry on third attempt."""
        async def run_test():
            error = Exception("Stream interrupted")
            
            # Third attempt (retry_count=2) should return True
            result = await ErrorHandler.handle_audio_error(self.ctx, error, retry_count=2)
            
            self.assertTrue(result)
            # Should not send error message yet
            self.ctx.send.assert_not_called()
        
        asyncio.run(run_test())
    
    def test_handle_audio_error_max_retries_reached(self):
        """Test handle_audio_error returns False after 3 attempts."""
        async def run_test():
            error = Exception("Stream interrupted")
            
            # Fourth attempt (retry_count=3) should return False
            result = await ErrorHandler.handle_audio_error(self.ctx, error, retry_count=3)
            
            self.assertFalse(result)
            # Should send error message
            self.ctx.send.assert_called_once_with(
                "❌ Audio error: Unable to play track after 3 attempts. Skipping to next track."
            )
        
        asyncio.run(run_test())
    
    def test_handle_audio_error_exponential_backoff_timing(self):
        """Test handle_audio_error uses exponential backoff delays."""
        async def run_test():
            error = Exception("Stream interrupted")
            
            # Test delay for retry_count=0 (should be 2^0 = 1 second)
            start_time = asyncio.get_event_loop().time()
            await ErrorHandler.handle_audio_error(self.ctx, error, retry_count=0)
            elapsed = asyncio.get_event_loop().time() - start_time
            self.assertGreaterEqual(elapsed, 1.0)
            self.assertLess(elapsed, 1.5)
            
            # Test delay for retry_count=1 (should be 2^1 = 2 seconds)
            start_time = asyncio.get_event_loop().time()
            await ErrorHandler.handle_audio_error(self.ctx, error, retry_count=1)
            elapsed = asyncio.get_event_loop().time() - start_time
            self.assertGreaterEqual(elapsed, 2.0)
            self.assertLess(elapsed, 2.5)
            
            # Test delay for retry_count=2 (should be 2^2 = 4 seconds)
            start_time = asyncio.get_event_loop().time()
            await ErrorHandler.handle_audio_error(self.ctx, error, retry_count=2)
            elapsed = asyncio.get_event_loop().time() - start_time
            self.assertGreaterEqual(elapsed, 4.0)
            self.assertLess(elapsed, 4.5)
        
        asyncio.run(run_test())
    
    @patch('error_handler.logger')
    def test_log_error_with_context(self, mock_logger):
        """Test log_error logs error with context."""
        error = Exception("Test error")
        context = "test_function"
        
        ErrorHandler.log_error(error, context)
        
        # Verify logger.error was called with context
        mock_logger.error.assert_called_once()
        call_args = mock_logger.error.call_args[0][0]
        self.assertIn("test_function", call_args)
        self.assertIn("Test error", call_args)
    
    @patch('error_handler.logger')
    def test_log_error_without_context(self, mock_logger):
        """Test log_error logs error without context."""
        error = Exception("Test error")
        
        ErrorHandler.log_error(error)
        
        # Verify logger.error was called
        mock_logger.error.assert_called_once()
        call_args = mock_logger.error.call_args[0][0]
        self.assertIn("Test error", call_args)
    
    @patch('error_handler.logger')
    def test_all_handlers_log_with_stack_trace(self, mock_logger):
        """Test that all error handlers log errors with exc_info=True."""
        async def run_test():
            error = Exception("Test error")
            
            # Test handle_network_error
            await ErrorHandler.handle_network_error(self.ctx, error, retry_count=0)
            self.assertTrue(any(
                call[1].get('exc_info') is True 
                for call in mock_logger.error.call_args_list
            ))
            
            mock_logger.reset_mock()
            
            # Test handle_source_error
            await ErrorHandler.handle_source_error(self.ctx, error)
            self.assertTrue(any(
                call[1].get('exc_info') is True 
                for call in mock_logger.error.call_args_list
            ))
            
            mock_logger.reset_mock()
            
            # Test handle_audio_error
            await ErrorHandler.handle_audio_error(self.ctx, error, retry_count=0)
            self.assertTrue(any(
                call[1].get('exc_info') is True 
                for call in mock_logger.error.call_args_list
            ))
        
        asyncio.run(run_test())


if __name__ == '__main__':
    unittest.main()
