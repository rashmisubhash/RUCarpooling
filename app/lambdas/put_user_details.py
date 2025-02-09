import boto3
import json
import os

dynamodb = boto3.resource('dynamodb')
table = os.getenv('USERS_TABLE', 'RUCarpoolingUsers')
table = dynamodb.Table(table)

def lambda_handler(event, context):
    user_id = event['pathParameters']['user_id']
    body = json.loads(event['body'])
    
    update_expression = "SET " + ", ".join([f"{key} = :{key}" for key in body.keys()])
    expression_values = {f":{key}": value for key, value in body.items()}
    
    try:
        table.update_item(
            Key={'user_id': user_id},
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_values
        )
        
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'User updated successfully'})
        }
    
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
        
# Upload the Zip File to AWS Lambda
# zip function.zip put_user_details.py
# aws lambda update-function-code \
#     --function-name updateUser \
#     --zip-file fileb://function.zip \
#     --region us-east-1