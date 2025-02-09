from decimal import Decimal
import json
import traceback
import uuid
import boto3
from datetime import datetime

dynamodb = boto3.resource('dynamodb')
book_ride_table = dynamodb.Table('RUBookRide')
rides_table = dynamodb.Table('RUCarRides')  # Existing rides table
event_bridge = boto3.client("events", region_name="us-east-1")


def to_serializable(value):
    """Recursively converts Decimal values to int or float."""
    if isinstance(value, Decimal):
        return int(value) if value % 1 == 0 else float(value)
    elif isinstance(value, dict):
        return {k: to_serializable(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [to_serializable(v) for v in value]
    return value

def lambda_handler(event, context):
    """Universal error handling for all requests"""
    try:
        print("=== Received Event ===")
        print(json.dumps(event, indent=2))

        method = event.get('httpMethod') or event.get('requestContext', {}).get('http', {}).get('method')
        path_params = event.get('pathParameters', {}) or event.get('requestContext', {}).get('pathParameters', {})

        print("Extracted Path Parameters:", path_params)

        if method == 'POST' and 'ride_id' in path_params:
            return create_ride_request(event, path_params['ride_id'])
        
        elif method == 'PUT' and 'ride_id' in path_params and 'request_id' in path_params:
            return update_ride_request(event, path_params['ride_id'], path_params['request_id'])
        
        elif method == 'GET' and 'ride_id' in path_params:
            return get_ride_requests(path_params['ride_id'])
        
        elif method == 'GET' and 'driver_id' in path_params:
            return get_driver_requests(path_params['driver_id'])
        
        elif method == 'DELETE' and 'request_id' in path_params:
            return delete_ride_request(path_params['request_id'])
        
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Invalid request or missing parameters'})
        }

    except Exception as e:
        error_message = str(e)
        stack_trace = traceback.format_exc()  # Get full traceback

        print(f"❌ Error: {error_message}")
        print(f"❌ Stack Trace:\n{stack_trace}")

        return {
            'statusCode': 500,
            'body': json.dumps({'error': error_message, 'stack_trace': stack_trace})
        }

# 🟢 1️⃣ POST - Create a Ride Request
def create_ride_request(event, ride_id):
    try:
        print("Creating ride request")
        print("Event body:", event.get('body'))
        
        body = event.get("body", "{}")  # Ensure body is not None
        body = json.loads(body)

        rider_id = body.get('rider_id')
        
        print(f"Ride ID: {ride_id}")
        print(f"Rider ID: {rider_id}")
        
        if not rider_id:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'rider_id is required'})
            }

        # 🔍 Retrieve ride details from DynamoDB
        try:
            response = rides_table.get_item(Key={'ride_id': ride_id})
            ride = response.get('Item')

            if not ride:
                return {
                    'statusCode': 404,
                    'body': json.dumps({'error': 'Ride not found'})
                }
            
            # 🔧 Convert Decimal values before using json.dumps()
            ride = to_serializable(ride)
            print(f"Retrieved ride: {json.dumps(ride, indent=2)}")
            print("Driver id is ", ride["user_id"])

        except Exception as e:
            print(f"Error getting ride: {str(e)}")
            return {
                'statusCode': 500,
                'body': json.dumps({'error': f'Error retrieving ride: {str(e)}'})
            }

        # 🆕 Create ride request
        request_id = str(uuid.uuid4())
        request = {
            'request_id': request_id,
            'ride_id': ride_id,
            'rider_id': rider_id,
            'driver_id': ride["user_id"],
            'seats_requested': body.get('seats_requested'),
            'notes': body.get('notes'),
            'ride_status': 'pending',
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }

        print(f"Saving request: {json.dumps(to_serializable(request), indent=2)}")  # Convert request before saving
        book_ride_table.put_item(Item=request)
        
        # 🚀 Step 1: Publish to EventBridge
        event_bridge.put_events(
            Entries=[
                {
                    "Source": "ru.carpooling",
                    "DetailType": "RideRequested",
                    "Detail": json.dumps({
                        "RideID": ride_id,
                        "RequestID": request_id,
                        "RiderID": rider_id,
                        "DriverID": ride.get('user_id'),
                        "SeatsRequested": body.get('seats_requested'),
                        "Timestamp": datetime.utcnow().isoformat()
                    }),
                    "EventBusName": "RUCarpoolingEventBus"
                }
            ]
        )

        return {
            'statusCode': 201,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(to_serializable({  # Ensure output is JSON-safe
                'message': 'Ride request created successfully',
                'request_id': request_id
            }))
        }

    except Exception as e:
        print(f"Error in create_ride_request: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': f'Internal server error: {str(e)}'})
        }

