"""
Data Processor

This module contains the logic for processing Spotify track data, including:
- Selecting seed tracks and artists for recommendations
- Filtering out tracks from previous playlists
- Processing user listening data to identify preferences
"""

import logging
import json
import os
from typing import Dict, List, Set, Tuple, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class DataProcessor:
    
    def __init__(self, data_dir: str = "data"):

        self.data_dir = data_dir
        self._ensure_data_directory()
    
    def _ensure_data_directory(self) -> None:

        os.makedirs(self.data_dir, exist_ok=True)
    
    def select_seed_tracks_and_artists(
        self,
        top_tracks: List[Dict],
        recent_tracks: List[Dict],
        max_seed_tracks: int = 3,
        max_seed_artists: int = 2
    ) -> Tuple[List[str], List[str]]:

        logger.info("Selecting seed tracks and artists...")
        
        weighted_tracks = {}
        
        for i, track in enumerate(top_tracks):
            track_id = track['id']
            weight = (len(top_tracks) - i) / len(top_tracks)
            weighted_tracks[track_id] = weighted_tracks.get(track_id, 0) + weight
        
        for i, track in enumerate(recent_tracks):
            track_id = track['id']
            # Weight inversely by position and lower than top tracks
            weight = ((len(recent_tracks) - i) / len(recent_tracks)) * 0.5
            weighted_tracks[track_id] = weighted_tracks.get(track_id, 0) + weight
        
        # Sort tracks by weight
        sorted_tracks = sorted(weighted_tracks.items(), key=lambda x: x[1], reverse=True)
        
        # Select seed tracks
        seed_track_ids = [track_id for track_id, _ in sorted_tracks[:max_seed_tracks]]
        
        # Get artist weights
        artist_weights = {}
        for track in top_tracks + recent_tracks:
            for artist in track['artists']:
                artist_id = artist['id']
                artist_weights[artist_id] = artist_weights.get(artist_id, 0) + 1
        
        # Filter out artists already represented in seed tracks
        seed_track_artists = set()
        for track_id in seed_track_ids:
            track_objects = [t for t in top_tracks + recent_tracks if t['id'] == track_id]
            for track in track_objects:
                for artist in track['artists']:
                    seed_track_artists.add(artist['id'])
        
        # Remove artists already represented in seed tracks to increase diversity
        artist_weights = {k: v for k, v in artist_weights.items() if k not in seed_track_artists}
        
        # Sort artists by weight
        sorted_artists = sorted(artist_weights.items(), key=lambda x: x[1], reverse=True)
        
        # Select seed artists
        seed_artist_ids = [artist_id for artist_id, _ in sorted_artists[:max_seed_artists]]
        
        logger.info(f"Selected {len(seed_track_ids)} seed tracks and {len(seed_artist_ids)} seed artists")
        return seed_track_ids, seed_artist_ids
    
    def filter_tracks(
        self,
        tracks: List[Dict],
        exclude_track_ids: Set[str] = None
    ) -> List[Dict]:

        exclude_track_ids = exclude_track_ids or set()
        logger.info(f"Filtering {len(tracks)} tracks, excluding {len(exclude_track_ids)} tracks...")
        
        # Remove excluded tracks
        filtered_tracks = [track for track in tracks if track['id'] not in exclude_track_ids]
        
        # Remove duplicates
        seen_ids = set()
        unique_tracks = []
        for track in filtered_tracks:
            if track['id'] not in seen_ids:
                seen_ids.add(track['id'])
                unique_tracks.append(track)
        
        logger.info(f"Filtered to {len(unique_tracks)} tracks")
        return unique_tracks
    
    def save_playlist_history(
        self,
        playlist_id: str,
        filename: str = "playlist_history.json"
    ) -> None:

        filepath = os.path.join(self.data_dir, filename)
        
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                try:
                    history = json.load(f)
                except json.JSONDecodeError:
                    logger.warning(f"Could not parse {filepath}, creating new history")
                    history = []
        else:
            history = []
        
        # Add new playlist ID with timestamp
        history.append({
            "playlist_id": playlist_id,
            "created_at": datetime.now().isoformat()
        })
        
        # Write updated history
        with open(filepath, 'w') as f:
            json.dump(history, f, indent=2)
        
        logger.info(f"Added playlist {playlist_id} to history")
    
    def get_previous_playlist_ids(
        self,
        filename: str = "playlist_history.json",
        count: int = 4
    ) -> List[str]:
        filepath = os.path.join(self.data_dir, filename)
        
        if not os.path.exists(filepath):
            logger.warning(f"History file {filepath} does not exist")
            return []
        
        try:
            with open(filepath, 'r') as f:
                history = json.load(f)
            
            # Sort by creation time (newest first) and get the most recent ones
            sorted_history = sorted(
                history,
                key=lambda x: x.get("created_at", ""),
                reverse=True
            )
            
            playlist_ids = [item["playlist_id"] for item in sorted_history[:count]]
            logger.info(f"Retrieved {len(playlist_ids)} previous playlist IDs")
            return playlist_ids
            
        except Exception as e:
            logger.error(f"Error getting previous playlist IDs: {e}")
            return []
    
    def analyze_music_preferences(
        self,
        top_tracks: List[Dict],
        recent_tracks: List[Dict]
    ) -> Dict[str, Any]:

        logger.info("Analyzing music preferences...")
        
        all_tracks = top_tracks + recent_tracks
        
        if not all_tracks:
            logger.warning("No tracks available for preference analysis")
            return {}
        
        # Extract audio features that might be in the track objects
        # (If full audio features are needed, they should be fetched separately)
        preferences = {
            "artist_counts": {},
            "genre_counts": {},
        }

        for track in all_tracks:
            for artist in track.get('artists', []):
                artist_id = artist.get('id')
                artist_name = artist.get('name')
                if artist_id and artist_name:
                    if artist_id not in preferences["artist_counts"]:
                        preferences["artist_counts"][artist_id] = {
                            "name": artist_name,
                            "count": 0
                        }
                    preferences["artist_counts"][artist_id]["count"] += 1

        top_artists = sorted(
            preferences["artist_counts"].items(),
            key=lambda x: x[1]["count"],
            reverse=True
        )
        preferences["top_artists"] = [
            {"id": artist_id, "name": info["name"], "count": info["count"]}
            for artist_id, info in top_artists[:10]
        ]
        
        logger.info("Completed music preference analysis")
        return preferences

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    processor = DataProcessor()
    
    example_tracks = [
        {"id": "track1", "artists": [{"id": "artist1", "name": "Artist One"}]},
        {"id": "track2", "artists": [{"id": "artist2", "name": "Artist Two"}]},
        {"id": "track3", "artists": [{"id": "artist1", "name": "Artist One"}]},
    ]
    
    seed_tracks, seed_artists = processor.select_seed_tracks_and_artists(
        example_tracks, example_tracks
    )
    print(f"Seed tracks: {seed_tracks}")
    print(f"Seed artists: {seed_artists}")
    
    filtered_tracks = processor.filter_tracks(example_tracks, {"track1"})
    print(f"Filtered tracks: {len(filtered_tracks)}")