"""
Track module for Discord Music Bot

Handles track metadata extraction and formatting.
"""

import discord


class Track:
    """Represents a music track with metadata."""
    
    def __init__(self, data):
        """
        Initialize a Track with metadata from yt-dlp extraction.
        
        Args:
            data (dict): Dictionary containing track metadata from yt-dlp
                Expected keys: title, url, duration, thumbnail, uploader, extractor
        
        Validates Requirements: 3.1, 3.4
        """
        self.title = data.get('title', 'Unknown')
        self.url = data.get('url')
        self.duration = data.get('duration', 0)
        self.thumbnail = data.get('thumbnail')
        self.uploader = data.get('uploader', 'Unknown')
        self.source = data.get('extractor', 'Unknown')
    
    def format_duration(self):
        """
        Format duration as MM:SS or HH:MM:SS.
        
        Returns:
            str: Formatted duration string
                - MM:SS for tracks < 1 hour
                - HH:MM:SS for tracks >= 1 hour
        
        Validates Requirements: 3.5
        """
        if self.duration < 3600:
            # Format as MM:SS for tracks less than 1 hour
            minutes = self.duration // 60
            seconds = self.duration % 60
            return f"{minutes}:{seconds:02d}"
        else:
            # Format as HH:MM:SS for tracks 1 hour or longer
            hours = self.duration // 3600
            minutes = (self.duration % 3600) // 60
            seconds = self.duration % 60
            return f"{hours}:{minutes:02d}:{seconds:02d}"
    
    def get_embed(self):
        """
        Create a Discord embed with track metadata.
        
        Returns:
            discord.Embed: Embed object with track information including
                title, url, duration, thumbnail (if available), and uploader
        
        Validates Requirements: 3.2, 3.4, 3.5
        """
        embed = discord.Embed(
            title=self.title,
            url=self.url,
            description=f"Duration: {self.format_duration()}"
        )
        
        # Add thumbnail if available
        if self.thumbnail:
            embed.set_thumbnail(url=self.thumbnail)
        
        # Add uploader information
        embed.add_field(name="Uploader", value=self.uploader)
        
        return embed
