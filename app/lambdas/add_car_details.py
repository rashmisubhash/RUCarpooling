import json
import boto3
import uuid

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('RUCarDetails')

def lambda_handler(event, context):
    user_id = event['pathParameters']['user_id']
    data = json.loads(event['body'])
    
    car_id = str(uuid.uuid4())  # Generate unique car_id
    car_model = data.get('car_model')
    license_number = data.get('license_number')

    if not car_model or not license_number:
        return {"statusCode": 400, "body": json.dumps("Missing required fields")}

    item = {
        "car_id": car_id,
        "user_id": user_id,
        "car_model": car_model,
        "license_number": license_number
    }

    table.put_item(Item=item)

    return {"statusCode": 201, "body": json.dumps({"message": "Car added", "car_id": car_id})}

# Upload the Zip File to AWS Lambda
# zip function.zip add_car_details.py
# aws lambda update-function-code \
#     --function-name RUaddCarDetails \
#     --zip-file fileb://function.zip \
#     --region us-east-1