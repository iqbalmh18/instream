import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'static/upload')
    LOG_FOLDER = os.getenv('LOG_FOLDER', 'logs')
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY')
    DEFAULT_LIVE_TITLE = os.getenv('DEFAULT_LIVE_TITLE', 'LIVE')
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_FILE_SIZE_MB', 1000)) * 1024 * 1024
    ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'flv', 'wmv'}
    MAX_STREAM_DURATION_HOURS = int(os.getenv('MAX_STREAM_DURATION_HOURS', 24))
    PERMANENT_SESSION_LIFETIME = timedelta(days=12)
    
    @staticmethod
    def init_app(app):
        for path in [Config.UPLOAD_FOLDER, Config.LOG_FOLDER]:
            os.makedirs(path, exist_ok=True)