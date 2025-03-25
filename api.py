import os
from telethon import TelegramClient, events

# Telegram API credentials (from https://my.telegram.org/apps)
API_ID = 25984339
API_HASH = "cbdceb42b060579bfceb1b847d318c6a"
SESSION_NAME = "telegram_video_downloader"

# Folder to save videos
DOWNLOAD_FOLDER = "/media/hd_media/Downloads/Incoming/files/Telegram"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# Initialize client
client = TelegramClient(SESSION_NAME, API_ID, API_HASH)

@client.on(events.NewMessage(incoming=True))
async def handle_video(event):
    if event.video:  # Check if the message contains a video
        print("Downloading video...")
        file_path = await event.download_media(file=DOWNLOAD_FOLDER)
        print(f"Video saved: {file_path}")

client.start()
print("Listening for videos...")
client.run_until_disconnected()
