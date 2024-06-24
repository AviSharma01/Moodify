import configparser
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

class SpotifyAPI:
    def __init__(self, config_file):
        # Load and parse configuration file
        config = configparser.ConfigParser()
        config.read(config_file)

        # Retrieve Spotify credentials from the configuration file
        self.client_id = config.get('spotify', 'client_id')
        self.client_secret = config.get('spotify', 'client_secret')

        # Setup the client credentials manager and Spotify client
        self.client_credentials_manager = SpotifyClientCredentials(client_id=self.client_id,
                                                                   client_secret=self.client_secret)
        self.sp = spotipy.Spotify(client_credentials_manager=self.client_credentials_manager)

    def get_user_id(self):
        #Fetches the Spotify user ID for the current authenticated user
        user = self.sp.current_user()
        return user['id']

    def check_playlist_exists(self, user_id):
        #Checks if a specific playlist exists for the given user ID and returns its ID if found.
        playlists = self.sp.user_playlists(user_id)
        playlist_id = None
        for playlist in playlists['items']:
            if playlist['name'] == self.playlist_name:
                playlist_id = playlist['id']
                break
        return playlist_id

    def create_playlist(self, user_id, name, description='', public=False):
        #Creates a new playlist for the user with the given name and description.
        new_playlist = self.sp.user_playlist_create(user=user_id, name=name, public=public, description=description)
        return new_playlist['id']

    def get_playlist_tracks(self, playlist_id):
        #Fetches all tracks in a given playlist by its ID.
        playlist_tracks = []
        offset = 0
        while True:
            tracks = self.sp.playlist_tracks(playlist_id, offset=offset)
            playlist_tracks += tracks['items']
            if tracks['next'] is not None:
                offset += len(tracks['items'])
            else:
                break
        return playlist_tracks

    def get_user_top_tracks(self, limit=20, time_range='short_term'):
        #Fetches the top tracks for the current user based on the specified time range and limit, returning track IDs.
        results = self.sp.current_user_top_tracks(limit=limit, time_range=time_range)
        track_ids = [track['id'] for track in results['items']]
        return track_ids

    def get_audio_features(self, track_ids):
        #Fetches audio features for a list of track IDs and returns a dictionary mapping track IDs to their features.
        audio_features = self.sp.audio_features(track_ids)
        return {track['id']: track for track in audio_features if track is not None}

