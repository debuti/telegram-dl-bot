import os
from telethon import TelegramClient, events

# Telegram API credentials (from https://my.telegram.org/apps)
API_ID = 25984339
API_HASH = "cbdceb42b060579bfceb1b847d318c6a"
SESSION_NAME = "telegram_video_downloader"
client = TelegramClient(SESSION_NAME, api_id=API_ID, api_hash=API_HASH)

# Folder to save videos
DOWNLOAD_FOLDER = "/media/hd_media/Downloads/Incoming/files/Telegram"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

async def progress_callback(current, total, event, sender_id, msg):
    """Sends progress updates to the user."""
    percent = int(current / total * 100)
    
    if percent % 2 == 0:
        new_text = f"⬇ Downloading... {percent}% ({current / 1024 / 1024:.2f} MB / {total / 1024 / 1024:.2f} MB)"
        try:
            await client.edit_message(sender_id, msg.id, new_text)  # Update progress
        except:
            pass  # Ignore errors if Telegram rate-limits updates

@client.on(events.NewMessage(incoming=True))
async def handle_video(event):
    """Handles incoming video messages and downloads them."""
    if event.video:  # Check if the message contains a video
        sender = await event.get_sender()
        sender_id = sender.id

        # Extract filename from the message caption (if available)
        filename = event.message.text or "video"
        filename = filename.replace(" ", "_")  # Replace spaces with underscores

        # Send initial message
        msg = await client.send_message(sender_id, f"⬇ Download started for `{filename}`...")

        print(f"Downloading video: {filename}...")
        file_path = await event.download_media(
            file=f"{DOWNLOAD_FOLDER}/{filename}.mp4",  # Save using extracted filename
            progress_callback=lambda current, total: progress_callback(current, total, event, sender_id, msg)
        )
        print(f"Video saved: {file_path}")

        # Notify the user when the download is complete
        await client.edit_message(sender_id, msg.id, f"✅ Download complete: `{file_path}`")


client.start()  # Uses saved session, no login required
print("Listening for videos...")
client.run_until_disconnected()
