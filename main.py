#!/usr/bin/env python
"""
Spotify Weekly Playlist Generator

This script automatically creates a personalized Spotify playlist
based on a user's recent listening habits, excluding songs from previous playlists.
It focuses on discovering new music that matches the user's taste profile.
"""

import logging
import argparse
from datetime import datetime
from dotenv import load_dotenv
import os
from email_notifier import send_email

from src.api.spotify_api import SpotifyAPI
from src.data.data_processor import DataProcessor
from data.playlist_data import PlaylistTracker, PlaylistData

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("spotify_playlist.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("spotify_playlist")

load_dotenv()

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Generate a weekly Spotify playlist')
    parser.add_argument('--name', type=str, help='Custom playlist name (default: Weekly Discoveries - YYYY-MM-DD)')
    parser.add_argument('--tracks', type=int, default=20, help='Number of tracks to include (default: 20)')
    parser.add_argument('--public', action='store_true', help='Make the playlist public (default: private)')
    parser.add_argument('--dry-run', action='store_true', help='Run without creating a playlist')
    return parser.parse_args()

def generate_playlist():
    """Generate a weekly Spotify playlist of music discoveries."""
    args = parse_args()
    
    try:
        logger.info("Initializing components...")
        spotify = SpotifyAPI()
        processor = DataProcessor()
        tracker = PlaylistTracker()
        
        logger.info("Retrieving user listening data...")
        top_tracks = spotify.get_top_tracks(time_range="short_term", limit=50)
        recent_tracks = spotify.get_recently_played_tracks(limit=50)
        
        if not top_tracks and not recent_tracks:
            logger.error("No listening data available. Exiting.")
            return None
        
        logger.info("Selecting seeds for recommendations...")
        seed_tracks, seed_artists = processor.select_seed_tracks_and_artists(
            top_tracks=top_tracks,
            recent_tracks=recent_tracks,
            max_seed_tracks=3,
            max_seed_artists=2
        )
        
        logger.info("Getting discovery recommendations...")
        recommendations = spotify.get_discovery_recommendations(
            seed_tracks=seed_tracks,
            seed_artists=seed_artists,
            limit=args.tracks * 2  # Get more than needed for better filtering
        )
        
        if not recommendations:
            logger.info("Trying search-based recommendations as fallback")
            recommendations = spotify.get_recommendations_via_search(
                seed_tracks=seed_tracks,
                seed_artists=seed_artists,
                limit=args.tracks * 2
            )
        
        if not recommendations:
            logger.info("Trying regular recommendations as final fallback")
            try:
                recommendations = spotify.get_recommendations(
                    seed_tracks=seed_tracks,
                    seed_artists=seed_artists,
                    limit=args.tracks * 2,
                    target_popularity=70
                )
            except Exception as e:
                logger.warning(f"Recommendations API failed: {e}")
        
        if not recommendations:
            logger.error("No recommendations available. Exiting.")
            return None
        
        logger.info("Retrieving previous playlist tracks...")
        previous_track_ids = set(tracker.get_recent_track_ids(weeks=1))
        
        logger.info("Filtering recommendations...")
        filtered_tracks = processor.filter_tracks(
            tracks=recommendations,
            exclude_track_ids=previous_track_ids
        )
        
        playlist_tracks = filtered_tracks[:args.tracks]
        
        if not playlist_tracks:
            logger.warning("No tracks available after filtering. Using unfiltered recommendations.")
            playlist_tracks = recommendations[:args.tracks]
        
        if args.name:
            playlist_name = args.name
        else:
            date_str = datetime.now().strftime("%Y-%m-%d")
            playlist_name = f"Weekly Discoveries - {date_str}"
        
        playlist_description = (
            "Personalized music discoveries based on your listening profile. "
            f"Created on {datetime.now().strftime('%Y-%m-%d')}."
        )
        
        if args.dry_run:
            logger.info(f"DRY RUN: Would create playlist '{playlist_name}' with {len(playlist_tracks)} tracks")
            for i, track in enumerate(playlist_tracks):
                artists = ", ".join([artist["name"] for artist in track["artists"]])
                logger.info(f"  {i+1}. {track['name']} - {artists}")
            
            # Add email sending for dry run testing
            gmail_user = os.environ.get("GMAIL_USER")
            gmail_app_password = os.environ.get("GMAIL_APP_PASSWORD")
            recipient = os.environ.get("NOTIFICATION_EMAIL")
            
            if gmail_user and gmail_app_password and recipient:
                # Format playlist info for email
                subject = f"[TEST] Your Weekly Spotify Playlist: {playlist_name}"
                
                tracks_preview = "\n".join([
                    f"{i+1}. {track['name']} - {', '.join([artist['name'] for artist in track['artists']])}" 
                    for i, track in enumerate(playlist_tracks[:5])
                ])
                
                body = f"""
This is a TEST email - No playlist was actually created.

Your weekly Spotify playlist "{playlist_name}" would have been created!

Playlist Details:
- {len(playlist_tracks)} tracks of fresh music discoveries
- Test run on {datetime.now().strftime('%Y-%m-%d')}

Featured tracks:
{tracks_preview}

In a real run, you would be able to listen to your playlist with a link.

Enjoy your music discoveries!

--
Moodify
                """
                
                send_email(subject, body, recipient, gmail_user, gmail_app_password)
                logger.info(f"Test email notification sent to {recipient}")
            else:
                logger.warning("Test email notification not sent: missing email credentials")
            
            # Return mock playlist info for dry runs
            return {
                'id': 'dry-run',
                'name': playlist_name,
                'track_count': len(playlist_tracks),
                'tracks': [{'name': t['name'], 'artists': [a['name'] for a in t['artists']]} for t in playlist_tracks],
                'dry_run': True
            }
        
        logger.info(f"Creating playlist '{playlist_name}' with {len(playlist_tracks)} tracks...")
        playlist = spotify.create_playlist(
            name=playlist_name,
            description=playlist_description,
            public=args.public
        )
        
        if not playlist:
            logger.error("Failed to create playlist. Exiting.")
            return None
        
        track_uris = [track["uri"] for track in playlist_tracks]
        track_ids = [track["id"] for track in playlist_tracks]
        
        success = spotify.add_tracks_to_playlist(
            playlist_id=playlist["id"],
            track_uris=track_uris
        )
        
        if not success:
            logger.error("Failed to add tracks to playlist.")
            return None
        
        tracker.add_playlist(
            playlist_id=playlist["id"],
            name=playlist_name,
            track_ids=track_ids,
            metadata={
                "seed_tracks": seed_tracks,
                "seed_artists": seed_artists,
                "filter_count": len(previous_track_ids)
            }
        )
        
        logger.info(f"Successfully created playlist: {playlist_name} ({playlist['id']})")
        logger.info(f"Link: https://open.spotify.com/playlist/{playlist['id']}")
        
        # Get email credentials from environment variables
        gmail_user = os.environ.get("GMAIL_USER")
        gmail_app_password = os.environ.get("GMAIL_APP_PASSWORD")
        recipient = os.environ.get("NOTIFICATION_EMAIL")
        
        if gmail_user and gmail_app_password and recipient:
            # Format playlist info for email
            subject = f"Your Weekly Spotify Playlist: {playlist_name}"
            
            tracks_preview = "\n".join([
                f"{i+1}. {track['name']} - {', '.join([artist['name'] for artist in track['artists']])}" 
                for i, track in enumerate(playlist_tracks[:5])
            ])
            
            body = f"""
Your weekly Spotify playlist "{playlist_name}" has been created!

Playlist Details:
- {len(playlist_tracks)} tracks of fresh music discoveries
- Created on {datetime.now().strftime('%Y-%m-%d')}

Featured tracks:
{tracks_preview}

Listen to your playlist here:
https://open.spotify.com/playlist/{playlist['id']}

Enjoy your music discoveries!

--
Moodify
            """
            
            send_email(subject, body, recipient, gmail_user, gmail_app_password)
            logger.info(f"Email notification sent to {recipient}")
        else:
            logger.warning("Email notification not sent: missing email credentials")
        
        return {
            'id': playlist['id'],
            'name': playlist_name,
            'track_count': len(playlist_tracks),
            'tracks': [{'name': t['name'], 'artists': [a['name'] for a in t['artists']]} for t in playlist_tracks[:5]],  # First 5 tracks for the email
            'url': f"https://open.spotify.com/playlist/{playlist['id']}"
        }
        
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}", exc_info=True)
        return None

if __name__ == "__main__":
    logger.info("Starting Spotify Weekly Playlist Generator")
    result = generate_playlist()
    if result:
        if result.get('dry_run'):
            logger.info("Dry run completed successfully")
        else:
            logger.info(f"Playlist generation completed successfully: {result['name']} ({result['id']})")
    else:
        logger.error("Playlist generation failed")