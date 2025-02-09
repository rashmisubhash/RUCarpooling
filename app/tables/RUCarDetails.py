import boto3

# Initialize DynamoDB resource
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

# Table Name
TABLE_NAME = "RUCarDetails"

def create_table():
    """Creates the RUCarDetails table with all necessary attributes."""
    try:
        table = dynamodb.create_table(
            TableName=TABLE_NAME,
            KeySchema=[
                {'AttributeName': 'car_id', 'KeyType': 'HASH'}  # Primary Key (Partition Key)
            ],
            AttributeDefinitions=[
                {'AttributeName': 'car_id', 'AttributeType': 'S'},  # String type
                {'AttributeName': 'car_model', 'AttributeType': 'S'},
                {'AttributeName': 'license_number', 'AttributeType': 'S'},
                {'AttributeName': 'user_id', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'  # Uses On-Demand Pricing (No need for throughput units)
        )

        print(f"Creating table {TABLE_NAME}...")
        table.wait_until_exists()
        print(f"Table {TABLE_NAME} created successfully!")

    except Exception as e:
        print(f"Error creating table: {str(e)}")

if __name__ == "__main__":
    create_table()
    
# python3 RUCarDetails.py
