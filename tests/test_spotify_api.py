import pytest
from api.spotify_api import SpotifyAPI
print("Module imported successfully")

# Fixture to initialize SpotifyAPI
@pytest.fixture
def spotify_api():
    config_file_path = 'config/config.ini'  # Ensure this path is correct
    return SpotifyAPI(config_file=config_file_path)

def test_get_user_id(spotify_api):
    user_id = spotify_api.get_user_id()
    assert user_id is not None, "Failed to fetch user ID"

def test_playlist_management(spotify_api):
    user_id = spotify_api.get_user_id()
    playlist_id = spotify_api.check_playlist_exists(user_id)
    if not playlist_id:
        playlist_id = spotify_api.create_playlist(user_id, name="Test Playlist", description="A test playlist created for testing.")
    assert playlist_id is not None, "Failed to manage playlist"

def test_get_user_top_tracks(spotify_api):
    top_tracks = spotify_api.get_user_top_tracks(limit=10)
    assert top_tracks is not None, "Failed to fetch top tracks"
    assert len(top_tracks) > 0, "Top tracks should not be empty"

def test_get_audio_features(spotify_api):
    top_tracks = spotify_api.get_user_top_tracks(limit=10)
    if top_tracks:
        audio_features = spotify_api.get_audio_features(top_tracks)
        assert audio_features is not None, "Failed to fetch audio features"
        assert len(audio_features) == len(top_tracks), "Mismatch in number of tracks and audio features retrieved"
