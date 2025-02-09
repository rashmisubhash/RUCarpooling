import boto3
import os
from dotenv import load_dotenv

# Load environment variables if needed
load_dotenv()

# AWS Configuration
region = os.getenv("REGION", "us-east-1")  
user_pool_id = os.getenv("COGNITO_USER_POOL_ID", "us-east-1_ABC123xyz")  # Replace with actual User Pool ID
presignup_lambda_arn = "arn:aws:lambda:us-east-1:184226036469:function:CognitoPreSignUpValidation"
postconfirmation_lambda_arn = "arn:aws:lambda:us-east-1:184226036469:function:CognitoPostConfirmation"

# Initialize Cognito Client
cognito_client = boto3.client("cognito-idp", region_name=region)

def attach_triggers():
    """Attach PreSignUp & PostConfirmation Lambda triggers to Cognito."""
    try:
        response = cognito_client.update_user_pool(
            UserPoolId=user_pool_id,
            LambdaConfig={
                "PreSignUp": presignup_lambda_arn,
                "PostConfirmation": postconfirmation_lambda_arn
            }
        )
        print("✅ Successfully attached Lambda triggers:", response)
    except Exception as e:
        print("❌ Error attaching triggers:", str(e))

if __name__ == "__main__":
    attach_triggers()
