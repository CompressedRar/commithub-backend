
from app import create_app  # or your app module
application = create_app()


from app import create_app, db

application = create_app()

if __name__ == "__main__":
    with application.app_context():
        db.create_all() 
    application.run(debug=True, host='0.0.0.0', port=5000) 