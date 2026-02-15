import logging
import asyncio
from pyrogram import Client
from pyrogram.errors import ApiIdInvalid, AccessTokenInvalid
from config import Config
from database import Database
from tmdb_client import TMDBClient
from broadcast import BroadcastManager
from indexer import ChannelIndexer, setup_channel_monitor
from handlers.user_handlers import UserHandlers
from handlers.callback_handlers import CallbackHandlers
from handlers.admin_handlers import AdminHandlers

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class SubtitleBot:
    def __init__(self):
        self.app = None
        self.db = None
        self.tmdb = None
        self.broadcast_manager = None
        self.indexer = None
        self.user_handlers = None
        self.callback_handlers = None
        self.admin_handlers = None
    
    async def initialize(self):
        """Initialize bot and all components"""
        try:
            logger.info("Initializing Subtitle Bot...")
            
            # Validate configuration
            if not self.validate_config():
                raise ValueError("Invalid configuration. Please check your .env file.")
            
            # Initialize Pyrogram client
            self.app = Client(
                name="subtitle_bot",
                api_id=Config.API_ID,
                api_hash=Config.API_HASH,
                bot_token=Config.BOT_TOKEN,
                workers=8,
                sleep_threshold=10
            )
            
            logger.info("Pyrogram client initialized")
            
            # Initialize database
            self.db = Database(Config.MONGO_URI, Config.DATABASE_NAME)
            await self.db.setup_indexes()
            logger.info("Database connected and indexes created")
            
            # Initialize TMDB client
            self.tmdb = TMDBClient(Config.TMDB_API_KEY)
            await self.tmdb.init_session()
            logger.info("TMDB client initialized")
            
            # Initialize broadcast manager
            self.broadcast_manager = BroadcastManager(self.app, self.db)
            logger.info("Broadcast manager initialized")
            
            # Initialize indexer
            self.indexer = ChannelIndexer(self.app, self.db)
            logger.info("Channel indexer initialized")
            
            # Initialize handlers
            self.user_handlers = UserHandlers(self.app, self.db, self.tmdb)
            self.callback_handlers = CallbackHandlers(self.app, self.db, self.tmdb)
            self.admin_handlers = AdminHandlers(
                self.app, 
                self.db, 
                self.broadcast_manager, 
                self.indexer
            )
            
            # Share search data between handlers
            self.callback_handlers.user_searches = self.user_handlers.user_searches
            
            logger.info("All handlers initialized")
            
            return True
        
        except Exception as e:
            logger.error(f"Error during initialization: {e}")
            return False
    
    def validate_config(self) -> bool:
        """Validate required configuration"""
        required_configs = [
            ("API_ID", Config.API_ID),
            ("API_HASH", Config.API_HASH),
            ("BOT_TOKEN", Config.BOT_TOKEN),
            ("MONGO_URI", Config.MONGO_URI),
            ("SOURCE_CHANNEL_ID", Config.SOURCE_CHANNEL_ID),
        ]
        
        for name, value in required_configs:
            if not value or value == "" or (isinstance(value, int) and value == 0):
                logger.error(f"Missing required config: {name}")
                return False
        
        return True
    
    def register_all_handlers(self):
        """Register all handlers"""
        logger.info("Registering handlers...")
        
        # Register user handlers
        self.user_handlers.register_handlers()
        
        # Register callback handlers
        self.callback_handlers.register_handlers()
        
        # Register admin handlers
        self.admin_handlers.register_handlers()
        
        logger.info("All handlers registered successfully")
    
    async def start(self):
        """Start the bot"""
        try:
            # Start Pyrogram client
            await self.app.start()
            logger.info("Bot started successfully!")
            
            # Get bot info
            me = await self.app.get_me()
            logger.info(f"Bot Username: @{me.username}")
            logger.info(f"Bot ID: {me.id}")
            
            # Setup channel monitoring for new files
            await setup_channel_monitor(self.app, self.db)
            logger.info("Channel monitoring setup completed")
            
            # Print startup message
            print("\n" + "="*50)
            print("🎬 SUBTITLE BOT STARTED SUCCESSFULLY!")
            print("="*50)
            print(f"Bot Username: @{me.username}")
            print(f"Bot ID: {me.id}")
            print(f"Total Users: {await self.db.get_total_users()}")
            print(f"Total Files: {await self.db.get_total_files()}")
            print("="*50 + "\n")
            
        except ApiIdInvalid:
            logger.error("Invalid API_ID or API_HASH")
            raise
        except AccessTokenInvalid:
            logger.error("Invalid BOT_TOKEN")
            raise
        except Exception as e:
            logger.error(f"Error starting bot: {e}")
            raise
    
    async def stop(self):
        """Stop the bot gracefully"""
        logger.info("Stopping bot...")
        
        try:
            # Close TMDB session
            if self.tmdb:
                await self.tmdb.close_session()
                logger.info("TMDB session closed")
            
            # Close database connection
            if self.db:
                await self.db.close()
                logger.info("Database connection closed")
            
            # Stop Pyrogram client
            if self.app:
                await self.app.stop()
                logger.info("Bot stopped successfully")
        
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
    
    async def run(self):
        """Main run method"""
        try:
            # Initialize
            if not await self.initialize():
                logger.error("Initialization failed!")
                return
            
            # Register handlers
            self.register_all_handlers()
            
            # Start bot
            await self.start()
            
            # Keep running
            await asyncio.Event().wait()
        
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
        except Exception as e:
            logger.error(f"Fatal error: {e}")
        finally:
            await self.stop()


async def main():
    """Main entry point"""
    bot = SubtitleBot()
    await bot.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error in main: {e}")
