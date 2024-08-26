from spotipy.oauth2 import SpotifyOAuth
from spotipy.cache_handler import CacheFileHandler
import configparser
import spotipy
import os

class SpotifyAPI:
    def __init__(self):
        config = configparser.ConfigParser()
        config.read('config/config.ini')
        
        cache_path = '.cache-spotify'
        if os.path.exists(cache_path):
            os.remove(cache_path)  # Remove the cache file to force a new authentication

        self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
            client_id=config['spotify']['client_id'],
            client_secret=config['spotify']['client_secret'],
            redirect_uri=config['spotify']['redirect_uri'],
            scope="user-read-recently-played user-top-read user-library-read",
            cache_handler=CacheFileHandler(cache_path=cache_path),
            open_browser=True
        ))

    def get_recently_played(self, limit=50):
        return self.sp.current_user_recently_played(limit=limit)

    def get_top_tracks(self, limit=50, time_range='short_term'):
        return self.sp.current_user_top_tracks(limit=limit, time_range=time_range)

    def get_saved_tracks(self, limit=50):
        return self.sp.current_user_saved_tracks(limit=limit)

    def get_track_features(self, track_ids):
        features = []
        for i in range(0, len(track_ids), 100):
            batch = track_ids[i:i+100]
            batch_features = self.sp.audio_features(batch)
            features.extend(batch_features)
        return features