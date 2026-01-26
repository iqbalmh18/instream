"""Streaming routes - refactored with service layer."""

from flask import Blueprint, request, jsonify, session, current_app
from werkzeug.utils import secure_filename
import os

from config import Config
from utils import LiveStreamManager
from services import StreamService, VideoService
from helpers import validate_duration

streaming_bp = Blueprint('streaming', __name__)


@streaming_bp.route('/download', methods=['POST'])
def download_video():
    """Download video from URL (supports Instagram)."""
    try:
        url = request.form.get('url', '').strip()
        if not url:
            return jsonify({'success': False, 'message': 'URL is required'})
        
        cookies = session.get('ig_cookies')
        result = VideoService.download_video(url, cookies)
        
        return jsonify(result)
        
    except Exception as e:
        current_app.logger.error(f"Download endpoint error: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'message': f'Download process failed: {str(e)}'})


@streaming_bp.route('/upload', methods=['POST'])
def upload_video():
    """Upload video file."""
    try:
        if 'video' not in request.files:
            return jsonify({'success': False, 'message': 'No video file provided'})
        
        video_file = request.files['video']
        result = VideoService.upload_video(video_file)
        
        return jsonify(result)
        
    except Exception as e:
        current_app.logger.error(f"Upload endpoint error: {str(e)}")
        return jsonify({'success': False, 'message': f'Upload failed: {str(e)}'})


@streaming_bp.route('/start', methods=['POST'])
def start_stream():
    """Start Instagram live stream."""
    try:
        # Check cookies
        if 'ig_cookies' not in session:
            return jsonify({
                'success': False,
                'message': 'Instagram session cookies required. Please configure cookies first.'
            })
        
        # Get parameters
        cookies = session['ig_cookies']
        title = request.form.get('title', Config.DEFAULT_LIVE_TITLE).strip()
        hours = int(request.form.get('hours', 0))
        minutes = int(request.form.get('minutes', 0))
        seconds = int(request.form.get('seconds', 0))
        filename = request.form.get('filename', '').strip()
        
        # Validate input
        if not filename:
            return jsonify({'success': False, 'message': 'Video filename is required'})
        
        duration_valid, duration_error = validate_duration(hours, minutes, seconds)
        if not duration_valid:
            return jsonify({'success': False, 'message': duration_error})
        
        filepath = os.path.join(Config.UPLOAD_FOLDER, secure_filename(filename))
        if not os.path.exists(filepath):
            return jsonify({'success': False, 'message': 'Video file not found'})
        
        # Check for active stream
        session_id = session.get('session_id')
        if session_id and LiveStreamManager.is_active(session_id):
            return jsonify({'success': False, 'message': 'A live stream is already active'})
        
        # Start stream
        result = StreamService.start_stream(cookies, filepath, title, hours, minutes, seconds)
        
        if result['success']:
            # Save session info
            session_id = result['session_id']
            session['session_id'] = session_id
            session['broadcast_id'] = result['broadcast_id']
            session['stream_title'] = title
            session['start_time'] = result['start_time']
            session.permanent = True
            
            # Store live instance
            LiveStreamManager.create_instance(session_id, result['live_instance'])
            
            return jsonify({
                'success': True,
                'message': 'Live stream started successfully',
                'broadcast_id': result['broadcast_id'],
                'session_id': session_id
            })
        else:
            return jsonify(result)
            
    except ValueError as e:
        return jsonify({'success': False, 'message': f'Invalid input values: {str(e)}'})
    except Exception as e:
        current_app.logger.error(f"Start stream endpoint error: {str(e)}")
        return jsonify({'success': False, 'message': f'Failed to start stream: {str(e)}'})


@streaming_bp.route('/stop', methods=['POST'])
def stop_stream():
    """Stop Instagram live stream."""
    try:
        session_id = session.get('session_id')
        
        if not session_id:
            return jsonify({'success': False, 'message': 'No active session found'})
        
        if not LiveStreamManager.is_active(session_id):
            return jsonify({'success': False, 'message': 'No active live stream found'})
        
        # Stop stream
        live_instance = LiveStreamManager.get_instance(session_id)
        result = StreamService.stop_stream(live_instance)
        
        # Clean up session
        LiveStreamManager.remove_instance(session_id)
        session.pop('session_id', None)
        session.pop('broadcast_id', None)
        session.pop('stream_title', None)
        session.pop('start_time', None)
        
        return jsonify(result)
        
    except Exception as e:
        current_app.logger.error(f"Stop stream endpoint error: {str(e)}")
        return jsonify({'success': False, 'message': f'Failed to stop stream: {str(e)}'})


@streaming_bp.route('/info')
def stream_info():
    """Get live stream information."""
    try:
        session_id = session.get('session_id')
        
        if not session_id or not LiveStreamManager.is_active(session_id):
            return jsonify({'success': False, 'message': 'No active live stream found'})
        
        live_instance = LiveStreamManager.get_instance(session_id)
        result = StreamService.get_stream_info(live_instance)
        
        if result['success']:
            # Add session info
            result['data']['session_info'] = {
                'title': session.get('stream_title', 'N/A'),
                'start_time': session.get('start_time', 0)
            }
        
        return jsonify(result)
        
    except Exception as e:
        current_app.logger.error(f"Stream info endpoint error: {str(e)}")
        return jsonify({'success': False, 'message': f'Failed to get stream information: {str(e)}'})


@streaming_bp.route('/comment', methods=['POST'])
def stream_comment():
    """Post comment to live stream."""
    try:
        session_id = session.get('session_id')
        
        if not session_id or not LiveStreamManager.is_active(session_id):
            return jsonify({'success': False, 'message': 'No active live stream found'})
        
        text = request.form.get('text', '').strip()
        if not text:
            return jsonify({'success': False, 'message': 'Comment text is required'})
        
        live_instance = LiveStreamManager.get_instance(session_id)
        result = StreamService.post_comment(live_instance, text)
        
        return jsonify(result)
        
    except Exception as e:
        current_app.logger.error(f"Post comment endpoint error: {str(e)}")
        return jsonify({'success': False, 'message': f'Failed to post comment: {str(e)}'})


@streaming_bp.route('/delete/<filename>', methods=['DELETE'])
def delete_video(filename):
    """Delete uploaded video file."""
    try:
        # Check if streaming
        session_id = session.get('session_id')
        if LiveStreamManager.is_active(session_id):
            return jsonify({'success': False, 'message': 'Cannot delete video while streaming'})
        
        result = VideoService.delete_video(filename)
        return jsonify(result)
        
    except Exception as e:
        current_app.logger.error(f"Delete video endpoint error: {str(e)}")
        return jsonify({'success': False, 'message': f'Failed to delete video: {str(e)}'})


@streaming_bp.route('/validate-cookies', methods=['POST'])
def validate_cookies():
    """Validate Instagram cookies."""
    try:
        cookies = request.form.get('cookies', '').strip()
        
        if not cookies:
            return jsonify({'success': False, 'message': 'Cookies are required'})
        
        result = StreamService.validate_cookies(cookies)
        
        if result['success']:
            # Save to session
            session['ig_cookies'] = cookies
            session['ig_username'] = result['username']
            session['ig_userid'] = result['userid']
            session.permanent = True
            
            return jsonify({
                'success': True,
                'message': 'Instagram cookies validated successfully',
                'username': result['username'],
                'userid': result['userid'],
                'session_valid': True
            })
        else:
            return jsonify(result)
        
    except Exception as e:
        current_app.logger.error(f"Validate cookies endpoint error: {str(e)}")
        return jsonify({'success': False, 'message': f'Failed to validate cookies: {str(e)}'})


@streaming_bp.route('/cookie-status', methods=['GET'])
def cookie_status():
    """Get current cookie session status."""
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
        current_app.logger.error(f"Cookie status endpoint error: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Failed to get cookie status: {str(e)}',
            'has_cookies': False
        })