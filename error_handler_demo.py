"""
Demo script to demonstrate ErrorHandler functionality

This script shows how ErrorHandler integrates with the Discord Music Bot.
"""

import asyncio
import logging
from unittest.mock import MagicMock, AsyncMock
from error_handler import ErrorHandler


# Configure logging to see error handler output
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


async def demo_user_error():
    """Demonstrate user error handling."""
    print("\n=== Demo: User Error ===")
    ctx = MagicMock()
    ctx.send = AsyncMock()
    ctx.guild = MagicMock()
    ctx.guild.id = 12345
    
    await ErrorHandler.handle_user_error(ctx, "You must be in a voice channel")
    print(f"Message sent: {ctx.send.call_args[0][0]}")


async def demo_network_error_with_retry():
    """Demonstrate network error with retry logic."""
    print("\n=== Demo: Network Error with Retry ===")
    ctx = MagicMock()
    ctx.send = AsyncMock()
    ctx.guild = MagicMock()
    ctx.guild.id = 12345
    
    error = Exception("Connection timeout")
    
    # Simulate retry attempts
    for attempt in range(4):
        print(f"\nAttempt {attempt + 1}:")
        should_retry = await ErrorHandler.handle_network_error(ctx, error, retry_count=attempt)
        
        if should_retry:
            print(f"  -> Retry scheduled (waited {2**attempt} seconds)")
        else:
            print(f"  -> Max retries reached, giving up")
            print(f"  -> Message sent: {ctx.send.call_args[0][0]}")
            break


async def demo_source_error():
    """Demonstrate source error handling."""
    print("\n=== Demo: Source Error ===")
    ctx = MagicMock()
    ctx.send = AsyncMock()
    ctx.guild = MagicMock()
    ctx.guild.id = 12345
    
    error = Exception("Video unavailable")
    await ErrorHandler.handle_source_error(ctx, error)
    print(f"Message sent: {ctx.send.call_args[0][0]}")


async def demo_audio_error_with_retry():
    """Demonstrate audio error with retry logic."""
    print("\n=== Demo: Audio Error with Retry ===")
    ctx = MagicMock()
    ctx.send = AsyncMock()
    ctx.guild = MagicMock()
    ctx.guild.id = 12345
    
    error = Exception("Stream interrupted")
    
    # Simulate retry attempts
    for attempt in range(4):
        print(f"\nAttempt {attempt + 1}:")
        should_retry = await ErrorHandler.handle_audio_error(ctx, error, retry_count=attempt)
        
        if should_retry:
            print(f"  -> Retry scheduled (waited {2**attempt} seconds)")
        else:
            print(f"  -> Max retries reached, skipping track")
            print(f"  -> Message sent: {ctx.send.call_args[0][0]}")
            break


async def demo_exponential_backoff():
    """Demonstrate exponential backoff timing."""
    print("\n=== Demo: Exponential Backoff Timing ===")
    ctx = MagicMock()
    ctx.send = AsyncMock()
    ctx.guild = MagicMock()
    ctx.guild.id = 12345
    
    error = Exception("Test error")
    
    for attempt in range(3):
        expected_delay = 2 ** attempt
        print(f"\nRetry {attempt + 1}: Expected delay = {expected_delay} seconds")
        
        start_time = asyncio.get_event_loop().time()
        await ErrorHandler.handle_network_error(ctx, error, retry_count=attempt)
        elapsed = asyncio.get_event_loop().time() - start_time
        
        print(f"  -> Actual delay = {elapsed:.2f} seconds")


async def main():
    """Run all demos."""
    print("=" * 60)
    print("ErrorHandler Demo - Discord Music Bot")
    print("=" * 60)
    
    await demo_user_error()
    await demo_network_error_with_retry()
    await demo_source_error()
    await demo_audio_error_with_retry()
    await demo_exponential_backoff()
    
    print("\n" + "=" * 60)
    print("Demo completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
