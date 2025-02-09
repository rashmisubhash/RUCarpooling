import json
import boto3

dynamodb = boto3.resource("dynamodb")
notifications_table = dynamodb.Table("RUNotifications")

def lambda_handler(event, context):
    """Marks a notification as read."""
    try:
        # ✅ Step 1: Parse request body
        body = json.loads(event["body"])
        notification_id = body.get("notification_id")
        user_id = body.get("user_id")  # Include if your table uses user_id as a sort key

        # ✅ Step 2: Validate input
        if not notification_id or not user_id:
            return {"statusCode": 400, "body": json.dumps({"error": "Missing notification_id or user_id"})}

        # ✅ Step 3: Update notification status in DynamoDB
        notifications_table.update_item(
            Key={"notification_id": notification_id, "user_id": user_id},  # Include user_id if required
            UpdateExpression="SET #s = :new_status",
            ExpressionAttributeNames={"#s": "status"},  # Ensure this matches your actual field name
            ExpressionAttributeValues={":new_status": "read"}
        )

        return {"statusCode": 200, "body": json.dumps({"message": "Notification marked as read"})}

    except Exception as e:
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
    
# zip function.zip update_noti.py
# aws lambda update-function-code \
#     --function-name RUUpdateNotificationStatusHandler \
#     --zip-file fileb://function.zip \
#     --region us-east-1