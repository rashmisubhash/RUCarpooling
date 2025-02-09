import json
import boto3

# AWS DynamoDB
dynamodb = boto3.resource("dynamodb")
notifications_table = dynamodb.Table("RUNotifications")

def lambda_handler(event, context):
    """Fetches notifications for a given user_id"""
    try:
        user_id = event["pathParameters"]["user_id"]  # Extract user_id from API path

        response = notifications_table.query(
            IndexName="UserIdIndex",  # Using GSI on user_id
            KeyConditionExpression="user_id = :uid",
            ExpressionAttributeValues={":uid": user_id}
        )

        return {
            "statusCode": 200,
            "body": json.dumps({"notifications": response.get("Items", [])})
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }

# zip function.zip handle_fetch_not.py
# aws lambda update-function-code \
#     --function-name handle_fetch_notifications \
#     --zip-file fileb://function.zip \
#     --region us-east-1