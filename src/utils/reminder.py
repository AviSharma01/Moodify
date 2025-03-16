"""
Reminder Utility

This module provides utilities for scheduling and sending notifications
about playlist generation.
"""

import os
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

class NotificationManager:

    
    def __init__(
        self,
        smtp_server: Optional[str] = None,
        smtp_port: Optional[int] = None,
        smtp_username: Optional[str] = None,
        smtp_password: Optional[str] = None,
        from_email: Optional[str] = None,
        to_email: Optional[str] = None
    ):

        self.smtp_server = smtp_server or os.environ.get("NOTIFICATION_SMTP_SERVER")
        self.smtp_port = smtp_port or int(os.environ.get("NOTIFICATION_SMTP_PORT", "587"))
        self.smtp_username = smtp_username or os.environ.get("NOTIFICATION_SMTP_USERNAME")
        self.smtp_password = smtp_password or os.environ.get("NOTIFICATION_SMTP_PASSWORD")
        self.from_email = from_email or os.environ.get("NOTIFICATION_FROM_EMAIL")
        self.to_email = to_email or os.environ.get("NOTIFICATION_TO_EMAIL")
        
        self.email_configured = all([
            self.smtp_server,
            self.smtp_username,
            self.smtp_password,
            self.from_email,
            self.to_email
        ])
        
        if not self.email_configured:
            logger.warning("Email notifications not fully configured")
    
    def send_playlist_created_notification(
        self,
        playlist_id: str,
        playlist_name: str,
        track_count: int
    ) -> bool:
        
        if not self.email_configured:
            logger.info("Email notifications not configured, skipping")
            return False
        
        try:
            subject = f"New Spotify Playlist Created: {playlist_name}"
            
            # Create playlist link
            playlist_url = f"https://open.spotify.com/playlist/{playlist_id}"
            
            # Create email body
            body = f"""
            Your weekly Spotify playlist "{playlist_name}" has been created!
            
            Playlist Details:
            - Name: {playlist_name}
            - Tracks: {track_count}
            - Created: {datetime.now().strftime('%Y-%m-%d %H:%M')}
            
            You can access your playlist here:
            {playlist_url}
            
            Enjoy your music!
            
            --
            Moodify
            """
            
            return self._send_email(subject, body)
            
        except Exception as e:
            logger.error(f"Error sending playlist created notification: {e}")
            return False
    
    def send_error_notification(
        self,
        error_message: str,
        error_details: Optional[str] = None
    ) -> bool:
       
        if not self.email_configured:
            logger.info("Email notifications not configured, skipping")
            return False
        
        try:
            subject = "Error: Spotify Playlist Generation Failed"
            
            body = f"""
            There was an error creating your weekly Spotify playlist.
            
            Error: {error_message}
            
            Time: {datetime.now().strftime('%Y-%m-%d %H:%M')}
            """
            
            if error_details:
                body += f"\nError Details:\n{error_details}"
            
            body += """
            
            Please check the application logs for more information.
            
            --
            Moodify
            """
            
            return self._send_email(subject, body)
            
        except Exception as e:
            logger.error(f"Error sending error notification: {e}")
            return False
    
    def _send_email(self, subject: str, body: str) -> bool:

        if not self.email_configured:
            return False
        
        try:
            # Create message
            msg = MIMEMultipart()
            msg["From"] = self.from_email
            msg["To"] = self.to_email
            msg["Subject"] = subject
            
            # Add body
            msg.attach(MIMEText(body.strip(), "plain"))
            
            # Connect to SMTP server
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()  # Secure the connection
            server.login(self.smtp_username, self.smtp_password)
            
            # Send email
            server.send_message(msg)
            server.quit()
            
            logger.info(f"Email notification sent: {subject}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return False

class ScheduleInfo:

    
    @staticmethod
    def get_next_run_info() -> Dict[str, Any]:

        # Calculate next Monday at 9:00 AM
        now = datetime.now()
        days_until_monday = (7 - now.weekday()) % 7
        if days_until_monday == 0 and now.hour >= 9:
            days_until_monday = 7  # Move to next Monday if today is Monday and it's after 9 AM
            
        next_run = now.replace(hour=9, minute=0, second=0, microsecond=0) + timedelta(days=days_until_monday)
        
        return {
            "next_run": next_run.isoformat(),
            "days_until_next_run": days_until_monday,
            "hours_until_next_run": (next_run - now).total_seconds() / 3600,
            "formatted": next_run.strftime("%Y-%m-%d %H:%M")
        }
    
    @staticmethod
    def get_schedule_description() -> str:

        next_run = ScheduleInfo.get_next_run_info()
        
        return (
            f"The playlist generator is scheduled to run every Monday at 9:00 AM.\n"
            f"Next run: {next_run['formatted']} "
            f"({next_run['days_until_next_run']} days, "
            f"{next_run['hours_until_next_run']:.1f} hours from now)"
        )

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    schedule_info = ScheduleInfo.get_next_run_info()
    print(f"Next run: {schedule_info['formatted']}")
    print(ScheduleInfo.get_schedule_description())
    
    notifier = NotificationManager()
    
    if notifier.email_configured:
        success = notifier.send_playlist_created_notification(
            playlist_id="example123",
            playlist_name="Test Playlist",
            track_count=25
        )
        print(f"Notification sent: {success}")
    else:
        print("Email notifications not configured")