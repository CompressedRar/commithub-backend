import boto3
import os
from botocore.exceptions import NoCredentialsError
from dotenv import load_dotenv
from flask import jsonify
# Initialize S3 client
import uuid

load_dotenv()

id = os.getenv("AWS_SECRET_KEY_ID")
key = os.getenv("AWS_SECRET_KEY")
region = os.getenv("AWS_REGION")

BUCKET = "commithub-bucket"
ALLOWED_TYPES = {
    # Documents
    "application/pdf":                                                    "pdf",
    "application/msword":                                                 "doc",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
    "application/vnd.ms-excel":                                           "xls",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "xlsx",
    "application/vnd.ms-powerpoint":                                      "ppt",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": "pptx",

    "image/jpeg": "jpg",
    "image/png":  "png",
    "image/gif":  "gif",
    "image/webp": "webp",
}
MAX_ORIGINAL_NAME_LENGTH = 200

s3 = boto3.client(
    "s3",
    aws_access_key_id = id,
    aws_secret_access_key=key,
    region_name= region  # Change to your region
)

def _safe_original_name(file_name: str) -> str:
    """Return a sanitised version of the original filename for display only.
    This is stored in the DB for the user to recognise their file — it is
    NEVER used as the S3 key.
    """
    # Strip path separators and null bytes
    name = file_name.replace("/", "").replace("\\", "").replace("\x00", "")
    # Truncate to a reasonable length
    return name[:MAX_ORIGINAL_NAME_LENGTH] if name else "file"

def upload_profile_pic(file_path, bucket_name, object_name=None):
    if object_name is None:
        object_name = file_path
    try:
        s3.upload_file(file_path, bucket_name, object_name)
        return object_name
    except FileNotFoundError:
        return None
    except NoCredentialsError:
        return None

def upload_file(file_path, bucket_name, object_name=None):
    if object_name is None:
        object_name = file_path
    try:
        s3.upload_file(file_path, bucket_name, object_name)
        url = s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket_name, "Key": object_name},
        )
        return url
    except FileNotFoundError:
        return None
    except NoCredentialsError:
        return None

def get_file(object_name=None):
    """Generate a presigned GET URL for an existing S3 object."""
    try:
        url = s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": BUCKET, "Key": object_name},
            ExpiresIn=3600,
        )
        return url
    except NoCredentialsError:
        return None
    except Exception:
        return None


def generate_presigned_url(file_name: str, file_type: str):
    """Generate a presigned S3 PUT URL for a supporting document upload.
 
    Changes from the original:
    - file_type validated against ALLOWED_TYPES allowlist
    - S3 key is a UUID, not the user-supplied filename (prevents path traversal)
    - Original filename sanitised and returned for display / DB storage only
    """
    # 1. Validate MIME type
    if file_type not in ALLOWED_TYPES:
        return jsonify(
            error=f"File type '{file_type}' is not allowed. "
                  f"Accepted types: PDF, Word, Excel, PowerPoint, JPEG, PNG."
        ), 400
 
    # 2. Build a safe S3 key — UUID + validated extension, no user input
    ext = ALLOWED_TYPES[file_type]
    safe_key = f"documents/{uuid.uuid4()}.{ext}"
 
    # 3. Sanitise the original name for display purposes only
    display_name = _safe_original_name(file_name)
 
    try:
        url = s3.generate_presigned_url(
            "put_object",
            Params={
                "Bucket":      BUCKET,
                "Key":         safe_key,        # UUID-based, not user input
                "ContentType": file_type,        # validated against allowlist
            },
            ExpiresIn=3600,
        )
 
        return jsonify(
            link=url,
            key=safe_key,           # frontend must send this back when recording
            display_name=display_name,
        ), 200
 
    except NoCredentialsError:
        return jsonify(error="Storage credentials unavailable"), 500
    except Exception as e:
        return jsonify(error="Failed to generate upload URL"), 400

# Example usage
#upload_file("background.png", "commithub-bucket", "test/example.png")
