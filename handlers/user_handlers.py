from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery
from database import Database
from config import Config
from keyboards import Keyboards
from utils import Utils
from force_subscribe import ForceSubscribe
from tmdb_client import TMDBClient
import logging

logger = logging.getLogger(__name__)

class UserHandlers:
    def __init__(self, bot: Client, db: Database, tmdb: TMDBClient):
        self.bot = bot
        self.db = db
        self.tmdb = tmdb
        self.force_sub = ForceSubscribe(bot)
        self.user_searches = {}  # Store user search results temporarily
        self.user_requests = {}  # Store user request data temporarily
    
    async def start_handler(self, client: Client, message: Message):
        """Handle /start command"""
        user = message.from_user
        user_id = user.id
        
        # Get or create user
        user_data = await self.db.get_user(user_id)
        
        if not user_data:
            # New user
            await self.db.add_user(
                user_id=user_id,
                username=user.username,
                first_name=user.first_name
            )
            language = "sinhala"
        else:
            language = user_data.get("language", "sinhala")
        
        # Check force subscribe
        is_subscribed = await self.force_sub.handle_force_subscribe(message, language)
        
        if not is_subscribed:
            return
        
        # Send welcome message
        messages = Config.SINHALA if language == "sinhala" else Config.ENGLISH
        welcome_text = messages["start_message"].format(name=user.first_name)
        
        try:
            await message.reply_photo(
                photo=Config.IMAGES.get("start", "https://via.placeholder.com/800x400"),
                caption=welcome_text,
                reply_markup=Keyboards.main_menu(language)
            )
        except:
            await message.reply_text(
                text=welcome_text,
                reply_markup=Keyboards.main_menu(language)
            )
    
    async def help_handler(self, client: Client, message: Message):
        """Handle /help command"""
        user_id = message.from_user.id
        user_data = await self.db.get_user(user_id)
        language = user_data.get("language", "sinhala") if user_data else "sinhala"
        
        # Check force subscribe
        is_subscribed = await self.force_sub.handle_force_subscribe(message, language)
        if not is_subscribed:
            return
        
        messages = Config.SINHALA if language == "sinhala" else Config.ENGLISH
        help_text = messages["help_message"]
        
        try:
            await message.reply_photo(
                photo=Config.IMAGES.get("help", "https://via.placeholder.com/800x400"),
                caption=help_text,
                reply_markup=Keyboards.help_menu(language)
            )
        except:
            await message.reply_text(
                text=help_text,
                reply_markup=Keyboards.help_menu(language)
            )
    
    async def profile_handler(self, client: Client, message: Message):
        """Handle /profile command"""
        user_id = message.from_user.id
        user_data = await self.db.get_user(user_id)
        
        if not user_data:
            await message.reply_text("❌ User not found. Please /start first.")
            return
        
        language = user_data.get("language", "sinhala")
        
        # Check force subscribe
        is_subscribed = await self.force_sub.handle_force_subscribe(message, language)
        if not is_subscribed:
            return
        
        # Calculate rank
        downloads = user_data.get("downloads", 0)
        rank = Utils.calculate_rank(downloads)
        
        # Format joined date
        joined_date = Utils.format_date(user_data.get("joined_at"), "%Y-%m-%d")
        
        messages = Config.SINHALA if language == "sinhala" else Config.ENGLISH
        profile_text = messages["profile_message"].format(
            user_id=user_id,
            downloads=downloads,
            rank=rank,
            points=user_data.get("points", 0),
            joined_date=joined_date
        )
        
        try:
            await message.reply_photo(
                photo=Config.IMAGES.get("profile", "https://via.placeholder.com/800x400"),
                caption=profile_text,
                reply_markup=Keyboards.profile_menu(language)
            )
        except:
            await message.reply_text(
                text=profile_text,
                reply_markup=Keyboards.profile_menu(language)
            )
    
    async def leaderboard_handler(self, client: Client, message: Message):
        """Handle /leaderboard command"""
        user_id = message.from_user.id
        user_data = await self.db.get_user(user_id)
        language = user_data.get("language", "sinhala") if user_data else "sinhala"
        
        # Check force subscribe
        is_subscribed = await self.force_sub.handle_force_subscribe(message, language)
        if not is_subscribed:
            return
        
        # Get top users by downloads
        top_users = await self.db.get_leaderboard(limit=10, by="downloads")
        
        # Format leaderboard
        leaderboard_text = Utils.format_leaderboard(top_users, language)
        
        await message.reply_text(
            text=leaderboard_text,
            reply_markup=Keyboards.leaderboard_menu(language)
        )
    
    async def language_handler(self, client: Client, message: Message):
        """Handle /language command"""
        await message.reply_text(
            text="🌐 Select your language / ඔබේ භාෂාව තෝරන්න:",
            reply_markup=Keyboards.language_menu()
        )
    
    async def search_handler(self, client: Client, message: Message):
        """Handle search queries"""
        user_id = message.from_user.id
        user_data = await self.db.get_user(user_id)
        
        if not user_data:
            await self.start_handler(client, message)
            return
        
        language = user_data.get("language", "sinhala")
        
        # Check force subscribe
        is_subscribed = await self.force_sub.handle_force_subscribe(message, language)
        if not is_subscribed:
            return
        
        query = message.text.strip()
        
        # Sanitize query
        clean_query = Utils.sanitize_query(query)
        
        if len(clean_query) < 2:
            messages = Config.SINHALA if language == "sinhala" else Config.ENGLISH
            await message.reply_text(messages["error_occurred"])
            return
        
        # Log search
        await self.db.log_search(user_id, clean_query)
        await self.db.increment_user_stats(user_id, "total_searches")
        
        # Show processing message
        messages = Config.SINHALA if language == "sinhala" else Config.ENGLISH
        processing_msg = await message.reply_text(messages["processing"])
        
        try:
            # Search in database
            results = await self.db.search_files(clean_query, limit=50)
            
            # If no results, use fuzzy search
            if not results:
                # Get all file titles for fuzzy matching
                all_files = await self.db.files.find().to_list(None)
                titles = [f.get("clean_title", "") for f in all_files]
                
                # Fuzzy search
                fuzzy_matches = Utils.fuzzy_search(clean_query, titles, threshold=Config.FUZZY_MATCH_THRESHOLD)
                
                if fuzzy_matches:
                    # Get matched files
                    matched_titles = [match[0] for match in fuzzy_matches[:50]]
                    results = await self.db.files.find(
                        {"clean_title": {"$in": matched_titles}}
                    ).to_list(50)
            
            if results:
                # Store results for pagination
                self.user_searches[user_id] = {
                    "query": query,
                    "results": results,
                    "page": 0
                }
                
                # Send results
                select_text = messages["select_movie"]
                keyboard = Keyboards.search_results(results, page=0, language=language)
                
                await processing_msg.edit_text(
                    text=f"{select_text}\n\n🔍 Query: `{query}`\n📊 Found: {len(results)} results",
                    reply_markup=keyboard
                )
            else:
                # No results found
                no_results_text = messages["no_results"].format(query)
                await processing_msg.edit_text(
                    text=no_results_text,
                    reply_markup=Keyboards.no_results(language)
                )
        
        except Exception as e:
            logger.error(f"Error in search: {e}")
            messages = Config.SINHALA if language == "sinhala" else Config.ENGLISH
            await processing_msg.edit_text(messages["error_occurred"])
    
    async def request_handler(self, client: Client, message: Message):
        """Handle /request command"""
        user_id = message.from_user.id
        user_data = await self.db.get_user(user_id)
        
        if not user_data:
            await self.start_handler(client, message)
            return
        
        language = user_data.get("language", "sinhala")
        
        # Check force subscribe
        is_subscribed = await self.force_sub.handle_force_subscribe(message, language)
        if not is_subscribed:
            return
        
        if language == "sinhala":
            text = "📝 ඔබට request කිරීමට අවශ්‍ය චිත්‍රපටයේ හෝ TV show එකේ නම type කරන්න:\n\nඋදාහරණය: Avengers Endgame"
        else:
            text = "📝 Type the name of the movie or TV show you want to request:\n\nExample: Avengers Endgame"
        
        await message.reply_text(text)
        
        # Set user state for request (would need state management)
    
    # Register all handlers
    def register_handlers(self):
        """Register all user handlers"""
        
        @self.bot.on_message(filters.command("start") & filters.private)
        async def start_cmd(client, message):
            await self.start_handler(client, message)
        
        @self.bot.on_message(filters.command("help") & filters.private)
        async def help_cmd(client, message):
            await self.help_handler(client, message)
        
        @self.bot.on_message(filters.command("profile") & filters.private)
        async def profile_cmd(client, message):
            await self.profile_handler(client, message)
        
        @self.bot.on_message(filters.command("leaderboard") & filters.private)
        async def leaderboard_cmd(client, message):
            await self.leaderboard_handler(client, message)
        
        @self.bot.on_message(filters.command("language") & filters.private)
        async def language_cmd(client, message):
            await self.language_handler(client, message)
        
        @self.bot.on_message(filters.command("request") & filters.private)
        async def request_cmd(client, message):
            await self.request_handler(client, message)
        
        @self.bot.on_message(filters.text & filters.private & ~filters.command(["start", "help", "profile", "leaderboard", "language", "request", "broadcast", "stats", "backup", "scan"]))
        async def search_query(client, message):
            await self.search_handler(client, message)
        
        logger.info("User handlers registered")
