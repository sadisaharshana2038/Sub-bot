# 🎬 Telegram Subtitle Bot

Advanced Telegram bot for managing and distributing Sinhala subtitles with dual language support (Sinhala/English).

## ✨ Features

### Core Features
- 🔍 **Smart Search**: Advanced fuzzy search with typo tolerance
- 📁 **Auto Indexing**: Automatically indexes files from source channel
- 🌐 **Dual Language**: Full support for Sinhala and English
- 📝 **Request System**: TMDB-powered subtitle request system
- 📊 **Analytics**: Comprehensive statistics and user tracking
- 🏆 **Leaderboard**: User ranking by downloads and points
- 🔔 **Force Subscribe**: Mandatory channel subscription
- 📢 **Broadcast**: Advanced broadcasting with progress tracking

### Admin Features
- 📊 **Detailed Statistics**: User, file, search, and download stats
- 📢 **Mass Messaging**: Broadcast to all users with live progress
- 💾 **Database Backup**: Export complete database
- 🔍 **Duplicate Scanner**: Find and remove duplicate entries
- 📈 **Analytics Dashboard**: Popular searches and trends
- 📑 **Channel Indexing**: Index historical channel content
- 👥 **User Management**: Track and manage all users

### User Experience
- 👤 **User Profiles**: Personal stats, rank, and download history
- 🎬 **TMDB Integration**: Rich movie information and posters
- 📥 **Smart Buttons**: File size, name, and year displayed
- 🔄 **Pagination**: Easy navigation through search results
- ⭐ **Points System**: Earn points for downloads and requests
- 🏆 **Ranks**: Progress through rank tiers

## 📋 Requirements

