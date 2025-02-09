import json
import boto3

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('RUCarDetails')

def lambda_handler(event, context):
    car_id = event['pathParameters']['car_id']
    
    table.delete_item(Key={'car_id': car_id})
    
    # user_id = event['pathParameters']['user_id']

    # # Temporary workaround: Use Scan instead of Query
    # response = table.scan(
    #     FilterExpression="user_id = :u",
    #     ExpressionAttributeValues={":u": user_id}
    # )

    return {"statusCode": 200, "body": json.dumps("Car deleted")}

# Upload the Zip File to AWS Lambda
# zip function.zip delete_car_details.py
# aws lambda update-function-code \
#     --function-name RUdelCarDetails \
#     --zip-file fileb://function.zip \
#     --region us-east-1