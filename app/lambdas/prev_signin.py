modify my signin lambda

import json
import boto3
import os

# AWS Configuration
region = os.getenv("REGION", "us-east-1")
dynamodb = boto3.resource("dynamodb", region_name=region)
table = dynamodb.Table("RUCarpoolingUsers")  # ✅ Ensure this table exists

def lambda_handler(event, context):
    try:
        print("🔹 Received event:", json.dumps(event, indent=2))  # ✅ Debugging Log
        
        if event.get("triggerSource") == "PostAuthentication_Authentication":
            user_attributes = event.get("request", {}).get("userAttributes", {})  # ✅ Extract user attributes
            user_id = user_attributes.get("sub")  # ✅ Cognito User ID
            email = user_attributes.get("email")  # ✅ Email

            print(f"✅ Authenticated User, User ID: {user_id}")

            # ✅ Fetch `user_id` from DynamoDB using email
            dynamo_response = table.query(
                IndexName="email-index",  # ✅ Must have a GSI on "email"
                KeyConditionExpression="email = :email_value",
                ExpressionAttributeValues={":email_value": email}
            )

            if "Items" in dynamo_response and dynamo_response["Items"]:
                user_id = dynamo_response["Items"][0]["user_id"]  # ✅ Extract user_id

            # ✅ Store `user_id` in Cognito event (Frontend can retrieve later)
            event["response"]["claimsOverrideDetails"] = {
                "idTokenClaims": {
                    "custom:user_id": user_id  # ✅ Must prefix with `custom:`
                }
            }

            print("✅ Updated Cognito Response:", json.dumps(event, indent=2))

        # ✅ Return event back to Cognito (MUST return full event)
        return event  

    except Exception as e:
        print("❌ Lambda Execution Error:", str(e))
        return event  # ✅ Even if an error occurs, return event to avoid Cognito failure