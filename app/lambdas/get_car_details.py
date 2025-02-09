import json
import boto3

# Initialize DynamoDB
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('RUCarDetails')

def lambda_handler(event, context):
    try:
        # Extract user_id from path parameters
        user_id = event.get("pathParameters", {}).get("user_id")

        if not user_id:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Missing user_id in request"})
            }

        # ✅ Query DynamoDB using Global Secondary Index (GSI) if needed
        response = table.query(
            IndexName="user_id-index",  # Replace with actual index name if needed
            KeyConditionExpression="user_id = :u",
            ExpressionAttributeValues={":u": user_id}
        )

        # ✅ Extract car details
        cars = response.get("Items", [])

        return {
            "statusCode": 200,
            "body": json.dumps({"cars": cars})  # Ensure response is structured properly
        }

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Internal server error", "message": str(e)})
        }

# Upload the Zip File to AWS Lambda
# zip function.zip get_car_details.py
# aws lambda update-function-code \
#     --function-name RUgetCarDetails \
#     --zip-file fileb://function.zip \
#     --region us-east-1