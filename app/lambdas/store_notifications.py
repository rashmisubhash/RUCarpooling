import json
import boto3
import uuid
from datetime import datetime

# AWS Clients
dynamodb = boto3.resource("dynamodb")
notifications_table = dynamodb.Table("RUNotifications")

def lambda_handler(event, context):
    try:
        for record in event["Records"]:
            detail = json.loads(record["body"])
            ride_id = detail["RideID"]
            request_id = detail["RequestID"]
            rider_id = detail["RiderID"]
            driver_id = detail["DriverID"]
            seats_requested = detail["SeatsRequested"]

            # 🆕 Generate a unique notification ID
            notification_id = str(uuid.uuid4())

            # 📝 Store Notification in DynamoDB
            notifications_table.put_item(Item={
                "notification_id": notification_id,
                "user_id": driver_id,
                "notification_type": "RideRequested",
                "message": f"You have a new ride request from {rider_id}",
                "ride_id": ride_id,
                "request_id": request_id,
                "timestamp": datetime.utcnow().isoformat(),
                "status": "unread"
            })
            print(f"Notification stored: {notification_id}")

        return {"statusCode": 200, "body": "Notification stored"}
    
    except Exception as e:
        print(f"Error storing notification: {str(e)}")
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}

# zip function.zip store_notifications.py
# aws lambda update-function-code \
#     --function-name RUStoreNotifcations \
#     --zip-file fileb://function.zip \
#     --region us-east-1