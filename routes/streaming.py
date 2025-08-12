
from flask import Blueprint, request, jsonify, session, current_app
from pygramcl import Live, Client, Download
from werkzeug.utils import secure_filename
from urllib.parse import urlparse

from config import Config
from utils import allowed_file, validate_duration, LiveStreamManager, safe_remove_file

import os
import uuid
import time

streaming_bp = Blueprint('streaming', __name__)

@streaming_bp.route('/download', methods=['POST'])
def download_video():
    try:
        if 'ig_cookies' not in session:
            return jsonify({
                'success': False,
                'message': 'Instagram session cookies required.'
            })
        
        url = request.form.get('url', '').strip()
        if not url:
            return jsonify({
                'success': False, 
                'message': 'URL is required'
            })

        parsed = urlparse(url)
        if not all([parsed.scheme, parsed.netloc]):
            return jsonify({
                'success': False, 
                'message': 'Invalid URL format'
            })

        if 'instagram.com' in url and ('/p/' in url or '/reel/' in url):
            try:
                cookies = session['ig_cookies']
                client = Client(cookies=cookies)
                media = client.media_info(url)
                
                if not media:
                    return jsonify({
                        'success': False,
                        'message': 'Failed to fetch Instagram media information'
                    })
                
                if hasattr(media, 'url'):
                    if isinstance(media.url, (list, tuple)) and len(media.url) > 0:
                        url = media.url[0]
                    elif isinstance(media.url, str):
                        url = media.url
                    elif hasattr(media.url, 'url'):
                        url = media.url.url
                    elif hasattr(media.url, '__str__'):
                        url = str(media.url)
                    else:
                        return jsonify({
                            'success': False,
                            'message': 'Unable to extract video URL from Instagram media'
                        })
                elif hasattr(media, 'video_url'):
                    url = media.video_url
                elif hasattr(media, 'media_url'):
                    url = media.media_url
                else:
                    return jsonify({
                        'success': False,
                        'message': 'No video URL found in Instagram media'
                    })
                
                if not url or not isinstance(url, str):
                    return jsonify({
                        'success': False,
                        'message': 'Invalid video URL extracted from Instagram media'
                    })
                
            except Exception as e:
                current_app.logger.error(f"Instagram media fetch error: {str(e)}")
                return jsonify({
                    'success': False,
                    'message': f'Failed to process Instagram URL: {str(e)}'
                })
        filename = f'ig_download_{int(time.time())}'
        
        try:
            downloaded_file = Download.from_url(
                url, 
                filename=filename,
                directory=Config.UPLOAD_FOLDER
            )
        except Exception as e:
            current_app.logger.error(f"Download.from_url error: {str(e)}")
            return jsonify({
                'success': False,
                'message': f'Download failed: {str(e)}'
            })

        if not downloaded_file:
            return jsonify({
                'success': False,
                'message': 'Download failed - no file returned'
            })

        try:
            if isinstance(downloaded_file, dict):
                filename = os.path.basename(downloaded_file.get('file', ''))
                filesize = downloaded_file.get('size', 'Unknown')
            elif isinstance(downloaded_file, str):
                filename = os.path.basename(downloaded_file)
                try:
                    filesize = os.path.getsize(os.path.join(Config.UPLOAD_FOLDER, filename))
                    filesize = f"{filesize / (1024*1024):.2f} MB"
                except:
                    filesize = 'Unknown'
            elif hasattr(downloaded_file, 'file') and hasattr(downloaded_file, 'size'):
                filename = os.path.basename(downloaded_file.file)
                filesize = downloaded_file.size
            else:
                filename = os.path.basename(str(downloaded_file))
                filesize = 'Unknown'
                
        except Exception as e:
            current_app.logger.error(f"Error processing downloaded file info: {str(e)}")
            return jsonify({
                'success': False,
                'message': f'Download completed but failed to process file info: {str(e)}'
            })

        return jsonify({
            'success': True,
            'message': 'File downloaded successfully',
            'filename': filename,
            'filesize': filesize
        })

    except Exception as e:
        current_app.logger.error(f"Download error: {str(e)}", exc_info=True)
        return jsonify({
            'success': False, 
            'message': f'Download process failed: {str(e)}'
        })

@streaming_bp.route('/upload', methods=['POST'])
def upload_video():
    """Upload video file"""
    try:
        if 'video' not in request.files:
            return jsonify({
                'success': False, 
                'message': 'No video file provided'
            })
        
        video = request.files['video']
        
        if video.filename == '':
            return jsonify({
                'success': False, 
                'message': 'No video file selected'
            })
        
        if not allowed_file(video.filename):
            return jsonify({
                'success': False, 
                'message': f'Invalid file format. Allowed: {", ".join(Config.ALLOWED_VIDEO_EXTENSIONS)}'
            })
        
        filename = secure_filename(video.filename)
        name, ext = os.path.splitext(filename)
        filename = f"ig_upload_{int(time.time())}{ext}"
        
        filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
        video.save(filepath)
        
        return jsonify({
            'success': True,
            'message': 'Video uploaded successfully',
            'filename': filename
        })
        
    except Exception as e:
        current_app.logger.error(f"Upload error: {str(e)}")
        return jsonify({
            'success': False, 
            'message': f'Upload failed: {str(e)}'
        })

