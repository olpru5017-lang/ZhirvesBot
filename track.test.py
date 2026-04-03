"""
Unit tests for Track class

Tests track metadata extraction, duration formatting, and embed creation.
"""

import unittest
import discord
from track import Track


class TestTrack(unittest.TestCase):
    """Test cases for Track class."""
    
    def test_init_with_complete_metadata(self):
        """Test Track initialization with all metadata fields."""
        data = {
            'title': 'Test Song',
            'url': 'https://example.com/song',
            'duration': 180,
            'thumbnail': 'https://example.com/thumb.jpg',
            'uploader': 'Test Artist',
            'extractor': 'youtube'
        }
        
        track = Track(data)
        
        self.assertEqual(track.title, 'Test Song')
        self.assertEqual(track.url, 'https://example.com/song')
        self.assertEqual(track.duration, 180)
        self.assertEqual(track.thumbnail, 'https://example.com/thumb.jpg')
        self.assertEqual(track.uploader, 'Test Artist')
        self.assertEqual(track.source, 'youtube')
    
    def test_init_with_missing_metadata(self):
        """Test Track initialization with missing metadata (fallback to defaults)."""
        data = {
            'url': 'https://example.com/song'
        }
        
        track = Track(data)
        
        self.assertEqual(track.title, 'Unknown')
        self.assertEqual(track.url, 'https://example.com/song')
        self.assertEqual(track.duration, 0)
        self.assertIsNone(track.thumbnail)
        self.assertEqual(track.uploader, 'Unknown')
        self.assertEqual(track.source, 'Unknown')
    
    def test_format_duration_less_than_hour(self):
        """Test duration formatting for tracks < 1 hour (MM:SS format)."""
        # Test 3 minutes 5 seconds
        data = {'duration': 185}
        track = Track(data)
        self.assertEqual(track.format_duration(), '3:05')
        
        # Test 0 seconds
        data = {'duration': 0}
        track = Track(data)
        self.assertEqual(track.format_duration(), '0:00')
        
        # Test 59 minutes 59 seconds
        data = {'duration': 3599}
        track = Track(data)
        self.assertEqual(track.format_duration(), '59:59')
    
    def test_format_duration_hour_or_more(self):
        """Test duration formatting for tracks >= 1 hour (HH:MM:SS format)."""
        # Test exactly 1 hour
        data = {'duration': 3600}
        track = Track(data)
        self.assertEqual(track.format_duration(), '1:00:00')
        
        # Test 1 hour 30 minutes 45 seconds
        data = {'duration': 5445}
        track = Track(data)
        self.assertEqual(track.format_duration(), '1:30:45')
        
        # Test 2 hours 5 minutes 3 seconds
        data = {'duration': 7503}
        track = Track(data)
        self.assertEqual(track.format_duration(), '2:05:03')
    
    def test_get_embed_with_thumbnail(self):
        """Test embed creation with thumbnail."""
        data = {
            'title': 'Test Song',
            'url': 'https://example.com/song',
            'duration': 180,
            'thumbnail': 'https://example.com/thumb.jpg',
            'uploader': 'Test Artist'
        }
        
        track = Track(data)
        embed = track.get_embed()
        
        self.assertEqual(embed.title, 'Test Song')
        self.assertEqual(embed.url, 'https://example.com/song')
        self.assertIn('Duration: 3:00', embed.description)
        self.assertEqual(embed.thumbnail.url, 'https://example.com/thumb.jpg')
        self.assertEqual(embed.fields[0].name, 'Uploader')
        self.assertEqual(embed.fields[0].value, 'Test Artist')
    
    def test_get_embed_without_thumbnail(self):
        """Test embed creation without thumbnail."""
        data = {
            'title': 'Test Song',
            'url': 'https://example.com/song',
            'duration': 180,
            'uploader': 'Test Artist'
        }
        
        track = Track(data)
        embed = track.get_embed()
        
        self.assertEqual(embed.title, 'Test Song')
        self.assertEqual(embed.url, 'https://example.com/song')
        self.assertIn('Duration: 3:00', embed.description)
        # Thumbnail should not be set (url will be None or empty)
        self.assertIsNone(embed.thumbnail.url)
        self.assertEqual(embed.fields[0].name, 'Uploader')
        self.assertEqual(embed.fields[0].value, 'Test Artist')


if __name__ == '__main__':
    unittest.main()
