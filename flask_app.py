"""
Flask application entry point
This module is referenced by package.json and Procfile
Simply creates and returns the app instance
"""
from app_new import create_app, socketio, setup_health_check

# Create the application
application = create_app()

# Setup health check endpoints
setup_health_check(application)

# For use with: flask --app flask_app run
if __name__ == '__main__':
    with application.app_context():
        from app_new import db
        db.create_all()
    
    socketio.run(application, debug=application.config['DEBUG'], host='0.0.0.0', port=5000)
