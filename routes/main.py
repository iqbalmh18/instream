from flask import Blueprint, render_template, jsonify, session
from utils import get_video_files, LiveStreamManager

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    return render_template('index.html')

@main_bp.route('/dashboard')
def dashboard():
    try:
        videos = get_video_files()
        session_id = session.get('session_id')
        is_live = LiveStreamManager.is_active(session_id) if session_id else False
        
        context = {
            'videos': videos,
            'is_live': is_live,
            'total_videos': len(videos),
            'error': None
        }
        
        return render_template('dashboard.html', **context)
        
    except Exception as e:
        context = {
            'error': f"Failed to load dashboard: {str(e)}",
            'videos': [],
            'is_live': False,
            'total_videos': 0
        }
        return render_template('dashboard.html', **context)

@main_bp.route('/status')
def status():
    try:
        session_id = session.get('session_id')
        is_live = LiveStreamManager.is_active(session_id) if session_id else False
        broadcast_id = session.get('broadcast_id')
        
        return jsonify({
            'success': True,
            'is_live': is_live,
            'broadcast_id': broadcast_id,
            'session_active': session_id is not None,
            'session_id': session_id
        })
    except Exception as e:
        return jsonify({
            'success': False, 
            'message': f"Failed to get status: {str(e)}"
        })

@main_bp.route('/videos')
def list_videos():
    try:
        videos = get_video_files()
        return jsonify({
            'success': True,
            'videos': videos,
            'total': len(videos)
        })
    except Exception as e:
        return jsonify({
            'success': False, 
            'message': f"Failed to list videos: {str(e)}"
        })
        
@main_bp.route('/health')
def health_check():
    try:
        import os
        from config import Config
        from datetime import datetime
        from __init__ import __version__
        
        upload_folder_ok = os.path.exists(Config.UPLOAD_FOLDER) and os.access(Config.UPLOAD_FOLDER, os.W_OK)
        try:
            import psutil
            memory_usage = psutil.virtual_memory().percent
            disk_usage = psutil.disk_usage('/').percent
        except ImportError:
            memory_usage = 0
            disk_usage = 0
        status = {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'version': __version__,
            'checks': {
                'upload_folder': 'ok' if upload_folder_ok else 'error',
                'memory_usage': f'{memory_usage:.1f}%' if memory_usage > 0 else 'unknown',
                'disk_usage': f'{disk_usage:.1f}%' if disk_usage > 0 else 'unknown',
                'session_active': 'session_id' in session,
                'cookies_configured': 'ig_cookies' in session
            }
        }
        
        if not upload_folder_ok:
            status['status'] = 'unhealthy'
            status['issues'] = ['Upload folder not accessible']
        elif memory_usage > 90 or disk_usage > 90:
            status['status'] = 'warning'
            status['issues'] = ['High resource usage']
        
        return jsonify(status)
        
    except Exception as e:
        from __init__ import __version__
        return jsonify({
            'status': 'unhealthy',
            'timestamp': datetime.utcnow().isoformat(),
            'error': str(e),
            'version': __version__
        }), 500