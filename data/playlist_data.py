import random
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

class GenrePlaylist:
    def __init__(self, genre_name, playlist_name, min_plays=5):
        self.genre_name = genre_name
        self.playlist_name = playlist_name
        self.min_plays = min_plays
        self.sp = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials())

    def get_genre_top_tracks(self, time_range='short_term', limit=20):
        """
        Get the top tracks for a given genre and time range from Spotify.
        """
        # Get genre ID
        genre_results = self.sp.search(q='genre:' + self.genre_name, type='genre')
        if genre_results['genres']['items']:
            genre_id = genre_results['genres']['items'][0]['id']
        else:
            raise ValueError(f"Genre '{self.genre_name}' not found on Spotify.")

        # Get top tracks for the genre and time range
        track_uris = []
        results = self.sp.search(q='genre:' + self.genre_name, type='track', limit=50)
        tracks = results['tracks']['items']
        random.shuffle(tracks)
        for track in tracks:
            # Check if the track meets the minimum play count requirement
            if track['popularity'] >= self.min_plays:
                track_uris.append(track['uri'])
            if len(track_uris) >= limit:
                break

        return track_uris

    def create_playlist(self, public=False):
        """
        Create a new playlist on the current user's Spotify account.
        """
        new_playlist = self.sp.user_playlist_create(user='', name=self.playlist_name, public=public)
        return new_playlist['id']

    def add_tracks_to_playlist(self, playlist_id, track_uris):
        """
        Add a list of track URIs to a playlist.
        """
        existing_tracks = set(self.sp.playlist_tracks(playlist_id)['items'])
        tracks_to_add = [uri for uri in track_uris if uri not in existing_tracks]
        if tracks_to_add:
            self.sp.playlist_add_items(playlist_id, tracks_to_add)

        return len(tracks_to_add)
