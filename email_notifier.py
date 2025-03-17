import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging

logger = logging.getLogger(__name__)

def send_email(subject, body, recipient, gmail_user, gmail_app_password):
    """Send an email notification using Gmail SMTP."""
    try:
        msg = MIMEMultipart('alternative') 
        msg['From'] = gmail_user
        msg['To'] = recipient
        msg['Subject'] = subject
        
        html_body = body.replace('\n', '<br>')
        msg.attach(MIMEText(html_body, 'html'))  
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(gmail_user, gmail_app_password)
        
        server.send_message(msg)
        server.quit()
        
        logger.info("Email notification sent successfully")
        return True
    except Exception as e:
        logger.error(f"Error sending email: {e}")
        return False