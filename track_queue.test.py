"""
Unit tests for TrackQueue class

Tests queue operations including add, next, clear, and order preservation.
"""

import unittest
from track_queue import TrackQueue
from track import Track


class TestTrackQueue(unittest.TestCase):
    """Test cases for TrackQueue class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.queue = TrackQueue()
        
        # Create mock track data
        self.track1_data = {
            'title': 'Track 1',
            'url': 'https://example.com/track1',
            'duration': 180
        }
        self.track2_data = {
            'title': 'Track 2',
            'url': 'https://example.com/track2',
            'duration': 240
        }
        self.track3_data = {
            'title': 'Track 3',
            'url': 'https://example.com/track3',
            'duration': 200
        }
        
        self.track1 = Track(self.track1_data)
        self.track2 = Track(self.track2_data)
        self.track3 = Track(self.track3_data)
    
    def test_init_empty_queue(self):
        """Test queue initialization creates empty queue."""
        queue = TrackQueue()
        self.assertEqual(len(queue.tracks), 0)
        self.assertEqual(queue.position, 0)
        self.assertTrue(queue.is_empty())
    
    def test_add_single_track(self):
        """Test adding a single track to the queue."""
        self.queue.add(self.track1)
        
        self.assertEqual(len(self.queue.tracks), 1)
        self.assertEqual(self.queue.tracks[0], self.track1)
        self.assertFalse(self.queue.is_empty())
    
    def test_add_multiple_tracks_sequentially(self):
        """Test adding multiple tracks one by one preserves order."""
        self.queue.add(self.track1)
        self.queue.add(self.track2)
        self.queue.add(self.track3)
        
        self.assertEqual(len(self.queue.tracks), 3)
        self.assertEqual(self.queue.tracks[0], self.track1)
        self.assertEqual(self.queue.tracks[1], self.track2)
        self.assertEqual(self.queue.tracks[2], self.track3)
    
    def test_add_multiple_tracks_at_once(self):
        """Test adding multiple tracks at once (playlist scenario)."""
        tracks = [self.track1, self.track2, self.track3]
        self.queue.add_multiple(tracks)
        
        self.assertEqual(len(self.queue.tracks), 3)
        self.assertEqual(self.queue.tracks[0], self.track1)
        self.assertEqual(self.queue.tracks[1], self.track2)
        self.assertEqual(self.queue.tracks[2], self.track3)
    
    def test_next_returns_tracks_in_order(self):
        """Test next() returns tracks in the order they were added."""
        self.queue.add(self.track1)
        self.queue.add(self.track2)
        self.queue.add(self.track3)
        
        # Get tracks in order
        track = self.queue.next()
        self.assertEqual(track, self.track1)
        
        track = self.queue.next()
        self.assertEqual(track, self.track2)
        
        track = self.queue.next()
        self.assertEqual(track, self.track3)
    
    def test_next_returns_none_when_empty(self):
        """Test next() returns None when queue is empty."""
        result = self.queue.next()
        self.assertIsNone(result)
    
    def test_next_returns_none_after_all_tracks_consumed(self):
        """Test next() returns None after all tracks have been played."""
        self.queue.add(self.track1)
        self.queue.add(self.track2)
        
        # Consume all tracks
        self.queue.next()
        self.queue.next()
        
        # Should return None now
        result = self.queue.next()
        self.assertIsNone(result)
    
    def test_is_empty_on_new_queue(self):
        """Test is_empty() returns True for new queue."""
        self.assertTrue(self.queue.is_empty())
    
    def test_is_empty_after_adding_tracks(self):
        """Test is_empty() returns False after adding tracks."""
        self.queue.add(self.track1)
        self.assertFalse(self.queue.is_empty())
    
    def test_is_empty_after_consuming_all_tracks(self):
        """Test is_empty() returns True after all tracks consumed."""
        self.queue.add(self.track1)
        self.queue.add(self.track2)
        
        self.queue.next()
        self.queue.next()
        
        self.assertTrue(self.queue.is_empty())
    
    def test_get_all_returns_remaining_tracks(self):
        """Test get_all() returns only tracks not yet played."""
        self.queue.add(self.track1)
        self.queue.add(self.track2)
        self.queue.add(self.track3)
        
        # Play first track
        self.queue.next()
        
        # get_all should return only track2 and track3
        remaining = self.queue.get_all()
        self.assertEqual(len(remaining), 2)
        self.assertEqual(remaining[0], self.track2)
        self.assertEqual(remaining[1], self.track3)
    
    def test_get_all_returns_empty_list_when_queue_empty(self):
        """Test get_all() returns empty list when no tracks remain."""
        result = self.queue.get_all()
        self.assertEqual(result, [])
    
    def test_get_all_returns_all_tracks_when_none_played(self):
        """Test get_all() returns all tracks when none have been played."""
        self.queue.add(self.track1)
        self.queue.add(self.track2)
        
        remaining = self.queue.get_all()
        self.assertEqual(len(remaining), 2)
        self.assertEqual(remaining[0], self.track1)
        self.assertEqual(remaining[1], self.track2)
    
    def test_clear_preserves_current_track(self):
        """Test clear() removes all tracks except the currently playing one."""
        self.queue.add(self.track1)
        self.queue.add(self.track2)
        self.queue.add(self.track3)
        
        # Start playing first track
        self.queue.next()
        
        # Clear the queue
        self.queue.clear()
        
        # Should have only track1 in tracks list (the current one)
        self.assertEqual(len(self.queue.tracks), 1)
        self.assertEqual(self.queue.tracks[0], self.track1)
        
        # Queue should be empty (no more tracks to play)
        self.assertTrue(self.queue.is_empty())
    
    def test_clear_on_empty_queue(self):
        """Test clear() on empty queue doesn't cause errors."""
        self.queue.clear()
        self.assertEqual(len(self.queue.tracks), 0)
        self.assertTrue(self.queue.is_empty())
    
    def test_clear_before_playing_any_track(self):
        """Test clear() when tracks added but none played yet."""
        self.queue.add(self.track1)
        self.queue.add(self.track2)
        
        # Clear without playing anything
        self.queue.clear()
        
        # Should have empty tracks list
        self.assertEqual(len(self.queue.tracks), 0)
        self.assertTrue(self.queue.is_empty())


if __name__ == '__main__':
    unittest.main()
