import configparser
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

class SpotifyAPI:
    def __init__(self, config_file):
        config = configparser.ConfigParser()
        config.read(config_file)

        self.client_id = config.get('spotify', 'client_id')
        self.client_secret = config.get('spotify', 'client_secret')

        self.client_credentials_manager = SpotifyClientCredentials(client_id=self.client_id,
                                                                   client_secret=self.client_secret)
        self.sp = spotipy.Spotify(client_credentials_manager=self.client_credentials_manager)

        self.playlist_name = config.get('playlist', 'name')
        self.min_plays = config.getint('playlist', 'min_plays')

    def check_playlist_exists(self):
        playlists = self.sp.current_user_playlists()
        playlist_id = None
        for playlist in playlists['items']:
            if playlist['name'] == self.playlist_name:
                playlist_id = playlist['id']
                break
        return playlist_id

    def create_playlist(self, description='', public=False):
        new_playlist = self.sp.user_playlist_create(user='', name=self.playlist_name, public=public, description=description)
        return new_playlist['id']

    def get_playlist_tracks(self, playlist_id):
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

    def get_user_top_tracks(self, time_range='short_term', limit=20):
        user_tracks = []
        results = self.sp.current_user_top_tracks(time_range=time_range, limit=limit)
        user_tracks += results['items']
        while results['next']:
            results = self.sp.next(results)
            user_tracks += results['items']
        return user_tracks

    def add_tracks_to_playlist(self, playlist_id, track_uris):
        self.sp.playlist_add_items(playlist_id, track_uris)
        return len(track_uris)

    ''' def search_track(self, track_name, artist_name):
        query = f'track:{track_name} artist:{artist_name}'
        results = self.sp.search(q=query, type='track')
        if results['tracks']['total'] > 0:
            return results['tracks']['items'][0]['uri']
        else:
            return None

    def search_artist(self, artist_name):
        results = self.sp.search(q=f'artist:{artist_name}', type='artist')
        if results['artists']['total'] > 0:
            return results['artists']['items'][0]['uri']
        else:
            return None

    def get_artist_top_tracks(self, artist_uri):
        results = self.sp.artist_top_tracks(artist_uri)
        return results['tracks']

    def get_related_artists(self, artist_uri):
        results = self.sp.artist_related_artists(artist_uri)
        return results['artists'] '''
