from pyrogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton
)
from typing import List, Dict, Optional
from utils import Utils

class Keyboards:
    
    # ==================== MAIN MENU KEYBOARDS ====================
    
    @staticmethod
    def main_menu(language: str = "sinhala") -> InlineKeyboardMarkup:
        """Main menu keyboard"""
        if language == "sinhala":
            buttons = [
                [
                    InlineKeyboardButton("🔍 සොයන්න", callback_data="menu:search"),
                    InlineKeyboardButton("📝 Request", callback_data="menu:request")
                ],
                [
                    InlineKeyboardButton("👤 Profile", callback_data="menu:profile"),
                    InlineKeyboardButton("🏆 Leaderboard", callback_data="menu:leaderboard")
                ],
                [
                    InlineKeyboardButton("❓ උදව්", callback_data="menu:help"),
                    InlineKeyboardButton("🌐 භාෂාව", callback_data="menu:language")
                ]
            ]
        else:
            buttons = [
                [
                    InlineKeyboardButton("🔍 Search", callback_data="menu:search"),
                    InlineKeyboardButton("📝 Request", callback_data="menu:request")
                ],
                [
                    InlineKeyboardButton("👤 Profile", callback_data="menu:profile"),
                    InlineKeyboardButton("🏆 Leaderboard", callback_data="menu:leaderboard")
                ],
                [
                    InlineKeyboardButton("❓ Help", callback_data="menu:help"),
                    InlineKeyboardButton("🌐 Language", callback_data="menu:language")
                ]
            ]
        
        return InlineKeyboardMarkup(buttons)
    
    @staticmethod
    def language_menu() -> InlineKeyboardMarkup:
        """Language selection menu"""
        buttons = [
            [
                InlineKeyboardButton("🇱🇰 සිංහල", callback_data="lang:sinhala"),
                InlineKeyboardButton("🇬🇧 English", callback_data="lang:english")
            ],
            [
                InlineKeyboardButton("◀️ ආපසු / Back", callback_data="menu:main")
            ]
        ]
        return InlineKeyboardMarkup(buttons)
    
    @staticmethod
    def help_menu(language: str = "sinhala") -> InlineKeyboardMarkup:
        """Help menu keyboard"""
        if language == "sinhala":
            buttons = [
                [InlineKeyboardButton("◀️ ආපසු", callback_data="menu:main")]
            ]
        else:
            buttons = [
                [InlineKeyboardButton("◀️ Back", callback_data="menu:main")]
            ]
        
        return InlineKeyboardMarkup(buttons)
    
    # ==================== SEARCH RESULT KEYBOARDS ====================
    
    @staticmethod
    def search_results(files: List[Dict], page: int = 0, language: str = "sinhala") -> InlineKeyboardMarkup:
        """Create keyboard for search results"""
        buttons = []
        
        # Show 10 results per page
        start_idx = page * 10
        end_idx = start_idx + 10
        page_files = files[start_idx:end_idx]
        
        for file in page_files:
            file_id = file.get("file_id")
            title = file.get("title", "Unknown")
            file_size = file.get("file_size", 0)
            year = file.get("year")
            
            # Format button text
            button_text = Utils.format_button_text(file_size, title, year)
            
            buttons.append([
                InlineKeyboardButton(button_text, callback_data=f"file:{file_id}")
            ])
        
        # Navigation buttons
        nav_buttons = []
        
        # Previous button
        if page > 0:
            nav_buttons.append(
                InlineKeyboardButton("◀️ Previous", callback_data=f"page:{page-1}")
            )
        
        # Page indicator
        total_pages = (len(files) + 9) // 10  # Ceiling division
        nav_buttons.append(
            InlineKeyboardButton(f"{page + 1}/{total_pages}", callback_data="noop")
        )
        
        # Next button
        if end_idx < len(files):
            nav_buttons.append(
                InlineKeyboardButton("Next ▶️", callback_data=f"page:{page+1}")
            )
        
        if nav_buttons:
            buttons.append(nav_buttons)
        
        # Back to menu button
        if language == "sinhala":
            buttons.append([
                InlineKeyboardButton("🏠 මුල් පිටුව", callback_data="menu:main")
            ])
        else:
            buttons.append([
                InlineKeyboardButton("🏠 Main Menu", callback_data="menu:main")
            ])
        
        return InlineKeyboardMarkup(buttons)
    
    @staticmethod
    def no_results(language: str = "sinhala") -> InlineKeyboardMarkup:
        """No results found keyboard"""
        if language == "sinhala":
            buttons = [
                [InlineKeyboardButton("📝 Request කරන්න", callback_data="request:start")],
                [InlineKeyboardButton("🏠 මුල් පිටුව", callback_data="menu:main")]
            ]
        else:
            buttons = [
                [InlineKeyboardButton("📝 Request", callback_data="request:start")],
                [InlineKeyboardButton("🏠 Main Menu", callback_data="menu:main")]
            ]
        
        return InlineKeyboardMarkup(buttons)
    
    # ==================== TMDB SEARCH KEYBOARDS ====================
    
    @staticmethod
    def tmdb_results(movies: List[Dict], language: str = "sinhala") -> InlineKeyboardMarkup:
        """Create keyboard for TMDB search results"""
        buttons = []
        
        for movie in movies[:10]:  # Limit to 10 results
            tmdb_id = movie.get("id")
            title = movie.get("title", "Unknown")
            year = movie.get("year", "")
            media_type = movie.get("media_type", "movie")
            
            display_title = f"{title} ({year})" if year else title
            display_title = Utils.truncate_text(display_title, 40)
            
            buttons.append([
                InlineKeyboardButton(
                    display_title,
                    callback_data=f"tmdb:{media_type}:{tmdb_id}"
                )
            ])
        
        # Cancel button
        if language == "sinhala":
            buttons.append([
                InlineKeyboardButton("❌ අවලංගු කරන්න", callback_data="request:cancel")
            ])
        else:
            buttons.append([
                InlineKeyboardButton("❌ Cancel", callback_data="request:cancel")
            ])
        
        return InlineKeyboardMarkup(buttons)
    
    @staticmethod
    def tmdb_details(tmdb_id: int, media_type: str, language: str = "sinhala") -> InlineKeyboardMarkup:
        """Create keyboard for TMDB movie details"""
        if language == "sinhala":
            buttons = [
                [InlineKeyboardButton(
                    "✅ මේක Request කරන්න",
                    callback_data=f"request:confirm:{media_type}:{tmdb_id}"
                )],
                [InlineKeyboardButton("◀️ ආපසු", callback_data="request:start")]
            ]
        else:
            buttons = [
                [InlineKeyboardButton(
                    "✅ Request This",
                    callback_data=f"request:confirm:{media_type}:{tmdb_id}"
                )],
                [InlineKeyboardButton("◀️ Back", callback_data="request:start")]
            ]
        
        return InlineKeyboardMarkup(buttons)
    
    # ==================== REQUEST KEYBOARDS ====================
    
    @staticmethod
    def request_actions(request_id: str, user_id: int) -> InlineKeyboardMarkup:
        """Create keyboard for admin to handle requests"""
        buttons = [
            [
                InlineKeyboardButton("✅ Done", callback_data=f"req_done:{request_id}:{user_id}"),
                InlineKeyboardButton("❌ No", callback_data=f"req_no:{request_id}:{user_id}")
            ]
        ]
        return InlineKeyboardMarkup(buttons)
    
    # ==================== ADMIN KEYBOARDS ====================
    
    @staticmethod
    def admin_menu() -> InlineKeyboardMarkup:
        """Admin menu keyboard"""
        buttons = [
            [
                InlineKeyboardButton("📊 Statistics", callback_data="admin:stats"),
                InlineKeyboardButton("📢 Broadcast", callback_data="admin:broadcast")
            ],
            [
                InlineKeyboardButton("💾 Backup", callback_data="admin:backup"),
                InlineKeyboardButton("🔍 Scan Duplicates", callback_data="admin:scan")
            ],
            [
                InlineKeyboardButton("📝 Pending Requests", callback_data="admin:requests"),
                InlineKeyboardButton("📈 Analytics", callback_data="admin:analytics")
            ],
            [
                InlineKeyboardButton("👥 User Management", callback_data="admin:users"),
                InlineKeyboardButton("📁 File Management", callback_data="admin:files")
            ],
            [
                InlineKeyboardButton("❌ Close", callback_data="admin:close")
            ]
        ]
        return InlineKeyboardMarkup(buttons)
    
    @staticmethod
    def broadcast_confirm() -> InlineKeyboardMarkup:
        """Broadcast confirmation keyboard"""
        buttons = [
            [
                InlineKeyboardButton("✅ Confirm", callback_data="broadcast:confirm"),
                InlineKeyboardButton("❌ Cancel", callback_data="broadcast:cancel")
            ]
        ]
        return InlineKeyboardMarkup(buttons)
    
    @staticmethod
    def scan_actions(duplicate_count: int) -> InlineKeyboardMarkup:
        """Scan duplicates action keyboard"""
        buttons = [
            [
                InlineKeyboardButton(
                    f"🗑️ Delete {duplicate_count} Duplicates",
                    callback_data="scan:delete"
                )
            ],
            [
                InlineKeyboardButton("❌ Cancel", callback_data="scan:cancel")
            ]
        ]
        return InlineKeyboardMarkup(buttons)
    
    # ==================== PROFILE KEYBOARDS ====================
    
    @staticmethod
    def profile_menu(language: str = "sinhala") -> InlineKeyboardMarkup:
        """Profile menu keyboard"""
        if language == "sinhala":
            buttons = [
                [InlineKeyboardButton("📥 මගේ Downloads", callback_data="profile:downloads")],
                [InlineKeyboardButton("📝 මගේ Requests", callback_data="profile:requests")],
                [InlineKeyboardButton("◀️ ආපසු", callback_data="menu:main")]
            ]
        else:
            buttons = [
                [InlineKeyboardButton("📥 My Downloads", callback_data="profile:downloads")],
                [InlineKeyboardButton("📝 My Requests", callback_data="profile:requests")],
                [InlineKeyboardButton("◀️ Back", callback_data="menu:main")]
            ]
        
        return InlineKeyboardMarkup(buttons)
    
    # ==================== FORCE SUBSCRIBE KEYBOARD ====================
    
    @staticmethod
    def force_subscribe(channel_username: str, language: str = "sinhala") -> InlineKeyboardMarkup:
        """Force subscribe keyboard"""
        if language == "sinhala":
            buttons = [
                [InlineKeyboardButton("📢 Channel එකට Join වන්න", url=f"https://t.me/{channel_username}")],
                [InlineKeyboardButton("🔄 Check කරන්න", callback_data="check:subscription")]
            ]
        else:
            buttons = [
                [InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{channel_username}")],
                [InlineKeyboardButton("🔄 Check Subscription", callback_data="check:subscription")]
            ]
        
        return InlineKeyboardMarkup(buttons)
    
    # ==================== UTILITY KEYBOARDS ====================
    
    @staticmethod
    def close_button(language: str = "sinhala") -> InlineKeyboardMarkup:
        """Simple close button"""
        if language == "sinhala":
            buttons = [[InlineKeyboardButton("❌ වසන්න", callback_data="close")]]
        else:
            buttons = [[InlineKeyboardButton("❌ Close", callback_data="close")]]
        
        return InlineKeyboardMarkup(buttons)
    
    @staticmethod
    def back_to_main(language: str = "sinhala") -> InlineKeyboardMarkup:
        """Back to main menu button"""
        if language == "sinhala":
            buttons = [[InlineKeyboardButton("🏠 මුල් පිටුව", callback_data="menu:main")]]
        else:
            buttons = [[InlineKeyboardButton("🏠 Main Menu", callback_data="menu:main")]]
        
        return InlineKeyboardMarkup(buttons)
    
    @staticmethod
    def url_button(text: str, url: str) -> InlineKeyboardMarkup:
        """Single URL button"""
        buttons = [[InlineKeyboardButton(text, url=url)]]
        return InlineKeyboardMarkup(buttons)
    
    @staticmethod
    def custom_buttons(buttons_data: List[List[Dict]]) -> InlineKeyboardMarkup:
        """Create custom keyboard from data"""
        buttons = []
        for row in buttons_data:
            button_row = []
            for btn in row:
                if "url" in btn:
                    button_row.append(
                        InlineKeyboardButton(btn["text"], url=btn["url"])
                    )
                elif "callback_data" in btn:
                    button_row.append(
                        InlineKeyboardButton(btn["text"], callback_data=btn["callback_data"])
                    )
            buttons.append(button_row)
        
        return InlineKeyboardMarkup(buttons)
    
    # ==================== LEADERBOARD KEYBOARDS ====================
    
    @staticmethod
    def leaderboard_menu(language: str = "sinhala") -> InlineKeyboardMarkup:
        """Leaderboard type selection"""
        if language == "sinhala":
            buttons = [
                [
                    InlineKeyboardButton("📥 Downloads", callback_data="leaderboard:downloads"),
                    InlineKeyboardButton("⭐ Points", callback_data="leaderboard:points")
                ],
                [
                    InlineKeyboardButton("📝 Requests", callback_data="leaderboard:requests"),
                    InlineKeyboardButton("🔍 Searches", callback_data="leaderboard:searches")
                ],
                [InlineKeyboardButton("◀️ ආපසු", callback_data="menu:main")]
            ]
        else:
            buttons = [
                [
                    InlineKeyboardButton("📥 Downloads", callback_data="leaderboard:downloads"),
                    InlineKeyboardButton("⭐ Points", callback_data="leaderboard:points")
                ],
                [
                    InlineKeyboardButton("📝 Requests", callback_data="leaderboard:requests"),
                    InlineKeyboardButton("🔍 Searches", callback_data="leaderboard:searches")
                ],
                [InlineKeyboardButton("◀️ Back", callback_data="menu:main")]
            ]
        
        return InlineKeyboardMarkup(buttons)
    
    # ==================== PAGINATION ====================
    
    @staticmethod
    def paginated_buttons(items: List[Dict], page: int, items_per_page: int,
                         callback_prefix: str, language: str = "sinhala") -> InlineKeyboardMarkup:
        """Create paginated buttons"""
        buttons = []
        
        start_idx = page * items_per_page
        end_idx = start_idx + items_per_page
        page_items = items[start_idx:end_idx]
        
        # Item buttons
        for item in page_items:
            buttons.append([
                InlineKeyboardButton(
                    item.get("text", "Unknown"),
                    callback_data=f"{callback_prefix}:{item.get('id')}"
                )
            ])
        
        # Navigation
        nav_buttons = []
        total_pages = (len(items) + items_per_page - 1) // items_per_page
        
        if page > 0:
            nav_buttons.append(
                InlineKeyboardButton("◀️", callback_data=f"{callback_prefix}_page:{page-1}")
            )
        
        nav_buttons.append(
            InlineKeyboardButton(f"{page + 1}/{total_pages}", callback_data="noop")
        )
        
        if end_idx < len(items):
            nav_buttons.append(
                InlineKeyboardButton("▶️", callback_data=f"{callback_prefix}_page:{page+1}")
            )
        
        if nav_buttons:
            buttons.append(nav_buttons)
        
        # Back button
        if language == "sinhala":
            buttons.append([InlineKeyboardButton("◀️ ආපසු", callback_data="menu:main")])
        else:
            buttons.append([InlineKeyboardButton("◀️ Back", callback_data="menu:main")])
        
        return InlineKeyboardMarkup(buttons)
    
    # ==================== FILE DETAILS KEYBOARD ====================
    
    @staticmethod
    def file_details(file_id: str, language: str = "sinhala") -> InlineKeyboardMarkup:
        """File details keyboard with download button"""
        if language == "sinhala":
            buttons = [
                [InlineKeyboardButton("📥 Download කරන්න", callback_data=f"download:{file_id}")],
                [InlineKeyboardButton("◀️ ආපසු", callback_data="search:back")]
            ]
        else:
            buttons = [
                [InlineKeyboardButton("📥 Download", callback_data=f"download:{file_id}")],
                [InlineKeyboardButton("◀️ Back", callback_data="search:back")]
            ]
        
        return InlineKeyboardMarkup(buttons)
