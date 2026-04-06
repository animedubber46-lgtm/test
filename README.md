📂 Telegram File Share Bot (Pyrogram)

A powerful Telegram File Sharing Bot built with Pyrogram that allows users to upload files and generate shareable links. Anyone with the link can access the file instantly.

Supports files up to 2GB 🚀

✨ Features
📤 Upload any file (video, audio, document, photo, etc.)
🔗 Generate shareable deep links
📥 Users can download files via link
🗄️ SQLite database (no setup required)
👤 User tracking system
📊 Owner stats panel
🔒 Optional Force Join system
⚡ Fast file delivery using file_id
🧠 Smart file type detection
📁 Supported File Types
Documents
Videos
Audio files
Photos
Voice messages
Animations (GIFs)
Stickers
⚙️ Requirements
Python 3.8+
Telegram API credentials

Install dependencies:

pip install -r requirements.txt
🔑 Setup
1. Get Telegram API Credentials

Go to: https://my.telegram.org

Login → Create App → Get:

API_ID
API_HASH
2. Create Bot Token

Message BotFather on Telegram:

/newbot

Copy your BOT_TOKEN

3. Configure Environment

Create .env file:

API_ID=12345678
API_HASH=your_api_hash
BOT_TOKEN=your_bot_token
OWNER_IDS=123456789
FORCE_SUB_CHANNEL=@yourchannel
BOT_USERNAME=your_bot_username
🚀 Run the Bot
python bot.py
🧠 How It Works
User sends a file to bot
Bot stores file metadata (file_id)

Bot generates a unique link:

https://t.me/YourBot?start=get_xxxxx
Anyone clicking the link receives the file instantly
📊 Commands
Command	Description
/start	Start bot
/help	Usage guide
/stats	Bot stats (Owner only)
🔒 Force Join (Optional)

If enabled, users must join your channel before accessing files.

FORCE_SUB_CHANNEL=@yourchannel
📂 Project Structure
bot/
├── bot.py
├── requirements.txt
├── fileshare_bot.db
└── README.md
⚠️ Notes
Telegram file limit: ~2GB
Files are not re-uploaded → fast delivery
If Telegram deletes cached file → link may stop working
🔧 Future Improvements (Optional)
MongoDB support
Link expiry system
Auto delete files
Admin panel
Broadcast system
File indexing & search
URL shortener integration
❤️ Credits
Built using Pyrogram
Inspired by Telegram file sharing systems
🧑‍💻 Developer

Made with ❤️ by Anime Dev

⭐ Support

If you like this project:

⭐ Star the repo
🔄 Share with friends
🧠 Contribute ideas
