import boto3
import os
from botocore.exceptions import NoCredentialsError
from dotenv import load_dotenv
from flask import jsonify
# Initialize S3 client

load_dotenv()

id = os.getenv("AWS_SECRET_KEY_ID")
key = os.getenv("AWS_SECRET_KEY")
region = os.getenv("AWS_REGION")

s3 = boto3.client(
    "s3",
    aws_access_key_id = id,
    aws_secret_access_key=key,
    region_name= region  # Change to your region
)

def upload_profile_pic(file_path, bucket_name, object_name=None):
    if object_name is None:
        object_name = file_path  # Default to same filename

    try:
        s3.upload_file(file_path, bucket_name, object_name)

        print(f"✅ File uploaded successfully to s3://{bucket_name}/{object_name}")

        """
        url = s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket_name, 'Key': object_name},
            
        )"""

        return object_name
    except FileNotFoundError:
        print("❌ The file was not found")
    except NoCredentialsError:
        print("❌ AWS credentials not available")

def upload_file(file_path, bucket_name, object_name=None):
    if object_name is None:
        object_name = file_path  # Default to same filename

    try:
        s3.upload_file(file_path, bucket_name, object_name)

        print(f"✅ File uploaded successfully to s3://{bucket_name}/{object_name}")

        
        url = s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket_name, 'Key': object_name},
            
        )

        return url
    except FileNotFoundError:
        print("❌ The file was not found")
    except NoCredentialsError:
        print("❌ AWS credentials not available")


def get_file(object_name=None):
    
    try:        
        url = s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': "commithub-bucket", 'Key': object_name},
            ExpiresIn=3600  # link valid for 1 hour
        )
        return url
    except FileNotFoundError:
        print("❌ The file was not found")
    except NoCredentialsError:
        print("❌ AWS credentials not available")


def generate_presigned_url(file_name, file_type):
    try:
        url = s3.generate_presigned_url(
            "put_object",
            Params={"Bucket": "commithub-bucket", "Key": f"documents/{file_name}", "ContentType": file_type},
            ExpiresIn=3600
        )


        return jsonify(link= url), 200
    except:
        return jsonify(error = "there is an error generating url"), 400

# Example usage
#upload_file("background.png", "commithub-bucket", "test/example.png")
