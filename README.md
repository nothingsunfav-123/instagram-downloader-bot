# Instagram Downloader Bot

A Telegram bot that allows users to download Instagram videos and photos by providing a public Instagram URL. It supports posts, reels, and IGTV videos.

## Features
- Download Instagram videos and photos.
- Supports Instagram posts, reels, and IGTV videos.
- Simple and easy to use.
- Powered by [@Instasave_downloader_bot](https://t.me/Instasave_downloader_bot).

## How to Use
1. Start the bot by searching for **@Instasave_downloader_bot** on Telegram.
2. Send the bot a public Instagram link (post, reel, or IGTV).
3. The bot will process the request and send you the video or photo in a few seconds.
4. The bot adds a caption with a link to the bot for sharing.

## Example
1. Send a link like this:  
   `https://www.instagram.com/p/B4zvXCIlNTw/`
2. The bot will reply with the media (either video or photo).

## Installation

### Prerequisites
1. Python 3.x
2. Libraries:
   - `python-telegram-bot`
   - `instaloader`
   - `requests`
   - `python-dotenv`

You can install the required libraries using `pip`:

```bash
pip install python-telegram-bot instaloader requests python-dotenv
```
### Setup
1. Clone this repository:
- `git clone https://github.com/yourusername/instagram-downloader-bot.git`

2. Create a .env file in the project directory and add your Telegram bot token:
- TELEGRAM_BOT_TOKEN=your_telegram_bot_token
3. Run the bot:
- `python bot.py`

### License
This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](https://github.com/melibayev/instagram-downloader-bot/blob/main/LICENCE) file for details.