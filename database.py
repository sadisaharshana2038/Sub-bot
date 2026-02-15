from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ASCENDING, DESCENDING, TEXT
from datetime import datetime
from typing import Optional, Dict, List, Any
import logging

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, uri: str, database_name: str):
        self.client = AsyncIOMotorClient(uri)
        self.db = self.client[database_name]
        
        # Collections
        self.users = self.db.users
        self.files = self.db.files
        self.requests = self.db.requests
        self.searches = self.db.searches
        self.broadcast = self.db.broadcast
        self.analytics = self.db.analytics
        
    async def setup_indexes(self):
        """Create indexes for better performance"""
        try:
            # Users collection indexes
            await self.users.create_index([("user_id", ASCENDING)], unique=True)
            await self.users.create_index([("username", ASCENDING)])
            await self.users.create_index([("downloads", DESCENDING)])
            await self.users.create_index([("points", DESCENDING)])
            
            # Files collection indexes
            await self.files.create_index([("file_id", ASCENDING)], unique=True)
            await self.files.create_index([("title", TEXT)])
            await self.files.create_index([("clean_title", ASCENDING)])
            await self.files.create_index([("year", ASCENDING)])
            await self.files.create_index([("file_size", ASCENDING)])
            await self.files.create_index([("downloads", DESCENDING)])
            
            # Requests collection indexes
            await self.requests.create_index([("user_id", ASCENDING)])
            await self.requests.create_index([("status", ASCENDING)])
            await self.requests.create_index([("created_at", DESCENDING)])
            await self.requests.create_index([("tmdb_id", ASCENDING)])
            
            # Searches collection indexes
            await self.searches.create_index([("query", ASCENDING)])
            await self.searches.create_index([("user_id", ASCENDING)])
            await self.searches.create_index([("count", DESCENDING)])
            await self.searches.create_index([("last_searched", DESCENDING)])
            
            logger.info("Database indexes created successfully")
        except Exception as e:
            logger.error(f"Error creating indexes: {e}")
    
    # ==================== USER OPERATIONS ====================
    
    async def add_user(self, user_id: int, username: str = None, first_name: str = None, 
                       language: str = "sinhala") -> Dict:
        """Add new user to database"""
        user_data = {
            "user_id": user_id,
            "username": username,
            "first_name": first_name,
            "language": language,
            "downloads": 0,
            "points": 0,
            "requests_made": 0,
            "total_searches": 0,
            "is_banned": False,
            "joined_at": datetime.now(),
            "last_active": datetime.now()
        }
        
        try:
            await self.users.insert_one(user_data)
            logger.info(f"New user added: {user_id}")
            return user_data
        except Exception as e:
            logger.error(f"Error adding user: {e}")
            return None
    
    async def get_user(self, user_id: int) -> Optional[Dict]:
        """Get user from database"""
        return await self.users.find_one({"user_id": user_id})
    
    async def update_user(self, user_id: int, update_data: Dict) -> bool:
        """Update user data"""
        try:
            update_data["last_active"] = datetime.now()
            result = await self.users.update_one(
                {"user_id": user_id},
                {"$set": update_data}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating user: {e}")
            return False
    
    async def increment_user_stats(self, user_id: int, field: str, amount: int = 1) -> bool:
        """Increment user statistics"""
        try:
            await self.users.update_one(
                {"user_id": user_id},
                {
                    "$inc": {field: amount},
                    "$set": {"last_active": datetime.now()}
                }
            )
            return True
        except Exception as e:
            logger.error(f"Error incrementing user stats: {e}")
            return False
    
    async def get_all_users(self, banned: bool = False) -> List[Dict]:
        """Get all users"""
        return await self.users.find({"is_banned": banned}).to_list(None)
    
    async def get_total_users(self) -> int:
        """Get total user count"""
        return await self.users.count_documents({})
    
    async def get_leaderboard(self, limit: int = 10, by: str = "downloads") -> List[Dict]:
        """Get top users leaderboard"""
        return await self.users.find(
            {"is_banned": False}
        ).sort(by, DESCENDING).limit(limit).to_list(None)
    
    # ==================== FILE OPERATIONS ====================
    
    async def add_file(self, file_data: Dict) -> bool:
        """Add file to database"""
        try:
            file_data["added_at"] = datetime.now()
            file_data["downloads"] = 0
            file_data["last_downloaded"] = None
            
            await self.files.insert_one(file_data)
            logger.info(f"File added: {file_data.get('title')}")
            return True
        except Exception as e:
            logger.error(f"Error adding file: {e}")
            return False
    
    async def get_file(self, file_id: str) -> Optional[Dict]:
        """Get file by file_id"""
        return await self.files.find_one({"file_id": file_id})
    
    async def search_files(self, query: str, limit: int = 10) -> List[Dict]:
        """Search files by title"""
        # Text search
        results = await self.files.find(
            {"$text": {"$search": query}}
        ).limit(limit).to_list(None)
        
        # If no text search results, try regex
        if not results:
            results = await self.files.find(
                {"clean_title": {"$regex": query, "$options": "i"}}
            ).limit(limit).to_list(None)
        
        return results
    
    async def get_file_by_clean_title(self, clean_title: str) -> Optional[Dict]:
        """Get file by clean title (for duplicate check)"""
        return await self.files.find_one({"clean_title": clean_title})
    
    async def update_file(self, file_id: str, update_data: Dict) -> bool:
        """Update file data"""
        try:
            result = await self.files.update_one(
                {"file_id": file_id},
                {"$set": update_data}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating file: {e}")
            return False
    
    async def increment_file_downloads(self, file_id: str) -> bool:
        """Increment file download count"""
        try:
            await self.files.update_one(
                {"file_id": file_id},
                {
                    "$inc": {"downloads": 1},
                    "$set": {"last_downloaded": datetime.now()}
                }
            )
            return True
        except Exception as e:
            logger.error(f"Error incrementing downloads: {e}")
            return False
    
    async def delete_file(self, file_id: str) -> bool:
        """Delete file from database"""
        try:
            result = await self.files.delete_one({"file_id": file_id})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error deleting file: {e}")
            return False
    
    async def get_total_files(self) -> int:
        """Get total file count"""
        return await self.files.count_documents({})
    
    async def find_duplicates(self) -> List[Dict]:
        """Find duplicate files by clean_title"""
        pipeline = [
            {
                "$group": {
                    "_id": "$clean_title",
                    "count": {"$sum": 1},
                    "files": {"$push": "$$ROOT"}
                }
            },
            {
                "$match": {
                    "count": {"$gt": 1}
                }
            }
        ]
        return await self.files.aggregate(pipeline).to_list(None)
    
    async def get_most_downloaded(self, limit: int = 10) -> List[Dict]:
        """Get most downloaded files"""
        return await self.files.find().sort("downloads", DESCENDING).limit(limit).to_list(None)
    
    # ==================== REQUEST OPERATIONS ====================
    
    async def add_request(self, request_data: Dict) -> bool:
        """Add new request"""
        try:
            request_data["created_at"] = datetime.now()
            request_data["status"] = "pending"
            request_data["admin_response"] = None
            request_data["fulfilled_at"] = None
            
            await self.requests.insert_one(request_data)
            logger.info(f"Request added: {request_data.get('title')}")
            return True
        except Exception as e:
            logger.error(f"Error adding request: {e}")
            return False
    
    async def get_request(self, request_id: str) -> Optional[Dict]:
        """Get request by ID"""
        from bson import ObjectId
        try:
            return await self.requests.find_one({"_id": ObjectId(request_id)})
        except:
            return None
    
    async def get_user_requests(self, user_id: int, status: str = None) -> List[Dict]:
        """Get user's requests"""
        query = {"user_id": user_id}
        if status:
            query["status"] = status
        return await self.requests.find(query).sort("created_at", DESCENDING).to_list(None)
    
    async def get_pending_requests(self) -> List[Dict]:
        """Get all pending requests"""
        return await self.requests.find({"status": "pending"}).sort("created_at", DESCENDING).to_list(None)
    
    async def update_request_status(self, request_id: str, status: str, 
                                   admin_response: str = None) -> bool:
        """Update request status"""
        try:
            from bson import ObjectId
            update_data = {
                "status": status,
                "admin_response": admin_response
            }
            if status == "fulfilled":
                update_data["fulfilled_at"] = datetime.now()
            
            result = await self.requests.update_one(
                {"_id": ObjectId(request_id)},
                {"$set": update_data}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating request: {e}")
            return False
    
    async def get_request_stats(self) -> Dict:
        """Get request statistics"""
        total = await self.requests.count_documents({})
        pending = await self.requests.count_documents({"status": "pending"})
        fulfilled = await self.requests.count_documents({"status": "fulfilled"})
        rejected = await self.requests.count_documents({"status": "rejected"})
        
        return {
            "total": total,
            "pending": pending,
            "fulfilled": fulfilled,
            "rejected": rejected
        }
    
    async def get_most_requested(self, limit: int = 10) -> List[Dict]:
        """Get most requested titles"""
        pipeline = [
            {
                "$group": {
                    "_id": "$title",
                    "count": {"$sum": 1},
                    "tmdb_id": {"$first": "$tmdb_id"}
                }
            },
            {
                "$sort": {"count": -1}
            },
            {
                "$limit": limit
            }
        ]
        return await self.requests.aggregate(pipeline).to_list(None)
    
    # ==================== SEARCH OPERATIONS ====================
    
    async def log_search(self, user_id: int, query: str) -> bool:
        """Log search query"""
        try:
            await self.searches.update_one(
                {"query": query.lower()},
                {
                    "$inc": {"count": 1},
                    "$set": {"last_searched": datetime.now()},
                    "$push": {"users": user_id}
                },
                upsert=True
            )
            return True
        except Exception as e:
            logger.error(f"Error logging search: {e}")
            return False
    
    async def get_popular_searches(self, limit: int = 10) -> List[Dict]:
        """Get most popular searches"""
        return await self.searches.find().sort("count", DESCENDING).limit(limit).to_list(None)
    
    async def get_total_searches(self) -> int:
        """Get total search count"""
        pipeline = [
            {
                "$group": {
                    "_id": None,
                    "total": {"$sum": "$count"}
                }
            }
        ]
        result = await self.searches.aggregate(pipeline).to_list(None)
        return result[0]["total"] if result else 0
    
    # ==================== BROADCAST OPERATIONS ====================
    
    async def save_broadcast(self, broadcast_data: Dict) -> str:
        """Save broadcast message"""
        try:
            broadcast_data["created_at"] = datetime.now()
            broadcast_data["completed_at"] = None
            result = await self.broadcast.insert_one(broadcast_data)
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Error saving broadcast: {e}")
            return None
    
    async def update_broadcast_stats(self, broadcast_id: str, stats: Dict) -> bool:
        """Update broadcast statistics"""
        try:
            from bson import ObjectId
            result = await self.broadcast.update_one(
                {"_id": ObjectId(broadcast_id)},
                {"$set": stats}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating broadcast: {e}")
            return False
    
    # ==================== ANALYTICS OPERATIONS ====================
    
    async def save_analytics(self, analytics_type: str, data: Dict) -> bool:
        """Save analytics data"""
        try:
            analytics_data = {
                "type": analytics_type,
                "data": data,
                "timestamp": datetime.now()
            }
            await self.analytics.insert_one(analytics_data)
            return True
        except Exception as e:
            logger.error(f"Error saving analytics: {e}")
            return False
    
    async def get_analytics(self, analytics_type: str, days: int = 7) -> List[Dict]:
        """Get analytics data for specified days"""
        from datetime import timedelta
        start_date = datetime.now() - timedelta(days=days)
        
        return await self.analytics.find({
            "type": analytics_type,
            "timestamp": {"$gte": start_date}
        }).sort("timestamp", DESCENDING).to_list(None)
    
    # ==================== UTILITY OPERATIONS ====================
    
    async def backup_database(self) -> Dict:
        """Create database backup"""
        try:
            backup_data = {
                "users": await self.users.find().to_list(None),
                "files": await self.files.find().to_list(None),
                "requests": await self.requests.find().to_list(None),
                "searches": await self.searches.find().to_list(None),
                "broadcast": await self.broadcast.find().to_list(None),
                "analytics": await self.analytics.find().to_list(None),
                "backup_date": datetime.now()
            }
            return backup_data
        except Exception as e:
            logger.error(f"Error creating backup: {e}")
            return None
    
    async def close(self):
        """Close database connection"""
        self.client.close()
