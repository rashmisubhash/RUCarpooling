import json
import boto3
import requests
import jwt  # Install using: pip install PyJWT
from botocore.exceptions import BotoCoreError, ClientError
import process

# AWS DynamoDB Table
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table("RUWebSocketConnections")

# Cognito Settings (Ensure these are set in AWS Lambda environment variables)
COGNITO_USER_POOL_ID = process.env.COGNITO_USER_POOL_ID
COGNITO_REGION = process.env.COGNITO_REGION
COGNITO_JWKS_URL = f"https://cognito-idp.{COGNITO_REGION}.amazonaws.com/{COGNITO_USER_POOL_ID}/.well-known/jwks.json"

# Cache for JWKS Keys
jwks_keys = None

def fetch_jwks_keys():
    """Fetch and cache JWKS keys from Cognito."""
    global jwks_keys
    if not jwks_keys:
        response = requests.get(COGNITO_JWKS_URL)
        jwks_keys = response.json()
    return jwks_keys

def verify_token(token):
    """Verify Cognito JWT token using JWKS keys."""
    try:
        # Fetch JWKS keys
        keys = fetch_jwks_keys()

        # Decode JWT header
        decoded_header = jwt.get_unverified_header(token)
        kid = decoded_header.get("kid")

        if not kid:
            raise ValueError("No 'kid' found in token header.")

        # Find the matching JWKS key
        key = next((k for k in keys["keys"] if k["kid"] == kid), None)
        if not key:
            raise ValueError("Invalid signing key.")

        # Create public key
        public_key = jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(key))

        # Verify token
        decoded_token = jwt.decode(token, public_key, algorithms=["RS256"], audience=COGNITO_USER_POOL_ID)

        return decoded_token

    except jwt.ExpiredSignatureError:
        raise ValueError("Token has expired.")
    except jwt.JWTClaimsError:
        raise ValueError("Invalid claims in token.")
    except Exception as e:
        raise ValueError(f"Token verification failed: {str(e)}")

def lambda_handler(event, context):
    """WebSocket $connect route."""
    connection_id = event["requestContext"]["connectionId"]
    token = event.get("queryStringParameters", {}).get("token")

    if not token:
        return {"statusCode": 401, "body": "Unauthorized - No Token Provided"}

    try:
        decoded = verify_token(token)
        user_id = decoded["sub"]

        # Store connection in DynamoDB
        table.put_item(Item={"connectionId": connection_id, "userId": user_id})

        return {"statusCode": 200, "body": "Connected ✅"}
    
    except ValueError as error:
        print(f"Authentication failed: {error}")
        return {"statusCode": 401, "body": "Unauthorized"}
    except (BotoCoreError, ClientError) as db_error:
        print(f"DynamoDB Error: {db_error}")
        return {"statusCode": 500, "body": "Internal Server Error"}
    
# zip function.zip connect_websockets.py
# zip -r function.zip .


