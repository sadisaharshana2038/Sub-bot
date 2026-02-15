from pyrogram import Client, filters
from pyrogram.types import Message
from database import Database
from utils import Utils
from config import Config
import logging
import asyncio
from datetime import datetime

logger = logging.getLogger(__name__)

class ChannelIndexer:
    def __init__(self, bot: Client, db: Database):
        self.bot = bot
        self.db = db
        self.source_channel = Config.SOURCE_CHANNEL_ID
        self.update_channel = Config.UPDATE_CHANNEL_ID
        self.indexing = False
    
    async def index_channel_history(self, limit: int = None) -> dict:
        """
        Index all files from channel history
        Returns statistics about indexing
        """
        if self.indexing:
            logger.warning("Indexing already in progress")
            return {"status": "already_running"}
        
        self.indexing = True
        stats = {
            "total_messages": 0,
            "indexed_files": 0,
            "skipped_files": 0,
            "duplicates": 0,
            "errors": 0,
            "start_time": datetime.now()
        }
        
        try:
            logger.info(f"Starting channel indexing from {self.source_channel}")
            
            async for message in self.bot.get_chat_history(self.source_channel, limit=limit):
                stats["total_messages"] += 1
                
                # Process only document messages
                if message.document:
                    result = await self.process_message(message)
                    
                    if result["status"] == "indexed":
                        stats["indexed_files"] += 1
                    elif result["status"] == "duplicate":
                        stats["duplicates"] += 1
                    elif result["status"] == "skipped":
                        stats["skipped_files"] += 1
                    else:
                        stats["errors"] += 1
                
                # Log progress every 100 messages
                if stats["total_messages"] % 100 == 0:
                    logger.info(f"Processed {stats['total_messages']} messages, "
                              f"indexed {stats['indexed_files']} files")
                
                # Small delay to avoid flood
                await asyncio.sleep(0.1)
            
            stats["end_time"] = datetime.now()
            stats["duration"] = (stats["end_time"] - stats["start_time"]).total_seconds()
            stats["status"] = "completed"
            
            logger.info(f"Indexing completed: {stats}")
            
        except Exception as e:
            logger.error(f"Error during channel indexing: {e}")
            stats["status"] = "error"
            stats["error_message"] = str(e)
        
        finally:
            self.indexing = False
        
        return stats
    
    async def process_message(self, message: Message) -> dict:
        """
        Process a single message and index if it's a subtitle file
        """
        try:
            if not message.document:
                return {"status": "skipped", "reason": "not_document"}
            
            # Get file details
            file = message.document
            file_name = file.file_name
            file_size = file.file_size
            file_id = file.file_id
            
            # Check if it's a subtitle file
            if not self.is_subtitle_file(file_name):
                return {"status": "skipped", "reason": "not_subtitle"}
            
            # Extract movie information
            movie_info = Utils.extract_movie_info(file_name)
            clean_title = movie_info["clean_title"]
            
            # Check for duplicates
            existing_file = await self.db.get_file_by_clean_title(clean_title)
            
            if existing_file:
                # Check if this is a better version (newer/larger)
                if file_size > existing_file.get("file_size", 0):
                    # Update existing file
                    await self.db.update_file(existing_file["file_id"], {
                        "file_id": file_id,
                        "file_name": file_name,
                        "file_size": file_size,
                        "updated_at": datetime.now()
                    })
                    logger.info(f"Updated file: {clean_title}")
                    return {"status": "updated"}
                else:
                    return {"status": "duplicate", "reason": "already_exists"}
            
            # Prepare file data
            file_data = {
                "file_id": file_id,
                "file_name": file_name,
                "file_size": file_size,
                "title": clean_title,
                "clean_title": clean_title.lower(),
                "year": movie_info.get("year"),
                "quality": movie_info.get("quality"),
                "message_id": message.id,
                "channel_id": self.source_channel,
                "file_type": Utils.get_file_extension(file_name),
                "caption": message.caption if message.caption else None
            }
            
            # Add to database
            success = await self.db.add_file(file_data)
            
            if success:
                logger.info(f"Indexed new file: {clean_title}")
                return {"status": "indexed"}
            else:
                return {"status": "error", "reason": "database_error"}
        
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return {"status": "error", "reason": str(e)}
    
    async def handle_new_file(self, message: Message) -> bool:
        """
        Handle new file posted to channel (real-time indexing)
        """
        try:
            result = await self.process_message(message)
            
            if result["status"] == "indexed":
                # Send notification to update channel
                await self.send_new_file_notification(message)
                return True
            
            return False
        
        except Exception as e:
            logger.error(f"Error handling new file: {e}")
            return False
    
    async def send_new_file_notification(self, message: Message):
        """
        Send notification to update channel about new file
        """
        try:
            if not self.update_channel or self.update_channel == 0:
                return
            
            # Get file details
            file = message.document
            file_name = file.file_name
            movie_info = Utils.extract_movie_info(file_name)
            
            # Create notification message
            notification_text = f"🆕 **New Subtitle Added!**\n\n"
            notification_text += f"📁 {movie_info['clean_title']}\n"
            
            if movie_info.get('year'):
                notification_text += f"📅 Year: {movie_info['year']}\n"
            
            if movie_info.get('quality'):
                notification_text += f"🎬 Quality: {movie_info['quality']}\n"
            
            notification_text += f"📦 Size: {Utils.format_file_size(file.file_size)}\n\n"
            notification_text += f"🔍 Search now in the bot to download!"
            
            # Send to update channel
            await self.bot.send_message(
                chat_id=self.update_channel,
                text=notification_text
            )
            
            logger.info(f"Sent notification for: {movie_info['clean_title']}")
        
        except Exception as e:
            logger.error(f"Error sending notification: {e}")
    
    @staticmethod
    def is_subtitle_file(filename: str) -> bool:
        """Check if file is a subtitle file"""
        subtitle_extensions = ['.srt', '.ass', '.sub', '.ssa', '.vtt']
        return any(filename.lower().endswith(ext) for ext in subtitle_extensions)
    
    async def reindex_file(self, file_id: str) -> bool:
        """
        Reindex a specific file
        """
        try:
            # Get file from database
            file_data = await self.db.get_file(file_id)
            
            if not file_data:
                logger.error(f"File not found: {file_id}")
                return False
            
            # Get message from channel
            message_id = file_data.get("message_id")
            channel_id = file_data.get("channel_id")
            
            if not message_id or not channel_id:
                logger.error("Message ID or Channel ID missing")
                return False
            
            message = await self.bot.get_messages(channel_id, message_id)
            
            # Reprocess the message
            result = await self.process_message(message)
            
            return result["status"] in ["indexed", "updated"]
        
        except Exception as e:
            logger.error(f"Error reindexing file: {e}")
            return False
    
    async def remove_deleted_files(self) -> dict:
        """
        Check all indexed files and remove those deleted from channel
        """
        stats = {
            "checked": 0,
            "removed": 0,
            "errors": 0
        }
        
        try:
            # Get all files from database
            total_files = await self.db.get_total_files()
            logger.info(f"Checking {total_files} files for deletion")
            
            # This is a placeholder - implement batch checking
            # For large databases, this should be done in batches
            
            logger.info(f"Removal check completed: {stats}")
        
        except Exception as e:
            logger.error(f"Error removing deleted files: {e}")
            stats["error"] = str(e)
        
        return stats
    
    async def clean_database(self) -> dict:
        """
        Clean database by removing invalid entries
        """
        stats = {
            "removed_invalid": 0,
            "removed_duplicates": 0,
            "updated": 0
        }
        
        try:
            # Find and remove duplicates
            duplicates = await self.db.find_duplicates()
            
            for dup_group in duplicates:
                files = dup_group["files"]
                
                # Keep the newest/largest file
                best_file = max(files, key=lambda x: (
                    x.get("file_size", 0),
                    x.get("added_at", datetime.min)
                ))
                
                # Remove others
                for file in files:
                    if file["file_id"] != best_file["file_id"]:
                        await self.db.delete_file(file["file_id"])
                        stats["removed_duplicates"] += 1
            
            logger.info(f"Database cleaning completed: {stats}")
        
        except Exception as e:
            logger.error(f"Error cleaning database: {e}")
            stats["error"] = str(e)
        
        return stats
    
    async def get_indexing_progress(self) -> dict:
        """
        Get current indexing progress
        """
        total_files = await self.db.get_total_files()
        
        return {
            "is_indexing": self.indexing,
            "total_indexed_files": total_files,
            "source_channel": self.source_channel
        }
    
    async def batch_update_metadata(self) -> dict:
        """
        Update metadata for all files (re-extract year, quality, etc.)
        """
        stats = {
            "processed": 0,
            "updated": 0,
            "errors": 0
        }
        
        try:
            # Get all files
            logger.info("Starting batch metadata update")
            
            # This would iterate through all files and update their metadata
            # Implementation depends on database size
            
            logger.info(f"Batch update completed: {stats}")
        
        except Exception as e:
            logger.error(f"Error in batch update: {e}")
            stats["error"] = str(e)
        
        return stats


# Background indexing handler
async def setup_channel_monitor(bot: Client, db: Database):
    """
    Setup channel monitoring for new files
    """
    indexer = ChannelIndexer(bot, db)
    
    @bot.on_message(filters.chat(Config.SOURCE_CHANNEL_ID) & filters.document)
    async def handle_new_document(client, message):
        """Handle new documents posted to source channel"""
        await indexer.handle_new_file(message)
    
    logger.info("Channel monitor setup completed")
    return indexer
