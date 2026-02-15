from pyrogram import Client
from pyrogram.types import Message
from pyrogram.errors import (
    UserIsBlocked, 
    InputUserDeactivated,
    PeerIdInvalid,
    FloodWait
)
from database import Database
from utils import Utils
import asyncio
import logging
from datetime import datetime
from typing import List, Dict

logger = logging.getLogger(__name__)

class BroadcastManager:
    def __init__(self, bot: Client, db: Database):
        self.bot = bot
        self.db = db
        self.broadcasting = False
        self.current_broadcast = None
    
    async def start_broadcast(self, message: Message, admin_id: int) -> str:
        """
        Start broadcasting a message to all users
        Returns broadcast ID
        """
        if self.broadcasting:
            return None
        
        self.broadcasting = True
        
        # Save broadcast to database
        broadcast_data = {
            "admin_id": admin_id,
            "message_text": message.text or message.caption or "",
            "message_type": self.get_message_type(message),
            "status": "in_progress",
            "total_users": 0,
            "success": 0,
            "failed": 0,
            "blocked": 0,
            "deleted": 0
        }
        
        broadcast_id = await self.db.save_broadcast(broadcast_data)
        self.current_broadcast = broadcast_id
        
        return broadcast_id
    
    async def broadcast_message(self, message: Message, admin_id: int, 
                               status_message: Message = None) -> Dict:
        """
        Broadcast message to all users with progress tracking
        """
        from config import Config
        
        # Start broadcast
        broadcast_id = await self.start_broadcast(message, admin_id)
        
        if not broadcast_id:
            return {"status": "error", "message": "Another broadcast is in progress"}
        
        # Get all users
        users = await self.db.get_all_users(banned=False)
        total_users = len(users)
        
        stats = {
            "total": total_users,
            "success": 0,
            "failed": 0,
            "blocked": 0,
            "deleted": 0,
            "invalid": 0,
            "start_time": datetime.now()
        }
        
        # Update total users in database
        await self.db.update_broadcast_stats(broadcast_id, {"total_users": total_users})
        
        logger.info(f"Starting broadcast to {total_users} users")
        
        # Progress bar message
        if status_message:
            progress_text = self.create_progress_message(stats, total_users)
            try:
                await status_message.edit_text(progress_text)
            except:
                pass
        
        # Broadcast in batches
        batch_size = Config.BROADCAST_BATCH_SIZE
        sleep_time = Config.BROADCAST_SLEEP_TIME
        
        for i in range(0, total_users, batch_size):
            batch = users[i:i + batch_size]
            
            # Process batch
            tasks = [self.send_broadcast_message(message, user) for user in batch]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Update statistics
            for result in results:
                if isinstance(result, dict):
                    if result["status"] == "success":
                        stats["success"] += 1
                    elif result["status"] == "blocked":
                        stats["blocked"] += 1
                    elif result["status"] == "deleted":
                        stats["deleted"] += 1
                    elif result["status"] == "invalid":
                        stats["invalid"] += 1
                    else:
                        stats["failed"] += 1
                else:
                    stats["failed"] += 1
            
            # Update progress
            if status_message and (i + batch_size) % 100 == 0:
                progress_text = self.create_progress_message(stats, total_users)
                try:
                    await status_message.edit_text(progress_text)
                except:
                    pass
            
            # Sleep to avoid flood
            if i + batch_size < total_users:
                await asyncio.sleep(sleep_time)
        
        # Final statistics
        stats["end_time"] = datetime.now()
        stats["duration"] = (stats["end_time"] - stats["start_time"]).total_seconds()
        
        # Update database
        await self.db.update_broadcast_stats(broadcast_id, {
            "status": "completed",
            "success": stats["success"],
            "failed": stats["failed"],
            "blocked": stats["blocked"],
            "deleted": stats["deleted"],
            "completed_at": datetime.now()
        })
        
        # Final progress message
        if status_message:
            final_text = self.create_final_report(stats)
            try:
                await status_message.edit_text(final_text)
            except:
                pass
        
        self.broadcasting = False
        self.current_broadcast = None
        
        logger.info(f"Broadcast completed: {stats}")
        
        return stats
    
    async def send_broadcast_message(self, message: Message, user: Dict) -> Dict:
        """
        Send broadcast message to a single user
        """
        user_id = user.get("user_id")
        
        try:
            # Copy message to user
            if message.text:
                await self.bot.send_message(
                    chat_id=user_id,
                    text=message.text,
                    reply_markup=message.reply_markup
                )
            elif message.photo:
                await self.bot.send_photo(
                    chat_id=user_id,
                    photo=message.photo.file_id,
                    caption=message.caption,
                    reply_markup=message.reply_markup
                )
            elif message.video:
                await self.bot.send_video(
                    chat_id=user_id,
                    video=message.video.file_id,
                    caption=message.caption,
                    reply_markup=message.reply_markup
                )
            elif message.document:
                await self.bot.send_document(
                    chat_id=user_id,
                    document=message.document.file_id,
                    caption=message.caption,
                    reply_markup=message.reply_markup
                )
            elif message.audio:
                await self.bot.send_audio(
                    chat_id=user_id,
                    audio=message.audio.file_id,
                    caption=message.caption,
                    reply_markup=message.reply_markup
                )
            elif message.animation:
                await self.bot.send_animation(
                    chat_id=user_id,
                    animation=message.animation.file_id,
                    caption=message.caption,
                    reply_markup=message.reply_markup
                )
            else:
                await self.bot.copy_message(
                    chat_id=user_id,
                    from_chat_id=message.chat.id,
                    message_id=message.id
                )
            
            return {"status": "success", "user_id": user_id}
        
        except UserIsBlocked:
            # User blocked the bot
            await self.db.update_user(user_id, {"is_banned": True})
            return {"status": "blocked", "user_id": user_id}
        
        except InputUserDeactivated:
            # User deleted account
            await self.db.update_user(user_id, {"is_banned": True})
            return {"status": "deleted", "user_id": user_id}
        
        except PeerIdInvalid:
            # Invalid user ID
            return {"status": "invalid", "user_id": user_id}
        
        except FloodWait as e:
            # Flood wait, sleep and retry
            logger.warning(f"FloodWait: {e.value} seconds")
            await asyncio.sleep(e.value)
            return await self.send_broadcast_message(message, user)
        
        except Exception as e:
            logger.error(f"Error sending to {user_id}: {e}")
            return {"status": "failed", "user_id": user_id, "error": str(e)}
    
    def create_progress_message(self, stats: Dict, total: int) -> str:
        """Create progress message text"""
        processed = stats["success"] + stats["failed"] + stats["blocked"] + stats["deleted"] + stats["invalid"]
        percentage = (processed / total * 100) if total > 0 else 0
        
        # Progress bar
        progress_bar = Utils.create_progress_bar(processed, total, 20)
        
        message = f"📢 **Broadcasting...**\n\n"
        message += f"{progress_bar}\n\n"
        message += f"📊 **Statistics:**\n\n"
        message += f"✅ Success: {stats['success']}\n"
        message += f"❌ Failed: {stats['failed']}\n"
        message += f"🚫 Blocked: {stats['blocked']}\n"
        message += f"🗑️ Deleted: {stats['deleted']}\n"
        message += f"⚠️ Invalid: {stats['invalid']}\n\n"
        message += f"📈 Progress: {processed}/{total} ({percentage:.1f}%)"
        
        return message
    
    def create_final_report(self, stats: Dict) -> str:
        """Create final broadcast report"""
        message = f"📢 **Broadcast Completed!**\n\n"
        message += f"📊 **Final Statistics:**\n\n"
        message += f"👥 Total Users: {stats['total']}\n"
        message += f"✅ Successfully Sent: {stats['success']}\n"
        message += f"❌ Failed: {stats['failed']}\n"
        message += f"🚫 Blocked Bot: {stats['blocked']}\n"
        message += f"🗑️ Deleted Account: {stats['deleted']}\n"
        message += f"⚠️ Invalid Users: {stats['invalid']}\n\n"
        
        total_sent = stats['success']
        total_not_sent = stats['failed'] + stats['blocked'] + stats['deleted'] + stats['invalid']
        
        message += f"📨 **Summary:**\n"
        message += f"✅ Delivered: {total_sent}\n"
        message += f"❌ Not Delivered: {total_not_sent}\n"
        message += f"📊 Success Rate: {(total_sent/stats['total']*100):.1f}%\n\n"
        
        duration = stats.get('duration', 0)
        message += f"⏱️ Duration: {Utils.format_duration(int(duration))}\n"
        
        return message
    
    @staticmethod
    def get_message_type(message: Message) -> str:
        """Get message type"""
        if message.text:
            return "text"
        elif message.photo:
            return "photo"
        elif message.video:
            return "video"
        elif message.document:
            return "document"
        elif message.audio:
            return "audio"
        elif message.animation:
            return "animation"
        else:
            return "other"
    
    async def get_broadcast_statistics(self) -> Dict:
        """Get broadcast statistics"""
        try:
            # Get total broadcasts
            all_broadcasts = await self.db.broadcast.find().to_list(None)
            
            stats = {
                "total_broadcasts": len(all_broadcasts),
                "completed": len([b for b in all_broadcasts if b.get("status") == "completed"]),
                "in_progress": len([b for b in all_broadcasts if b.get("status") == "in_progress"]),
                "failed": len([b for b in all_broadcasts if b.get("status") == "failed"])
            }
            
            # Calculate average success rate
            completed_broadcasts = [b for b in all_broadcasts if b.get("status") == "completed"]
            
            if completed_broadcasts:
                total_success = sum(b.get("success", 0) for b in completed_broadcasts)
                total_attempted = sum(b.get("total_users", 0) for b in completed_broadcasts)
                
                stats["average_success_rate"] = (total_success / total_attempted * 100) if total_attempted > 0 else 0
                stats["total_messages_sent"] = total_success
            else:
                stats["average_success_rate"] = 0
                stats["total_messages_sent"] = 0
            
            return stats
        
        except Exception as e:
            logger.error(f"Error getting broadcast statistics: {e}")
            return {}
    
    async def cancel_broadcast(self) -> bool:
        """Cancel ongoing broadcast"""
        if not self.broadcasting:
            return False
        
        try:
            if self.current_broadcast:
                await self.db.update_broadcast_stats(self.current_broadcast, {
                    "status": "cancelled",
                    "completed_at": datetime.now()
                })
            
            self.broadcasting = False
            self.current_broadcast = None
            
            logger.info("Broadcast cancelled")
            return True
        
        except Exception as e:
            logger.error(f"Error cancelling broadcast: {e}")
            return False
    
    async def is_broadcasting(self) -> bool:
        """Check if currently broadcasting"""
        return self.broadcasting
    
    async def get_active_broadcast_info(self) -> Dict:
        """Get information about active broadcast"""
        if not self.broadcasting or not self.current_broadcast:
            return None
        
        try:
            from bson import ObjectId
            broadcast = await self.db.broadcast.find_one({"_id": ObjectId(self.current_broadcast)})
            return broadcast
        except:
            return None


class BroadcastScheduler:
    """Schedule broadcasts for future sending"""
    
    def __init__(self, bot: Client, db: Database):
        self.bot = bot
        self.db = db
        self.scheduled_broadcasts = []
    
    async def schedule_broadcast(self, message: Message, scheduled_time: datetime, 
                                admin_id: int) -> str:
        """Schedule a broadcast for future"""
        # This is a placeholder for scheduled broadcasts
        # Implementation would require a task scheduler like APScheduler
        pass
    
    async def cancel_scheduled_broadcast(self, broadcast_id: str) -> bool:
        """Cancel a scheduled broadcast"""
        pass
    
    async def get_scheduled_broadcasts(self) -> List[Dict]:
        """Get all scheduled broadcasts"""
        pass
