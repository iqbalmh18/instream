"""Video service for video operations."""

from typing import Dict, Any, Optional
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
from pygramcl import Download, Client
from flask import current_app
from urllib.parse import urlparse
import os
import time

from config import Config
from utils import allowed_file, get_file_size, format_file_size


class VideoService:
    """Handle video upload and download operations."""
    
    @staticmethod
    def upload_video(video_file: FileStorage) -> Dict[str, Any]:
        """
        Upload video file to server.
        
        Args:
            video_file: Video file from request
            
        Returns:
            Dict with success status and filename or error message
        """
        try:
            if not video_file or video_file.filename == '':
                return {
                    'success': False,
                    'message': 'No video file provided'
                }
            
            if not allowed_file(video_file.filename):
                return {
                    'success': False,
                    'message': f'Invalid file format. Allowed: {", ".join(Config.ALLOWED_VIDEO_EXTENSIONS)}'
                }
            
            filename = secure_filename(video_file.filename)
            name, ext = os.path.splitext(filename)
            filename = f"ig_upload_{int(time.time())}{ext}"
            
            filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
            video_file.save(filepath)
            
            return {
                'success': True,
                'message': 'Video uploaded successfully',
                'filename': filename
            }
            
        except Exception as e:
            current_app.logger.error(f"Upload error: {str(e)}")
            return {
                'success': False,
                'message': f'Upload failed: {str(e)}'
            }
    
    @staticmethod
    def download_video(url: str, cookies: Optional[str] = None) -> Dict[str, Any]:
        """
        Download video from URL (supports Instagram URLs).
        
        Args:
            url: Video URL
            cookies: Instagram cookies (required for Instagram URLs)
            
        Returns:
            Dict with success status and file info or error message
        """
        try:
            # Validate URL
            parsed = urlparse(url)
            if not all([parsed.scheme, parsed.netloc]):
                return {
                    'success': False,
                    'message': 'Invalid URL format'
                }
            
            # Handle Instagram URLs
            if 'instagram.com' in url and ('/p/' in url or '/reel/' in url):
                if not cookies:
                    return {
                        'success': False,
                        'message': 'Instagram cookies required for Instagram URLs'
                    }
                
                return VideoService._download_instagram_video(url, cookies)
            
            # Handle direct video URLs
            return VideoService._download_direct_url(url)
            
        except Exception as e:
            current_app.logger.error(f"Download error: {str(e)}")
            return {
                'success': False,
                'message': f'Download process failed: {str(e)}'
            }
    
    @staticmethod
    def _download_instagram_video(post_url: str, cookies: str) -> Dict[str, Any]:
        """Download video from Instagram post using pygramcl."""
        try:
            from pygramcl import Client
            
            client = Client(cookies=cookies)
            filename = f'ig_download_{int(time.time())}'
            
            # Use Client's download_post method
            result = client.download_post(
                url=post_url,
                filename=filename,
                directory=Config.UPLOAD_FOLDER
            )
            
            if not result:
                return {
                    'success': False,
                    'message': 'Failed to download Instagram video'
                }
            
            # Get the downloaded file info
            if isinstance(result, dict):
                filename = os.path.basename(result.get('file', ''))
                filesize = result.get('size', 'Unknown')
            elif isinstance(result, str):
                filename = os.path.basename(result)
                try:
                    full_path = os.path.join(Config.UPLOAD_FOLDER, filename)
                    size_bytes = os.path.getsize(full_path)
                    filesize = f"{size_bytes / (1024*1024):.2f} MB"
                except:
                    filesize = 'Unknown'
            else:
                filename = f"{filename}.mp4"  # Default extension
                filesize = 'Unknown'
            
            return {
                'success': True,
                'message': 'Instagram video downloaded successfully',
                'filename': filename,
                'filesize': filesize
            }
            
        except Exception as e:
            current_app.logger.error(f"Instagram download error: {str(e)}")
            return {
                'success': False,
                'message': f'Failed to download from Instagram: {str(e)}'
            }
    
    @staticmethod
    def _download_direct_url(url: str) -> Dict[str, Any]:
        """Download video from direct URL."""
        try:
            import requests
            
            filename = f'ig_download_{int(time.time())}.mp4'
            filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
            
            # Download with streaming
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            # Check if it's actually a video
            content_type = response.headers.get('content-type', '')
            if not any(vtype in content_type.lower() for vtype in ['video', 'octet-stream']):
                return {
                    'success': False,
                    'message': f'URL does not point to a video file (Content-Type: {content_type})'
                }
            
            # Save the file
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            # Get file size
            size_bytes = os.path.getsize(filepath)
            filesize = f"{size_bytes / (1024*1024):.2f} MB"
            
            return {
                'success': True,
                'message': 'Video downloaded successfully',
                'filename': filename,
                'filesize': filesize
            }
            
        except Exception as e:
            current_app.logger.error(f"Direct download error: {str(e)}")
            return {
                'success': False,
                'message': f'Failed to download video: {str(e)}'
            }
    
    @staticmethod
    def delete_video(filename: str) -> Dict[str, Any]:
        """
        Delete video file from server.
        
        Args:
            filename: Name of file to delete
            
        Returns:
            Dict with success status or error message
        """
        try:
            secure_name = secure_filename(filename)
            if not secure_name or not allowed_file(secure_name):
                return {
                    'success': False,
                    'message': 'Invalid filename'
                }
            
            filepath = os.path.join(Config.UPLOAD_FOLDER, secure_name)
            if os.path.exists(filepath):
                os.remove(filepath)
                return {
                    'success': True,
                    'message': 'Video deleted successfully'
                }
            else:
                return {
                    'success': False,
                    'message': 'Video file not found'
                }
                
        except Exception as e:
            current_app.logger.error(f"Delete video error: {str(e)}")
            return {
                'success': False,
                'message': f'Failed to delete video: {str(e)}'
            }
    
    @staticmethod
    def _extract_instagram_video_url(post_url: str, cookies: str) -> Optional[str]:
        """Extract video URL from Instagram post."""
        try:
            client = Client(cookies=cookies)
            media = client.media_info(post_url)
            
            if not media:
                return None
            
            # Try different attributes to get video URL
            if hasattr(media, 'url'):
                if isinstance(media.url, (list, tuple)) and len(media.url) > 0:
                    return media.url[0]
                elif isinstance(media.url, str):
                    return media.url
                elif hasattr(media.url, 'url'):
                    return media.url.url
                elif hasattr(media.url, '__str__'):
                    return str(media.url)
            elif hasattr(media, 'video_url'):
                return media.video_url
            elif hasattr(media, 'media_url'):
                return media.media_url
            
            return None
            
        except Exception as e:
            current_app.logger.error(f"Instagram media fetch error: {str(e)}")
            return None
    
    @staticmethod
    def _extract_file_info(downloaded_file: Any) -> Dict[str, str]:
        """Extract filename and filesize from downloaded file."""
        try:
            if isinstance(downloaded_file, dict):
                filename = os.path.basename(downloaded_file.get('file', ''))
                filesize = downloaded_file.get('size', 'Unknown')
            elif isinstance(downloaded_file, str):
                filename = os.path.basename(downloaded_file)
                try:
                    full_path = os.path.join(Config.UPLOAD_FOLDER, filename)
                    size_bytes = os.path.getsize(full_path)
                    filesize = f"{size_bytes / (1024*1024):.2f} MB"
                except:
                    filesize = 'Unknown'
            elif hasattr(downloaded_file, 'file') and hasattr(downloaded_file, 'size'):
                filename = os.path.basename(downloaded_file.file)
                filesize = downloaded_file.size
            else:
                filename = os.path.basename(str(downloaded_file))
                filesize = 'Unknown'
            
            return {'filename': filename, 'filesize': filesize}
            
        except Exception as e:
            current_app.logger.error(f"Error extracting file info: {str(e)}")
            return {'filename': 'unknown', 'filesize': 'Unknown'}
