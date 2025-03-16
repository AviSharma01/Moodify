import datetime
import subprocess
import boto3
import os

def set_reminder(apple_id, reminder_name, reminder_date):
    # Set reminder in Reminders app
    reminder_date = datetime.datetime.strptime(reminder_date, "%Y-%m-%d %H:%M:%S")
    reminder_text = f"Reminder: {reminder_name} is available!"
    applescript = f'do shell script "echo \'{reminder_text}\' | pbcopy && echo \'{reminder_text}\' | pbpaste | osascript -e \'tell application \\"Reminders\\" to make new reminder with properties {{name:\'{reminder_name}\', remind me date:date \\"{reminder_date}\\"}}\'"'
    subprocess.call(["osascript", "-e", applescript])
    
    # Send email notification
    subject = "Weekly playlist is available!"
    body = f"The '{reminder_name}' playlist is now available on Spotify."
    
    client = boto3.client('ses', region_name=os.environ['AWS_REGION'], aws_access_key_id=os.environ['AWS_ACCESS_KEY_ID'], aws_secret_access_key=os.environ['AWS_SECRET_ACCESS_KEY'])
    response = client.send_email(
        Destination={
            'ToAddresses': [
                os.environ['RECIPIENT_EMAIL']
            ]
        },
        Message={
            'Body': {
                'Text': {
                    'Charset': 'UTF-8',
                    'Data': body,
                },
            },
            'Subject': {
                'Charset': 'UTF-8',
                'Data': subject,
            },
        },
        Source=os.environ['SENDER_EMAIL']
    )