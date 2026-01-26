"""Validation helper functions."""

from typing import Tuple, Optional
from config import Config


def validate_duration(hours: int, minutes: int, seconds: int) -> Tuple[bool, Optional[str]]:
    """
    Validate stream duration.
    
    Args:
        hours: Duration hours
        minutes: Duration minutes
        seconds: Duration seconds
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if hours < 0 or minutes < 0 or seconds < 0:
        return False, "Duration values cannot be negative"
    
    if minutes >= 60 or seconds >= 60:
        return False, "Minutes and seconds must be less than 60"
    
    total_hours = hours + (minutes / 60) + (seconds / 3600)
    if total_hours > Config.MAX_STREAM_DURATION_HOURS:
        return False, f"Maximum stream duration is {Config.MAX_STREAM_DURATION_HOURS} hours"
    
    return True, None


def validate_file(filename: str) -> bool:
    """
    Check if file extension is allowed.
    
    Args:
        filename: Name of file
        
    Returns:
        True if allowed, False otherwise
    """
    if '.' not in filename:
        return False
    extension = filename.rsplit('.', 1)[1].lower()
    return extension in Config.ALLOWED_VIDEO_EXTENSIONS


def validate_cookies_format(cookies: str) -> Tuple[bool, Optional[str]]:
    """
    Validate basic format of Instagram cookies.
    
    Args:
        cookies: Cookies string
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not cookies or not cookies.strip():
        return False, "Cookies are required"
    
    required_fields = ['sessionid', 'ds_user_id']
    cookies_lower = cookies.lower()
    missing_fields = [field for field in required_fields if field not in cookies_lower]
    
    if missing_fields:
        return False, f'Missing required cookie fields: {", ".join(missing_fields)}'
    
    return True, None
