from fastapi import HTTPException
from app.services.jwt_utils import generate_custom_jwt
from app.utils.helpers import calculate_secret_hash
from app.core.config import settings
import boto3

cognito_client = boto3.client("cognito-idp", region_name=settings.REGION)

def signup(user):
    secret_hash = calculate_secret_hash(user.username, settings.CLIENT_ID, settings.CLIENT_SECRET)
    try:
        response = cognito_client.sign_up(
            ClientId=settings.CLIENT_ID,
            Username=user.username,
            Password=user.password,
            SecretHash=secret_hash,
            UserAttributes=[{"Name": "email", "Value": user.email}],
        )
        return response
    except cognito_client.exceptions.UsernameExistsException:
        raise HTTPException(status_code=400, detail="Username already exists")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

def confirm_signup(user):
    secret_hash = calculate_secret_hash(user.username, settings.CLIENT_ID, settings.CLIENT_SECRET)
    try:
        response = cognito_client.confirm_sign_up(
            ClientId=settings.CLIENT_ID,
            Username=user.username,
            ConfirmationCode=user.confirmation_code,
            SecretHash=secret_hash,
        )
        return response
    except cognito_client.exceptions.CodeMismatchException:
        raise HTTPException(status_code=400, detail="Invalid confirmation code")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

def signin(user):
    secret_hash = calculate_secret_hash(user.username, settings.CLIENT_ID, settings.CLIENT_SECRET)
    try:
        response = cognito_client.initiate_auth(
            ClientId=settings.CLIENT_ID,
            AuthFlow="USER_PASSWORD_AUTH",
            AuthParameters={
                "USERNAME": user.username,
                "PASSWORD": user.password,
                "SECRET_HASH": secret_hash,
            },
        )
        cognito_access_token = response["AuthenticationResult"]["AccessToken"]
        custom_token = generate_custom_jwt(user.username)
        return {"cognito_access_token": cognito_access_token, "custom_access_token": custom_token, "token_type": "bearer"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

def logout(token):
    try:
        cognito_client.global_sign_out(AccessToken=token)
        return {"message": "User logged out successfully"}
    except cognito_client.exceptions.NotAuthorizedException as e:
        raise HTTPException(status_code=401, detail=f"Not authorized: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))