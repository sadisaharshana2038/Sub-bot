from pyrogram import Client
from pyrogram.types import Message
from pyrogram.errors import UserNotParticipant, ChatAdminRequired, ChannelPrivate
from config import Config
from keyboards import Keyboards
import logging

logger = logging.getLogger(__name__)

class ForceSubscribe:
    def __init__(self, bot: Client):
        self.bot = bot
        self.channel_id = Config.FORCE_SUB_CHANNEL
        self.channel_username = None
    
    async def get_channel_username(self) -> str:
        """Get channel username for force subscribe"""
        if self.channel_username:
            return self.channel_username
        
        try:
            chat = await self.bot.get_chat(self.channel_id)
            if chat.username:
                self.channel_username = chat.username
            else:
                # If no username, use invite link
                try:
                    invite_link = await self.bot.export_chat_invite_link(self.channel_id)
                    self.channel_username = invite_link.replace("https://t.me/", "")
                except:
                    logger.error("Failed to get channel invite link")
                    self.channel_username = "unknown"
            
            return self.channel_username
        except Exception as e:
            logger.error(f"Error getting channel username: {e}")
            return "unknown"
    
    async def is_user_subscribed(self, user_id: int) -> bool:
        """Check if user is subscribed to the channel"""
        if not self.channel_id or self.channel_id == 0:
            return True  # No force sub configured
        
        try:
            member = await self.bot.get_chat_member(self.channel_id, user_id)
            
            # Check if user is member, admin, or creator
            if member.status in ["member", "administrator", "creator"]:
                return True
            else:
                return False
        
        except UserNotParticipant:
            return False
        except (ChatAdminRequired, ChannelPrivate):
            logger.error("Bot is not admin in the force sub channel")
            return True  # Allow access if bot can't check
        except Exception as e:
            logger.error(f"Error checking subscription: {e}")
            return True  # Allow access on error
    
    async def handle_force_subscribe(self, message: Message, language: str = "sinhala") -> bool:
        """
        Handle force subscribe check
        Returns True if user is subscribed, False otherwise
        """
        user_id = message.from_user.id
        
        # Check if user is subscribed
        is_subscribed = await self.is_user_subscribed(user_id)
        
        if not is_subscribed:
            # Get channel username
            channel_username = await self.get_channel_username()
            
            # Get message text based on language
            if language == "sinhala":
                from config import Config
                text = Config.SINHALA["force_sub"]
            else:
                from config import Config
                text = Config.ENGLISH["force_sub"]
            
            # Send force subscribe message
            keyboard = Keyboards.force_subscribe(channel_username, language)
            
            try:
                await message.reply_photo(
                    photo=Config.IMAGES.get("start", "https://via.placeholder.com/800x400"),
                    caption=text,
                    reply_markup=keyboard
                )
            except:
                # If photo fails, send text only
                await message.reply_text(
                    text=text,
                    reply_markup=keyboard
                )
            
            return False
        
        return True
    
    async def handle_subscription_check(self, user_id: int, message: Message, 
                                       language: str = "sinhala") -> bool:
        """
        Handle subscription check button callback
        Returns True if user is now subscribed
        """
        is_subscribed = await self.is_user_subscribed(user_id)
        
        if is_subscribed:
            if language == "sinhala":
                success_text = "✅ ස්තූතියි! ඔබ දැන් bot භාවිතා කළ හැකිය.\n\n/start ඔබන්න."
            else:
                success_text = "✅ Thank you! You can now use the bot.\n\nPress /start."
            
            try:
                await message.edit_text(success_text)
            except:
                await message.reply_text(success_text)
            
            return True
        else:
            if language == "sinhala":
                error_text = "❌ ඔබ තවමත් channel එකට join වී නැත.\n\nකරුණාකර පළමුව join වන්න."
            else:
                error_text = "❌ You haven't joined the channel yet.\n\nPlease join first."
            
            try:
                await message.answer(error_text, show_alert=True)
            except:
                pass
            
            return False
    
    @staticmethod
    async def is_admin(user_id: int, admin_ids: list = None) -> bool:
        """Check if user is admin"""
        if admin_ids is None:
            admin_ids = Config.ADMIN_IDS
        
        return user_id in admin_ids
    
    @staticmethod
    async def admin_only(func):
        """Decorator to restrict function to admins only"""
        async def wrapper(client, message):
            user_id = message.from_user.id
            
            if not await ForceSubscribe.is_admin(user_id):
                await message.reply_text("⚠️ This command is only for admins.")
                return
            
            return await func(client, message)
        
        return wrapper


