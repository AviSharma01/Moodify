import datetime
import subprocess

def add_weekly_reminder(reminder_name, reminder_date):
    reminder_date = datetime.datetime.strptime(reminder_date, "%m/%d/%Y")
    today = datetime.datetime.now().date()
    next_reminder_date = reminder_date + datetime.timedelta(weeks=(today - reminder_date.date()).days // 7)
    next_reminder_date_str = datetime.datetime.strftime(next_reminder_date, "%Y-%m-%dT%H:%M:%SZ")
    reminder_text = f"Reminder: {reminder_name} is available!"
    applescript = f'do shell script "echo \'{reminder_text}\' | pbcopy && echo \'{reminder_text}\' | pbpaste | osascript -e \'tell application \\"Reminders\\" to make new reminder with properties {{name:\'{reminder_name}\', remind me date:date \\"{next_reminder_date_str}\\"}}\'"'
    subprocess.call(["osascript", "-e", applescript])