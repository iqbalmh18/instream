"""Stream service for Instagram live streaming operations."""

from typing import Optional, Dict, Any
from pygramcl import Live, Client
from flask import current_app
import uuid
import time


class StreamService:
    """Handle Instagram streaming operations."""
    
    @staticmethod
    def validate_cookies(cookies: str) -> Dict[str, Any]:
        """
        Validate Instagram session cookies.
        
        Args:
            cookies: Instagram session cookies string
            
        Returns:
            Dict with success status and user info or error message
        """
        try:
            # Check for required fields
            required_fields = ['sessionid', 'ds_user_id']
            cookies_lower = cookies.lower()
            missing_fields = [field for field in required_fields if field not in cookies_lower]
            
            if missing_fields:
                return {
                    'success': False,
                    'message': f'Missing required cookie fields: {", ".join(missing_fields)}'
                }
            
            # Validate with Instagram
            live = Live(cookies)
            if not hasattr(live, 'live_user') or not live.live_user:
                return {
                    'success': False,
                    'message': 'Invalid Instagram session cookies or session expired'
                }
            
            username = live.live_user.get('username', 'unknown')
            userid = str(live.live_user.get('id', '0'))
            
            return {
                'success': True,
                'username': username,
                'userid': userid,
                'session_valid': True
            }
            
        except Exception as e:
            current_app.logger.error(f"Cookie validation error: {str(e)}")
            error_message = str(e).lower()
            
            if 'login' in error_message or 'authentication' in error_message:
                message = 'Instagram login failed. Please check your cookies.'
            elif 'network' in error_message or 'connection' in error_message:
                message = 'Network error. Please check your internet connection.'
            elif 'rate' in error_message or 'limit' in error_message:
                message = 'Instagram rate limit reached. Please try again later.'
            else:
                message = f'Instagram session validation failed: {str(e)}'
            
            return {'success': False, 'message': message}
    
    @staticmethod
    def start_stream(
        cookies: str,
        video_path: str,
        title: str,
        hours: int,
        minutes: int,
        seconds: int
    ) -> Dict[str, Any]:
        """
        Start Instagram live stream.
        
        Args:
            cookies: Instagram session cookies
            video_path: Path to video file
            title: Stream title
            hours: Duration hours
            minutes: Duration minutes
            seconds: Duration seconds
            
        Returns:
            Dict with success status and stream info or error message
        """
        try:
            live = Live(cookies)
            
            if not live.live_user:
                return {
                    'success': False,
                    'message': 'Invalid Instagram session. Please reconfigure cookies.'
                }
            
            stream_started = live.start(
                video=video_path,
                title=title,
                hours=hours,
                minutes=minutes,
                seconds=seconds
            )
            
            time.sleep(3)  # Wait for stream to initialize
            
            if stream_started:
                session_id = str(uuid.uuid4())
                broadcast_id = live.live_info.get('broadcast_id')
                
                return {
                    'success': True,
                    'session_id': session_id,
                    'broadcast_id': broadcast_id,
                    'start_time': live.live_time,
                    'live_instance': live
                }
            else:
                return {
                    'success': False,
                    'message': 'Failed to start live stream'
                }
                
        except Exception as e:
            current_app.logger.error(f"Start stream error: {str(e)}")
            return {
                'success': False,
                'message': f'Failed to start stream: {str(e)}'
            }
    
    @staticmethod
    def stop_stream(live_instance: Any) -> Dict[str, Any]:
        """
        Stop Instagram live stream.
        
        Args:
            live_instance: Live stream instance
            
        Returns:
            Dict with success status or error message
        """
        try:
            if live_instance:
                live_instance.stop()
            
            return {
                'success': True,
                'message': 'Live stream stopped successfully'
            }
            
        except Exception as e:
            current_app.logger.error(f"Stop stream error: {str(e)}")
            return {
                'success': False,
                'message': f'Failed to stop stream: {str(e)}'
            }
    
    @staticmethod
    def get_stream_info(live_instance: Any) -> Dict[str, Any]:
        """
        Get live stream information.
        
        Args:
            live_instance: Live stream instance
            
        Returns:
            Dict with success status and stream info or error message
        """
        try:
            if not live_instance:
                return {
                    'success': False,
                    'message': 'Live stream instance not found'
                }
            
            info = live_instance.info()
            if not info:
                return {
                    'success': False,
                    'message': 'Failed to fetch stream information'
                }
            
            return {
                'success': True,
                'data': {
                    'broadcast_id': info.get('broadcast_id'),
                    'viewer_count': info.get('viewer_count', 0),
                    'comment_count': info.get('comment_count', 0),
                    'comments': [
                        {
                            'user': comment.get('user', 'unknown'),
                            'text': comment.get('text', ''),
                            'time': comment.get('time', '')
                        } for comment in info.get('comment_users', [])
                    ]
                }
            }
            
        except Exception as e:
            current_app.logger.error(f"Stream info error: {str(e)}")
            return {
                'success': False,
                'message': f'Failed to get stream information: {str(e)}'
            }
    
    @staticmethod
    def post_comment(live_instance: Any, text: str) -> Dict[str, Any]:
        """
        Post comment to live stream.
        
        Args:
            live_instance: Live stream instance
            text: Comment text
            
        Returns:
            Dict with success status or error message
        """
        try:
            if not live_instance:
                return {
                    'success': False,
                    'message': 'Live stream instance not found'
                }
            
            success = live_instance.comment(text)
            if success:
                return {
                    'success': True,
                    'message': 'Comment posted successfully'
                }
            else:
                return {
                    'success': False,
                    'message': 'Failed to post comment'
                }
                
        except Exception as e:
            current_app.logger.error(f"Post comment error: {str(e)}")
            return {
                'success': False,
                'message': f'Failed to post comment: {str(e)}'
            }
