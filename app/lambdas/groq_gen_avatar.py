import json
import os
import boto3
import requests

# AWS Resources
dynamodb = boto3.resource("dynamodb")
s3 = boto3.client("s3")

# Environment Variables
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")
USER_TABLE_NAME = "RUCarpoolingUsers"
S3_BUCKET_NAME = "ru-carpool-avatars"

# Hugging Face Stable Diffusion API
HUGGINGFACE_API = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-2"

def lambda_handler(event, context):
    try:
        # Parse request
        body = json.loads(event["body"])
        user_id = body["user_id"]
        car_type = body["car_type"]
        expression = body["expression"]
        color_theme = body["color_theme"]
        background = body["background"]

        # Validate API Key
        if not HUGGINGFACE_API_KEY:
            return {"statusCode": 500, "body": json.dumps({"error": "Hugging Face API Key is missing."})}

        # Construct prompt for Stable Diffusion
        prompt = f"A {car_type} with a {expression} expression, themed in {color_theme}, set in a {background}, digital art, ultra-realistic."

        # Call Hugging Face API for image generation
        response = requests.post(
            HUGGINGFACE_API,
            headers={"Authorization": f"Bearer {HUGGINGFACE_API_KEY}"},
            json={"inputs": prompt}
        )

        if response.status_code != 200:
            return {"statusCode": 400, "body": json.dumps({"error": "Image API call failed.", "details": response.text})}

        # Get generated image bytes
        image_bytes = response.content

        # Store the image in S3
        s3_key = f"avatars/{user_id}.png"
        s3.put_object(
            Bucket=S3_BUCKET_NAME,
            Key=s3_key,
            Body=image_bytes,
            ContentType="image/png",
            ACL="public-read"
        )

        # Get permanent S3 URL
        s3_avatar_url = f"https://{S3_BUCKET_NAME}.s3.amazonaws.com/{s3_key}"

        # Update user's "photo" attribute in RUCarpoolingUsers table
        table = dynamodb.Table(USER_TABLE_NAME)
        table.update_item(
            Key={"user_id": user_id},
            UpdateExpression="SET photo = :photo_url",
            ExpressionAttributeValues={":photo_url": s3_avatar_url}
        )

        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "Avatar created and stored successfully!",
                "avatar_url": s3_avatar_url
            })
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }



# zip function.zip groq_gen_avatar.py
# aws lambda update-function-code \
#     --function-name RUOpenAIGenAvatar \
#     --zip-file fileb://function.zip \
#     --region us-east-1
