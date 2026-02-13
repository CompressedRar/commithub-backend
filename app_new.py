"""
Flask application factory
Creates and configures the Flask app with all extensions
"""
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask_socketio import SocketIO
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from utils.Email import mail
from config_new import get_config


# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
socketio = SocketIO()
limiter = Limiter(key_func=get_remote_address)


def create_app(config_name=None):
    """
    Create and configure the Flask application
    
    Args:
        config_name: Configuration name ('development', 'testing', 'production')
                    If None, uses FLASK_ENV environment variable
    
    Returns:
        Flask application instance
    """
    app = Flask(__name__)
    
    # Load configuration
    config = get_config(config_name)
    app.config.from_object(config)
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)
    socketio.init_app(app, cors_allowed_origins=config.CORS_ORIGINS)
    limiter.init_app(app)
    
    # Setup CORS
    CORS(app, supports_credentials=True, origins=config.CORS_ORIGINS)
    
    # Register blueprints
    _register_blueprints(app)
    
    # Register error handlers
    _register_error_handlers(app)
    
    # Register CLI commands
    _register_cli_commands(app)
    
    return app


def _register_blueprints(app):
    """Register all application blueprints"""
    blueprints = [
        ('routes.Auth', 'auth'),
        ('routes.Tests', 'test'),
        ('routes.Department', 'department'),
        ('routes.Category', 'category'),
        ('routes.Task', 'task'),
        ('routes.Users', 'users'),
        ('routes.Logs', 'logs'),
        ('routes.PCR', 'pcrs'),
        ('routes.Chart', 'charts'),
        ('routes.AI', 'ai'),
        ('routes.Positions', 'positions'),
        ('routes.Settings', 'settings'),
        ('routes.Administrator', 'administrator'),
    ]
    
    for module_name, blueprint_name in blueprints:
        try:
            module = __import__(module_name, fromlist=[blueprint_name])
            blueprint = getattr(module, blueprint_name)
            app.register_blueprint(blueprint)
        except (ImportError, AttributeError) as e:
            app.logger.warning(f"Failed to register blueprint {blueprint_name}: {e}")


def _register_error_handlers(app):
    """Register global error handlers"""
    from flask import jsonify
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Resource not found'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500
    
    @app.errorhandler(403)
    def forbidden(error):
        return jsonify({'error': 'Forbidden'}), 403
    
    @app.errorhandler(401)
    def unauthorized(error):
        return jsonify({'error': 'Unauthorized'}), 401


def _register_cli_commands(app):
    """Register Flask CLI commands"""
    
    @app.cli.command()
    def init_db():
        """Initialize the database"""
        db.create_all()
        print("Database initialized")
    
    @app.cli.command()
    def drop_db():
        """Drop all database tables (be careful!)"""
        if app.config['TESTING'] or app.config['DEBUG']:
            db.drop_all()
            print("Database dropped")
        else:
            print("Cannot drop database in production")
    
    @app.cli.command()
    def seed_db():
        """Seed the database with initial data"""
        print("Database seeding - implement as needed")


# Health check endpoint
def setup_health_check(app):
    """Setup health check endpoints"""
    
    @app.route('/health')
    def health_check():
        from flask import jsonify
        return jsonify({
            'status': 'ok',
            'message': f'{app.config["APP_NAME"]} is running'
        }), 200
    
    @app.route('/api/v1/health')
    def api_health_check():
        from flask import jsonify
        return jsonify({
            'status': 'ok',
            'api_version': app.config['API_VERSION'],
            'app_name': app.config['APP_NAME']
        }), 200


if __name__ == '__main__':
    app = create_app()
    setup_health_check(app)
    
    with app.app_context():
        db.create_all()
    
    socketio.run(app, debug=app.config['DEBUG'], host='0.0.0.0', port=5000)
