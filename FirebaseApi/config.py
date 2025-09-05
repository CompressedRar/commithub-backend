import firebase_admin
from firebase_admin import credentials, firestore, storage
from dotenv import load_dotenv
import os
import uuid

from werkzeug.datastructures import FileStorage
load_dotenv()


cred = credentials.Certificate("FirebaseApi/qrsence-firebase-adminsdk-7k5ew-8edd4b858d.json")
app2 = None
try:
    app2 = firebase_admin.initialize_app(cred, {
        'storageBucket': 'qrsence.appspot.com'
    }, name = "storageapp")
    print("Firebase Storage initialized ✅")
except Exception as e:
    print("Error:", e)


profile_storage = storage.bucket("qrsence.appspot.com", app= app2)

def upload_file(profile_picture):
    image_name = f"commithub_profile_pictures/{uuid.uuid4()}.jpg"
    profile_image = profile_storage.blob(image_name)
    profile_image.upload_from_file(profile_picture, content_type=profile_picture.content_type)

    profile_image.make_public()
    file_url = profile_image.public_url
    print(file_url)


def test_upload(filepath):
    with open(filepath, "rb") as f:
        file_storage = FileStorage(stream=f, filename=filepath, content_type="image/png")

        upload_file(file_storage)

#test_upload("background.png")