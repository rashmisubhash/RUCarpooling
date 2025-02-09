import json
import boto3
import json

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('RUCarDetails')

def lambda_handler(event, context):
    user_id = event['pathParameters']['user_id']
    car_id = event['pathParameters']['car_id']
    data = json.loads(event['body'])

    update_expression = "SET "
    expression_values = {}

    if 'car_model' in data:
        update_expression += "car_model = :m, "
        expression_values[':m'] = data['car_model']

    if 'license_number' in data:
        update_expression += "license_number = :l, "
        expression_values[':l'] = data['license_number']

    update_expression = update_expression.rstrip(", ")

    table.update_item(
        Key={'car_id': car_id},
        UpdateExpression=update_expression,
        ExpressionAttributeValues=expression_values
    )

    return {"statusCode": 200, "body": json.dumps("Car details updated")}


# Upload the Zip File to AWS Lambda
# zip function.zip update_car_details.py
# aws lambda update-function-code \
#     --function-name RUupdateCarDetails \
#     --zip-file fileb://function.zip \
#     --region us-east-1