- Python 3.8 or higher
- MongoDB database
- Telegram Bot Token (from @BotFather)
- Telegram API credentials (from https://my.telegram.org)
- TMDB API Key (from https://www.themoviedb.org/settings/api)

## 🚀 Installation

### 1. Clone Repository
```bash
git clone <your-repo-url>
cd subtitle-bot
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create a `.env` file in the root directory:

```env
# Bot Configuration
API_ID=your_api_id
API_HASH=your_api_hash
BOT_TOKEN=your_bot_token

# Database
MONGO_URI=mongodb://username:password@host:port/database
DATABASE_NAME=subtitle_bot

# Channels (use channel ID with -100 prefix)
SOURCE_CHANNEL_ID=-1001234567890
UPDATE_CHANNEL_ID=-1001234567890
ADMIN_CHANNEL_ID=-1001234567890
FORCE_SUB_CHANNEL=-1001234567890

# Admin Users (comma separated Telegram user IDs)
ADMIN_IDS=123456789,987654321,456789123

# TMDB API
TMDB_API_KEY=your_tmdb_api_key

# Bot Settings
BOT_USERNAME=your_bot_username
```

### 4. Setup MongoDB

**Option A: MongoDB Atlas (Cloud - Free)**
1. Go to https://www.mongodb.com/cloud/atlas
2. Create a free cluster
3. Get connection string
4. Replace `<password>` in the connection string

**Option B: Local MongoDB**
```bash
# Install MongoDB locally
# Ubuntu/Debian
sudo apt-get install mongodb

# Start MongoDB
sudo systemctl start mongodb

# Connection string
MONGO_URI=mongodb://localhost:27017
```

### 5. Get Required Credentials

**Telegram API Credentials:**
1. Go to https://my.telegram.org
2. Log in with your phone number
3. Go to "API Development Tools"
4. Create a new application
5. Note down `API_ID` and `API_HASH`

**Bot Token:**
1. Message @BotFather on Telegram
2. Send `/newbot` and follow instructions
3. Copy the bot token

**TMDB API Key:**
1. Sign up at https://www.themoviedb.org
2. Go to Settings > API
3. Request an API key
4. Copy the API Key (v3 auth)

**Channel IDs:**
1. Forward a message from your channel to @userinfobot
2. Note the channel ID (it will have -100 prefix)
3. Make sure the bot is admin in all channels

### 6. Run the Bot

```bash
python main.py
```

## 🌐 Deploy to Heroku

### 1. Install Heroku CLI
```bash
# Ubuntu/Debian
curl https://cli-assets.heroku.com/install.sh | sh

# Login
heroku login
```

### 2. Create Heroku App
```bash
heroku create your-bot-name
```

### 3. Set Config Vars
```bash
heroku config:set API_ID=your_api_id
heroku config:set API_HASH=your_api_hash
heroku config:set BOT_TOKEN=your_bot_token
heroku config:set MONGO_URI=your_mongodb_uri
heroku config:set DATABASE_NAME=subtitle_bot
heroku config:set SOURCE_CHANNEL_ID=-1001234567890
heroku config:set UPDATE_CHANNEL_ID=-1001234567890
heroku config:set ADMIN_CHANNEL_ID=-1001234567890
heroku config:set FORCE_SUB_CHANNEL=-1001234567890
heroku config:set ADMIN_IDS=123456789,987654321
heroku config:set TMDB_API_KEY=your_tmdb_api_key
heroku config:set BOT_USERNAME=your_bot_username
```

### 4. Deploy
```bash
git init
git add .
git commit -m "Initial commit"
heroku git:remote -a your-bot-name
git push heroku master
```

### 5. Scale Worker
```bash
heroku ps:scale worker=1
```

### 6. Check Logs
```bash
heroku logs --tail
```

## 📝 Usage

### User Commands
- `/start` - Start the bot
- `/help` - Get help
- `/profile` - View your profile
- `/language` - Change language
- `/request` - Request subtitles
- `/leaderboard` - View top users

### Admin Commands
- `/admin` - Admin panel
- `/stats` - View statistics
- `/broadcast` - Broadcast message
- `/backup` - Backup database
- `/scan` - Scan duplicates
- `/index` - Index channel
- `/analytics` - View analytics

### Search
Simply type the movie name to search for subtitles.

## 🎨 Customization

### Change Images
Edit `config.py` and update the `IMAGES` dictionary with your Telegraph image URLs:
```python
IMAGES = {
    "start": "https://telegra.ph/file/your-image.jpg",
    "help": "https://telegra.ph/file/your-image.jpg",
    "profile": "https://telegra.ph/file/your-image.jpg",
    "request": "https://telegra.ph/file/your-image.jpg",
}
```

### Upload Images to Telegraph
```python
from telegraph import Telegraph

telegraph = Telegraph()
telegraph.create_account(short_name='subtitle_bot')

with open('image.jpg', 'rb') as f:
    response = telegraph.upload_file(f)
    print(f"https://telegra.ph{response[0]['src']}")
```

### Modify Messages
Edit messages in `config.py` under `SINHALA` and `ENGLISH` dictionaries.

### Adjust Settings
Edit `config.py` to modify:
- Points per download/request
- Search result limits
- Broadcast batch size
- Fuzzy match threshold
- Rank system thresholds

## 🔧 Maintenance

### Index Channel History
```bash
# Run once to index all existing files
/index
```

### Create Backup
```bash
# Regular backups recommended
/backup
```

### Scan Duplicates
```bash
# Clean up database periodically
/scan
```

### Monitor Logs
```bash
# Check bot.log file
tail -f bot.log

# Or on Heroku
heroku logs --tail
```

## 📊 Database Collections

- **users** - User information and statistics
- **files** - Indexed subtitle files
- **requests** - User subtitle requests
- **searches** - Search query logs
- **broadcast** - Broadcast history
- **analytics** - Analytics data

## 🐛 Troubleshooting

### Bot Not Starting
- Check `.env` file has all required variables
- Verify MongoDB connection
- Check bot token is valid
- Ensure bot is admin in all channels

### Files Not Indexing
- Verify bot is admin in source channel
- Check SOURCE_CHANNEL_ID is correct
- Ensure files have proper subtitle extensions

### Force Subscribe Not Working
- Bot must be admin in force sub channel
- Check FORCE_SUB_CHANNEL ID is correct
- Verify channel is public or bot has invite link access

### Database Connection Failed
- Check MongoDB is running
- Verify MONGO_URI is correct
- Ensure IP is whitelisted (MongoDB Atlas)

### TMDB Not Working
- Verify TMDB_API_KEY is correct
- Check API key hasn't expired
- Ensure internet connection is stable

## 🤝 Contributing

Contributions are welcome! Please feel free to submit pull requests.

## 📄 License

This project is licensed under the MIT License.

## 🙏 Credits

- [Pyrogram](https://github.com/pyrogram/pyrogram) - MTProto API framework
- [MongoDB](https://www.mongodb.com/) - Database
- [TMDB](https://www.themoviedb.org/) - Movie database API

## 💬 Support

For support, join our Telegram channel or create an issue on GitHub.

## ⚠️ Disclaimer

This bot is for educational purposes. Make sure you have rights to distribute the subtitle files you're sharing.

---

Made with ❤️ by Your Name
