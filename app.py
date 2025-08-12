from logging.handlers import RotatingFileHandler
from flask import Flask, request, session
from utils import LiveStreamManager
from datetime import datetime
from config import Config

import logging
import atexit
import os

from routes.main import main_bp
from routes.streaming import streaming_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    Config.init_app(app)
    setup_logging(app)
    app.register_blueprint(main_bp)
    app.register_blueprint(streaming_bp, url_prefix='/api')
    register_error_handlers(app)
    register_request_handlers(app)
    atexit.register(lambda: cleanup_on_exit(app))
    return app

def setup_logging(app):
    if not app.debug and not app.testing:
        log_dir = Config.LOG_FOLDER
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        file_handler = RotatingFileHandler(
            os.path.join(log_dir, 'app.log'),
            maxBytes=10240000,  # 10MB
            backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s %(name)s [%(pathname)s:%(lineno)d] - %(message)s'
        ))
        file_handler.setLevel(getattr(logging, Config.LOG_LEVEL))
        error_handler = RotatingFileHandler(
            os.path.join(log_dir, 'errors.log'),
            maxBytes=10240000,
            backupCount=5
        )
        error_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s %(name)s [%(pathname)s:%(lineno)d] - %(message)s'
        ))
        error_handler.setLevel(logging.ERROR)
        app.logger.addHandler(file_handler)
        app.logger.addHandler(error_handler)
        app.logger.setLevel(getattr(logging, Config.LOG_LEVEL))
        app.logger.info('InStream application startup')

def register_error_handlers(app):
    
    @app.errorhandler(404)
    def not_found_error(error):
        app.logger.warning(f'404 error: {request.url}')
        return {'success': False, 'message': 'Resource not found'}, 404
    
    @app.errorhandler(413)
    def file_too_large_error(error):
        app.logger.warning(f'File too large error: {request.url}')
        max_size = Config.MAX_CONTENT_LENGTH / (1024 * 1024)
        return {
            'success': False, 
            'message': f'File too large. Maximum size is {max_size:.0f}MB'
        }, 413
    
    @app.errorhandler(500)
    def internal_server_error(error):
        app.logger.error(f'Server Error: {error}', exc_info=True)
        return {'success': False, 'message': 'Internal server error occurred'}, 500
    
    @app.errorhandler(Exception)
    def handle_exception(error):
        app.logger.error(f'Unhandled Exception: {error}', exc_info=True)
        return {'success': False, 'message': 'An unexpected error occurred'}, 500

def register_request_handlers(app):
    
    @app.before_request
    def before_request():
        if not request.path.startswith('/static'):
            app.logger.info(
                f'{request.method} {request.path} - '
                f'IP: {request.remote_addr} - '
                f'User-Agent: {request.headers.get("User-Agent", "Unknown")}'
            )
        
        if hasattr(request, 'path') and request.path == '/':
            LiveStreamManager.cleanup_old_instances()
    
    @app.after_request
    def after_request(response):
        if not request.path.startswith('/static'):
            app.logger.info(f'Response: {response.status_code}')
        return response
    
    @app.context_processor
    def inject_template_vars():
        return {
            'current_time': datetime.now(),
            'app_name': 'Instagram Live Streaming',
            'app_version': '2.0.0'
        }

def cleanup_on_exit(app):
    try:
        app.logger.info('Application shutting down, cleaning up resources...')
        for session_id in list(LiveStreamManager._instances.keys()):
            LiveStreamManager.remove_instance(session_id)
        
        app.logger.info('Cleanup completed successfully')
        
    except Exception as e:
        print(f'Error during cleanup: {str(e)}')

app = create_app()

@app.route('/debug/sessions')
def debug_sessions():
    if app.debug:
        return {
            'session_data': dict(session),
            'active_instances': len(LiveStreamManager._instances),
            'instances': {
                k: {
                    'active': v.get('active', False),
                    'created_at': v.get('created_at', 0)
                } for k, v in LiveStreamManager._instances.items()
            }
        }
    return {'message': 'Debug mode disabled'}, 403

if __name__ == '__main__':
    app.run(
        host=os.getenv('FLASK_HOST', '0.0.0.0'),
        port=int(os.getenv('FLASK_PORT', 5000)),
        debug=True #os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    )