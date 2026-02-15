import aiohttp
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

class TMDBClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.themoviedb.org/3"
        self.image_base_url = "https://image.tmdb.org/t/p/w500"
        self.session = None
    
    async def init_session(self):
        """Initialize aiohttp session"""
        if not self.session:
            self.session = aiohttp.ClientSession()
    
    async def close_session(self):
        """Close aiohttp session"""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def search_movie(self, query: str, year: int = None, language: str = "en") -> List[Dict]:
        """Search for movies"""
        await self.init_session()
        
        try:
            params = {
                "api_key": self.api_key,
                "query": query,
                "language": language,
                "include_adult": False,
                "page": 1
            }
            
            if year:
                params["year"] = year
            
            async with self.session.get(f"{self.base_url}/search/movie", params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("results", [])
                else:
                    logger.error(f"TMDB API error: {response.status}")
                    return []
        except Exception as e:
            logger.error(f"Error searching movie: {e}")
            return []
    
    async def search_tv(self, query: str, year: int = None, language: str = "en") -> List[Dict]:
        """Search for TV shows"""
        await self.init_session()
        
        try:
            params = {
                "api_key": self.api_key,
                "query": query,
                "language": language,
                "include_adult": False,
                "page": 1
            }
            
            if year:
                params["first_air_date_year"] = year
            
            async with self.session.get(f"{self.base_url}/search/tv", params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("results", [])
                else:
                    logger.error(f"TMDB API error: {response.status}")
                    return []
        except Exception as e:
            logger.error(f"Error searching TV show: {e}")
            return []
    
    async def search_multi(self, query: str, language: str = "en") -> List[Dict]:
        """Search for movies and TV shows together"""
        await self.init_session()
        
        try:
            params = {
                "api_key": self.api_key,
                "query": query,
                "language": language,
                "include_adult": False,
                "page": 1
            }
            
            async with self.session.get(f"{self.base_url}/search/multi", params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    # Filter only movies and TV shows
                    results = [r for r in data.get("results", []) 
                             if r.get("media_type") in ["movie", "tv"]]
                    return results
                else:
                    logger.error(f"TMDB API error: {response.status}")
                    return []
        except Exception as e:
            logger.error(f"Error in multi search: {e}")
            return []
    
    async def get_movie_details(self, movie_id: int, language: str = "en") -> Optional[Dict]:
        """Get detailed movie information"""
        await self.init_session()
        
        try:
            params = {
                "api_key": self.api_key,
                "language": language,
                "append_to_response": "credits,videos,release_dates"
            }
            
            async with self.session.get(f"{self.base_url}/movie/{movie_id}", params=params) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"TMDB API error: {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Error getting movie details: {e}")
            return None
    
    async def get_tv_details(self, tv_id: int, language: str = "en") -> Optional[Dict]:
        """Get detailed TV show information"""
        await self.init_session()
        
        try:
            params = {
                "api_key": self.api_key,
                "language": language,
                "append_to_response": "credits,videos"
            }
            
            async with self.session.get(f"{self.base_url}/tv/{tv_id}", params=params) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"TMDB API error: {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Error getting TV details: {e}")
            return None
    
    def get_poster_url(self, poster_path: str, size: str = "w500") -> Optional[str]:
        """Get full poster URL"""
        if poster_path:
            return f"https://image.tmdb.org/t/p/{size}{poster_path}"
        return None
    
    def get_backdrop_url(self, backdrop_path: str, size: str = "original") -> Optional[str]:
        """Get full backdrop URL"""
        if backdrop_path:
            return f"https://image.tmdb.org/t/p/{size}{backdrop_path}"
        return None
    
    def format_movie_result(self, movie: Dict) -> Dict:
        """Format movie result for display"""
        return {
            "id": movie.get("id"),
            "title": movie.get("title", "Unknown"),
            "original_title": movie.get("original_title"),
            "year": movie.get("release_date", "")[:4] if movie.get("release_date") else None,
            "overview": movie.get("overview", "No description available"),
            "poster": self.get_poster_url(movie.get("poster_path")),
            "backdrop": self.get_backdrop_url(movie.get("backdrop_path")),
            "rating": movie.get("vote_average", 0),
            "popularity": movie.get("popularity", 0),
            "media_type": "movie"
        }
    
    def format_tv_result(self, tv: Dict) -> Dict:
        """Format TV show result for display"""
        return {
            "id": tv.get("id"),
            "title": tv.get("name", "Unknown"),
            "original_title": tv.get("original_name"),
            "year": tv.get("first_air_date", "")[:4] if tv.get("first_air_date") else None,
            "overview": tv.get("overview", "No description available"),
            "poster": self.get_poster_url(tv.get("poster_path")),
            "backdrop": self.get_backdrop_url(tv.get("backdrop_path")),
            "rating": tv.get("vote_average", 0),
            "popularity": tv.get("popularity", 0),
            "media_type": "tv"
        }
    
    def format_multi_result(self, item: Dict) -> Dict:
        """Format multi search result"""
        media_type = item.get("media_type")
        
        if media_type == "movie":
            return self.format_movie_result(item)
        elif media_type == "tv":
            return self.format_tv_result(item)
        else:
            return None
    
    async def get_formatted_results(self, query: str, year: int = None, 
                                   search_type: str = "multi", limit: int = 10) -> List[Dict]:
        """Get formatted search results"""
        results = []
        
        try:
            if search_type == "movie":
                raw_results = await self.search_movie(query, year)
                results = [self.format_movie_result(m) for m in raw_results[:limit]]
            elif search_type == "tv":
                raw_results = await self.search_tv(query, year)
                results = [self.format_tv_result(t) for t in raw_results[:limit]]
            else:  # multi
                raw_results = await self.search_multi(query)
                formatted = [self.format_multi_result(r) for r in raw_results]
                results = [r for r in formatted if r is not None][:limit]
        except Exception as e:
            logger.error(f"Error getting formatted results: {e}")
        
        return results
    
    def create_movie_caption(self, movie: Dict, language: str = "sinhala") -> str:
        """Create caption for movie with details"""
        title = movie.get("title", "Unknown")
        year = movie.get("year", "N/A")
        rating = movie.get("rating", 0)
        overview = movie.get("overview", "")
        
        # Truncate overview to 200 characters
        if len(overview) > 200:
            overview = overview[:200] + "..."
        
        if language == "sinhala":
            caption = f"🎬 **{title}**"
            if year:
                caption += f" ({year})"
            caption += f"\n\n⭐ Rating: {rating}/10\n\n"
            caption += f"📝 {overview}\n"
        else:
            caption = f"🎬 **{title}**"
            if year:
                caption += f" ({year})"
            caption += f"\n\n⭐ Rating: {rating}/10\n\n"
            caption += f"📝 {overview}\n"
        
        return caption
    
    async def get_trending(self, media_type: str = "movie", time_window: str = "week", 
                          language: str = "en") -> List[Dict]:
        """Get trending movies or TV shows"""
        await self.init_session()
        
        try:
            params = {
                "api_key": self.api_key,
                "language": language
            }
            
            url = f"{self.base_url}/trending/{media_type}/{time_window}"
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    results = data.get("results", [])
                    
                    if media_type == "movie":
                        return [self.format_movie_result(m) for m in results]
                    else:
                        return [self.format_tv_result(t) for t in results]
                else:
                    logger.error(f"TMDB API error: {response.status}")
                    return []
        except Exception as e:
            logger.error(f"Error getting trending: {e}")
            return []
    
    async def get_popular(self, media_type: str = "movie", language: str = "en") -> List[Dict]:
        """Get popular movies or TV shows"""
        await self.init_session()
        
        try:
            params = {
                "api_key": self.api_key,
                "language": language,
                "page": 1
            }
            
            url = f"{self.base_url}/{media_type}/popular"
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    results = data.get("results", [])
                    
                    if media_type == "movie":
                        return [self.format_movie_result(m) for m in results]
                    else:
                        return [self.format_tv_result(t) for t in results]
                else:
                    logger.error(f"TMDB API error: {response.status}")
                    return []
        except Exception as e:
            logger.error(f"Error getting popular: {e}")
            return []
