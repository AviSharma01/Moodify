"""
Tests for the Spotify API wrapper.
"""

import os
import unittest
from unittest.mock import patch, MagicMock

import pytest
from src.api.spotify_api import SpotifyAPI

class TestSpotifyAPI(unittest.TestCase):
    
    @patch('spotipy.Spotify')
    @patch('spotipy.oauth2.SpotifyOAuth')
    def test_initialization(self, mock_oauth, mock_spotify):
        """Test that the SpotifyAPI initializes correctly."""
        mock_spotify_instance = MagicMock()
        mock_spotify_instance.current_user.return_value = {"id": "test_user"}
        mock_spotify.return_value = mock_spotify_instance
        
        api = SpotifyAPI(
            client_id="test_client_id",
            client_secret="test_client_secret",
            redirect_uri="http://localhost:8888/callback"
        )
        
        mock_spotify.assert_called_once()
        
        self.assertEqual(api.user_id, "test_user")
    
    @patch('spotipy.Spotify')
    @patch('spotipy.oauth2.SpotifyOAuth')
    def test_get_top_tracks(self, mock_oauth, mock_spotify):
        """Test getting top tracks."""
        mock_spotify_instance = MagicMock()
        mock_spotify_instance.current_user.return_value = {"id": "test_user"}
        mock_spotify_instance.current_user_top_tracks.return_value = {
            "items": [
                {"id": "track1", "name": "Track 1"},
                {"id": "track2", "name": "Track 2"}
            ]
        }
        mock_spotify.return_value = mock_spotify_instance
        
        api = SpotifyAPI(
            client_id="test_client_id",
            client_secret="test_client_secret"
        )

        tracks = api.get_top_tracks(limit=2)
        
        mock_spotify_instance.current_user_top_tracks.assert_called_once_with(
            time_range="short_term",
            limit=2
        )
        
        self.assertEqual(len(tracks), 2)
        self.assertEqual(tracks[0]["id"], "track1")
        self.assertEqual(tracks[1]["id"], "track2")
    
    @patch('spotipy.Spotify')
    @patch('spotipy.oauth2.SpotifyOAuth')
    def test_get_recommendations(self, mock_oauth, mock_spotify):
        """Test getting recommendations."""
        mock_spotify_instance = MagicMock()
        mock_spotify_instance.current_user.return_value = {"id": "test_user"}
        mock_spotify_instance.recommendations.return_value = {
            "tracks": [
                {"id": "rec1", "name": "Recommendation 1"},
                {"id": "rec2", "name": "Recommendation 2"}
            ]
        }
        mock_spotify.return_value = mock_spotify_instance

        api = SpotifyAPI(
            client_id="test_client_id",
            client_secret="test_client_secret"
        )

        recommendations = api.get_recommendations(
            seed_tracks=["track1", "track2"],
            seed_artists=["artist1"],
            limit=2,
            target_popularity=50
        )

        mock_spotify_instance.recommendations.assert_called_once_with(
            seed_tracks=["track1", "track2"],
            seed_artists=["artist1"],
            seed_genres=None,
            limit=2,
            target_popularity=50
        )

        self.assertEqual(len(recommendations), 2)
        self.assertEqual(recommendations[0]["id"], "rec1")
        self.assertEqual(recommendations[1]["id"], "rec2")
    
    @patch('spotipy.Spotify')
    @patch('spotipy.oauth2.SpotifyOAuth')
    def test_create_playlist(self, mock_oauth, mock_spotify):
        """Test creating a playlist."""
        mock_spotify_instance = MagicMock()
        mock_spotify_instance.current_user.return_value = {"id": "test_user"}
        mock_spotify_instance.user_playlist_create.return_value = {
            "id": "playlist1",
            "name": "Test Playlist"
        }
        mock_spotify.return_value = mock_spotify_instance
        
        api = SpotifyAPI(
            client_id="test_client_id",
            client_secret="test_client_secret"
        )
        
        playlist = api.create_playlist(
            name="Test Playlist",
            description="A test playlist",
            public=False
        )
        
        mock_spotify_instance.user_playlist_create.assert_called_once_with(
            user="test_user",
            name="Test Playlist",
            public=False,
            description="A test playlist"
        )

        self.assertEqual(playlist["id"], "playlist1")
        self.assertEqual(playlist["name"], "Test Playlist")
    
    @patch('spotipy.Spotify')
    @patch('spotipy.oauth2.SpotifyOAuth')
    def test_add_tracks_to_playlist(self, mock_oauth, mock_spotify):
        mock_spotify_instance = MagicMock()
        mock_spotify_instance.current_user.return_value = {"id": "test_user"}
        mock_spotify_instance.playlist_add_items.return_value = {"snapshot_id": "snapshot1"}
        mock_spotify.return_value = mock_spotify_instance

        api = SpotifyAPI(
            client_id="test_client_id",
            client_secret="test_client_secret"
        )

        success = api.add_tracks_to_playlist(
            playlist_id="playlist1",
            track_uris=["spotify:track:track1", "spotify:track:track2"]
        )

        mock_spotify_instance.playlist_add_items.assert_called_once_with(
            "playlist1",
            ["spotify:track:track1", "spotify:track:track2"]
        )
        
        self.assertTrue(success)
    
    @patch('spotipy.Spotify')
    @patch('spotipy.oauth2.SpotifyOAuth')
    def test_error_handling(self, mock_oauth, mock_spotify):
        """Test error handling."""
        mock_spotify_instance = MagicMock()
        mock_spotify_instance.current_user.return_value = {"id": "test_user"}
        mock_spotify_instance.current_user_top_tracks.side_effect = Exception("API error")
        mock_spotify.return_value = mock_spotify_instance

        api = SpotifyAPI(
            client_id="test_client_id",
            client_secret="test_client_secret"
        )

        tracks = api.get_top_tracks()

        self.assertEqual(tracks, [])
    
    @patch('spotipy.Spotify')
    @patch('spotipy.oauth2.SpotifyOAuth')
    def test_get_recommendations_via_search(self, mock_oauth, mock_spotify):
        """Test the search-based recommendations method."""
        mock_spotify_instance = MagicMock()
        mock_spotify_instance.current_user.return_value = {"id": "test_user"}
        
        mock_spotify_instance.artist.return_value = {
            "id": "artist1", 
            "name": "Test Artist",
            "genres": ["pop", "rock"]
        }
        
        mock_spotify_instance.track.return_value = {
            "id": "track1",
            "name": "Test Track",
            "artists": [{"id": "artist1", "name": "Test Artist"}]
        }
        
        mock_spotify_instance.search.return_value = {
            "tracks": {
                "items": [
                    {"id": "rec1", "name": "Search Result 1", "artists": [{"name": "Artist A"}]},
                    {"id": "rec2", "name": "Search Result 2", "artists": [{"name": "Artist B"}]}
                ]
            }
        }
        
        mock_spotify.return_value = mock_spotify_instance
        
        api = SpotifyAPI(
            client_id="test_client_id",
            client_secret="test_client_secret"
        )
        
        recommendations = api.get_recommendations_via_search(
            seed_tracks=["track1"],
            seed_artists=["artist1"],
            limit=5
        )
        
        mock_spotify_instance.search.assert_called()
        
        self.assertEqual(len(recommendations), 2)
    
    @patch('spotipy.Spotify')
    @patch('spotipy.oauth2.SpotifyOAuth')
    def test_get_discovery_recommendations(self, mock_oauth, mock_spotify):
        """Test the discovery recommendations method."""
        mock_spotify_instance = MagicMock()
        mock_spotify_instance.current_user.return_value = {"id": "test_user"}
        
        mock_spotify_instance.current_user_recently_played.return_value = {
            "items": [
                {"track": {"id": "recent1", "name": "Recent Track 1"}},
                {"track": {"id": "recent2", "name": "Recent Track 2"}}
            ]
        }
        
        mock_spotify_instance.current_user_saved_tracks.return_value = {
            "items": [
                {"track": {"id": "saved1", "name": "Saved Track 1"}},
                {"track": {"id": "saved2", "name": "Saved Track 2"}}
            ]
        }
        
        # Mock user playlists
        mock_spotify_instance.current_user_playlists.return_value = {
            "items": [
                {"id": "playlist1", "name": "Test Playlist 1", "owner": {"id": "test_user"}}
            ]
        }
        
        mock_spotify_instance.playlist_items.return_value = {
            "items": [
                {"track": {"id": "pl_track1", "name": "Playlist Track 1"}},
                {"track": {"id": "pl_track2", "name": "Playlist Track 2"}}
            ]
        }
        
        mock_spotify_instance.artist.return_value = {
            "id": "artist1",
            "name": "Test Artist",
            "genres": ["pop", "rock"]
        }
        
        mock_spotify_instance.track.return_value = {
            "id": "track1",
            "name": "Test Track",
            "artists": [{"id": "artist1", "name": "Test Artist"}]
        }
        
        mock_spotify_instance.artist_related_artists.return_value = {
            "artists": [
                {"id": "related1", "name": "Related Artist 1"},
                {"id": "related2", "name": "Related Artist 2"}
            ]
        }
        
        mock_spotify_instance.current_user_top_artists.return_value = {
            "items": [
                {"id": "top_artist1", "name": "Top Artist 1", "genres": ["pop", "dance"]},
                {"id": "top_artist2", "name": "Top Artist 2", "genres": ["rock", "alternative"]}
            ]
        }
        
        mock_spotify_instance.search.return_value = {
            "tracks": {
                "items": [
                    {"id": "new1", "name": "New Track 1", "artists": [{"name": "New Artist 1"}], "popularity": 60},
                    {"id": "new2", "name": "New Track 2", "artists": [{"name": "New Artist 2"}], "popularity": 70}
                ]
            }
        }
        
        mock_spotify.return_value = mock_spotify_instance
        
        api = SpotifyAPI(
            client_id="test_client_id",
            client_secret="test_client_secret"
        )
        
        recommendations = api.get_discovery_recommendations(
            seed_tracks=["track1"],
            seed_artists=["artist1"],
            limit=5
        )
        
        mock_spotify_instance.current_user_recently_played.assert_called()
        mock_spotify_instance.current_user_saved_tracks.assert_called()
        mock_spotify_instance.current_user_playlists.assert_called()
        mock_spotify_instance.artist_related_artists.assert_called()
        mock_spotify_instance.search.assert_called()
        
        self.assertTrue(len(recommendations) > 0)
        for rec in recommendations:
            self.assertNotIn(rec["id"], ["recent1", "recent2", "saved1", "saved2", "pl_track1", "pl_track2"])
    
    def test_api_permissions_real(self):
        """
        Test real API permissions (requires actual credentials).
        Skip if credentials not available.
        """
        if not os.environ.get("SPOTIFY_CLIENT_ID") or not os.environ.get("SPOTIFY_CLIENT_SECRET"):
            self.skipTest("Spotify credentials not available for real API tests")
        
        try:
            api = SpotifyAPI()
            
            playlists = api.client.current_user_playlists(limit=1)
            self.assertIsNotNone(playlists)
            self.assertIn("items", playlists)
            
            saved_tracks = api.client.current_user_saved_tracks(limit=1)
            self.assertIsNotNone(saved_tracks)
            self.assertIn("items", saved_tracks)
            
            recent = api.client.current_user_recently_played(limit=1)
            self.assertIsNotNone(recent)
            self.assertIn("items", recent)
            
            search_results = api.client.search("genre:pop", type="track", limit=1)
            self.assertIsNotNone(search_results)
            self.assertIn("tracks", search_results)
            
            print("All API permission tests passed")
        except Exception as e:
            self.fail(f"API permission test failed: {str(e)}")
    
    def test_search_capabilities_real(self):
        """
        Test real search capabilities (requires actual credentials).
        Skip if credentials not available.
        """
        if not os.environ.get("SPOTIFY_CLIENT_ID") or not os.environ.get("SPOTIFY_CLIENT_SECRET"):
            self.skipTest("Spotify credentials not available for real API tests")
        
        try:
            api = SpotifyAPI()
            
            # Test artist search
            artist_results = api.client.search("artist:Taylor Swift", type="track", limit=1)
            self.assertIsNotNone(artist_results)
            self.assertIn("tracks", artist_results)
            
            # Test genre search (this may not work directly as Spotify search doesn't directly support genre)
            genre_results = api.client.search("genre:rock", type="track", limit=1)
            self.assertIsNotNone(genre_results)
            
            # Test year search
            year_results = api.client.search("year:2020-2023", type="track", limit=1)
            self.assertIsNotNone(year_results)
            
            # Test NOT operator
            not_results = api.client.search("pop NOT artist:Taylor Swift", type="track", limit=1)
            self.assertIsNotNone(not_results)
            
            print("All search capability tests passed")
        except Exception as e:
            self.fail(f"Search capability test failed: {str(e)}")

if __name__ == "__main__":
    unittest.main()