@streaming_bp.route('/start', methods=['POST'])
def start_stream():
    try:
        if 'ig_cookies' not in session:
            return jsonify({
                'success': False,
                'message': 'Instagram session cookies required. Please configure cookies first.'
            })
        
        cookies = session['ig_cookies']
        title = request.form.get('title', Config.DEFAULT_LIVE_TITLE).strip()
        hours = int(request.form.get('hours', 0))
        minutes = int(request.form.get('minutes', 0))
        seconds = int(request.form.get('seconds', 0))
        filename = request.form.get('filename', '').strip()
        
        if not filename:
            return jsonify({
                'success': False, 
                'message': 'Video filename is required'
            })
        
        duration_valid, duration_error = validate_duration(hours, minutes, seconds)
        if not duration_valid:
            return jsonify({
                'success': False, 
                'message': duration_error
            })
        
        filepath = os.path.join(Config.UPLOAD_FOLDER, secure_filename(filename))
        if not os.path.exists(filepath):
            return jsonify({
                'success': False, 
                'message': 'Video file not found'
            })
        
        session_id = session.get('session_id')
        if session_id and LiveStreamManager.is_active(session_id):
            return jsonify({
                'success': False, 
                'message': 'A live stream is already active'
            })
        
        live = Live(cookies)
        
        if not live.live_user:
            return jsonify({
                'success': False, 
                'message': 'Invalid Instagram session. Please reconfigure cookies.'
            })
        
        stream_started = live.start(
            video=filepath, 
            title=title, 
            hours=hours, 
            minutes=minutes, 
            seconds=seconds
        )
        time.sleep(3)
        
        if stream_started:
            session_id = str(uuid.uuid4())
            session['session_id'] = session_id
            session['broadcast_id'] = live.live_info.get('broadcast_id')
            session['stream_title'] = title
            session['start_time'] = live.live_time
            session.permanent = True
            
            LiveStreamManager.create_instance(session_id, live)
            
            return jsonify({
                'success': True,
                'message': 'Live stream started successfully',
                'broadcast_id': live.live_info.get('broadcast_id'),
                'session_id': session_id
            })
        else:
            return jsonify({
                'success': False, 
                'message': 'Failed to start live stream'
            })
            
    except ValueError as e:
        return jsonify({
            'success': False, 
            'message': f'Invalid input values: {str(e)}'
        })
    except Exception as e:
        current_app.logger.error(f"Start stream error: {str(e)}")
        return jsonify({
            'success': False, 
            'message': f'Failed to start stream: {str(e)}'
        })

@streaming_bp.route('/stop', methods=['POST'])
def stop_stream():
    try:
        session_id = session.get('session_id')
        
        if not session_id:
            return jsonify({
                'success': False, 
                'message': 'No active session found'
            })
        
        if not LiveStreamManager.is_active(session_id):
            return jsonify({
                'success': False, 
                'message': 'No active live stream found'
            })
        
        live = LiveStreamManager.get_instance(session_id)
        if live:
            live.stop()
        
        LiveStreamManager.remove_instance(session_id)
        session.pop('session_id', None)
        session.pop('broadcast_id', None)
        session.pop('stream_title', None)
        session.pop('start_time', None)
        
        return jsonify({
            'success': True, 
            'message': 'Live stream stopped successfully'
        })
        
    except Exception as e:
        current_app.logger.error(f"Stop stream error: {str(e)}")
        return jsonify({
            'success': False, 
            'message': f'Failed to stop stream: {str(e)}'
        })

