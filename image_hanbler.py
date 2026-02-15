import re
import logging

logger = logging.getLogger(__name__)

class ImageHandler:
    """Handle image URLs from different sources"""
    
    @staticmethod
    def parse_telegram_link(url: str) -> dict:
        """
        Parse Telegram link and extract file ID
        Returns dict with type and file_id/path
        """
        if not url:
            return None
        
        try:
            # t.me/channel/message_id format
            match = re.match(r'https?://t\.me/([^/]+)/(\d+)', url)
            if match:
                channel_username = match.group(1)
                message_id = int(match.group(2))
                return {
                    "type": "telegram",
                    "channel": channel_username,
                    "message_id": message_id,
                    "url": url
                }
            
            # Telegraph link
            if 'telegra.ph' in url:
                return {
                    "type": "telegraph",
                    "url": url
                }
            
            # Direct image URL
            if any(ext in url.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
                return {
                    "type": "direct",
                    "url": url
                }
            
            return None
        
        except Exception as e:
            logger.error(f"Error parsing image link: {e}")
            return None
    
    @staticmethod
    async def get_file_from_telegram(bot, channel: str, message_id: int):
        """Get file from Telegram channel message"""
        try:
            # Try to get message
            message = await bot.get_messages(f"@{channel}", message_id)
            
            if message.photo:
                return message.photo.file_id
            elif message.video:
                return message.video.file_id
            elif message.document:
                return message.document.file_id
            
            return None
        
        except Exception as e:
            logger.error(f"Error getting Telegram file: {e}")
            return None
    
    @staticmethod
    async def send_photo_with_image(bot, chat_id: int, image_url: str, caption: str = None, reply_markup = None):
        """Send photo message with image from URL or Telegram link"""
        try:
            # Parse image URL
            parsed = ImageHandler.parse_telegram_link(image_url)
            
            if not parsed:
                # Fallback to text message
                await bot.send_message(
                    chat_id=chat_id,
                    text=caption or "Message",
                    reply_markup=reply_markup
                )
                return True
            
            if parsed["type"] == "telegram":
                # Get file from Telegram
                file_id = await ImageHandler.get_file_from_telegram(
                    bot, 
                    parsed["channel"], 
                    parsed["message_id"]
                )
                
                if file_id:
                    await bot.send_photo(
                        chat_id=chat_id,
                        photo=file_id,
                        caption=caption,
                        reply_markup=reply_markup
                    )
                    return True
            
            # Try direct URL (Telegraph or direct image)
            try:
                await bot.send_photo(
                    chat_id=chat_id,
                    photo=parsed["url"],
                    caption=caption,
                    reply_markup=reply_markup
                )
                return True
            except:
                pass
            
            # Fallback to text
            await bot.send_message(
                chat_id=chat_id,
                text=caption or "Message",
                reply_markup=reply_markup
            )
            return True
        
        except Exception as e:
            logger.error(f"Error sending photo: {e}")
            # Final fallback
            try:
                await bot.send_message(
                    chat_id=chat_id,
                    text=caption or "Message",
                    reply_markup=reply_markup
                )
            except:
                pass
            return False
