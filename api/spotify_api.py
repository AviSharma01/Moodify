import configparser
import spotipy
from spotipy.oauth2 import SpotifyOAuth

class SpotifyAPI:
    def __init__(self, config_file):
        config = configparser.ConfigParser()
        if not config.read(config_file):
            raise FileNotFoundError("Configuration file not found.")

        self.client_id = config.get('spotify', 'client_id')
        self.client_secret = config.get('spotify', 'client_secret')
        self.redirect_uri = config.get('spotify', 'redirect_uri')
        self.playlist_name = config.get('playlist', 'name')

        # Set the scope to request the correct permissions
        self.scope = "user-top-read playlist-modify-private user-read-private"
        
        # Initialize Spotify client with OAuth for user authentication
        self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
            client_id=self.client_id,
            client_secret=self.client_secret,
            redirect_uri=self.redirect_uri,
            scope=self.scope
        ))

    def get_user_id(self):
        return self.sp.current_user()['id']

    def check_playlist_exists(self, user_id):
        playlists = self.sp.user_playlists(user_id)
        for playlist in playlists['items']:
            if playlist['name'] == self.playlist_name:
                return playlist['id']
        return None

    def create_playlist(self, user_id, name, description='', public=False):
        return self.sp.user_playlist_create(user=user_id, name=name, public=public, description=description)['id']

    def get_playlist_tracks(self, playlist_id):
        tracks = []
        response = self.sp.playlist_tracks(playlist_id)
        while response:
            tracks += response['items']
            response = self.sp.next(response)
        return tracks

    def get_user_top_tracks(self, limit=20, time_range='short_term'):
        return [track['id'] for track in self.sp.current_user_top_tracks(limit=limit, time_range=time_range)['items']]

    def get_audio_features(self, track_ids):
        return {track['id']: track for track in self.sp.audio_features(track_ids) if track is not None}
