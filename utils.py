import os
import time
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import current_app
from config import Config

def allowed_file(filename):
    """Check if file extension is allowed"""
    if '.' not in filename:
        return False
    extension = filename.rsplit('.', 1)[1].lower()
    return extension in Config.ALLOWED_VIDEO_EXTENSIONS

def get_file_size(filepath):
    """Get file size in bytes"""
    try:
        return os.path.getsize(filepath)
    except OSError:
        return 0

def format_file_size(size_bytes):
    """Format file size to human readable format"""
    if size_bytes == 0:
        return "0 B"
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    return f"{size_bytes:.1f} {size_names[i]}"

def get_file_creation_date(filepath):
    """Get file creation date"""
    try:
        timestamp = os.path.getctime(filepath)
        return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
    except OSError:
        return "Unknown"

def validate_duration(hours, minutes, seconds):
    """Validate stream duration"""
    if hours < 0 or minutes < 0 or seconds < 0:
        return False, "Duration values cannot be negative"
    
    if minutes >= 60 or seconds >= 60:
        return False, "Minutes and seconds must be less than 60"
    
    total_hours = hours + (minutes / 60) + (seconds / 3600)
    if total_hours > Config.MAX_STREAM_DURATION_HOURS:
        return False, f"Maximum stream duration is {Config.MAX_STREAM_DURATION_HOURS} hours"
    
    return True, None

def safe_remove_file(filepath):
    """Safely remove file if it exists"""
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
            return True
    except OSError as e:
        current_app.logger.error(f"Failed to remove file {filepath}: {str(e)}")
    return False

def get_video_files():
    """Get list of uploaded video files with metadata"""
    video_files = []
    upload_folder = Config.UPLOAD_FOLDER
    
    try:
        for filename in os.listdir(upload_folder):
            if allowed_file(filename):
                filepath = os.path.join(upload_folder, filename)
                video_files.append({
                    'filename': filename,
                    'size_bytes': get_file_size(filepath),
                    'size_formatted': format_file_size(get_file_size(filepath)),
                    'upload_date': get_file_creation_date(filepath),
                    'secure_filename': secure_filename(filename)
                })
        
        # Sort by upload date (newest first)
        video_files.sort(key=lambda x: x['upload_date'], reverse=True)
        
    except OSError as e:
        current_app.logger.error(f"Failed to list video files: {str(e)}")
    
    return video_files

class LiveStreamManager:
    """Manage live stream instances and sessions"""
    
    _instances = {}
    
    @classmethod
    def create_instance(cls, session_id, live_obj):
        """Create new live stream instance"""
        cls._instances[session_id] = {
            'live': live_obj,
            'created_at': time.time(),
            'active': True
        }
    
    @classmethod
    def get_instance(cls, session_id):
        """Get live stream instance"""
        return cls._instances.get(session_id, {}).get('live')
    
    @classmethod
    def remove_instance(cls, session_id):
        """Remove live stream instance"""
        if session_id in cls._instances:
            instance = cls._instances[session_id]
            if instance.get('live'):
                try:
                    instance['live'].stop()
                except Exception as e:
                    current_app.logger.error(f"Error stopping live instance: {str(e)}")
            del cls._instances[session_id]
    
    @classmethod
    def is_active(cls, session_id):
        """Check if live stream is active"""
        instance = cls._instances.get(session_id)
        return instance and instance.get('active', False)
    
    @classmethod
    def set_inactive(cls, session_id):
        """Set live stream as inactive"""
        if session_id in cls._instances:
            cls._instances[session_id]['active'] = False
    
    @classmethod
    def cleanup_old_instances(cls, max_age_hours=24):
        """Cleanup old inactive instances"""
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        
        to_remove = []
        for session_id, instance in cls._instances.items():
            age = current_time - instance.get('created_at', current_time)
            if age > max_age_seconds and not instance.get('active', False):
                to_remove.append(session_id)
        
        for session_id in to_remove:
            cls.remove_instance(session_id)