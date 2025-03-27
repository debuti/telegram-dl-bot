from collections import defaultdict
import logging
import os
import argparse
import asyncio
import datetime
import re
import time
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
    parser.add_argument("-v", "--verbose", action="count", default=0, help="Increase verbosity (use -vv or -vvv for more details)")
    return parser.parse_args()

async def progress_callback(current, total, sender, msg, client, file_name):
    """Updates the user on download progress."""
    percent = int(current / total * 100)
    if percent % 5 == 0: 
        body = f"⬇ Downloading: \"{file_name}\"... {percent}% ({current / 1024 / 1024:.2f} MB / {total / 1024 / 1024:.2f} MB)"
        try:
            await client.edit_message(sender.id, msg.id, body)
        except:
            print (f"Unable to send message: {body}")

async def download_worker():
    """Processes video downloads one by one from the queue."""
    while True:
        (event, sender, (file_name, file_path), msg) = await download_queue.get()

        body = f"Downloading: \"{file_name}\"..."
        logging.info(body)
        try:
            await client.edit_message(sender.id, msg.id, body)
        except:
            print (f"Unable to send message: {body}")
   
        await event.download_media(
            file=file_path,
            progress_callback=lambda current, total: progress_callback(current, total, sender, msg, client, file_name)
        )

        body = f"✅ Download complete: `{file_path}`"
        current_wait = 1
        while True:
            # Try over and over again until 
            try:
                await client.edit_message(sender.id, msg.id, body)
                break
            except: 
                logging.debug(f"Download finished but cant send msg. Waiting {current_wait}s")
                time.sleep(current_wait)
                current_wait = current_wait << 1
        logging.info(body)

        download_queue.task_done()

last_msg = defaultdict(lambda: (None))  # {user_id: (timestamp, text)}

async def handle_video(event):
    """Adds incoming videos to the download queue."""

    def sanitize_filename(name):
        """Sanitizes the filename to be filesystem-friendly while keeping spaces."""
        name = re.sub(r'[<>:"/\\|?*]', '_', name)
        name = name.strip()
        return name[:100]

    def get_file_extension(event):
        """Extracts the file extension from the original filename, if available."""
        if event.document and event.document.attributes:
            for attr in event.document.attributes:
                if isinstance(attr, DocumentAttributeFilename):
                    return os.path.splitext(attr.file_name)[1]  # Extract file extension
        return ".mp4"  # Default fallback

    # Sometimes, when forwarding media to the bot, the message arrives 1st, then the media arrives 2nd
    if event.text and not event.media:
        last_msg[event.sender_id] = (datetime.datetime.now().timestamp(), event.text)
        return  # Store the message and exit

    if event.video or event.document:
        sender = await event.get_sender()

        if event.message.text:
            filename = sanitize_filename(event.message.text)
            logging.debug(f"Received filename as caption: {filename}")
        elif event.sender_id in last_msg:
            ts, text = last_msg.pop(event.sender_id)
            if (datetime.datetime.now().timestamp() - ts) <= 5:
                filename = text
                logging.debug(f"Received filename as previous message: {filename}")
        else:
            filename = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            logging.debug(f"No filename received, default: {filename}")

        file_extension = get_file_extension(event)
        file_name = f"{filename}{file_extension}"
        file_path = os.path.join(args.download_folder, file_name)

        body = f"📥 Queued {file_name} for download."
        logging.info(body)
        try:
            msg = await client.send_message(sender.id, body)
        except:
            print (f"Unable to send message: {body}")

        await download_queue.put((event, sender, (file_name, file_path), msg))
    else:
        body = f"🗙 Unable to manage message, send videos or documents."
        logging.info(body)
        try:
            await client.send_message(sender.id, body)
        except:
            print (f"Unable to send message: {body}")


async def main(client, token):
    """Starts the bot and the download worker."""
    asyncio.create_task(download_worker())
    await client.start(bot_token=token)
    client.add_event_handler(handle_video, events.NewMessage(incoming=True))
    logging.info("Listening for videos...")
    await client.run_until_disconnected()

if __name__ == "__main__":
    args = parse_args()
    
    log_levels = [logging.WARNING, logging.INFO, logging.DEBUG]  # Levels: 0 = WARNING, 1 = INFO, 2+ = DEBUG
    log_level = log_levels[min(args.verbose, 2)]  # Cap at DEBUG
    logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=log_level)

    os.makedirs(args.download_folder, exist_ok=True)

    # Initialize Telegram client
    SESSION_NAME = "telegram-dl-bot"
    client = TelegramClient(SESSION_NAME, api_id=args.api_id, api_hash=args.api_hash)

    # Queue for sequential downloads
    download_queue = asyncio.Queue()

    asyncio.get_event_loop().run_until_complete(main(client, args.bot_token))