@streaming_bp.route('/info')
def stream_info():
    try:
        session_id = session.get('session_id')
        
        if not session_id or not LiveStreamManager.is_active(session_id):
            return jsonify({
                'success': False, 
                'message': 'No active live stream found'
            })
        
        live = LiveStreamManager.get_instance(session_id)
        if not live:
            return jsonify({
                'success': False, 
                'message': 'Live stream instance not found'
            })
        
        info = live.info()
        if not info:
            return jsonify({
                'success': False, 
                'message': 'Failed to fetch stream information'
            })
        
        return jsonify({
            'success': True,
            'message': 'Stream information retrieved successfully',
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
                ],
                'session_info': {
                    'title': session.get('stream_title', 'N/A'),
                    'start_time': session.get('start_time', 0)
                }
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Stream info error: {str(e)}")
        return jsonify({
            'success': False, 
            'message': f'Failed to get stream information: {str(e)}'
        })

@streaming_bp.route('/comment', methods=['POST'])
def stream_comment():
    try:
        session_id = session.get('session_id')
        
        if not session_id or not LiveStreamManager.is_active(session_id):
            return jsonify({
                'success': False, 
                'message': 'No active live stream found'
            })
        
        text = request.form.get('text', '').strip()
        if not text:
            return jsonify({
                'success': False, 
                'message': 'Comment text is required'
            })
        
        live = LiveStreamManager.get_instance(session_id)
        if not live:
            return jsonify({
                'success': False, 
                'message': 'Live stream instance not found'
            })
        
        success = live.comment(text)
        if success:
            return jsonify({
                'success': True,
                'message': 'Comment posted successfully'
            })
        else:
            return jsonify({
                'success': False, 
                'message': 'Failed to post comment'
            })
            
    except Exception as e:
        current_app.logger.error(f"Post comment error: {str(e)}")
        return jsonify({
            'success': False, 
            'message': f'Failed to post comment: {str(e)}'
        })

@streaming_bp.route('/delete/<filename>', methods=['DELETE'])
def delete_video(filename):
    """Delete uploaded video file"""
    try:
        session_id = session.get('session_id')
        if LiveStreamManager.is_active(session_id):
            return jsonify({
                'success': False, 
                'message': 'Cannot delete video while streaming'
            })
        
        secure_name = secure_filename(filename)
        if not secure_name or not allowed_file(secure_name):
            return jsonify({
                'success': False, 
                'message': 'Invalid filename'
            })
        
        filepath = os.path.join(Config.UPLOAD_FOLDER, secure_name)
        if safe_remove_file(filepath):
            return jsonify({
                'success': True, 
                'message': 'Video deleted successfully'
            })
        else:
            return jsonify({
                'success': False, 
                'message': 'Video file not found or cannot be deleted'
            })
            
    except Exception as e:
        current_app.logger.error(f"Delete video error: {str(e)}")
        return jsonify({
            'success': False, 
            'message': f'Failed to delete video: {str(e)}'
        })

@streaming_bp.route('/validate-cookies', methods=['POST'])
def validate_cookies():
    try:
        cookies = request.form.get('cookies', '').strip()
        if not cookies:
            return jsonify({
                'success': False,
                'message': 'Cookies are required'
            })
        
        try:
            required_fields = ['sessionid', 'ds_user_id']
            cookies_lower = cookies.lower()
            missing_fields = []
            for field in required_fields:
                if field not in cookies_lower:
                    missing_fields.append(field)
            if missing_fields:
                return jsonify({
                    'success': False,
                    'message': f'Missing required cookie fields: {", ".join(missing_fields)}'
                })
                
        except Exception as e:
            return jsonify({
                'success': False,
                'message': 'Invalid cookie format'
            })
        
        try:
            
            live = Live(cookies)
            if not hasattr(live, 'live_user') or not live.live_user:
                return jsonify({
                    'success': False,
                    'message': 'Invalid Instagram session cookies or session expired'
                })
            
            username = live.live_user.get('username', 'unknown')
            userid = live.live_user.get('id','0')
            
            session['ig_cookies'] = cookies
            session['ig_username'] = username
            session['ig_userid'] = str(userid)
            session.permanent = True
            
            return jsonify({
                'success': True,
                'message': 'Instagram cookies validated successfully',
                'username': username,
                'userid': str(userid),
                'session_valid': True
            })

        except Exception as e:
            current_app.logger.error(f"Cookie validation error: {str(e)}")
            error_message = str(e).lower()
            if 'login' in error_message or 'authentication' in error_message:
                return jsonify({
                    'success': False,
                    'message': 'Instagram login failed. Please check your cookies.'
                })
            elif 'network' in error_message or 'connection' in error_message:
                return jsonify({
                    'success': False,
                    'message': 'Network error. Please check your internet connection.'
                })
            elif 'rate' in error_message or 'limit' in error_message:
                return jsonify({
                    'success': False,
                    'message': 'Instagram rate limit reached. Please try again later.'
                })
            else:
                return jsonify({
                    'success': False,
                    'message': f'Instagram session validation failed: {str(e)}'
                })
        
    except Exception as e:
        current_app.logger.error(f"Validate cookies error: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Failed to validate cookies: {str(e)}'
        })

@streaming_bp.route('/cookie-status', methods=['GET'])
def cookie_status():
    try:
        cookies = session.get('ig_cookies')
        username = session.get('ig_username')
        userid = session.get('ig_userid')
        
        if not cookies or not username:
            return jsonify({
                'success': False,
                'message': 'No valid Instagram session found',
                'has_cookies': False
            })
        
        return jsonify({
            'success': True,
            'message': 'Valid Instagram session found',
            'has_cookies': True,
            'username': username,
            'userid': userid,
            'session_active': True
        })
        
    except Exception as e:
        current_app.logger.error(f"Cookie status error: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Failed to get cookie status: {str(e)}',
            'has_cookies': False
        })