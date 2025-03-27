# Telegram Video Downloader Bot

This bot allows you to download videos and files from Telegram channels or groups, processing them one-by-one. The script uses Telethon for interacting with the Telegram API, so no other tools are required.

## How It Works

The bot listens for incoming messages in Telegram.

If the message contains a video or file, it gets queued for download.

The bot downloads each file sequentially and updates the user with the progress.

## Prerequisites

Before running the script, make sure you have the following:

* Python 3.7 or higher

* Telethon library (`python3 -m pip install telethon`)

## Setting Up

### Obtain Telegram API Credentials

You will need the following credentials from Telegram to run the bot:

- `api_id`
- `api_hash`
- `bot_token`

You can obtain the `api_id` and `api_hash` by following these steps:

1. Go to [Telegram's Developer API page](https://core.telegram.org/api/obtaining_api_id).
2. Sign in with your Telegram account.
3. Create a new application and get the `api_id` and `api_hash`.

For the `bot_token`, you'll need to create a bot via [BotFather](https://telegram.me/BotFather) on Telegram and retrieve the token.

### Set the Environment Variables

You can set your environment variables by creating a `.env` file in the root directory of your project. Below is an example `.env` file:

```bash
# .env file

# Telegram API credentials
TELEGRAM_BOT_API_ID=your_api_id
TELEGRAM_BOT_API_HASH=your_api_hash
TELEGRAM_BOT_TOKEN=your_bot_token

# Default download folder
TELEGRAM_BOT_DL_FOLDER=/path/to/downloads
```

Alternatively, you can set the environment variables manually or through the command line.

## Running the Bot

To start the bot, simply run the Python script with the appropriate arguments. The bot will listen for video messages and download them one by one.

Don't forget to source your `.env` file

### Command Line Arguments

To get an up-to-date list of options run the script with the `-h` flag.

## Launch on boot

1. Copy the `telegram-dl-bot.service` file to `/etc/systemd/system`
2. Update the placeholders
  a. Replace /path/to/api.py with the actual path to your script.
  b. Replace /path/to/ with the working directory where your script is located.
  c. Replace /path/to/.env with the full path of your .env file.
  d. Replace your_user with the Linux user that should run the script.
3. Reload systemd and enable the service

```bash
sudo systemctl daemon-reload
sudo systemctl enable telegram-dl-bot.service
sudo systemctl start telegram-dl-bot.service
```

## License
This project is licensed under the MIT License - see the LICENSE file for details.