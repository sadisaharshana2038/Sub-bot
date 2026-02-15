from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, InputMediaPhoto
from database import Database
from config import Config
from keyboards import Keyboards
from utils import Utils
from tmdb_client import TMDBClient
from force_subscribe import ForceSubscribe
import logging

logger = logging.getLogger(__name__)

class CallbackHandlers:
    def __init__(self, bot: Client, db: Database, tmdb: TMDBClient):
        self.bot = bot
        self.db = db
        self.tmdb = tmdb
        self.force_sub = ForceSubscribe(bot)
        self.user_searches = {}  # Shared with user_handlers
        self.user_tmdb_results = {}  # Store TMDB results
    
    async def handle_menu_callback(self, client: Client, callback: CallbackQuery):
        """Handle menu navigation callbacks"""
        user_id = callback.from_user.id
        user_data = await self.db.get_user(user_id)
        language = user_data.get("language", "sinhala") if user_data else "sinhala"
        
        data = callback.data.split(":", 1)[1]
        
        try:
            if data == "main":
                # Main menu
                messages = Config.SINHALA if language == "sinhala" else Config.ENGLISH
                text = messages["start_message"].format(name=callback.from_user.first_name)
                
                await callback.message.edit_text(
                    text=text,
                    reply_markup=Keyboards.main_menu(language)
                )
            
            elif data == "help":
                # Help menu
                messages = Config.SINHALA if language == "sinhala" else Config.ENGLISH
                await callback.message.edit_text(
                    text=messages["help_message"],
                    reply_markup=Keyboards.help_menu(language)
                )
            
            elif data == "profile":
                # Profile
                downloads = user_data.get("downloads", 0)
                rank = Utils.calculate_rank(downloads)
                joined_date = Utils.format_date(user_data.get("joined_at"), "%Y-%m-%d")
                
                messages = Config.SINHALA if language == "sinhala" else Config.ENGLISH
                profile_text = messages["profile_message"].format(
                    user_id=user_id,
                    downloads=downloads,
                    rank=rank,
                    points=user_data.get("points", 0),
                    joined_date=joined_date
                )
                
                await callback.message.edit_text(
                    text=profile_text,
                    reply_markup=Keyboards.profile_menu(language)
                )
            
            elif data == "leaderboard":
                # Leaderboard
                top_users = await self.db.get_leaderboard(limit=10, by="downloads")
                leaderboard_text = Utils.format_leaderboard(top_users, language)
                
                await callback.message.edit_text(
                    text=leaderboard_text,
                    reply_markup=Keyboards.leaderboard_menu(language)
                )
            
            elif data == "request":
                # Request menu
                if language == "sinhala":
                    text = "📝 ඔබට request කිරීමට අවශ්‍ය චිත්‍රපටයේ හෝ TV show එකේ නම type කරන්න:"
                else:
                    text = "📝 Type the name of the movie or TV show you want to request:"
                
                await callback.message.edit_text(text)
            
            elif data == "language":
                # Language menu
                await callback.message.edit_text(
                    text="🌐 Select your language / ඔබේ භාෂාව තෝරන්න:",
                    reply_markup=Keyboards.language_menu()
                )
            
            elif data == "search":
                if language == "sinhala":
                    text = "🔍 චිත්‍රපටයේ නම type කරන්න:"
                else:
                    text = "🔍 Type the movie name:"
                
                await callback.message.edit_text(text)
            
            await callback.answer()
        
        except Exception as e:
            logger.error(f"Error in menu callback: {e}")
            await callback.answer("❌ Error occurred", show_alert=True)
    
    async def handle_language_callback(self, client: Client, callback: CallbackQuery):
        """Handle language change"""
        user_id = callback.from_user.id
        data = callback.data.split(":", 1)[1]
        
        # Update user language
        await self.db.update_user(user_id, {"language": data})
        
        messages = Config.SINHALA if data == "sinhala" else Config.ENGLISH
        
        await callback.message.edit_text(
            text=messages["language_changed"],
            reply_markup=Keyboards.back_to_main(data)
        )
        
        await callback.answer("✅ Language updated!")
    
    async def handle_file_callback(self, client: Client, callback: CallbackQuery):
        """Handle file download callback"""
        user_id = callback.from_user.id
        user_data = await self.db.get_user(user_id)
        language = user_data.get("language", "sinhala") if user_data else "sinhala"
        
        file_id = callback.data.split(":", 1)[1]
        
        try:
            # Get file from database
            file_data = await self.db.get_file(file_id)
            
            if not file_data:
                await callback.answer("❌ File not found!", show_alert=True)
                return
            
            # Send file to user
            caption = Utils.generate_file_caption(file_data, language)
            
            await callback.message.reply_document(
                document=file_id,
                caption=caption
            )
            
            # Update statistics
            await self.db.increment_file_downloads(file_id)
            await self.db.increment_user_stats(user_id, "downloads")
            await self.db.increment_user_stats(user_id, "points", Config.POINTS_PER_DOWNLOAD)
            
            if language == "sinhala":
                await callback.answer("✅ File එක යවමින්...", show_alert=False)
            else:
                await callback.answer("✅ Sending file...", show_alert=False)
        
        except Exception as e:
            logger.error(f"Error sending file: {e}")
            await callback.answer("❌ Error sending file", show_alert=True)
    
    async def handle_page_callback(self, client: Client, callback: CallbackQuery):
        """Handle pagination"""
        user_id = callback.from_user.id
        user_data = await self.db.get_user(user_id)
        language = user_data.get("language", "sinhala") if user_data else "sinhala"
        
        page = int(callback.data.split(":", 1)[1])
        
        # Get stored search results
        if user_id not in self.user_searches:
            await callback.answer("❌ Search expired. Please search again.", show_alert=True)
            return
        
        search_data = self.user_searches[user_id]
        results = search_data["results"]
        query = search_data["query"]
        
        # Update page
        search_data["page"] = page
        
        # Generate keyboard
        keyboard = Keyboards.search_results(results, page=page, language=language)
        
        messages = Config.SINHALA if language == "sinhala" else Config.ENGLISH
        select_text = messages["select_movie"]
        
        try:
            await callback.message.edit_text(
                text=f"{select_text}\n\n🔍 Query: `{query}`\n📊 Found: {len(results)} results",
                reply_markup=keyboard
            )
            await callback.answer()
        except Exception as e:
            logger.error(f"Error in pagination: {e}")
            await callback.answer("❌ Error", show_alert=True)
    
    async def handle_request_callback(self, client: Client, callback: CallbackQuery):
        """Handle request callbacks"""
        user_id = callback.from_user.id
        user_data = await self.db.get_user(user_id)
        language = user_data.get("language", "sinhala") if user_data else "sinhala"
        messages = Config.SINHALA if language == "sinhala" else Config.ENGLISH
        
        data = callback.data.split(":", 1)[1]
        
        try:
            if data == "start":
                # Start request process
                if language == "sinhala":
                    text = "📝 ඔබට request කිරීමට අවශ්‍ය චිත්‍රපටයේ නම type කරන්න:\n\nඋදාහරණය: Avatar"
                else:
                    text = "📝 Type the movie name you want to request:\n\nExample: Avatar"
                
                await callback.message.edit_text(text)
                await callback.answer()
            
            elif data == "cancel":
                # Cancel request
                await callback.message.edit_text(
                    text=messages["start_message"].format(name=callback.from_user.first_name),
                    reply_markup=Keyboards.main_menu(language)
                )
                await callback.answer("❌ Request cancelled")
        
        except Exception as e:
            logger.error(f"Error in request callback: {e}")
            await callback.answer("❌ Error", show_alert=True)
    
    async def handle_tmdb_callback(self, client: Client, callback: CallbackQuery):
        """Handle TMDB movie selection"""
        user_id = callback.from_user.id
        user_data = await self.db.get_user(user_id)
        language = user_data.get("language", "sinhala") if user_data else "sinhala"
        
        parts = callback.data.split(":")
        media_type = parts[1]  # movie or tv
        tmdb_id = int(parts[2])
        
        try:
            # Get movie/TV details from TMDB
            if media_type == "movie":
                details = await self.tmdb.get_movie_details(tmdb_id)
            else:
                details = await self.tmdb.get_tv_details(tmdb_id)
            
            if not details:
                await callback.answer("❌ Error fetching details", show_alert=True)
                return
            
            # Format details
            title = details.get("title") or details.get("name", "Unknown")
            year = details.get("release_date", "")[:4] if details.get("release_date") else None
            overview = details.get("overview", "No description")
            rating = details.get("vote_average", 0)
            poster = self.tmdb.get_poster_url(details.get("poster_path"))
            
            # Create caption
            caption = self.tmdb.create_movie_caption(
                {
                    "title": title,
                    "year": year,
                    "rating": rating,
                    "overview": overview
                },
                language
            )
            
            keyboard = Keyboards.tmdb_details(tmdb_id, media_type, language)
            
            # Send with poster if available
            if poster:
                try:
                    await callback.message.delete()
                    await self.bot.send_photo(
                        chat_id=user_id,
                        photo=poster,
                        caption=caption,
                        reply_markup=keyboard
                    )
                except:
                    await callback.message.edit_text(
                        text=caption,
                        reply_markup=keyboard
                    )
            else:
                await callback.message.edit_text(
                    text=caption,
                    reply_markup=keyboard
                )
            
            await callback.answer()
        
        except Exception as e:
            logger.error(f"Error in TMDB callback: {e}")
            await callback.answer("❌ Error", show_alert=True)
    
    async def handle_request_confirm_callback(self, client: Client, callback: CallbackQuery):
        """Handle request confirmation"""
        user_id = callback.from_user.id
        user_data = await self.db.get_user(user_id)
        language = user_data.get("language", "sinhala") if user_data else "sinhala"
        messages = Config.SINHALA if language == "sinhala" else Config.ENGLISH
        
        parts = callback.data.split(":")
        media_type = parts[2]
        tmdb_id = int(parts[3])
        
        try:
            # Get details
            if media_type == "movie":
                details = await self.tmdb.get_movie_details(tmdb_id)
            else:
                details = await self.tmdb.get_tv_details(tmdb_id)
            
            title = details.get("title") or details.get("name", "Unknown")
            year = details.get("release_date", "")[:4] if details.get("release_date") else None
            poster = self.tmdb.get_poster_url(details.get("poster_path"))
            
            # Save request to database
            request_data = {
                "user_id": user_id,
                "username": callback.from_user.username,
                "first_name": callback.from_user.first_name,
                "title": title,
                "year": year,
                "media_type": media_type,
                "tmdb_id": tmdb_id,
                "poster_url": poster
            }
            
            await self.db.add_request(request_data)
            await self.db.increment_user_stats(user_id, "requests_made")
            await self.db.increment_user_stats(user_id, "points", Config.POINTS_PER_REQUEST)
            
            # Send to admin channel
            await self.send_request_to_admin(request_data)
            
            # Notify user
            await callback.message.edit_text(
                text=messages["request_sent"],
                reply_markup=Keyboards.back_to_main(language)
            )
            
            await callback.answer("✅ Request sent successfully!")
        
        except Exception as e:
            logger.error(f"Error confirming request: {e}")
            await callback.answer("❌ Error sending request", show_alert=True)
    
    async def send_request_to_admin(self, request_data: dict):
        """Send request notification to admin channel"""
        try:
            title = request_data.get("title", "Unknown")
            year = request_data.get("year", "N/A")
            user_id = request_data.get("user_id")
            username = request_data.get("username", "N/A")
            first_name = request_data.get("first_name", "Unknown")
            poster = request_data.get("poster_url")
            
            text = f"📝 **New Subtitle Request**\n\n"
            text += f"🎬 Title: {title}\n"
            text += f"📅 Year: {year}\n"
            text += f"👤 User: {first_name}"
            if username:
                text += f" (@{username})"
            text += f"\n🆔 User ID: `{user_id}`\n"
            
            # Get request ID from last inserted
            request = await self.db.requests.find_one(
                {"user_id": user_id, "title": title},
                sort=[("created_at", -1)]
            )
            
            request_id = str(request["_id"]) if request else None
            
            keyboard = Keyboards.request_actions(request_id, user_id)
            
            if poster:
                await self.bot.send_photo(
                    chat_id=Config.ADMIN_CHANNEL_ID,
                    photo=poster,
                    caption=text,
                    reply_markup=keyboard
                )
            else:
                await self.bot.send_message(
                    chat_id=Config.ADMIN_CHANNEL_ID,
                    text=text,
                    reply_markup=keyboard
                )
        
        except Exception as e:
            logger.error(f"Error sending request to admin: {e}")
    
    async def handle_admin_request_callback(self, client: Client, callback: CallbackQuery):
        """Handle admin response to request"""
        if callback.from_user.id not in Config.ADMIN_IDS:
            await callback.answer("⚠️ Admin only!", show_alert=True)
            return
        
        parts = callback.data.split(":")
        action = parts[0]  # req_done or req_no
        request_id = parts[1]
        user_id = int(parts[2])
        
        try:
            # Get request
            request = await self.db.get_request(request_id)
            
            if not request:
                await callback.answer("❌ Request not found", show_alert=True)
                return
            
            # Get user data
            user_data = await self.db.get_user(user_id)
            language = user_data.get("language", "sinhala") if user_data else "sinhala"
            messages = Config.SINHALA if language == "sinhala" else Config.ENGLISH
            
            if action == "req_done":
                # Mark as fulfilled
                await self.db.update_request_status(request_id, "fulfilled", "Request fulfilled by admin")
                
                # Notify user
                title = request.get("title", "Unknown")
                notification_text = messages["request_fulfilled"].format(title)
                
                try:
                    await self.bot.send_message(
                        chat_id=user_id,
                        text=notification_text
                    )
                except:
                    logger.error(f"Could not send notification to user {user_id}")
                
                # Update callback message
                await callback.message.edit_caption(
                    caption=callback.message.caption + "\n\n✅ **Request Fulfilled**"
                )
                
                await callback.answer("✅ Request marked as fulfilled")
            
            elif action == "req_no":
                # Mark as rejected
                await self.db.update_request_status(request_id, "rejected", "Not available")
                
                # Notify user
                if language == "sinhala":
                    notification_text = f"❌ සමාවෙන්න, '{request.get('title')}' දැනට available නැත."
                else:
                    notification_text = f"❌ Sorry, '{request.get('title')}' is not available at the moment."
                
                try:
                    await self.bot.send_message(
                        chat_id=user_id,
                        text=notification_text
                    )
                except:
                    logger.error(f"Could not send notification to user {user_id}")
                
                # Update callback message
                await callback.message.edit_caption(
                    caption=callback.message.caption + "\n\n❌ **Request Rejected**"
                )
                
                await callback.answer("❌ Request marked as rejected")
        
        except Exception as e:
            logger.error(f"Error handling admin request: {e}")
            await callback.answer("❌ Error", show_alert=True)
    
    async def handle_subscription_check(self, client: Client, callback: CallbackQuery):
        """Handle subscription check callback"""
        user_id = callback.from_user.id
        user_data = await self.db.get_user(user_id)
        language = user_data.get("language", "sinhala") if user_data else "sinhala"
        
        is_subscribed = await self.force_sub.handle_subscription_check(
            user_id, callback.message, language
        )
        
        if is_subscribed:
            await callback.answer("✅ Verified!", show_alert=False)
        else:
            await callback.answer("❌ Not subscribed yet", show_alert=True)
    
    async def handle_close_callback(self, client: Client, callback: CallbackQuery):
        """Handle close button"""
        try:
            await callback.message.delete()
            await callback.answer()
        except:
            await callback.answer("❌ Cannot delete", show_alert=True)
    
    async def handle_noop_callback(self, client: Client, callback: CallbackQuery):
        """Handle no-operation callbacks (like page indicators)"""
        await callback.answer()
    
    # Register all callback handlers
    def register_handlers(self):
        """Register all callback handlers"""
        
        @self.bot.on_callback_query(filters.regex(r"^menu:"))
        async def menu_cb(client, callback):
            await self.handle_menu_callback(client, callback)
        
        @self.bot.on_callback_query(filters.regex(r"^lang:"))
        async def lang_cb(client, callback):
            await self.handle_language_callback(client, callback)
        
        @self.bot.on_callback_query(filters.regex(r"^file:"))
        async def file_cb(client, callback):
            await self.handle_file_callback(client, callback)
        
        @self.bot.on_callback_query(filters.regex(r"^page:"))
        async def page_cb(client, callback):
            await self.handle_page_callback(client, callback)
        
        @self.bot.on_callback_query(filters.regex(r"^request:"))
        async def request_cb(client, callback):
            await self.handle_request_callback(client, callback)
        
        @self.bot.on_callback_query(filters.regex(r"^tmdb:"))
        async def tmdb_cb(client, callback):
            await self.handle_tmdb_callback(client, callback)
        
        @self.bot.on_callback_query(filters.regex(r"^request:confirm:"))
        async def confirm_cb(client, callback):
            await self.handle_request_confirm_callback(client, callback)
        
        @self.bot.on_callback_query(filters.regex(r"^req_(done|no):"))
        async def admin_req_cb(client, callback):
            await self.handle_admin_request_callback(client, callback)
        
        @self.bot.on_callback_query(filters.regex(r"^check:subscription"))
        async def check_sub_cb(client, callback):
            await self.handle_subscription_check(client, callback)
        
        @self.bot.on_callback_query(filters.regex(r"^close$"))
        async def close_cb(client, callback):
            await self.handle_close_callback(client, callback)
        
        @self.bot.on_callback_query(filters.regex(r"^noop$"))
        async def noop_cb(client, callback):
            await self.handle_noop_callback(client, callback)
        
        logger.info("Callback handlers registered")
