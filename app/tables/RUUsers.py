import boto3

# Initialize DynamoDB resource
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

TABLE_NAME = "RUUsers"

def create_table():
    """Creates the RUUsers table with all necessary attributes."""
    try:
        table = dynamodb.create_table(
            TableName=TABLE_NAME,
            KeySchema=[
                {'AttributeName': 'user_id', 'KeyType': 'HASH'}  # Partition Key
            ],
            AttributeDefinitions=[
                {'AttributeName': 'user_id', 'AttributeType': 'S'},  # String (UUID)
                {'AttributeName': 'email', 'AttributeType': 'S'},  # String
                {'AttributeName': 'is_driver', 'AttributeType': 'B'},  # Boolean
                {'AttributeName': 'college_name', 'AttributeType': 'S'},  # String
                {'AttributeName': 'created_at', 'AttributeType': 'S'},  # String (ISO Timestamp)
            ],
            BillingMode='PAY_PER_REQUEST'  # On-demand pricing
        )

        print(f"Creating table {TABLE_NAME}...")
        table.wait_until_exists()
        print(f"Table {TABLE_NAME} created successfully!")

    except Exception as e:
        print(f"Error creating table: {str(e)}")

if __name__ == "__main__":
    create_table()