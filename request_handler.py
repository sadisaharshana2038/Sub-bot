from pyrogram import Client, filters
from pyrogram.types import Message
from database import Database
from config import Config
from keyboards import Keyboards
from tmdb_client import TMDBClient
import logging

logger = logging.getLogger(__name__)

class RequestHandler:
    """Handle subtitle request workflow with TMDB search"""
    
    def __init__(self, bot: Client, db: Database, tmdb: TMDBClient):
        self.bot = bot
        self.db = db
        self.tmdb = tmdb
        self.user_request_state = {}  # Track user request states
    
    async def start_request(self, user_id: int, language: str = "sinhala") -> str:
        """Start request process"""
        self.user_request_state[user_id] = {"state": "waiting_for_query"}
        
        if language == "sinhala":
            return "📝 ඔබට request කිරීමට අවශ්‍ය චිත්‍රපටයේ හෝ TV show එකේ නම type කරන්න:\n\nඋදාහරණය: Avatar"
        else:
            return "📝 Type the name of the movie or TV show you want to request:\n\nExample: Avatar"
    
    async def handle_request_query(self, client: Client, message: Message):
        """Handle user's request query"""
        user_id = message.from_user.id
        
        # Check if user is in request state
        if user_id not in self.user_request_state:
            return False
        
        state = self.user_request_state[user_id]
        
        if state.get("state") != "waiting_for_query":
            return False
        
        query = message.text.strip()
        user_data = await self.db.get_user(user_id)
        language = user_data.get("language", "sinhala") if user_data else "sinhala"
        messages = Config.SINHALA if language == "sinhala" else Config.ENGLISH
        
        # Show processing
        processing_msg = await message.reply_text(messages["processing"])
        
        try:
            # Search TMDB
            results = await self.tmdb.get_formatted_results(query, search_type="multi", limit=10)
            
            if not results:
                # No results
                if language == "sinhala":
                    text = f"😔 '{query}' සඳහා ප්‍රතිඵල සොයාගත නොහැකි විය.\n\nවෙනත් නමකින් උත්සාහ කරන්න."
                else:
                    text = f"😔 No results found for '{query}'.\n\nTry with a different name."
                
                await processing_msg.edit_text(text)
                
                # Reset state
                del self.user_request_state[user_id]
                return True
            
            # Show results
            keyboard = Keyboards.tmdb_results(results, language)
            
            if language == "sinhala":
                text = f"🎬 '{query}' සඳහා ප්‍රතිඵල:\n\nඔබට request කිරීමට අවශ්‍ය චිත්‍රපටය තෝරන්න:"
            else:
                text = f"🎬 Results for '{query}':\n\nSelect the movie/show you want to request:"
            
            await processing_msg.edit_text(
                text=text,
                reply_markup=keyboard
            )
            
            # Update state
            self.user_request_state[user_id] = {
                "state": "selected",
                "query": query,
                "results": results
            }
            
            return True
        
        except Exception as e:
            logger.error(f"Error in request query: {e}")
            await processing_msg.edit_text(messages["error_occurred"])
            
            # Reset state
            if user_id in self.user_request_state:
                del self.user_request_state[user_id]
            
            return True
    
    def clear_state(self, user_id: int):
        """Clear user request state"""
        if user_id in self.user_request_state:
            del self.user_request_state[user_id]
    
    def is_in_request_state(self, user_id: int) -> bool:
        """Check if user is in request state"""
        return user_id in self.user_request_state
