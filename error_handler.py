"""
Error Handler module for Discord Music Bot

Handles different types of errors with appropriate retry logic and user feedback.
"""

import asyncio
import logging
import traceback
from typing import Optional


logger = logging.getLogger(__name__)


class ErrorHandler:
    """Handles various error types with retry logic and user feedback."""
    
    @staticmethod
    async def handle_user_error(ctx, message: str):
        """
        Handle user errors (invalid input, not in voice channel, etc.).
        
        User errors do not require retry - they need user correction.
        Sends a user-friendly error message to the channel.
        
        Args:
            ctx: Discord command context
            message (str): User-friendly error message
        
        Validates Requirements: 8.1
        """
        try:
            await ctx.send(f"❌ {message}")
            logger.info(f"User error in guild {ctx.guild.id}: {message}")
        except Exception as e:
            logger.error(f"Failed to send user error message: {e}", exc_info=True)
    
    @staticmethod
    async def handle_network_error(ctx, error: Exception, retry_count: int = 0) -> bool:
        """
        Handle network errors with exponential backoff retry logic.
        
        Network errors include connection loss, timeouts, and API failures.
        Retries up to 3 times with exponential backoff (2^retry_count seconds).
        
        Args:
            ctx: Discord command context
            error (Exception): The network error that occurred
            retry_count (int): Current retry attempt (0-indexed)
        
        Returns:
            bool: True if should retry, False if max retries reached
        
        Validates Requirements: 8.2, 8.5
        """
        # Log the error with full stack trace
        logger.error(
            f"Network error in guild {ctx.guild.id} (attempt {retry_count + 1}/3): {error}",
            exc_info=True
        )
        
        # Check if we should retry
        if retry_count < 3:
            # Calculate exponential backoff delay
            delay = 2 ** retry_count
            logger.info(f"Retrying after {delay} seconds (attempt {retry_count + 1}/3)")
            
            # Wait before retry
            await asyncio.sleep(delay)
            return True  # Signal to retry
        else:
            # Max retries reached
            error_message = "❌ Network error: Unable to connect after 3 attempts"
            try:
                await ctx.send(error_message)
            except Exception as send_error:
                logger.error(f"Failed to send network error message: {send_error}", exc_info=True)
            
            logger.error(f"Network error: Max retries (3) reached for guild {ctx.guild.id}")
            return False  # Signal to stop retrying
    
    @staticmethod
    async def handle_source_error(ctx, error: Exception):
        """
        Handle source errors (unavailable video, blocked content, invalid URL).
        
        Source errors are not retryable - the content is unavailable.
        Sends error message and the player should skip to next track.
        
        Args:
            ctx: Discord command context
            error (Exception): The source error that occurred
        
        Validates Requirements: 8.3, 8.4, 8.5
        """
        # Log the error with full stack trace
        logger.error(
            f"Source error in guild {ctx.guild.id}: {error}",
            exc_info=True
        )
        
        # Send user-friendly error message
        error_message = f"❌ Source error: {str(error)}"
        try:
            await ctx.send(error_message)
        except Exception as send_error:
            logger.error(f"Failed to send source error message: {send_error}", exc_info=True)
        
        logger.info(f"Source error handled, track will be skipped in guild {ctx.guild.id}")
    
    @staticmethod
    async def handle_audio_error(ctx, error: Exception, retry_count: int = 0) -> bool:
        """
        Handle audio playback errors with retry logic.
        
        Audio errors include stream interruption, codec issues, and playback failures.
        Retries up to 3 times with exponential backoff before skipping track.
        
        Args:
            ctx: Discord command context
            error (Exception): The audio error that occurred
            retry_count (int): Current retry attempt (0-indexed)
        
        Returns:
            bool: True if should retry, False if max retries reached (skip track)
        
        Validates Requirements: 6.4, 6.5, 8.4, 8.5
        """
        # Log the error with full stack trace
        logger.error(
            f"Audio error in guild {ctx.guild.id} (attempt {retry_count + 1}/3): {error}",
            exc_info=True
        )
        
        # Check if we should retry
        if retry_count < 3:
            # Calculate exponential backoff delay
            delay = 2 ** retry_count
            logger.info(f"Retrying audio playback after {delay} seconds (attempt {retry_count + 1}/3)")
            
            # Wait before retry
            await asyncio.sleep(delay)
            return True  # Signal to retry
        else:
            # Max retries reached - skip track
            error_message = "❌ Audio error: Unable to play track after 3 attempts. Skipping to next track."
            try:
                await ctx.send(error_message)
            except Exception as send_error:
                logger.error(f"Failed to send audio error message: {send_error}", exc_info=True)
            
            logger.error(f"Audio error: Max retries (3) reached for guild {ctx.guild.id}, skipping track")
            return False  # Signal to skip track
    
    @staticmethod
    def log_error(error: Exception, context: str = ""):
        """
        Log an error with full stack trace for diagnostics.
        
        This is a utility method for logging errors that don't need
        specific handling logic but should be recorded for debugging.
        
        Args:
            error (Exception): The error to log
            context (str): Additional context about where the error occurred
        
        Validates Requirements: 8.5
        """
        if context:
            logger.error(f"Error in {context}: {error}", exc_info=True)
        else:
            logger.error(f"Error: {error}", exc_info=True)
        
        # Also log the full stack trace as a separate entry for easier debugging
        stack_trace = ''.join(traceback.format_exception(type(error), error, error.__traceback__))
        logger.debug(f"Full stack trace:\n{stack_trace}")
