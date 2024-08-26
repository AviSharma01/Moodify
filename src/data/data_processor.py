import pandas as pd

class DataProcessor:
    @staticmethod
    def process_track_data(tracks_data, data_type):
        tracks = []
        for item in tracks_data['items']:
            if data_type == 'recent':
                track = item['track']
            elif data_type == 'top':
                track = item
            else:  # saved tracks
                track = item['track']
            
            tracks.append({
                'id': track['id'],
                'name': track['name'],
                'artist': track['artists'][0]['name'],
                'popularity': track.get('popularity', None),
                'type': data_type
            })
        return pd.DataFrame(tracks)

    @staticmethod
    def process_audio_features(audio_features):
        return pd.DataFrame(audio_features)

    @staticmethod
    def combine_track_and_audio_data(tracks_df, audio_features_df):
        return pd.merge(tracks_df, audio_features_df, on='id')