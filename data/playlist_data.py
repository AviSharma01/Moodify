"""
Playlist Data

This module provides classes and functions for managing playlist data,
including storage, retrieval, and tracking of playlist history.
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

class PlaylistTracker:

    
    def __init__(self, data_dir: str = "data"):

        self.data_dir = data_dir
        self.history_file = os.path.join(data_dir, "playlist_history.json")
        self._ensure_data_directory()
    
    def _ensure_data_directory(self) -> None:

        os.makedirs(self.data_dir, exist_ok=True)
        
        # Create history file if it doesn't exist
        if not os.path.exists(self.history_file):
            with open(self.history_file, 'w') as f:
                json.dump([], f)
    
    def add_playlist(
        self,
        playlist_id: str,
        name: str,
        track_ids: List[str],
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:

        history = self._read_history()
        
        playlist_entry = {
            "id": playlist_id,
            "name": name,
            "created_at": datetime.now().isoformat(),
            "track_count": len(track_ids),
            "tracks": track_ids
        }
        
        if metadata:
            playlist_entry["metadata"] = metadata
        
        history.append(playlist_entry)
        
        self._write_history(history)
        
        logger.info(f"Added playlist {playlist_id} ({name}) to history")
    
    def get_recent_playlists(self, count: int = 1) -> List[Dict[str, Any]]:

        history = self._read_history()
        
        sorted_history = sorted(
            history,
            key=lambda x: x.get("created_at", ""),
            reverse=True
        )
        
        recent_playlists = sorted_history[:count]
        logger.info(f"Retrieved {len(recent_playlists)} recent playlists")
        
        return recent_playlists
    
    def get_recent_track_ids(self, weeks: int = 1) -> List[str]:
 
        recent_playlists = self.get_recent_playlists(count=weeks)
        
        # Collect all track IDs
        track_ids = []
        for playlist in recent_playlists:
            tracks = playlist.get("tracks", [])
            track_ids.extend(tracks)
        
        # Remove duplicates
        unique_track_ids = list(set(track_ids))
        
        logger.info(f"Retrieved {len(unique_track_ids)} unique tracks from the last {weeks} weeks")
        return unique_track_ids
    
    def _read_history(self) -> List[Dict[str, Any]]:

        try:
            with open(self.history_file, 'r') as f:
                history = json.load(f)
            return history
        except (json.JSONDecodeError, FileNotFoundError) as e:
            logger.warning(f"Error reading history file: {e}")
            return []
    
    def _write_history(self, history: List[Dict[str, Any]]) -> None:

        try:
            with open(self.history_file, 'w') as f:
                json.dump(history, f, indent=2)
        except Exception as e:
            logger.error(f"Error writing history file: {e}")

class PlaylistData:

    
    def __init__(
        self,
        name: str,
        description: str = "",
        track_ids: Optional[List[str]] = None,
        playlist_id: Optional[str] = None,
        created_at: Optional[str] = None
    ):

        self.name = name
        self.description = description
        self.track_ids = track_ids or []
        self.playlist_id = playlist_id
        self.created_at = created_at or datetime.now().isoformat()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PlaylistData':

        return cls(
            name=data.get("name", ""),
            description=data.get("description", ""),
            track_ids=data.get("tracks", []),
            playlist_id=data.get("id"),
            created_at=data.get("created_at")
        )
    
    def to_dict(self) -> Dict[str, Any]:

        return {
            "name": self.name,
            "description": self.description,
            "tracks": self.track_ids,
            "id": self.playlist_id,
            "created_at": self.created_at,
            "track_count": len(self.track_ids)
        }

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    tracker = PlaylistTracker()
    
    playlist = PlaylistData(
        name="Test Playlist",
        description="A test playlist",
        track_ids=["track1", "track2", "track3"]
    )
    
    tracker.add_playlist(
        playlist_id="playlist123",
        name=playlist.name,
        track_ids=playlist.track_ids,
        metadata={"source": "example"}
    )
    
    recent_playlists = tracker.get_recent_playlists()
    print(f"Recent playlists: {len(recent_playlists)}")
    
    recent_track_ids = tracker.get_recent_track_ids()
    print(f"Recent track IDs: {len(recent_track_ids)}")