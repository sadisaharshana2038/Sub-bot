import re
from typing import List, Dict, Optional
from fuzzywuzzy import fuzz, process
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class Utils:
    @staticmethod
    def clean_filename(filename: str, patterns: List[str] = None) -> str:
        """Clean filename by removing unwanted patterns"""
        from config import Config
        
        if patterns is None:
            patterns = Config.CLEAN_PATTERNS
        
        cleaned = filename
        
        # Remove patterns
        for pattern in patterns:
            cleaned = re.sub(pattern, '', cleaned)
        
        # Remove extra spaces and special characters
        cleaned = re.sub(r'\s+', ' ', cleaned)
        cleaned = cleaned.strip()
        
        # Remove file extension if present
        cleaned = re.sub(r'\.(srt|ass|sub|ssa)$', '', cleaned, flags=re.IGNORECASE)
        
        return cleaned
    
    @staticmethod
    def extract_year(filename: str) -> Optional[int]:
        """Extract year from filename"""
        # Look for 4-digit year between 1900-2099
        year_match = re.search(r'(19\d{2}|20\d{2})', filename)
        if year_match:
            return int(year_match.group(1))
        return None
    
    @staticmethod
    def extract_quality(filename: str) -> Optional[str]:
        """Extract quality from filename"""
        quality_patterns = [
            r'(4K|2160p|1080p|720p|480p|360p)',
            r'(BluRay|BRRip|WEBRip|HDRip|DVDRip)',
            r'(HEVC|x264|x265|H\.264|H\.265)'
        ]
        
        for pattern in quality_patterns:
            match = re.search(pattern, filename, re.IGNORECASE)
            if match:
                return match.group(1)
        return None
    
    @staticmethod
    def format_file_size(size_bytes: int) -> str:
        """Format file size to human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} TB"
    
    @staticmethod
    def fuzzy_search(query: str, choices: List[str], threshold: int = 70) -> List[tuple]:
        """Fuzzy search with threshold"""
        return process.extract(query, choices, scorer=fuzz.token_sort_ratio, limit=None)
    
    @staticmethod
    def calculate_rank(downloads: int) -> str:
        """Calculate user rank based on downloads"""
        from config import Config
        
        rank = Config.RANKS[0]  # Default rank
        for threshold, rank_name in sorted(Config.RANKS.items(), reverse=True):
            if downloads >= threshold:
                rank = rank_name
                break
        return rank
    
    @staticmethod
    def format_duration(seconds: int) -> str:
        """Format duration to readable format"""
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        
        if hours > 0:
            return f"{hours}h {minutes}m {secs}s"
        elif minutes > 0:
            return f"{minutes}m {secs}s"
        else:
            return f"{secs}s"
    
    @staticmethod
    def format_date(date: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
        """Format datetime to string"""
        if date:
            return date.strftime(format_str)
        return "N/A"
    
    @staticmethod
    def parse_callback_data(data: str) -> Dict:
        """Parse callback data from inline button"""
        try:
            parts = data.split(":")
            return {
                "action": parts[0],
                "data": ":".join(parts[1:]) if len(parts) > 1 else None
            }
        except:
            return {"action": data, "data": None}
    
    @staticmethod
    def create_progress_bar(current: int, total: int, length: int = 20) -> str:
        """Create progress bar"""
        if total == 0:
            return "█" * length
        
        filled = int(length * current / total)
        bar = "█" * filled + "░" * (length - filled)
        percentage = (current / total) * 100
        
        return f"{bar} {percentage:.1f}%"
    
    @staticmethod
    def escape_markdown(text: str) -> str:
        """Escape markdown special characters"""
        special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
        for char in special_chars:
            text = text.replace(char, f'\\{char}')
        return text
    
    @staticmethod
    def truncate_text(text: str, max_length: int = 50, suffix: str = "...") -> str:
        """Truncate text to max length"""
        if len(text) <= max_length:
            return text
        return text[:max_length - len(suffix)] + suffix
    
    @staticmethod
    def extract_movie_info(filename: str) -> Dict:
        """Extract all movie information from filename"""
        info = {
            "clean_title": Utils.clean_filename(filename),
            "year": Utils.extract_year(filename),
            "quality": Utils.extract_quality(filename),
            "original_name": filename
        }
        return info
    
    @staticmethod
    def format_button_text(file_size: int, title: str, year: Optional[int] = None) -> str:
        """Format button text with size, title, and year"""
        size_str = Utils.format_file_size(file_size)
        truncated_title = Utils.truncate_text(title, 30)
        
        if year:
            return f"{size_str} | {truncated_title} ({year})"
        else:
            return f"{size_str} | {truncated_title}"
    
    @staticmethod
    def is_valid_year(year: Optional[int]) -> bool:
        """Check if year is valid"""
        if year is None:
            return False
        current_year = datetime.now().year
        return 1900 <= year <= current_year + 2
    
    @staticmethod
    def split_list(lst: List, chunk_size: int) -> List[List]:
        """Split list into chunks"""
        return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]
    
    @staticmethod
    def generate_file_caption(file_data: Dict, language: str = "sinhala") -> str:
        """Generate caption for file"""
        title = file_data.get("title", "Unknown")
        year = file_data.get("year", "N/A")
        quality = file_data.get("quality", "N/A")
        size = Utils.format_file_size(file_data.get("file_size", 0))
        downloads = file_data.get("downloads", 0)
        
        if language == "sinhala":
            caption = f"📁 **{title}**\n\n"
            caption += f"📅 වර්ෂය: {year}\n"
            caption += f"🎬 ගුණාත්මකභාවය: {quality}\n"
            caption += f"📦 ප්‍රමාණය: {size}\n"
            caption += f"📥 Downloads: {downloads}\n"
        else:
            caption = f"📁 **{title}**\n\n"
            caption += f"📅 Year: {year}\n"
            caption += f"🎬 Quality: {quality}\n"
            caption += f"📦 Size: {size}\n"
            caption += f"📥 Downloads: {downloads}\n"
        
        return caption
    
    @staticmethod
    def sanitize_query(query: str) -> str:
        """Sanitize search query"""
        # Remove special characters except spaces and alphanumeric
        sanitized = re.sub(r'[^\w\s]', '', query)
        # Remove extra spaces
        sanitized = re.sub(r'\s+', ' ', sanitized)
        return sanitized.strip().lower()
    
    @staticmethod
    def validate_url(url: str) -> bool:
        """Validate URL format"""
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        return url_pattern.match(url) is not None
    
    @staticmethod
    def get_file_extension(filename: str) -> str:
        """Get file extension"""
        match = re.search(r'\.(srt|ass|sub|ssa)$', filename, re.IGNORECASE)
        if match:
            return match.group(1).lower()
        return "srt"
    
    @staticmethod
    def compare_titles(title1: str, title2: str, threshold: int = 80) -> bool:
        """Compare two titles using fuzzy matching"""
        score = fuzz.ratio(title1.lower(), title2.lower())
        return score >= threshold
    
    @staticmethod
    def extract_message_text(message) -> str:
        """Extract text from message or caption"""
        if message.text:
            return message.text
        elif message.caption:
            return message.caption
        return ""
    
    @staticmethod
    def format_leaderboard(users: List[Dict], language: str = "sinhala") -> str:
        """Format leaderboard message"""
        if language == "sinhala":
            message = "🏆 **Top 10 Users**\n\n"
            medals = ["🥇", "🥈", "🥉"]
        else:
            message = "🏆 **Top 10 Users**\n\n"
            medals = ["🥇", "🥈", "🥉"]
        
        for idx, user in enumerate(users, 1):
            medal = medals[idx - 1] if idx <= 3 else f"{idx}."
            name = user.get("first_name", "Unknown")
            downloads = user.get("downloads", 0)
            points = user.get("points", 0)
            
            message += f"{medal} {name}\n"
            message += f"   📥 {downloads} downloads | ⭐ {points} points\n\n"
        
        return message
    
    @staticmethod
    def format_stats(stats: Dict, language: str = "sinhala") -> str:
        """Format statistics message"""
        if language == "sinhala":
            message = "📊 **Bot Statistics**\n\n"
            message += f"👥 Total Users: {stats.get('total_users', 0)}\n"
            message += f"📁 Total Files: {stats.get('total_files', 0)}\n"
            message += f"📥 Total Downloads: {stats.get('total_downloads', 0)}\n"
            message += f"🔍 Total Searches: {stats.get('total_searches', 0)}\n"
            message += f"📝 Pending Requests: {stats.get('pending_requests', 0)}\n"
            message += f"✅ Fulfilled Requests: {stats.get('fulfilled_requests', 0)}\n"
        else:
            message = "📊 **Bot Statistics**\n\n"
            message += f"👥 Total Users: {stats.get('total_users', 0)}\n"
            message += f"📁 Total Files: {stats.get('total_files', 0)}\n"
            message += f"📥 Total Downloads: {stats.get('total_downloads', 0)}\n"
            message += f"🔍 Total Searches: {stats.get('total_searches', 0)}\n"
            message += f"📝 Pending Requests: {stats.get('pending_requests', 0)}\n"
            message += f"✅ Fulfilled Requests: {stats.get('fulfilled_requests', 0)}\n"
        
        return message
