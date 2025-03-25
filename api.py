import os
import argparse
import asyncio
import datetime
import re
from telethon import TelegramClient, events
from telethon.tl.types import DocumentAttributeFilename

# Load defaults from environment variables
DEFAULT_API_ID = int(os.getenv("TELEGRAM_BOT_API_ID", 0))
DEFAULT_API_HASH = os.getenv("TELEGRAM_BOT_API_HASH", "")
DEFAULT_DOWNLOAD_FOLDER = os.getenv("TELEGRAM_BOT_DL_FOLDER", "downloads")
DEFAULT_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

def parse_args():
    """Parses command-line arguments."""
    parser = argparse.ArgumentParser(description="Telegram Video Downloader Bot")
    parser.add_argument("--api-id", type=int, default=DEFAULT_API_ID, help="Telegram API ID (default: from env)")
    parser.add_argument("--api-hash", type=str, default=DEFAULT_API_HASH, help="Telegram API Hash (default: from env)")
    parser.add_argument("--download-folder", type=str, default=DEFAULT_DOWNLOAD_FOLDER, help="Download folder (default: from env)")
    parser.add_argument("--bot-token", type=str, default=DEFAULT_BOT_TOKEN, help="Telegram Bot Token (default: from env)")
    return parser.parse_args()

def sanitize_filename(name):
    """Sanitizes the filename to be filesystem-friendly while keeping spaces."""
    name = re.sub(r'[<>:"/\\|?*]', '_', name)  # Replace forbidden characters
    name = name.strip()  # Remove trailing spaces
    return name[:100]  # Limit length to 100 characters

def get_file_extension(event):
    """Extracts the file extension from the original filename, if available."""
    if event.document and event.document.attributes:
        for attr in event.document.attributes:
            if isinstance(attr, DocumentAttributeFilename):
                return os.path.splitext(attr.file_name)[1]  # Extract file extension
    return ".mp4"  # Default fallback

async def progress_callback(current, total, event, sender_id, msg):
    """Updates the user on download progress."""
    percent = int(current / total * 100)
    if percent % 2 == 0:
        new_text = f"⬇ Downloading... {percent}% ({current / 1024 / 1024:.2f} MB / {total / 1024 / 1024:.2f} MB)"
        try:
            await client.edit_message(sender_id, msg.id, new_text)
        except:
            pass  # Ignore if Telegram rate-limits updates

async def download_worker():
    """Processes video downloads one by one from the queue."""
    while True:
        event = await download_queue.get()
        if event.video or event.document:
            sender = await event.get_sender()
            sender_id = sender.id

            # Get filename from message text or default to timestamp
            if event.message.text:
                filename = sanitize_filename(event.message.text)
            else:
                filename = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

            file_extension = get_file_extension(event)
            file_path = os.path.join(args.download_folder, f"{filename}{file_extension}")

            # Notify user that the download has started, save the message to update it later
            msg = await client.send_message(sender_id, f"⬇ Downloading `{filename}{file_extension}`...")

            print(f"Downloading video: {filename}{file_extension}...")
            await event.download_media(
                file=file_path,
                progress_callback=lambda current, total: progress_callback(current, total, event, sender_id, msg)
            )

            print(f"✅ Video saved: {file_path}")
            await client.edit_message(sender_id, msg.id, f"✅ Download complete: `{file_path}`")

        download_queue.task_done()

async def handle_video(event):
    """Adds incoming videos to the download queue."""
    await download_queue.put(event)
    print(f"📥 Queued video for download. Queue size: {download_queue.qsize()}")

async def main(client, token):
    """Starts the bot and the download worker."""
    asyncio.create_task(download_worker())
    await client.start(bot_token=token)  # Start bot with bot token
    client.add_event_handler(handle_video, events.NewMessage(incoming=True))
    print("Listening for videos...")
    await client.run_until_disconnected()

if __name__ == "__main__":
    args = parse_args()
    os.makedirs(args.download_folder, exist_ok=True)  # Ensure download folder exists

    # Initialize Telegram client
    SESSION_NAME = "user_session"
    client = TelegramClient(SESSION_NAME, api_id=args.api_id, api_hash=args.api_hash)

    # Queue for sequential downloads
    download_queue = asyncio.Queue()

    asyncio.get_event_loop().run_until_complete(main(client, args.bot_token))

