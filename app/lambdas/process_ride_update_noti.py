import json
import boto3
import uuid
from datetime import datetime

# AWS Clients
dynamodb = boto3.resource("dynamodb")
ses_client = boto3.client("ses", region_name="us-east-1")
ws_client = boto3.client("apigatewaymanagementapi", endpoint_url="https://sy3ppk7bnh.execute-api.us-east-1.amazonaws.com/dev/")

# DynamoDB Tables
notifications_table = dynamodb.Table("RUNotifications")
connections_table = dynamodb.Table("RUWebSocketConnections")
users_table = dynamodb.Table("RUCarpoolingUsers")  # Table storing user details

def get_driver_email(driver_id):
    """Fetch driver email from RUCarpoolingUsers table."""
    response = users_table.get_item(Key={"user_id": driver_id})
    if "Item" in response:
        return response["Item"].get("email")
    return None  # Return None if email not found

def lambda_handler(event, context):
    try:
        print("Received event:", json.dumps(event, indent=2))  # ✅ Debugging output

        # ✅ Extract event details properly
        detail = event["detail"]
        if isinstance(detail, str):  # Convert to dictionary if it's a string
            detail = json.loads(detail)

        ride_id = detail["RideID"]
        request_id = detail["RequestID"]
        rider_id = detail["RiderID"]
        driver_id = detail["DriverID"]
        seats_requested = detail["SeatsRequested"]
        notification_type = detail["notification_type"]

        # 📝 Step 1: Store Notification in DynamoDB
        notification_id = str(uuid.uuid4())
        notifications_table.put_item(Item={
            "notification_id": notification_id,
            "user_id": rider_id,
            "message": f"You have a new ride update from {driver_id}",
            "ride_id": ride_id,
            "request_id": request_id,
            "timestamp": datetime.utcnow().isoformat(),
            "notification_status": "unread",
            "notification_type": notification_type
        })
        print(f"Notification stored for rider {rider_id}")
        
        
        # 🚀 Step 2: Send WebSocket Notification (Real-Time)
        
        response = connections_table.query(
            KeyConditionExpression="user_id = :user",
            ExpressionAttributeValues={":user": str(rider_id)}
        )
        print("Is1 the driver online ", response)
        items = response.get("Items", [])
        print("Is the driver online ", items)
        if items:
            conn_id = items[0]["connection_id"]  # Use the first connection ID found
            try:
                ws_client.post_to_connection(
                    ConnectionId=conn_id,
                    Data=json.dumps({
                        "notification_id": notification_id,
                        "message": f"You have a new ride Update from {driver_id}",
                        "ride_id": ride_id,
                        "request_id": request_id,
                        "notification_type": "notification_type"
                    })
                )
            except ws_client.exceptions.GoneException:
                print(f"Removing stale WebSocket connection for {rider_id}")
                connections_table.delete_item(Key={"user_id": rider_id})
            print(f"WebSocket notification sent to {rider_id}")

        else:
            # ✉️ Step 3: Send Email Notification via SES (If Driver is Offline)
            rider_email = get_driver_email(rider_id)
            if rider_email:
                ses_client.send_email(
                    Source="noreply@rucarpool.com",
                    Destination={"ToAddresses": [rider_email]},
                    Message={
                        "Subject": {"Data": "New Ride Request"},
                        "Body": {"Text": {"Data": f"You have a new ride updated from {driver_id} for {seats_requested} seat(s)."}}
                    }
                )
                print(f"Email notification sent to {rider_email}")

        return {"statusCode": 200, "body": "Notification processed"}

    except Exception as e:
        print(f"Error processing notification: {str(e)}")
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}

    
# zip function.zip process_ride_update_noti.py
# aws lambda update-function-code \
#     --function-name RUProcessRidenoti \
#     --zip-file fileb://function.zip \
#     --region us-east-1