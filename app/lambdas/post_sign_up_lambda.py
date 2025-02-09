import boto3
import os
import datetime
import re
import json

# Initialize DynamoDB
dynamodb = boto3.resource('dynamodb', region_name="us-east-1")  # Change region if needed
table_name = os.getenv('USERS_TABLE', 'RUCarpoolingUsers')  # Get table name from env or default to 'Users'
table = dynamodb.Table(table_name)

def lambda_handler(event, context):
    try:
        """ Triggered when a user registers in Cognito """
        
        # Ensure userAttributes exists before accessing it
        user_attributes = event.get("request", {}).get("userAttributes", {})

        if not user_attributes:
            raise ValueError("No user attributes found in the event payload.")
        
        # ✅ Print extracted attributes for debugging
        print(f"DEBUG: Extracted user attributes: {json.dumps(user_attributes, indent=2)}")

        # Extract Cognito UserID and attributes
        # user_id = user_attributes["sub"]
        # phone = user_attributes.get("phone_number", "")
        # username = event["userName"]  # Cognito username (same as email in some cases)
        # email = event["request"]["userAttributes"].get("email", "")
        # name = event["request"]["userAttributes"].get("name", "")
        
        user_id = user_attributes.get("sub", None)
        username = event.get("userName", None)  # Cognito username
        email = user_attributes.get("email", None)
        name = user_attributes.get("name", None)
        phone = user_attributes.get("phone_number", "")
        
        # user_id = event.get('userName')  # Cognito-generated UserID
        
        print(f"DEBUG: user_id received from Cognito: {user_id}")  # Add this line
        
        # ✅ Validate required fields
        missing_fields = [key for key, value in {"username": username, "email": email}.items() if not value]
        if missing_fields:
            raise ValueError(f"❌ Missing required fields: {', '.join(missing_fields)}.")


        # 🚨 Ensure UserID is not empty (Cognito should always provide it)
        if not user_id:
            print("Error: Missing UserID from Cognito")
            return {"statusCode": 400, "body": "UserID is missing!"}

        # Check if required fields are missing
        if not username or not email:
            raise ValueError("Missing required fields: name, username, or email.")

        # ✅ Validate email domain (must end with @rutgers.edu)
        if not re.match(r"^[a-zA-Z0-9._%+-]+@rutgers\.edu$", email):
            raise ValueError("Invalid email address. Must be a Rutgers University email (@rutgers.edu).")
        
        # Check if username or email already exists
        existing_user = check_existing_user(username, email)
        if existing_user:
            raise ValueError(f"User with email '{email}' or username '{username}' already exists.")
        
        # Construct user data
        user_item = {
            "user_id": user_id,
            "full_name": name,
            "email": email,
            "phone": phone,
            "is_driver": False,  # Default value
            "created_at": datetime.datetime.utcnow().isoformat(),
            "college_name": "Rutgers University",
            'ruid': '',
            'is_driver': False,
            'photo': '',
            "user_name": username

        }
        # Insert user details into DynamoDB
        table.put_item(Item=user_item)

        print(f"User {user_id} added to DynamoDB successfully!")
        return event  # Required for Cognito trigger to continue execution
    
    except Exception as e:
        print("❌ Error:", str(e))
        raise

def check_existing_user(username, email):
    """
    Check if a user with the given username or email already exists.
    """
    # Query DynamoDB to find existing user
    response = table.scan(
        FilterExpression="username = :username OR email = :email",
        ExpressionAttributeValues={
            ":username": username,
            ":email": email
        }
    )

    return response.get("Items", [])  # Returns list of users found

# Upload the Zip File to AWS Lambda
# zip function.zip post_sign_up_lambda.py
# aws lambda update-function-code \
#     --function-name CognitoPostConfirmation \
#     --zip-file fileb://function.zip \
#     --region us-east-1

# Attach Lambda as PostSignup Trigger
# aws cognito-idp update-user-pool \
#     --user-pool-id us-east-1_59SHFljXs \
#     --lambda-config PostConfirmation=arn:aws:lambda:us-east-1:184226036469:function:CognitoPostConfirmation \
#     --region us-east-1

# Add Invoke Permission for PreSignUp
# aws lambda add-permission \
#     --function-name CognitoPostConfirmation \
#     --statement-id CognitoInvokePermissionPreSignUp \
#     --action lambda:InvokeFunction \
#     --principal cognito-idp.amazonaws.com \
#     --source-arn arn:aws:cognito-idp:us-east-1:184226036469:userpool/us-east-1_59SHFljXs

# aws cognito-idp update-user-pool \
#     --user-pool-id us-east-1_59SHFljXs \
#     --lambda-config PostConfirmation=arn:aws:lambda:us-east-1:184226036469:function:CognitoPostConfirmation \
#     --region us-east-1

# Test the lambda function
# aws lambda invoke --function-name CognitoPostConfirmation output.json --region us-east-1