# 🟠 2️⃣ PUT - Update Ride Request (Accept/Reject)
def update_ride_request(event, ride_id, request_id):
    try:
        body = json.loads(event.get("body", "{}")) 
        action = body.get('action')
        user_id = body.get('user_id')
        
        # Validate action
        if action not in ['accept', 'reject', 'cancel']:
            return {'statusCode': 400, 'body': json.dumps({'error': 'Invalid action'})}    
        
        # Get request details
        request = book_ride_table.get_item(Key={'request_id': request_id}).get('Item')
        if not request:
            return {'statusCode': 404, 'body': json.dumps({'error': 'Request not found'})}
        
        # Get ride details
        ride = rides_table.get_item(Key={'ride_id': ride_id}).get('Item')
        if not ride:
            return {'statusCode': 404, 'body': json.dumps({'error': 'Ride not found'})}

        # Convert Decimal values for safe JSON serialization
        request = to_serializable(request)
        ride = to_serializable(ride)

        # Retrieve the number of seats requested from the request item
        # Default to 1 if it's missing, but you can enforce that it must exist
        seats_requested = int(request.get('seats_requested', 1))

        # Handling Driver Permissions for Accept/Reject
        if action in ['accept', 'reject']:
            if user_id != request['driver_id']:
                return {
                    'statusCode': 403,
                    'body': json.dumps({'error': 'Only the driver can accept or reject requests'})
                }
            
            updated_status = 'accepted' if action == 'accept' else 'rejected'

            # If accepted, decrease available seats by the number requested
            if updated_status == 'accepted':
                available_seats = ride['available_seats']
                
                # Check if enough seats are available
                if available_seats >= seats_requested:
                    new_seats = available_seats - seats_requested
                    rides_table.update_item(
                        Key={'ride_id': ride_id},
                        UpdateExpression='SET available_seats = :new_seats',
                        ExpressionAttributeValues={':new_seats': new_seats}
                    )
                else:
                    return {
                        'statusCode': 400,
                        'body': json.dumps({'error': 'Not enough available seats'})
                    }
        
        # Handling Cancellation (Both Rider & Driver)
        elif action == 'cancel':
            if user_id not in [request['rider_id'], request['driver_id']]:
                return {
                    'statusCode': 403,
                    'body': json.dumps({'error': 'Only the rider or driver can cancel the request'})
                }

            updated_status = 'canceled'

            # If canceling an already accepted ride, restore the seats
            if request['ride_status'] == 'accepted':
                available_seats = ride['available_seats']
                new_seats = available_seats + seats_requested
                rides_table.update_item(
                    Key={'ride_id': ride_id},
                    UpdateExpression='SET available_seats = :new_seats',
                    ExpressionAttributeValues={':new_seats': new_seats}
                )
       
        if action in ['accept', 'reject', 'cancel']:
            # 🚀 Step 1: Publish to EventBridge
            event_bridge.put_events(
                Entries=[
                    {
                        "Source": "ru.carpooling",
                        "DetailType": "RideDetailsUpdated",
                        "Detail": json.dumps({
                            "RideID": ride_id,
                            "RequestID": request_id,
                            "RiderID": request['rider_id'],
                            "DriverID": request['driver_id'],
                            "SeatsRequested": body.get('seats_requested'),
                            "Timestamp": datetime.utcnow().isoformat(),
                            "notification_type": "Ride " + action,
                        }),
                        "EventBusName": "RUCarpoolingEventBus"
                    }
                ]
            )
            print("Putting in the bus")
        
        # Update request status in DynamoDB
        book_ride_table.update_item(
            Key={'request_id': request_id},
            UpdateExpression='SET ride_status = :ride_status, updated_at = :updated_at',
            ExpressionAttributeValues={
                ':ride_status': updated_status,
                ':updated_at': datetime.utcnow().isoformat()
            }
        ) 
        
        # (Optional) Send notification to the relevant party here...

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': f'Ride request {updated_status}',
                'request_id': request_id
            })
        }
    
    except Exception as e:
        print(f"Error in update_ride_request: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': f'Internal server error: {str(e)}'})
        }
        
def convert_decimal(obj):
    """Recursively converts Decimal objects to int or float"""
    if isinstance(obj, list):
        return [convert_decimal(i) for i in obj]
    elif isinstance(obj, dict):
        return {k: convert_decimal(v) for k, v in obj.items()}
    elif isinstance(obj, Decimal):
        return int(obj) if obj % 1 == 0 else float(obj)  # Convert to int if no decimal part
    else:
        return obj
    

# 🔵 3️⃣ GET - Fetch Ride Requests (For a Specific Ride)
def get_ride_requests(ride_id):
    if not ride_id:
        return {'statusCode': 400, 'body': json.dumps({'error': 'Missing ride_id'})}
    
    response = book_ride_table.scan(
        FilterExpression='ride_id = :ride_id',
        ExpressionAttributeValues={':ride_id': ride_id}
    )
    
    # Convert Decimal values before returning
    items = convert_decimal(response.get('Items', []))
    
    return {
        'statusCode': 200,
        'body': json.dumps({'requests': items})
    }
    
# 🔵 3️⃣ GET - Fetch Rides (For a Specific Driver)
# @app.get("/rides/{driver_id}")
def get_driver_requests(driver_id):
    try:
        if not driver_id:
            return {'statusCode': 400, 'body': json.dumps({'error': 'Missing driver_id'})}
        
        response = book_ride_table.scan(
            FilterExpression='driver_id = :driver_id',
            ExpressionAttributeValues={':driver_id': driver_id}
        )
        
        print("response for the driver ", response)
        
        # Convert Decimal values before returning
        items = convert_decimal(response.get('Items', []))
        
        print("response1 for the driver ", response)
        
        return {
            'statusCode': 200,
            'body': json.dumps({'requests': items})
        }
    except Exception as e:
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}

# 🔴 4️⃣ DELETE - Cancel a Ride Request
def delete_ride_request(request_id):
    # Check if request exists
    request = book_ride_table.get_item(Key={'request_id': request_id}).get('Item')
    if not request:
        return {'statusCode': 404, 'body': json.dumps({'error': 'Request not found'})}

    # Delete request
    book_ride_table.delete_item(Key={'request_id': request_id})
    
    return {
        'statusCode': 200,
        'body': json.dumps({'message': 'Ride request cancelled'})
    }
    
# zip function.zip book_ride.py
# aws lambda update-function-code \
#     --function-name RUBookRideLambda \
#     --zip-file fileb://function.zip \
#     --region us-east-1
