from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery
from database import Database
from config import Config
from keyboards import Keyboards
from utils import Utils
from broadcast import BroadcastManager
from indexer import ChannelIndexer
import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class AdminHandlers:
    def __init__(self, bot: Client, db: Database, broadcast_manager: BroadcastManager, indexer: ChannelIndexer):
        self.bot = bot
        self.db = db
        self.broadcast_manager = broadcast_manager
        self.indexer = indexer
        self.broadcast_messages = {}  # Store broadcast messages for confirmation
    
    def is_admin(self, user_id: int) -> bool:
        """Check if user is admin"""
        return user_id in Config.ADMIN_IDS
    
    async def admin_menu_handler(self, client: Client, message: Message):
        """Show admin menu"""
        if not self.is_admin(message.from_user.id):
            await message.reply_text("⚠️ This command is only for admins.")
            return
        
        text = "🔐 **Admin Panel**\n\nSelect an option:"
        
        await message.reply_text(
            text=text,
            reply_markup=Keyboards.admin_menu()
        )
    
    async def stats_handler(self, client: Client, message: Message):
        """Show bot statistics"""
        if not self.is_admin(message.from_user.id):
            await message.reply_text("⚠️ This command is only for admins.")
            return
        
        processing_msg = await message.reply_text("⏳ Gathering statistics...")
        
        try:
            # Get statistics
            total_users = await self.db.get_total_users()
            total_files = await self.db.get_total_files()
            total_searches = await self.db.get_total_searches()
            request_stats = await self.db.get_request_stats()
            
            # Calculate total downloads
            all_files = await self.db.files.find().to_list(None)
            total_downloads = sum(f.get("downloads", 0) for f in all_files)
            
            # Get most downloaded files
            most_downloaded = await self.db.get_most_downloaded(limit=5)
            
            # Get most requested
            most_requested = await self.db.get_most_requested(limit=5)
            
            # Get top users
            top_users = await self.db.get_leaderboard(limit=5, by="downloads")
            
            # Format statistics
            stats_text = f"📊 **Bot Statistics**\n\n"
            stats_text += f"👥 **Users:**\n"
            stats_text += f"├ Total: {total_users}\n"
            stats_text += f"└ Active: {len([u for u in await self.db.get_all_users() if not u.get('is_banned', False)])}\n\n"
            
            stats_text += f"📁 **Files:**\n"
            stats_text += f"├ Total Files: {total_files}\n"
            stats_text += f"└ Total Downloads: {total_downloads}\n\n"
            
            stats_text += f"🔍 **Searches:**\n"
            stats_text += f"└ Total: {total_searches}\n\n"
            
            stats_text += f"📝 **Requests:**\n"
            stats_text += f"├ Total: {request_stats['total']}\n"
            stats_text += f"├ Pending: {request_stats['pending']}\n"
            stats_text += f"├ Fulfilled: {request_stats['fulfilled']}\n"
            stats_text += f"└ Rejected: {request_stats['rejected']}\n\n"
            
            stats_text += f"🔥 **Top 5 Downloads:**\n"
            for idx, file in enumerate(most_downloaded, 1):
                stats_text += f"{idx}. {file.get('title', 'Unknown')} ({file.get('downloads', 0)})\n"
            
            stats_text += f"\n📝 **Most Requested:**\n"
            for idx, req in enumerate(most_requested, 1):
                stats_text += f"{idx}. {req.get('_id', 'Unknown')} ({req.get('count', 0)})\n"
            
            stats_text += f"\n👑 **Top 5 Users:**\n"
            for idx, user in enumerate(top_users, 1):
                name = user.get("first_name", "Unknown")
                downloads = user.get("downloads", 0)
                stats_text += f"{idx}. {name} ({downloads} downloads)\n"
            
            await processing_msg.edit_text(
                text=stats_text,
                reply_markup=Keyboards.close_button()
            )
        
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            await processing_msg.edit_text("❌ Error getting statistics")
    
    async def broadcast_handler(self, client: Client, message: Message):
        """Handle broadcast command"""
        if not self.is_admin(message.from_user.id):
            await message.reply_text("⚠️ This command is only for admins.")
            return
        
        # Check if already broadcasting
        if await self.broadcast_manager.is_broadcasting():
            await message.reply_text("⚠️ Another broadcast is already in progress. Please wait.")
            return
        
        text = "📢 **Broadcast Message**\n\n"
        text += "Please reply to this message with the content you want to broadcast.\n\n"
        text += "Supported: Text, Photo, Video, Document, Audio, Animation\n\n"
        text += "Use /cancel to cancel the broadcast."
        
        await message.reply_text(text)
        
        # Store admin ID for later (would need state management)
        self.broadcast_messages[message.from_user.id] = {"waiting": True}
    
    async def handle_broadcast_reply(self, client: Client, message: Message):
        """Handle broadcast message reply"""
        user_id = message.from_user.id
        
        if not self.is_admin(user_id):
            return
        
        if user_id not in self.broadcast_messages or not self.broadcast_messages[user_id].get("waiting"):
            return
        
        # Store the message
        self.broadcast_messages[user_id] = {
            "message": message,
            "waiting": False
        }
        
        # Ask for confirmation
        total_users = await self.db.get_total_users()
        
        text = f"📢 **Confirm Broadcast**\n\n"
        text += f"You are about to send this message to {total_users} users.\n\n"
        text += f"Do you want to continue?"
        
        await message.reply_text(
            text=text,
            reply_markup=Keyboards.broadcast_confirm()
        )
    
    async def handle_broadcast_confirm(self, client: Client, callback: CallbackQuery):
        """Handle broadcast confirmation"""
        user_id = callback.from_user.id
        
        if not self.is_admin(user_id):
            await callback.answer("⚠️ Admin only!", show_alert=True)
            return
        
        data = callback.data.split(":", 1)[1]
        
        if data == "confirm":
            # Get stored message
            if user_id not in self.broadcast_messages:
                await callback.answer("❌ Message not found", show_alert=True)
                return
            
            broadcast_message = self.broadcast_messages[user_id].get("message")
            
            if not broadcast_message:
                await callback.answer("❌ Message not found", show_alert=True)
                return
            
            # Start broadcasting
            await callback.message.edit_text("📢 Starting broadcast...")
            
            # Run broadcast
            stats = await self.broadcast_manager.broadcast_message(
                message=broadcast_message,
                admin_id=user_id,
                status_message=callback.message
            )
            
            # Clean up
            if user_id in self.broadcast_messages:
                del self.broadcast_messages[user_id]
            
            await callback.answer("✅ Broadcast completed!")
        
        elif data == "cancel":
            # Cancel broadcast
            if user_id in self.broadcast_messages:
                del self.broadcast_messages[user_id]
            
            await callback.message.edit_text("❌ Broadcast cancelled")
            await callback.answer("Cancelled")
    
    async def backup_handler(self, client: Client, message: Message):
        """Create database backup"""
        if not self.is_admin(message.from_user.id):
            await message.reply_text("⚠️ This command is only for admins.")
            return
        
        processing_msg = await message.reply_text("⏳ Creating backup...")
        
        try:
            # Create backup
            backup_data = await self.db.backup_database()
            
            if not backup_data:
                await processing_msg.edit_text("❌ Error creating backup")
                return
            
            # Save to file
            filename = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            filepath = f"/home/claude/{filename}"
            
            with open(filepath, 'w') as f:
                json.dump(backup_data, f, default=str, indent=2)
            
            # Send file
            await message.reply_document(
                document=filepath,
                caption=f"💾 **Database Backup**\n\n"
                       f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                       f"👥 Users: {len(backup_data.get('users', []))}\n"
                       f"📁 Files: {len(backup_data.get('files', []))}\n"
                       f"📝 Requests: {len(backup_data.get('requests', []))}"
            )
            
            await processing_msg.delete()
        
        except Exception as e:
            logger.error(f"Error creating backup: {e}")
            await processing_msg.edit_text("❌ Error creating backup")
    
    async def scan_handler(self, client: Client, message: Message):
        """Scan for duplicate files"""
        if not self.is_admin(message.from_user.id):
            await message.reply_text("⚠️ This command is only for admins.")
            return
        
        processing_msg = await message.reply_text("🔍 Scanning for duplicates...")
        
        try:
            # Find duplicates
            duplicates = await self.db.find_duplicates()
            
            if not duplicates:
                await processing_msg.edit_text("✅ No duplicates found!")
                return
            
            # Count total duplicates
            total_duplicates = sum(dup.get("count", 0) - 1 for dup in duplicates)
            
            text = f"🔍 **Duplicate Scan Results**\n\n"
            text += f"Found {len(duplicates)} groups with {total_duplicates} duplicate files\n\n"
            text += f"**Details:**\n"
            
            for idx, dup in enumerate(duplicates[:10], 1):
                title = dup.get("_id", "Unknown")
                count = dup.get("count", 0)
                text += f"{idx}. {title} ({count} copies)\n"
            
            if len(duplicates) > 10:
                text += f"\n... and {len(duplicates) - 10} more"
            
            await processing_msg.edit_text(
                text=text,
                reply_markup=Keyboards.scan_actions(total_duplicates)
            )
        
        except Exception as e:
            logger.error(f"Error scanning duplicates: {e}")
            await processing_msg.edit_text("❌ Error scanning duplicates")
    
    async def handle_scan_callback(self, client: Client, callback: CallbackQuery):
        """Handle scan action callbacks"""
        if not self.is_admin(callback.from_user.id):
            await callback.answer("⚠️ Admin only!", show_alert=True)
            return
        
        data = callback.data.split(":", 1)[1]
        
        if data == "delete":
            await callback.message.edit_text("🗑️ Deleting duplicates...")
            
            try:
                # Clean database
                stats = await self.indexer.clean_database()
                
                text = f"✅ **Cleanup Completed**\n\n"
                text += f"🗑️ Removed {stats.get('removed_duplicates', 0)} duplicates\n"
                text += f"❌ Removed {stats.get('removed_invalid', 0)} invalid entries\n"
                text += f"🔄 Updated {stats.get('updated', 0)} entries"
                
                await callback.message.edit_text(text)
                await callback.answer("✅ Duplicates deleted!")
            
            except Exception as e:
                logger.error(f"Error deleting duplicates: {e}")
                await callback.message.edit_text("❌ Error deleting duplicates")
                await callback.answer("❌ Error", show_alert=True)
        
        elif data == "cancel":
            await callback.message.edit_text("❌ Scan cancelled")
            await callback.answer("Cancelled")
    
    async def index_handler(self, client: Client, message: Message):
        """Start channel indexing"""
        if not self.is_admin(message.from_user.id):
            await message.reply_text("⚠️ This command is only for admins.")
            return
        
        # Check if already indexing
        progress = await self.indexer.get_indexing_progress()
        
        if progress.get("is_indexing"):
            await message.reply_text("⚠️ Indexing is already in progress!")
            return
        
        # Ask for confirmation
        text = "📑 **Channel Indexing**\n\n"
        text += f"This will index all subtitle files from the source channel.\n\n"
        text += f"Channel ID: `{Config.SOURCE_CHANNEL_ID}`\n\n"
        text += f"Do you want to start?"
        
        keyboard = [[
            {"text": "✅ Start", "callback_data": "index:start"},
            {"text": "❌ Cancel", "callback_data": "index:cancel"}
        ]]
        
        await message.reply_text(
            text=text,
            reply_markup=Keyboards.custom_buttons(keyboard)
        )
    
    async def handle_index_callback(self, client: Client, callback: CallbackQuery):
        """Handle index callbacks"""
        if not self.is_admin(callback.from_user.id):
            await callback.answer("⚠️ Admin only!", show_alert=True)
            return
        
        data = callback.data.split(":", 1)[1]
        
        if data == "start":
            await callback.message.edit_text("📑 Starting indexing...")
            
            # Start indexing in background
            import asyncio
            asyncio.create_task(self.run_indexing(callback.message))
            
            await callback.answer("✅ Indexing started!")
        
        elif data == "cancel":
            await callback.message.edit_text("❌ Indexing cancelled")
            await callback.answer("Cancelled")
    
    async def run_indexing(self, message: Message):
        """Run indexing process"""
        try:
            stats = await self.indexer.index_channel_history()
            
            text = f"✅ **Indexing Completed**\n\n"
            text += f"📊 **Statistics:**\n\n"
            text += f"📨 Total Messages: {stats.get('total_messages', 0)}\n"
            text += f"✅ Indexed Files: {stats.get('indexed_files', 0)}\n"
            text += f"⏭️ Skipped: {stats.get('skipped_files', 0)}\n"
            text += f"🔄 Duplicates: {stats.get('duplicates', 0)}\n"
            text += f"❌ Errors: {stats.get('errors', 0)}\n\n"
            text += f"⏱️ Duration: {Utils.format_duration(int(stats.get('duration', 0)))}"
            
            await message.edit_text(text)
        
        except Exception as e:
            logger.error(f"Error in indexing: {e}")
            await message.edit_text("❌ Error during indexing")
    
    async def analytics_handler(self, client: Client, message: Message):
        """Show analytics"""
        if not self.is_admin(message.from_user.id):
            await message.reply_text("⚠️ This command is only for admins.")
            return
        
        processing_msg = await message.reply_text("⏳ Generating analytics...")
        
        try:
            # Get popular searches
            popular_searches = await self.db.get_popular_searches(limit=10)
            
            # Get broadcast stats
            broadcast_stats = await self.broadcast_manager.get_broadcast_statistics()
            
            text = f"📈 **Analytics Dashboard**\n\n"
            
            text += f"🔍 **Top 10 Searches:**\n"
            for idx, search in enumerate(popular_searches, 1):
                query = search.get("query", "Unknown")
                count = search.get("count", 0)
                text += f"{idx}. {query} ({count})\n"
            
            text += f"\n📢 **Broadcast Statistics:**\n"
            text += f"├ Total Broadcasts: {broadcast_stats.get('total_broadcasts', 0)}\n"
            text += f"├ Completed: {broadcast_stats.get('completed', 0)}\n"
            text += f"├ Success Rate: {broadcast_stats.get('average_success_rate', 0):.1f}%\n"
            text += f"└ Total Sent: {broadcast_stats.get('total_messages_sent', 0)}\n"
            
            await processing_msg.edit_text(
                text=text,
                reply_markup=Keyboards.close_button()
            )
        
        except Exception as e:
            logger.error(f"Error getting analytics: {e}")
            await processing_msg.edit_text("❌ Error generating analytics")
    
    # Register all admin handlers
    def register_handlers(self):
        """Register all admin handlers"""
        
        @self.bot.on_message(filters.command("admin") & filters.private)
        async def admin_cmd(client, message):
            await self.admin_menu_handler(client, message)
        
        @self.bot.on_message(filters.command("stats") & filters.private)
        async def stats_cmd(client, message):
            await self.stats_handler(client, message)
        
        @self.bot.on_message(filters.command("broadcast") & filters.private)
        async def broadcast_cmd(client, message):
            await self.broadcast_handler(client, message)
        
        @self.bot.on_message(filters.command("backup") & filters.private)
        async def backup_cmd(client, message):
            await self.backup_handler(client, message)
        
        @self.bot.on_message(filters.command("scan") & filters.private)
        async def scan_cmd(client, message):
            await self.scan_handler(client, message)
        
        @self.bot.on_message(filters.command("index") & filters.private)
        async def index_cmd(client, message):
            await self.index_handler(client, message)
        
        @self.bot.on_message(filters.command("analytics") & filters.private)
        async def analytics_cmd(client, message):
            await self.analytics_handler(client, message)
        
        @self.bot.on_callback_query(filters.regex(r"^broadcast:"))
        async def broadcast_cb(client, callback):
            await self.handle_broadcast_confirm(client, callback)
        
        @self.bot.on_callback_query(filters.regex(r"^scan:"))
        async def scan_cb(client, callback):
            await self.handle_scan_callback(client, callback)
        
        @self.bot.on_callback_query(filters.regex(r"^index:"))
        async def index_cb(client, callback):
            await self.handle_index_callback(client, callback)
        
        @self.bot.on_callback_query(filters.regex(r"^admin:"))
        async def admin_menu_cb(client, callback):
            # Handle admin menu callbacks
            if not self.is_admin(callback.from_user.id):
                await callback.answer("⚠️ Admin only!", show_alert=True)
                return
            
            data = callback.data.split(":", 1)[1]
            
            if data == "stats":
                await self.stats_handler(client, callback.message)
            elif data == "broadcast":
                await self.broadcast_handler(client, callback.message)
            elif data == "backup":
                await self.backup_handler(client, callback.message)
            elif data == "scan":
                await self.scan_handler(client, callback.message)
            elif data == "analytics":
                await self.analytics_handler(client, callback.message)
            elif data == "close":
                await callback.message.delete()
            
            await callback.answer()
        
        logger.info("Admin handlers registered")
