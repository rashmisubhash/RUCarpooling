import boto3
import os
from dotenv import load_dotenv

# AWS Configuration
region = os.getenv("REGION")  # Change this to your AWS region
user_pool_id = "us-east-1_59SHFljXs"
# os.getenv("COGNITO_USER_POOL_ID")  # Replace with your Cognito User Pool ID
lambda_arn = "arn:aws:lambda:us-east-1:184226036469:function:CognitoPreSignUpValidation"  # Replace with your Lambda ARN

# Initialize Cognito Client
cognito_client = boto3.client("cognito-idp", region_name=region)

def attach_trigger():
    """Attach Lambda as a Post Confirmation trigger for Cognito."""
    
    response = cognito_client.update_user_pool(
        UserPoolId=user_pool_id,
        LambdaConfig={
            "CognitoPreSignUpValidation": lambda_arn  # Fix: This should be a direct ARN reference
        }
    )

    print("Lambda trigger attached successfully:", response)

if __name__ == "__main__":
    attach_trigger()
    
# To run whenever we make any change here, or the respective lambda function 
# python3 app/triggers/attach_cognito_trigger.py

# aws cognito-idp update-user-pool \
#     --user-pool-id us-east-1_59SHFljXs \
#     --lambda-config PreSignUp=arn:aws:lambda:us-east-1:184226036469:function:CognitoPreSignUpValidation \
#     --region us-east-1
