"""
Queue Manager module for Discord Music Bot

Handles track queue management and ordering.
"""


class TrackQueue:
    """Manages the queue of tracks for playback."""
    
    def __init__(self):
        """
        Initialize an empty track queue.
        
        Validates Requirements: 5.1
        """
        self.tracks = []
        self.position = 0
    
    def add(self, track):
        """
        Add a single track to the end of the queue.
        
        Args:
            track: Track object to add to the queue
        
        Validates Requirements: 5.1
        """
        self.tracks.append(track)
    
    def add_multiple(self, tracks):
        """
        Add multiple tracks to the end of the queue (for playlists).
        
        Args:
            tracks (list): List of Track objects to add to the queue
        
        Validates Requirements: 5.1, 9.1
        """
        self.tracks.extend(tracks)
    
    def next(self):
        """
        Get the next track from the queue.
        
        Returns:
            Track object if available, None if queue is empty
        
        Validates Requirements: 5.2, 5.5
        """
        if self.position < len(self.tracks):
            track = self.tracks[self.position]
            self.position += 1
            return track
        return None
    
    def clear(self):
        """
        Clear all tracks from the queue except the currently playing track.
        
        The current track (at position - 1) is preserved, all other tracks
        are removed from the queue.
        
        Validates Requirements: 5.4
        """
        # Keep only tracks up to current position (preserves current track)
        self.tracks = self.tracks[:self.position]
    
    def get_all(self):
        """
        Get all tracks remaining in the queue (not including current track).
        
        Returns:
            list: List of Track objects that are queued for playback
        
        Validates Requirements: 5.3
        """
        return self.tracks[self.position:]
    
    def is_empty(self):
        """
        Check if the queue is empty (no more tracks to play).
        
        Returns:
            bool: True if queue is empty, False otherwise
        
        Validates Requirements: 5.5
        """
        return self.position >= len(self.tracks)
