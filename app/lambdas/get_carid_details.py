import json
import boto3
from decimal import Decimal

# Initialize DynamoDB
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('RUCarDetails')

def decimal_to_float(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, list):
        return [decimal_to_float(i) for i in obj]
    if isinstance(obj, dict):
        return {k: decimal_to_float(v) for k, v in obj.items()}
    return obj

def lambda_handler(event, context):
    try:
        # Extract user_id from path parameters
        car_id = event.get("pathParameters", {}).get("car_id")

        if not car_id:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Missing car_id in request"})
            }

        response = table.get_item(Key={"car_id": car_id})
        
        # Convert Decimal values before returning
        items = decimal_to_float(response.get('Item', []))
        
        if "Item" in response:
            return {"statusCode": 200, "body": json.dumps({"car_details": items})}
        else:
            return {"statusCode": 404, "body": json.dumps({"error": "Ride not found"})}
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Internal server error", "message": str(e)})
        }

# zip function.zip get_carid_details.py
# aws lambda update-function-code \
#     --function-name RUgetCarIDDetails \
#     --zip-file fileb://function.zip \
#     --region us-east-1