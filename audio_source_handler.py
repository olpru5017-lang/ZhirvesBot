"""
Audio Source Handler module for Discord Music Bot

Handles audio extraction from various sources using yt-dlp.
"""

import asyncio
import logging
import discord
import yt_dlp
from track import Track


logger = logging.getLogger(__name__)


class AudioSourceHandler:
    """Handles audio extraction and source management using yt-dlp."""
    
    def __init__(self):
        """
        Initialize AudioSourceHandler with yt-dlp configuration.
        
        Validates Requirements: 1.1, 2.1, 2.2, 2.3, 9.1
        """
        # List of clients to try in order
        self.clients_to_try = [
            ['android_testsuite'],
            ['android_creator'],
            ['android_music'],
            ['android_vr'],
            ['android_producer'],
            ['android'],
            ['ios'],
            ['mweb'],
            ['tv_embedded'],
            ['web']
        ]
        
        self.base_ytdl_options = {
            'format': 'bestaudio*+bestvideo/best',
            'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
            'restrictfilenames': True,
            'noplaylist': False,
            'nocheckcertificate': True,
            'ignoreerrors': False,
            'logtostderr': False,
            'quiet': True,
            'no_warnings': True,
            'default_search': 'ytsearch5',
            'source_address': '0.0.0.0',
            # Additional options to bypass restrictions
            'age_limit': None,
            'geo_bypass': True,
            'geo_bypass_country': 'US',
            # Format selection fallback
            'format_sort': ['quality', 'res', 'fps', 'hdr:12', 'codec:vp9.2', 'size', 'br', 'asr', 'proto'],
            'merge_output_format': 'webm/mp4/mkv'
        }
        
        # Check if cookies file exists
        import os
        cookies_path = 'youtube_cookies.txt'
        if os.path.exists(cookies_path):
            self.base_ytdl_options['cookiefile'] = cookies_path
            logger.info("YouTube cookies file found - using cookies for authentication")
        else:
            logger.warning("YouTube cookies file not found - YouTube may not work. See COOKIES_SETUP.md")
        
        self.ffmpeg_options = {
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
            'options': '-vn'
        }
    
    def _create_ytdl_with_client(self, client):
        """Create a YoutubeDL instance with specific client."""
        options = self.base_ytdl_options.copy()
        options['extractor_args'] = {
            'youtube': {
                'player_client': client,
                'skip': ['hls', 'dash']
            }
        }
        return yt_dlp.YoutubeDL(options)
    
    async def _extract_with_fallback(self, query, is_url=False):
        """Try extracting with different clients until one works."""
        last_error = None
        
        for client in self.clients_to_try:
            try:
                logger.info(f"Trying client: {client[0]}")
                ytdl = self._create_ytdl_with_client(client)
                
                loop = asyncio.get_event_loop()
                data = await asyncio.wait_for(
                    loop.run_in_executor(
                        None,
                        lambda: ytdl.extract_info(query, download=False)
                    ),
                    timeout=30.0
                )
                
                if data:
                    logger.info(f"Success with client: {client[0]}")
                    return data
                    
            except Exception as e:
                last_error = e
                logger.warning(f"Client {client[0]} failed: {str(e)[:100]}")
                continue
        
        # If all clients failed, raise the last error
        if last_error:
            raise last_error
        else:
            raise Exception("All clients failed to extract data")
    
    async def search(self, query: str, max_results: int = 5):
        """
        Search for tracks by query string.
        
        Args:
            query (str): Search query string
            max_results (int): Maximum number of results to return (default: 5)
        
        Returns:
            list[Track]: List of Track objects (max 5 results)
        
        Raises:
            asyncio.TimeoutError: If search takes longer than 30 seconds
            Exception: If search fails
        
        Validates Requirements: 1.1, 1.2, 1.4, 1.5
        """
        try:
            # Use fallback mechanism to try different clients
            data = await self._extract_with_fallback(f"ytsearch{max_results}:{query}")
            
            if not data:
                logger.warning(f"No results found for query: {query}")
                return []
            
            # Extract entries from search results
            entries = data.get('entries', [])
            if not entries:
                logger.warning(f"No entries in search results for query: {query}")
                return []
            
            # Convert to Track objects (limit to max_results)
            tracks = []
            for entry in entries[:max_results]:
                if entry:
                    tracks.append(Track(entry))
            
            logger.info(f"Search found {len(tracks)} results for query: {query}")
            return tracks
            
        except asyncio.TimeoutError:
            logger.error(f"Search timeout after 30 seconds for query: {query}")
            raise asyncio.TimeoutError("Search took too long (>30 seconds)")
        except Exception as e:
            logger.error(f"Search error for query '{query}': {e}", exc_info=True)
            raise
    
    async def extract_from_url(self, url: str):
        """
        Extract audio information from URL.
        
        Supports YouTube, SoundCloud, and direct audio file URLs.
        For playlists, limits to first 50 tracks.
        
        Args:
            url (str): URL to extract from
        
        Returns:
            Track or list[Track]: Single Track for videos, list of Tracks for playlists
        
        Raises:
            asyncio.TimeoutError: If extraction takes longer than 30 seconds
            Exception: If URL is invalid or extraction fails
        
        Validates Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 9.1, 9.2, 9.3, 9.4
        """
        try:
            # Use fallback mechanism to try different clients
            data = await self._extract_with_fallback(url, is_url=True)
            
            if not data:
                logger.error(f"No data extracted from URL: {url}")
                raise ValueError(f"Unable to extract audio from URL: {url}")
            
            # Check if this is a playlist
            if 'entries' in data:
                entries = data['entries']
                
                # Filter out None entries
                entries = [e for e in entries if e]
                
                if not entries:
                    logger.error(f"Playlist is empty: {url}")
                    raise ValueError("Playlist is empty or unavailable")
                
                # Limit to first 50 tracks
                limited_entries = entries[:50]
                
                tracks = [Track(entry) for entry in limited_entries]
                
                logger.info(f"Extracted {len(tracks)} tracks from playlist (limited to 50): {url}")
                return tracks
            else:
                # Single track
                track = Track(data)
                logger.info(f"Extracted single track from URL: {url}")
                return track
                
        except asyncio.TimeoutError:
            logger.error(f"URL extraction timeout after 30 seconds for URL: {url}")
            raise asyncio.TimeoutError("URL extraction took too long (>30 seconds)")
        except Exception as e:
            logger.error(f"Extraction error for URL '{url}': {e}", exc_info=True)
            raise
    
    async def get_audio_source(self, track: Track):
        """
        Get FFmpeg audio source for playback.
        
        Args:
            track (Track): Track object with URL
        
        Returns:
            discord.FFmpegPCMAudio: Audio source ready for playback
        
        Raises:
            Exception: If audio source creation fails
        
        Validates Requirements: 6.1, 6.2
        """
        try:
            # Extract fresh stream URL (URLs expire) using fallback
            data = await self._extract_with_fallback(track.url, is_url=True)
            
            if not data:
                raise ValueError(f"Unable to get audio source for track: {track.title}")
            
            # Get the actual stream URL
            stream_url = data.get('url')
            if not stream_url:
                raise ValueError(f"No stream URL found for track: {track.title}")
            
            # Create FFmpeg audio source
            audio_source = discord.FFmpegPCMAudio(stream_url, **self.ffmpeg_options)
            
            logger.info(f"Created audio source for track: {track.title}")
            return audio_source
            
        except Exception as e:
            logger.error(f"Error creating audio source for track '{track.title}': {e}", exc_info=True)
            raise
