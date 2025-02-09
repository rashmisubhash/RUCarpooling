import json
import boto3
import os

# AWS Configuration
region = os.getenv("REGION", "us-east-1")
dynamodb = boto3.resource("dynamodb", region_name=region)
table = dynamodb.Table("RUCarpoolingUsers")

def lambda_handler(event, context):
    try:
        print("🔹 Received event:", json.dumps(event, indent=2))

        if event.get("triggerSource") == "PostAuthentication_Authentication":
            user_attributes = event.get("request", {}).get("userAttributes", {})
            user_id = user_attributes.get("sub")
            email = user_attributes.get("email")

            print(f"✅ Authenticated User: {user_id}, Email: {email}")

            # ✅ Fetch `user_id` from DynamoDB using email
            try:
                dynamo_response = table.query(
                    IndexName="email-index",
                    KeyConditionExpression="email = :email_value",
                    ExpressionAttributeValues={":email_value": email}
                )

                if "Items" in dynamo_response and dynamo_response["Items"]:
                    user_id = dynamo_response["Items"][0]["user_id"]
                    print(f"✅ Found user_id in DynamoDB: {user_id}")
                else:
                    print("⚠️ User not found in DynamoDB, using Cognito `sub` as `user_id`.")

            except Exception as db_error:
                print(f"⚠️ DynamoDB query error: {str(db_error)}, using Cognito `sub`.")

            # ✅ Store `user_id` in Cognito ID Token (Modify claims)
            event["response"]["claimsOverrideDetails"] = {
                "idTokenClaims": {
                    "custom:user_id": user_id,
                    "custom:email": email
                }
            }

            print("✅ Updated Cognito Response with custom claims.")

        # ✅ MUST return the original `event` object for Cognito to process
        return event  

    except Exception as e:
        print("❌ Lambda Execution Error:", str(e))
        return event  # ✅ Ensures Cognito does not fail, even if an error occurs



        
# zip function.zip sign_in_lambda.py
# aws lambda update-function-code \
#     --function-name CognitoSignIn \
#     --zip-file fileb://function.zip \
#     --region us-east-1

# aws cognito-idp update-user-pool \
#     --user-pool-id us-east-1_59SHFljXs \
#     --lambda-config '{"PostAuthentication": "arn:aws:lambda:us-east-1:184226036469:function:CognitoSignIn"}' \
#     --region us-east-1

# aws lambda remove-permission \
#     --function-name CognitoSignIn \
#     --statement-id CognitoInvokePermission \
#     --region us-east-1


# aws lambda add-permission \
#     --function-name CognitoSignIn \
#     --statement-id CognitoInvokePermission \
#     --action lambda:InvokeFunction \
#     --principal cognito-idp.amazonaws.com \
#     --source-arn "arn:aws:cognito-idp:us-east-1:184226036469:userpool/us-east-1_59SHFljXs"



