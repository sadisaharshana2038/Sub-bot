import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Bot Configuration
    API_ID = int(os.environ.get("API_ID", "0"))
    API_HASH = os.environ.get("API_HASH", "")
    BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
    
    # Database Configuration
    MONGO_URI = os.environ.get("MONGO_URI", "")
    DATABASE_NAME = os.environ.get("DATABASE_NAME", "subtitle_bot")
    
    # Channel Configuration
    SOURCE_CHANNEL_ID = int(os.environ.get("SOURCE_CHANNEL_ID", "0"))
    UPDATE_CHANNEL_ID = int(os.environ.get("UPDATE_CHANNEL_ID", "0"))
    ADMIN_CHANNEL_ID = int(os.environ.get("ADMIN_CHANNEL_ID", "0"))
    FORCE_SUB_CHANNEL = int(os.environ.get("FORCE_SUB_CHANNEL", "0"))
    
    # Admin Configuration
    ADMIN_IDS = [int(x) for x in os.environ.get("ADMIN_IDS", "").split(",") if x.strip()]
    
    # TMDB API
    TMDB_API_KEY = os.environ.get("TMDB_API_KEY", "")
    
    # Bot Settings
    BOT_USERNAME = os.environ.get("BOT_USERNAME", "")
    
    # Messages - Sinhala
    SINHALA = {
        "start_message": "👋 ආයුබෝවන් {name}!\n\n🎬 මම Subtitle Bot කෙනෙක්. මට ඔබට සිංහල උපසිරැසි සොයා දෙන්න පුළුවන්.\n\n📝 චිත්‍රපටයේ නම type කරන්න හෝ /help ඔබන්න.",
        "help_message": "🔍 **උදව් මෙනුව**\n\n**භාවිතා කරන්නේ කෙසේද:**\n\n1️⃣ චිත්‍රපටයේ නම type කරන්න\n2️⃣ ප්‍රතිඵල වලින් ඔබට අවශ්‍ය එක තෝරන්න\n3️⃣ උපසිරැසි ලබා ගන්න\n\n**විධාන:**\n/start - Bot එක ආරම්භ කරන්න\n/help - උදව් ලබා ගන්න\n/language - භාෂාව වෙනස් කරන්න\n/profile - ඔබේ profile එක බලන්න\n/request - උපසිරැසි request කරන්න\n/leaderboard - Top users බලන්න\n\n**Admin විධාන:**\n/broadcast - සියලු users ලට message යවන්න\n/stats - Bot statistics බලන්න\n/backup - Database backup ගන්න\n/scan - Duplicate files scan කරන්න",
        "no_results": "😔 සමාවෙන්න, '{}' සඳහා ප්‍රතිඵල සොයාගත නොහැකි විය.\n\n💡 අක්ෂර වින්‍යාසය නිවැරදිද දයාකර පරීක්ෂා කරන්න හෝ වෙනත් නමකින් උත්සාහ කරන්න.",
        "request_sent": "✅ ඔබගේ request එක සාර්ථකව යවන ලදී!\n\nඔබගේ request එක සලකා බලා ඉක්මනින් ප්‍රතිචාර දක්වන්නෙමු.",
        "request_fulfilled": "🎉 ඔබ request කළ '{}' දැන් available වේ!\n\nඔබට දැන් download කර ගත හැකිය.",
        "force_sub": "⚠️ මෙම bot භාවිතා කිරීමට පෙර අපගේ channel එකට join වන්න.\n\n👉 Join වීමෙන් පසු /start ඔබන්න.",
        "profile_message": "👤 **ඔබේ Profile**\n\n🆔 User ID: {user_id}\n📥 Downloads: {downloads}\n🏆 Rank: {rank}\n⭐ Points: {points}\n📅 Joined: {joined_date}",
        "select_movie": "🎬 ඔබේ චිත්‍රපටය තෝරන්න:",
        "request_button": "📝 Request කරන්න",
        "language_changed": "✅ භාෂාව සාර්ථකව වෙනස් කරන ලදී!",
        "choose_language": "🌐 ඔබේ භාෂාව තෝරන්න:",
        "processing": "⏳ සකසමින්...",
        "error_occurred": "❌ දෝෂයක් ඇතිවිය. කරුණාකර නැවත උත්සාහ කරන්න."
    }
    
    # Messages - English
    ENGLISH = {
        "start_message": "👋 Welcome {name}!\n\n🎬 I'm a Subtitle Bot. I can help you find Sinhala subtitles.\n\n📝 Type the movie name or press /help.",
        "help_message": "🔍 **Help Menu**\n\n**How to use:**\n\n1️⃣ Type the movie name\n2️⃣ Select from results\n3️⃣ Get your subtitles\n\n**Commands:**\n/start - Start the bot\n/help - Get help\n/language - Change language\n/profile - View your profile\n/request - Request subtitles\n/leaderboard - View top users\n\n**Admin Commands:**\n/broadcast - Send message to all users\n/stats - View bot statistics\n/backup - Backup database\n/scan - Scan duplicate files",
        "no_results": "😔 Sorry, no results found for '{}'.\n\n💡 Please check the spelling or try a different name.",
        "request_sent": "✅ Your request has been sent successfully!\n\nWe will review and respond soon.",
        "request_fulfilled": "🎉 The subtitle you requested '{}' is now available!\n\nYou can download it now.",
        "force_sub": "⚠️ Please join our channel to use this bot.\n\n👉 Press /start after joining.",
        "profile_message": "👤 **Your Profile**\n\n🆔 User ID: {user_id}\n📥 Downloads: {downloads}\n🏆 Rank: {rank}\n⭐ Points: {points}\n📅 Joined: {joined_date}",
        "select_movie": "🎬 Select your movie:",
        "request_button": "📝 Request",
        "language_changed": "✅ Language changed successfully!",
        "choose_language": "🌐 Choose your language:",
        "processing": "⏳ Processing...",
        "error_occurred": "❌ An error occurred. Please try again."
    }
    
    # Rank System
    RANKS = {
        0: "🥉 Beginner",
        10: "🥈 Regular User",
        50: "🥇 Active User",
        100: "💎 Premium User",
        500: "👑 VIP User",
        1000: "🌟 Legend"
    }
    
    # Points System
    POINTS_PER_DOWNLOAD = 1
    POINTS_PER_REQUEST = 2
    
    # Search Settings
    MAX_SEARCH_RESULTS = 10
    FUZZY_MATCH_THRESHOLD = 70
    
    # Broadcast Settings
    BROADCAST_BATCH_SIZE = 50
    BROADCAST_SLEEP_TIME = 1
    
    # File Cleaning Patterns
    CLEAN_PATTERNS = [
        r'@\w+',  # Remove @username
        r't\.me/\w+',  # Remove t.me/channel
        r'https?://\S+',  # Remove URLs
        r'\[.*?\]',  # Remove [text]
        r'\(.*?\)',  # Remove (text) if unwanted
    ]
    
    # Image URLs for menus
    IMAGES = {
        "start": "https://telegra.ph/file/example1.jpg",
        "help": "https://telegra.ph/file/example2.jpg",
        "profile": "https://telegra.ph/file/example3.jpg",
        "request": "https://telegra.ph/file/example4.jpg",
    }
