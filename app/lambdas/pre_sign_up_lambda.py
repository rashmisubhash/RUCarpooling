import json
import boto3
import os
import re

# AWS Configuration
region = os.getenv("REGION", "us-east-1")  
user_pool_id = os.getenv("COGNITO_USER_POOL_ID", "us-east-1_59SHFljXs")  

# Initialize Cognito Client
cognito_client = boto3.client("cognito-idp", region_name=region)

def lambda_handler(event, context):
    try:
        print("Received event:", json.dumps(event, indent=2))
        
        # Ensure userAttributes exists before accessing it
        user_attributes = event.get("request", {}).get("userAttributes", {})
        
        # ✅ Print extracted attributes for debugging
        print(f"DEBUG: Extracted user attributes: {json.dumps(user_attributes, indent=2)}")

        # Extract Cognito user attributes
        username = event["userName"]
        email = event["request"]["userAttributes"].get("email", "")

        # ✅ Validate email domain (must end with @rutgers.edu)
        if not re.match(r"^[a-zA-Z0-9._%+-]+@rutgers\.edu$", email):
            raise ValueError("Invalid email address. Must be a Rutgers University email (@rutgers.edu).")

        # ✅ Check if email or username already exists in Cognito
        if check_existing_cognito_user(username, email):
            raise ValueError(f"User with email '{email}' or username '{username}' already exists in Cognito.")

        # ✅ Auto-confirm user in Cognito (Optional)
        event["response"]["autoConfirmUser"] = False  

        print("✅ PreSignUp Validation Passed. User can proceed.")
        return event  # Cognito expects the full event back

    except Exception as e:
        print("❌ PreSignUp Error:", str(e))
        raise

def check_existing_cognito_user(username, email):
    """
    Check if a user with the given username or email already exists in Cognito.
    """
    try:
        # Search by username
        response = cognito_client.admin_get_user(
            UserPoolId=user_pool_id,
            Username=username
        )
        print(f"User '{username}' exists in Cognito.")
        return True  # User already exists

    except cognito_client.exceptions.UserNotFoundException:
        print(f"User '{username}' not found in Cognito, checking email.")

    try:
        # Search by email (Cognito doesn't support email search directly, workaround needed)
        response = cognito_client.list_users(
            UserPoolId=user_pool_id,
            Filter=f'email = "{email}"'
        )
        if response["Users"]:
            print(f"User with email '{email}' exists in Cognito.")
            return True  # Email already exists
    except Exception as e:
        print("❌ Error while checking email in Cognito:", str(e))

    return False  # No duplicate found

# Upload the Zip File to AWS Lambda
# zip function.zip pre_sign_up_lambda.py
# aws lambda update-function-code \
#     --function-name CognitoPreSignUpValidation \
#     --zip-file fileb://function.zip \
#     --region us-east-1

# NOOOO - Attach Lambda as PreSignUp Trigger
# aws cognito-idp update-user-pool \
#     --user-pool-id us-east-1_59SHFljXs \
#     --lambda-config PreAuthentication=arn:aws:lambda:us-east-1:184226036469:function:CognitoPreSignUpValidation \
#     --region us-east-1

# Add Invoke Permission for PreSignUp
# aws lambda add-permission \
#     --function-name CognitoPreSignUpValidation \
#     --statement-id CognitoInvokePermissionPreSignUp \
#     --action lambda:InvokeFunction \
#     --principal cognito-idp.amazonaws.com \
#     --source-arn arn:aws:cognito-idp:us-east-1:184226036469:userpool/us-east-1_59SHFljXs




# aws cognito-idp describe-user-pool --user-pool-id us-east-1_59SHFljXs --region us-east-1

# aws cognito-idp update-user-pool \
#     --user-pool-id us-east-1_59SHFljXs \
#     --lambda-config '{"PreSignUp": "arn:aws:lambda:us-east-1:184226036469:function:CognitoPreSignUpValidation", "PostConfirmation": "arn:aws:lambda:us-east-1:184226036469:function:CognitoPostConfirmation"}' \
#     --region us-east-1

