"""
Main entry point for running the application directly
Usage: python application.py
"""
import os
import sys
from app_new import create_app, socketio, setup_health_check, db

# Ensure the app context is set for any initialization
application = create_app()

setup_health_check(application)

@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

if __name__ == '__main__':
    with application.app_context():
        # Create all database tables if they don't exist
        # Note: For production, use Flask-Migrate: flask db upgrade
        if not os.path.exists('migrations'):
            db.create_all()
    
    # Get environment settings
    debug = application.config.get('DEBUG', False)
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', 5000))
    
    print(f"\n{'='*60}")
    print(f"Starting {application.config['APP_NAME']}")
    print(f"Environment: {application.config.get('FLASK_ENV', 'development').upper()}")
    print(f"Debug Mode: {debug}")
    print(f"Listening on: http://{host}:{port}")
    print(f"{'='*60}\n")
    
    # Run with SocketIO support
    socketio.run(
        application,
        debug=debug,
        host=host,
        port=port,
        allow_unsafe_werkzeug=True
    )
