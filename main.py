import logging
import re
import os
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from telegram import Update, ParseMode
from instaloader import Instaloader, Post
from dotenv import load_dotenv
import requests
import json
from datetime import datetime

# Loading environment variables from .env file
load_dotenv()

# Logger setup
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Telegram Bot Token
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Instagram username
USERNAME = os.getenv('INSTAGRAM_USERNAME')

# Instaloader setup
loader = Instaloader()

# File to store user data
USERS_LOG_FILE = "users.log"

ADMIN_FILE = "admin.json"

def get_admin():
    if os.path.exists(ADMIN_FILE):
        with open(ADMIN_FILE, "r") as file:
            return json.load(file).get("admin_id")
    return None

def set_admin(user_id):
    if not os.path.exists(ADMIN_FILE):  # Set admin only once
        with open(ADMIN_FILE, "w") as file:
            json.dump({"admin_id": user_id}, file)

# Command to list users
def list_users(update: Update, context: CallbackContext):
    user = update.effective_user
    admin_id = get_admin()

    # Check if the user is the admin
    if user.id != admin_id:
        update.message.reply_text("❌ You don't have permission to use this command.")
        return

    try:
        # Read the user log file and display logged users
        if os.path.exists(USERS_LOG_FILE):
            with open(USERS_LOG_FILE, "r") as file:
                users = json.load(file)

            if not users:
                update.message.reply_text("No users have used the bot yet.")
                return

            response = "📋 List of users who used the bot:\n\n"
            for u in users:
                response += (
                    f"👤 User ID: {u['user_id']}\n"
                    f"   Username: @{u['username'] or 'N/A'}\n"
                    f"   First Name: {u['first_name']}\n"
                    f"   Last Active: {u['timestamp']}\n\n"
                )
            update.message.reply_text(response)

        else:
            update.message.reply_text("No user log file found. No users have used the bot yet.")

    except Exception as e:
        logger.error(f"Error reading user log file: {e}")
        update.message.reply_text("⚠️ An error occurred while retrieving user data.")

# Function to log user data
def log_user_data(user):
    user_data = {
        "user_id": user.id,
        "username": user.username,
        "first_name": user.first_name,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    try:
        # Read existing data
        if os.path.exists(USERS_LOG_FILE):
            with open(USERS_LOG_FILE, "r") as file:
                users = json.load(file)
        else:
            users = []

        # Update the timestamp if the user already exists
        for existing_user in users:
            if existing_user["user_id"] == user_data["user_id"]:
                existing_user["timestamp"] = user_data["timestamp"]
                break
        else:
            # Add new user if not found
            users.append(user_data)

        # Write updated data back to the file
        with open(USERS_LOG_FILE, "w") as file:
            json.dump(users, file, indent=4)

    except Exception as e:
        logger.error(f"Error logging user data: {e}")

# Function to extract shortcode from Instagram URL
def extract_shortcode(instagram_post):
    try:
        match = re.search(r"instagram\.com/(?:p|reel|tv)/([^/?#&]+)", instagram_post)
        if match:
            return match.group(1)
        else:
            raise ValueError("Invalid Instagram URL format.")
    except Exception as e:
        logger.error(f"Error extracting shortcode: {e}")
        return None

# Function to validate Instagram URL
def is_valid_instagram_url(url):
    return bool(re.match(r"https?://(www\.)?instagram\.com/(p|reel|tv)/", url))

# Function to fetch Instagram data
def fetch_instagram_data(instagram_post):
    shortcode = extract_shortcode(instagram_post)
    if not shortcode:
        return None

    try:
        loader.load_session_from_file(USERNAME)
        post = Post.from_shortcode(loader.context, shortcode)
        if post.is_video:
            return post.video_url
        else:
            return post.url
    except Exception as e:
        logger.error(f"Error fetching Instagram data: {e}")
        return None

# Function to download media
def download_media(url, file_name):
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(file_name, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return file_name
    except Exception as e:
        logger.error(f"Error downloading media: {e}")
        return None

# Function to handle user messages
def download(update: Update, context: CallbackContext):
    user = update.effective_user
    log_user_data(user)  # Log user data on every interaction

    # Handle user messages to fetch Instagram videos/photos.
    message = update.effective_message
    instagram_post = message.text.strip()

    if not is_valid_instagram_url(instagram_post):
        update.message.reply_text("❌ Invalid Instagram URL. Please send a valid post, Reel, or IGTV link.")
        return

    # Sending initial "Processing your request..." message
    processing_message = update.message.reply_text("⏳ Processing your request...")

    # Fetch Instagram data
    media_url = fetch_instagram_data(instagram_post)
    if not media_url:
        processing_message.edit_text("❌ Could not fetch data. Ensure the post is public and the URL is correct.")
        return

    # Changing to "Almost done..." after fetching data
    processing_message.edit_text("🚀 Almost done... Just a few more seconds! ⏱️")

    # Download media locally
    file_name = f"temp_{update.message.chat_id}.mp4" if "video" in media_url else f"temp_{update.message.chat_id}.jpg"
    local_file = download_media(media_url, file_name)

    if not local_file:
        processing_message.edit_text("❌ Failed to download media. Please try again later.")
        return

    # Sending the media with bot link in the caption
    try:
        caption = "👾 Powered by @Instasave_downloader_bot"
        if "video" in media_url:
            context.bot.send_video(
                chat_id=update.message.chat_id,
                video=open(local_file, "rb"),
                caption=caption
            )
        else:
            context.bot.send_photo(
                chat_id=update.message.chat_id,
                photo=open(local_file, "rb"),
                caption=caption
            )

        # Removing the "processing" messages once the media is sent
        processing_message.delete()

    except Exception as e:
        logger.error(f"Error sending media: {e}")
        processing_message.edit_text("❌ Failed to send media. Please try again later.")
    finally:
        # Cleaning up local files
        if os.path.exists(local_file):
            os.remove(local_file)

# Function to send a custom message on /start
def start(update: Update, context: CallbackContext):
    user = update.effective_user
    log_user_data(user)  # Log user data

    # Automatically set the first user as admin
    if get_admin() is None:
        set_admin(user.id)
        update.message.reply_text("👑 You have been set as the admin!")

    welcome_message = """
    👋 Hi there!
    \nSend me a public Instagram link, and I'll send the media for you. 🎥📸
    """
    update.message.reply_text(welcome_message)

# Main function to run the bot
def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    # Add handlers
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("users", list_users))  # Add /users command
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, download))

    # Start polling
    updater.start_polling()
    logger.info("Bot started and polling for updates...")
    updater.idle()
# Runing the bot
if __name__ == "__main__":
    main()