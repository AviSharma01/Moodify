"""
Spotify API Wrapper

This module provides a wrapper around the Spotify Web API using the spotipy library.
It handles authentication, token refresh, and provides methods for interacting with
Spotify resources needed for playlist generation.
"""

import os
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple, Any, Union

import spotipy
from spotipy.oauth2 import SpotifyOAuth
from spotipy.cache_handler import CacheFileHandler

logger = logging.getLogger(__name__)

class SpotifyAPI:

    
    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        redirect_uri: Optional[str] = None,
        scope: Optional[List[str]] = None,
        cache_path: str = ".cache-spotify",
        username: Optional[str] = None
    ):

        # Use environment variables if parameters not provided
        self.client_id = client_id or os.environ.get("SPOTIFY_CLIENT_ID")
        self.client_secret = client_secret or os.environ.get("SPOTIFY_CLIENT_SECRET")
        self.redirect_uri = redirect_uri or os.environ.get("SPOTIFY_REDIRECT_URI", "http://localhost:8888/callback")
        
        if not self.client_id or not self.client_secret:
            raise ValueError(
                "Spotify API credentials not provided. Set SPOTIFY_CLIENT_ID and "
                "SPOTIFY_CLIENT_SECRET environment variables or pass them as parameters."
            )
        
        # Default scopes needed for the playlist generator
        self.scope = scope or [
            "user-read-recently-played",
            "user-top-read",
            "playlist-read-private",
            "playlist-modify-private",
            "playlist-modify-public"
        ]
        
        # Setup cache handling
        if username:
            cache_path = f"{cache_path}-{username}"
        self.cache_path = cache_path
        
        # Initialize the Spotify client
        self.client = self._create_spotify_client()
        
        # Get and store user ID
        self.user_id = self._get_user_id()
        
        logger.info(f"Spotify API initialized for user: {self.user_id}")
    
    def _create_spotify_client(self) -> spotipy.Spotify:

        try:
            auth_manager = SpotifyOAuth(
                client_id=self.client_id,
                client_secret=self.client_secret,
                redirect_uri=self.redirect_uri,
                scope=" ".join(self.scope),
                cache_handler=CacheFileHandler(cache_path=self.cache_path),
                show_dialog=True
            )
            
            client = spotipy.Spotify(auth_manager=auth_manager)
            
            # Test the connection and token
            client.current_user()
            return client
            
        except Exception as e:
            logger.error(f"Error creating Spotify client: {e}")
            raise
    
    def _get_user_id(self) -> str:
        try:
            user_info = self.client.current_user()
            return user_info["id"]
        except Exception as e:
            logger.error(f"Error getting user ID: {e}")
            raise
    
    def get_top_tracks(self, time_range: str = "short_term", limit: int = 50) -> List[Dict]:
        """
        Get the user's top tracks.
        
        Args:
            time_range: Time range for top tracks:
                        "short_term" (4 weeks),
                        "medium_term" (6 months),
                        "long_term" (several years)
            limit: Maximum number of tracks to return
        
        Returns:
            List of track objects
        """
        try:
            logger.info(f"Getting top {limit} tracks for time range '{time_range}'")
            results = self.client.current_user_top_tracks(
                time_range=time_range,
                limit=limit
            )
            tracks = results["items"]
            logger.info(f"Retrieved {len(tracks)} top tracks")
            return tracks
        except Exception as e:
            logger.error(f"Error getting top tracks: {e}")
            return []
    
    def get_recently_played_tracks(self, limit: int = 50) -> List[Dict]:
        try:
            logger.info(f"Getting {limit} recently played tracks")
            results = self.client.current_user_recently_played(limit=limit)
            
            # The "items" in recently played are play history objects with a "track" field
            tracks = [item["track"] for item in results["items"]]
            
            logger.info(f"Retrieved {len(tracks)} recently played tracks")
            return tracks
        except Exception as e:
            logger.error(f"Error getting recently played tracks: {e}")
            return []
    
    def get_recommendations(
        self,
        seed_tracks: List[str] = None,
        seed_artists: List[str] = None,
        seed_genres: List[str] = None,
        limit: int = 50,
        **kwargs
    ) -> List[Dict]:
        """
        Get track recommendations based on seed tracks, artists, and genres.
        
        Args:
            seed_tracks: List of Spotify track IDs to use as seeds (max 5 total seeds)
            seed_artists: List of Spotify artist IDs to use as seeds
            seed_genres: List of genres to use as seeds
            limit: Maximum number of recommendations to return
            **kwargs: Additional parameters for recommendation tuning:
                      - target_acousticness, target_danceability, etc.
                      - min_* and max_* variants for ranges
        
        Returns:
            List of recommended track objects
        """
        # Ensure we don't exceed the 5-seed limit
        seed_tracks = seed_tracks or []
        seed_artists = seed_artists or []
        seed_genres = seed_genres or []
        
        if len(seed_tracks) + len(seed_artists) + len(seed_genres) > 5:
            logger.warning("Too many seeds provided, limiting to 5 total")
            # Prioritize tracks, then artists, then genres
            total_allowed = 5
            if len(seed_tracks) > total_allowed:
                seed_tracks = seed_tracks[:total_allowed]
                seed_artists = []
                seed_genres = []
            else:
                total_allowed -= len(seed_tracks)
                if len(seed_artists) > total_allowed:
                    seed_artists = seed_artists[:total_allowed]
                    seed_genres = []
                else:
                    total_allowed -= len(seed_artists)
                    seed_genres = seed_genres[:total_allowed]
        
        try:
            logger.info(
                f"Getting recommendations with {len(seed_tracks)} tracks, "
                f"{len(seed_artists)} artists, {len(seed_genres)} genres"
            )
            
            results = self.client.recommendations(
                seed_tracks=seed_tracks,
                seed_artists=seed_artists,
                seed_genres=seed_genres,
                limit=limit,
                **kwargs
            )
            
            tracks = results["tracks"]
            logger.info(f"Retrieved {len(tracks)} recommended tracks")
            return tracks
        except Exception as e:
            logger.error(f"Error getting recommendations: {e}")
            return []
    
    def create_playlist(
        self,
        name: str,
        description: str = "",
        public: bool = False
    ) -> Optional[Dict]:
        """
        Create a new Spotify playlist.
        
        Args:
            name: Name of the playlist
            description: Description of the playlist
            public: Whether the playlist should be public
        
        Returns:
            Playlist object if successful, None otherwise
        """
        try:
            logger.info(f"Creating playlist '{name}'")
            playlist = self.client.user_playlist_create(
                user=self.user_id,
                name=name,
                public=public,
                description=description
            )
            logger.info(f"Created playlist: {playlist['id']}")
            return playlist
        except Exception as e:
            logger.error(f"Error creating playlist: {e}")
            return None
    
    def add_tracks_to_playlist(
        self,
        playlist_id: str,
        track_uris: List[str]
    ) -> bool:
        if not track_uris:
            logger.warning("No tracks to add to playlist")
            return False
        
        try:
            # Spotify API has a limit of 100 tracks per request
            chunk_size = 100
            for i in range(0, len(track_uris), chunk_size):
                chunk = track_uris[i:i + chunk_size]
                logger.info(f"Adding {len(chunk)} tracks to playlist {playlist_id}")
                self.client.playlist_add_items(playlist_id, chunk)
            
            logger.info(f"Added {len(track_uris)} tracks to playlist {playlist_id}")
            return True
        except Exception as e:
            logger.error(f"Error adding tracks to playlist: {e}")
            return False
    
    def get_playlist_tracks(self, playlist_id: str) -> List[Dict]:
        try:
            logger.info(f"Getting tracks from playlist {playlist_id}")
            results = self.client.playlist_items(playlist_id)
            tracks = results["items"]
            
            # Handle pagination (if the playlist has more than 100 tracks)
            while results["next"]:
                results = self.client.next(results)
                tracks.extend(results["items"])
            
            # Extract the track objects from the playlist items
            track_objects = [item["track"] for item in tracks if item["track"]]
            
            logger.info(f"Retrieved {len(track_objects)} tracks from playlist {playlist_id}")
            return track_objects
        except Exception as e:
            logger.error(f"Error getting playlist tracks: {e}")
            return []
    
    def get_available_genres(self) -> List[str]:
        try:
            results = self.client.recommendation_genre_seeds()
            genres = results["genres"]
            logger.info(f"Retrieved {len(genres)} available genres")
            return genres
        except Exception as e:
            logger.error(f"Error getting available genres: {e}")
            return []

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    api = SpotifyAPI()
    
    # Get top tracks
    top_tracks = api.get_top_tracks(time_range="short_term", limit=10)
    print(f"Top tracks: {len(top_tracks)}")

    if top_tracks:
        seed_track_ids = [track["id"] for track in top_tracks[:2]]
        recommendations = api.get_recommendations(seed_tracks=seed_track_ids, limit=10)
        print(f"Recommendations: {len(recommendations)}")