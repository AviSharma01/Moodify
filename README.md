# Moodify

Discover your hidden music gems with Moodify - a personalized playlist generator based on your weekly Spotify listening history. Automate your music discovery and get weekly reminders via email.

### Detailed Description:

Moodify is a Python script that analyzes a user's Spotify listening history and generates a customized playlist based on the user's top-played tracks over the week. The script utilizes Spotify's API to access the user's listening data and uses an algorithm to analyze the data and determine the user's top-played tracks. The generated playlist is designed to match the user's preferences and help the user find the hidden gems that they would usually forget after a week of listening. The script is meant to run weekly, and this automation process is done through the Amazon Web Services (AWS) services. These services include using an AWS Lambda function to execute the script, configuring a CloudWatch event to schedule the Lambda function to run weekly, and setting up the necessary IAM roles and permissions to allow the Lambda function to access other AWS resources such as S3 buckets. Additionally, the script would send reminders weekly via mail using the Simple Email Service (SES) provided by AWS to send emails as reminders. The email also includes a reminder to be added to the Remainders App (for Apple products, generated using AppleScript).

### For further development:
Initially, the focus of Moodify would be to be able to run successfully on different operating systems. Moreover, Moodify can be expanded to include additional features such as personalized recommendations based on the user's music preferences, generating different playlists based on the preference of genre, integration with other music streaming services, and a user interface to enhance the user experience. Additionally, Moodify can be extended to support other languages and integrate with other data sources to improve the accuracy of mood analysis.



