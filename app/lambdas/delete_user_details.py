import boto3
import json
import os

dynamodb = boto3.resource('dynamodb')
table = os.getenv('USERS_TABLE', 'RUCarpoolingUsers')
table = dynamodb.Table(table)

def lambda_handler(event, context):
    user_id = event['pathParameters']['user_id']
    
    try:
        table.delete_item(Key={'user_id': user_id})
        
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'User deleted successfully'})
        }
    
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
        
# Upload the Zip File to AWS Lambda
# zip function.zip delete_user_details.py
# aws lambda update-function-code \
#     --function-name deleteUser \
#     --zip-file fileb://function.zip \
#     --region us-east-1