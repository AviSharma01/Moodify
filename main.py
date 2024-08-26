from src.api.spotify_api import SpotifyAPI
from src.data.data_processor import DataProcessor
import pandas as pd
import spotipy

import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    try:
        # Initialize SpotifyAPI and DataProcessor
        api = SpotifyAPI()
        processor = DataProcessor()
        
        # Test the connection
        user = api.sp.current_user()
        logger.info(f"Connected to Spotify as {user['display_name']}")

        # Get recent, top, and saved tracks
        logger.info("Fetching recent tracks...")
        recent_tracks = api.get_recently_played(limit=50)
        logger.info("Fetching top tracks...")
        top_tracks = api.get_top_tracks(limit=50)
        logger.info("Fetching saved tracks...")
        saved_tracks = api.get_saved_tracks(limit=50)

        # Process track data
        logger.info("Processing track data...")
        recent_df = processor.process_track_data(recent_tracks, 'recent')
        top_df = processor.process_track_data(top_tracks, 'top')
        saved_df = processor.process_track_data(saved_tracks, 'saved')

        # Combine all tracks
        all_tracks = pd.concat([recent_df, top_df, saved_df])
        all_tracks = all_tracks.drop_duplicates(subset='id')
        logger.info(f"Total unique tracks: {len(all_tracks)}")

        # Get audio features for all unique tracks
        logger.info("Fetching audio features...")
        track_ids = all_tracks['id'].tolist()
        audio_features = api.get_track_features(track_ids)
        logger.info(f"Retrieved audio features for {len(audio_features)} tracks")

        # Process audio features
        audio_features_df = processor.process_audio_features(audio_features)

        # Combine track info with audio features
        final_df = processor.combine_track_and_audio_data(all_tracks, audio_features_df)

        logger.info("Data processing complete.")
        logger.info(f"Final dataset shape: {final_df.shape}")

        # Display sample of processed data
        print("\nSample of processed data:")
        print(final_df.head())

        print("\nColumns:", final_df.columns.tolist())

        # TODO: Add code here for further analysis, playlist generation, etc.

    except Exception as e:
        logger.error(f"An error occurred: {str(e)}", exc_info=True)

if __name__ == "__main__":
    main()