class SubscriptionHelper:
    """Helper class for subscription related tasks"""
    
    @staticmethod
    async def get_channel_info(bot: Client, channel_id: int) -> dict:
        """Get channel information"""
        try:
            chat = await bot.get_chat(channel_id)
            return {
                "id": chat.id,
                "title": chat.title,
                "username": chat.username,
                "members_count": chat.members_count,
                "type": chat.type
            }
        except Exception as e:
            logger.error(f"Error getting channel info: {e}")
            return None
    
    @staticmethod
    async def get_channel_members_count(bot: Client, channel_id: int) -> int:
        """Get total members in channel"""
        try:
            count = await bot.get_chat_members_count(channel_id)
            return count
        except Exception as e:
            logger.error(f"Error getting members count: {e}")
            return 0
    
    @staticmethod
    async def send_to_channel(bot: Client, channel_id: int, text: str = None,
                            photo: str = None, video: str = None, 
                            document: str = None, reply_markup = None) -> bool:
        """Send message to channel"""
        try:
            if photo:
                await bot.send_photo(
                    channel_id,
                    photo=photo,
                    caption=text,
                    reply_markup=reply_markup
                )
            elif video:
                await bot.send_video(
                    channel_id,
                    video=video,
                    caption=text,
                    reply_markup=reply_markup
                )
            elif document:
                await bot.send_document(
                    channel_id,
                    document=document,
                    caption=text,
                    reply_markup=reply_markup
                )
            else:
                await bot.send_message(
                    channel_id,
                    text=text,
                    reply_markup=reply_markup
                )
            
            return True
        except Exception as e:
            logger.error(f"Error sending to channel: {e}")
            return False
    
    @staticmethod
    async def forward_to_channel(bot: Client, channel_id: int, 
                                from_chat_id: int, message_id: int) -> bool:
        """Forward message to channel"""
        try:
            await bot.forward_messages(
                chat_id=channel_id,
                from_chat_id=from_chat_id,
                message_ids=message_id
            )
            return True
        except Exception as e:
            logger.error(f"Error forwarding to channel: {e}")
            return False
    
    @staticmethod
    async def copy_to_channel(bot: Client, channel_id: int,
                            from_chat_id: int, message_id: int,
                            caption: str = None) -> bool:
        """Copy message to channel"""
        try:
            await bot.copy_message(
                chat_id=channel_id,
                from_chat_id=from_chat_id,
                message_id=message_id,
                caption=caption
            )
            return True
        except Exception as e:
            logger.error(f"Error copying to channel: {e}")
            return False
    
    @staticmethod
    async def pin_message(bot: Client, chat_id: int, message_id: int,
                         disable_notification: bool = False) -> bool:
        """Pin a message in chat"""
        try:
            await bot.pin_chat_message(
                chat_id=chat_id,
                message_id=message_id,
                disable_notification=disable_notification
            )
            return True
        except Exception as e:
            logger.error(f"Error pinning message: {e}")
            return False
    
    @staticmethod
    async def unpin_message(bot: Client, chat_id: int, message_id: int = None) -> bool:
        """Unpin a message in chat"""
        try:
            if message_id:
                await bot.unpin_chat_message(chat_id=chat_id, message_id=message_id)
            else:
                await bot.unpin_all_chat_messages(chat_id=chat_id)
            return True
        except Exception as e:
            logger.error(f"Error unpinning message: {e}")
            return False
    
    @staticmethod
    async def ban_user(bot: Client, chat_id: int, user_id: int) -> bool:
        """Ban a user from chat"""
        try:
            await bot.ban_chat_member(chat_id=chat_id, user_id=user_id)
            return True
        except Exception as e:
            logger.error(f"Error banning user: {e}")
            return False
    
    @staticmethod
    async def unban_user(bot: Client, chat_id: int, user_id: int) -> bool:
        """Unban a user from chat"""
        try:
            await bot.unban_chat_member(chat_id=chat_id, user_id=user_id)
            return True
        except Exception as e:
            logger.error(f"Error unbanning user: {e}")
            return False
    
    @staticmethod
    async def get_user_profile_photos(bot: Client, user_id: int, limit: int = 1):
        """Get user profile photos"""
        try:
            photos = await bot.get_profile_photos(user_id, limit=limit)
            return photos
        except Exception as e:
            logger.error(f"Error getting profile photos: {e}")
            return None
