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
                show_dialog=True,
                open_browser=True  # Ensure browser opens for auth
            )
            
            # Force token refresh to ensure we have a valid token
            token_info = auth_manager.get_cached_token()
            if not token_info or auth_manager.is_token_expired(token_info):
                logger.info("Getting new token or refreshing existing token")
                if not token_info:
                    auth_manager.get_access_token(as_dict=False)
                else:
                    auth_manager.refresh_access_token(token_info['refresh_token'])
            
            client = spotipy.Spotify(auth_manager=auth_manager)
            
            # Test the connection and token
            client.current_user()
            logger.info("Successfully authenticated with Spotify")
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
        
    def get_simple_recommendations(self, limit=25):
        """Attempt to get some basic recommendations without complex seeds."""
        try:
            # Try with a simple popular genre
            logger.info("Getting simple recommendations with popular genre")
            
            # Use a single popular genre
            results = self.client.recommendations(
                seed_genres=["pop"],
                limit=limit,
                min_popularity=50  # Fairly popular tracks
            )
            
            tracks = results["tracks"]
            logger.info(f"Retrieved {len(tracks)} recommended tracks")
            return tracks
        except Exception as e:
            logger.error(f"Error getting simple recommendations: {e}")
            return []
    
    def get_recommendations_via_search(self, seed_tracks=None, seed_artists=None, limit=50):
        """Get recommendations by using the Search API as a workaround"""
        try:
            recommendations = []
            
            if seed_artists:
                for artist_id in seed_artists[:2]:
                    artist = self.client.artist(artist_id)
                    artist_name = artist['name']
                    
                    results = self.client.search(f"artist:{artist_name}", type="track", limit=limit//2)
                    if results and 'tracks' in results and 'items' in results['tracks']:
                        recommendations.extend(results['tracks']['items'])
            
            if seed_tracks and len(recommendations) < limit:
                for track_id in seed_tracks[:2]:
                    track = self.client.track(track_id)
                    track_name = track['name']
                    artist_name = track['artists'][0]['name']
                    
                    genres = " ".join(self.client.artist(track['artists'][0]['id']).get('genres', [])[:3])
                    query = f"artist:{artist_name} genre:{genres}"
                    results = self.client.search(query, type="track", limit=limit//2)
                    if results and 'tracks' in results and 'items' in results['tracks']:
                        recommendations.extend(results['tracks']['items'])
            
            unique_recommendations = []
            seen_ids = set()
            for track in recommendations:
                if track['id'] not in seen_ids:
                    seen_ids.add(track['id'])
                    unique_recommendations.append(track)
            
            limited_recommendations = unique_recommendations[:limit]
            logger.info(f"Retrieved {len(limited_recommendations)} recommendations via search")
            return limited_recommendations
        except Exception as e:
            logger.error(f"Error getting recommendations via search: {e}")
            return []
        
    def get_discovery_recommendations(self, seed_tracks=None, seed_artists=None, limit=20):
        """
        Get recommendations focused on tracks I haven't heard recently,
        enhanced with audio feature analysis for better musical matching.
        Includes a mix of new discoveries and a few familiar tracks.
        
        Args:
            seed_tracks: List of Spotify track IDs to use as seeds
            seed_artists: List of Spotify artist IDs to use as seeds
            limit: Maximum number of tracks to return (default: 20)
            
        Returns:
            List of track objects representing mostly new discoveries with some familiar tracks
        """
        try:
            logger.info("Building list of tracks to exclude from recommendations...")
            exclude_tracks = set()
            
            logger.info("Getting recently played tracks...")
            recent_plays = self.client.current_user_recently_played(limit=50)
            recent_tracks_list = []  # Store for later when we add familiar tracks
            for item in recent_plays['items']:
                exclude_tracks.add(item['track']['id'])
                recent_tracks_list.append(item['track'])

            try:
                logger.info("Getting saved tracks...")
                saved_tracks = self.client.current_user_saved_tracks(limit=50)
                for item in saved_tracks['items']:
                    exclude_tracks.add(item['track']['id'])
            except Exception as e:
                logger.warning(f"Couldn't get saved tracks: {e}")

            logger.info("Getting tracks from recent playlists...")
            playlists = self.client.current_user_playlists(limit=10)
            for playlist in playlists['items']:
                if playlist['owner']['id'] == self.user_id:
                    try:
                        logger.info(f"Getting tracks from playlist: {playlist['name']}")
                        tracks = self.client.playlist_items(playlist['id'], limit=30)
                        for item in tracks['items']:
                            if item['track'] and item['track']['id']:
                                exclude_tracks.add(item['track']['id'])
                    except Exception as e:
                        logger.warning(f"Couldn't get tracks from playlist {playlist['name']}: {e}")
            
            logger.info(f"Built exclusion set with {len(exclude_tracks)} track IDs")
            
            recommendations = []
            
            seed_audio_features = []
            if seed_tracks:
                try:
                    logger.info("Analyzing audio features of seed tracks...")
                    seed_audio_features = self.client.audio_features(seed_tracks)
                    seed_audio_features = [f for f in seed_audio_features if f] 
                    
                    if seed_audio_features:
                        avg_danceability = sum(f['danceability'] for f in seed_audio_features) / len(seed_audio_features)
                        avg_energy = sum(f['energy'] for f in seed_audio_features) / len(seed_audio_features)
                        avg_valence = sum(f['valence'] for f in seed_audio_features) / len(seed_audio_features)
                        avg_acousticness = sum(f['acousticness'] for f in seed_audio_features) / len(seed_audio_features)
                        
                        logger.info(f"Seed tracks audio profile - Dance: {avg_danceability:.2f}, Energy: {avg_energy:.2f}, Mood: {avg_valence:.2f}, Acoustic: {avg_acousticness:.2f}")
                except Exception as e:
                    logger.warning(f"Error analyzing seed track audio features: {e}")
            
            if seed_artists:
                for artist_id in seed_artists[:2]:
                    try:
                        artist = self.client.artist(artist_id)
                        artist_name = artist['name']
                        logger.info(f"Finding discoveries related to artist: {artist_name}")
                        
                        genres = artist.get('genres', [])
                        genre_str = " ".join([f"genre:{g}" for g in genres[:2]]) if genres else ""
                        
                        related_artists = self.client.artist_related_artists(artist_id)['artists'][:5]
                        logger.info(f"Found {len(related_artists)} related artists")
                        
                        for related in related_artists:
                            related_name = related['name']
                            query = f"artist:{related_name}"
                            if genre_str:
                                query += f" {genre_str}"
                                
                            logger.info(f"Searching for tracks from: {related_name}")
                            results = self.client.search(query, type="track", limit=15)
                            if results and 'tracks' in results and 'items' in results['tracks']:
                                new_tracks = [t for t in results['tracks']['items'] 
                                            if t['id'] not in exclude_tracks]
                                logger.info(f"Found {len(new_tracks)} new tracks from {related_name}")
                                recommendations.extend(new_tracks)
                    except Exception as e:
                        logger.warning(f"Error processing artist {artist_id}: {e}")
            
            if seed_tracks and len(recommendations) < limit * 2:
                for track_id in seed_tracks[:2]:
                    try:
                        track = self.client.track(track_id)
                        track_name = track['name']
                        artist_id = track['artists'][0]['id']

                        artist = self.client.artist(artist_id)
                        artist_name = artist['name']
                        genres = artist.get('genres', [])
                        
                        logger.info(f"Finding discoveries similar to track: {track_name} by {artist_name}")
                        
                        if genres:
                            for genre in genres[:2]:
                                query = f"genre:{genre} NOT artist:{artist_name}"
                                logger.info(f"Searching with query: {query}")
                                results = self.client.search(query, type="track", limit=15)
                                if results and 'tracks' in results and 'items' in results['tracks']:
                                    new_tracks = [t for t in results['tracks']['items'] 
                                                if t['id'] not in exclude_tracks]
                                    logger.info(f"Found {len(new_tracks)} new tracks for genre: {genre}")
                                    recommendations.extend(new_tracks)
                    except Exception as e:
                        logger.warning(f"Error processing track {track_id}: {e}")

            if len(recommendations) < limit:
                logger.info("Not enough recommendations, searching by top genres")
                try:
                    top_artists = self.client.current_user_top_artists(limit=5)
                    all_genres = []
                    for artist in top_artists['items']:
                        all_genres.extend(artist.get('genres', []))
                    
                    unique_genres = list(set(all_genres))[:5]
                    logger.info(f"Using top genres: {', '.join(unique_genres)}")

                    for genre in unique_genres:
                        query = f"genre:{genre}"
                        results = self.client.search(query, type="track", limit=15)
                        if results and 'tracks' in results and 'items' in results['tracks']:
                            new_tracks = [t for t in results['tracks']['items'] 
                                        if t['id'] not in exclude_tracks]
                            logger.info(f"Found {len(new_tracks)} new tracks for genre: {genre}")
                            recommendations.extend(new_tracks)
                except Exception as e:
                    logger.warning(f"Error searching by genres: {e}")
            
            unique_recommendations = []
            seen_ids = set()
            for track in recommendations:
                if track['id'] not in seen_ids and track['id'] not in exclude_tracks:
                    seen_ids.add(track['id'])
                    unique_recommendations.append(track)
            
            if seed_audio_features and unique_recommendations:
                try:
                    logger.info("Scoring recommendations by audio feature similarity...")
                    chunk_size = 50
                    all_features = []
                    track_ids_to_features = {}
                    
                    for i in range(0, len(unique_recommendations), chunk_size):
                        chunk = unique_recommendations[i:min(i + chunk_size, len(unique_recommendations))]
                        chunk_ids = [track['id'] for track in chunk]
                        chunk_features = self.client.audio_features(chunk_ids)
                        
                        for j, features in enumerate(chunk_features):
                            if features:
                                track_ids_to_features[chunk[j]['id']] = features
                    
                    scored_recommendations = []
                    for track in unique_recommendations:
                        features = track_ids_to_features.get(track['id'])
                        if features:
                            similarity_score = 0
                            
                            if len(seed_audio_features) > 0:
                                dance_diff = abs(features['danceability'] - avg_danceability)
                                energy_diff = abs(features['energy'] - avg_energy)
                                valence_diff = abs(features['valence'] - avg_valence)
                                acousticness_diff = abs(features['acousticness'] - avg_acousticness)
                                
                                similarity_score = (
                                    (1 - dance_diff) * 0.25 +
                                    (1 - energy_diff) * 0.25 +
                                    (1 - valence_diff) * 0.25 +
                                    (1 - acousticness_diff) * 0.25
                                )
                            
                            popularity_score = 1 - abs(track.get('popularity', 50) - 60) / 100
                            
                            final_score = (similarity_score * 0.8) + (popularity_score * 0.2) if similarity_score > 0 else popularity_score
                            
                            scored_recommendations.append((track, final_score))
                        else:
                            popularity_score = 1 - abs(track.get('popularity', 50) - 60) / 100
                            scored_recommendations.append((track, popularity_score))
                    
                    scored_recommendations.sort(key=lambda x: x[1], reverse=True)
                    
                    sorted_recommendations = [t[0] for t in scored_recommendations]
                    logger.info(f"Sorted {len(sorted_recommendations)} tracks using audio feature matching")
                except Exception as e:
                    logger.warning(f"Error during audio feature analysis: {e}")
                    sorted_recommendations = sorted(
                        unique_recommendations,
                        key=lambda t: abs(t.get('popularity', 50) - 60)  
                    )
            else:
                sorted_recommendations = sorted(
                    unique_recommendations,
                    key=lambda t: abs(t.get('popularity', 50) - 60)  
                )
            
            if len(sorted_recommendations) > 0:
                discovery_limit = int(limit * 0.85)
                familiar_limit = limit - discovery_limit
                
                diverse_recommendations = sorted_recommendations[:discovery_limit]
                
                try:
                    familiar_candidates = []
                    for track in recent_tracks_list[:20]:  
                        if track and 40 <= track.get('popularity', 0) <= 85:
                            familiar_candidates.append(track)
                    
                    if familiar_candidates:
                        import random
                        familiar_tracks = random.sample(
                            familiar_candidates, 
                            min(familiar_limit, len(familiar_candidates))
                        )
                        diverse_recommendations.extend(familiar_tracks)
                        logger.info(f"Added {len(familiar_tracks)} familiar tracks from recent listening")
                except Exception as e:
                    logger.warning(f"Could not add familiar tracks: {e}")
                    diverse_recommendations = sorted_recommendations[:limit]
            else:
                diverse_recommendations = sorted_recommendations[:limit]
            
            logger.info(f"Retrieved {len(diverse_recommendations)} recommendations (mix of discoveries and familiar tracks)")
            return diverse_recommendations
        except Exception as e:
            logger.error(f"Error getting discovery recommendations: {e}")
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
        (Note: This endpoint is deprecated but included for compatibility)
        
        Args:
            seed_tracks: List of Spotify track IDs to use as seeds
            seed_artists: List of Spotify artist IDs to use as seeds
            seed_genres: List of genres to use as seeds
            limit: Maximum number of recommendations to return
            **kwargs: Additional parameters for recommendation tuning
            
        Returns:
            List of recommended track objects
        """
        # Ensure we don't exceed the 5-seed limit
        seed_tracks = seed_tracks or []
        seed_artists = seed_artists or []
        seed_genres = seed_genres or []
        
        logger.info(f"DEBUG: Raw seed tracks: {seed_tracks}")
        logger.info(f"DEBUG: Raw seed artists: {seed_artists}")
        
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
            
            # Log the exact parameters being sent to the API
            params = {
                "seed_tracks": seed_tracks,
                "seed_artists": seed_artists,
                "seed_genres": seed_genres or None,
                "limit": limit
            }
            params.update(kwargs)
            logger.info(f"DEBUG: API parameters: {params}")
            
            results = self.client.recommendations(
                seed_tracks=seed_tracks,
                seed_artists=seed_artists,
                seed_genres=seed_genres if seed_genres else None,
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