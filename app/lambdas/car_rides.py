import json
import boto3
import os
import uuid
from boto3.dynamodb.conditions import Key
from decimal import Decimal

import requests
import polyline
import geohash2
import traceback

# ✅ Modify the ride search (search_rides) to query rides based on geohashes instead of scanning all rides.
# ✅ Optionally, add a GSI (Global Secondary Index) on route_geohashes to speed up queries.

dynamodb = boto3.resource("dynamodb")
TABLE_NAME = "RUCarRides"  # Ensure this is set in Lambda env variables

# Initialize AWS Lambda Client
lambda_client = boto3.client("lambda", region_name="us-east-1")

def convert_to_decimal(value):
    # """ Convert float to Decimal to comply with DynamoDB requirements. """
    if isinstance(value, float):
        return Decimal(str(value))  # Convert float to string first to prevent precision issues
    return value

def decimal_to_float(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, list):
        return [decimal_to_float(i) for i in obj]
    if isinstance(obj, dict):
        return {k: decimal_to_float(v) for k, v in obj.items()}
    return obj


def get_osrm_route(start_lat: float, start_lng: float, end_lat: float, end_lng: float):
    """Get actual driving route using OSRM"""
    print(f"Fetching route from OSRM: {start_lat}, {start_lng} to {end_lat}, {end_lng}")
    base_url = "http://router.project-osrm.org/route/v1/driving"
    url = f"{base_url}/{start_lng},{start_lat};{end_lng},{end_lat}"
    
    params = {
        "overview": "full",
        "geometries": "geojson"
    }
    
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            if data["code"] == "Ok":
                return {
                    'route': data["routes"][0]["geometry"]["coordinates"],
                    'duration': data["routes"][0]["duration"],
                    'distance': data["routes"][0]["distance"]
                }
                # Remove this line that only returns coordinates
                # return data["routes"][0]["geometry"]["coordinates"]
    except Exception as e:
        print(f"OSRM API error: {str(e)}")
    return None

def convert_route_to_geohashes(route, distance_km, precision=6):
    """Convert a route to a reduced list of geohashes with dynamic step size."""
    # Determine step size based on route distance
    if distance_km < 10:
        step = 3
    elif distance_km < 50:
        step = 5
    elif distance_km < 200:
        step = 10
    else:
        step = 15
    
    # Convert to geohashes and remove duplicates
    unique_geohashes = list(set(
        geohash2.encode(lat, lon, precision) 
        for i, (lon, lat) in enumerate(route) 
        if i % step == 0
    ))
    
    print(f"Route stats:")
    print(f"- Distance: {distance_km:.2f} km")
    print(f"- Step size: {step}")
    print(f"- Total points: {len(route)}")
    print(f"- Unique geohashes: {len(unique_geohashes)}")
    
    return unique_geohashes


def create_ride(event, context):
    try:
        body = event.get("body", "{}")  # Ensure body is not None
        
        data = json.loads(body)
        ride_id = str(uuid.uuid4())
        
        print(body)
        print(data)
        print(data.get("from_lat"))
        print(convert_to_decimal(data.get("from_lat")))
        
        # When creating a ride
        route_data = get_osrm_route(data.get("from_lat"), data.get("from_long"), data.get("to_lat"), data.get("to_long"))
        distance_km = route_data['distance'] / 1000
        route_geohashes = convert_route_to_geohashes(route_data['route'], distance_km)
        
        if not route_data:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Could not calculate route'})
            }
            
        print("Generated route geohashes:", {
            'count': len(route_geohashes),
            'first_few': route_geohashes[:5],
            'distance_km': distance_km
        })

        print("So much fo routes ", route_data)        
        
        table = dynamodb.Table(TABLE_NAME)
        item = {
            "ride_id": ride_id,
            "user_id": data.get("user_id"),
            "car_id": data.get("car_id"),
            "from_location": data.get("from_location"),
            "from_lat": convert_to_decimal(data.get("from_lat")),
            "from_long": convert_to_decimal(data.get("from_long")),
            "to_location": data.get("to_location"),
            "to_lat": convert_to_decimal(data.get("to_lat")),
            "to_long": convert_to_decimal(data.get("to_long")),
            "total_seats": data.get("total_seats"),
            "available_seats": data.get("available_seats"),
            "departure_time": data.get("departure_time"),
            "pet_friendly": data.get("pet_friendly", False),
            "trunk_space": data.get("trunk_space", False),
            "air_conditioning": data.get("air_conditioning", False),
            "wheelchair_access": data.get("wheelchair_access", False),
            "note": data.get("note", ""),
            "ride_price": convert_to_decimal(data.get("ride_price")),
            "ride_status":data.get("ride_status", ""),
            "distance_km": convert_to_decimal(distance_km),
            "route_geohashes": route_geohashes,
            "created_at": data.get("timestamp"),
            "updated_at": data.get("timestamp")
        }
        print("printing item...", item)
        
        table.put_item(Item=item)
        
        
        
        # Define payload for Lambda B (Emission Calculator)
        payload = {
            "ride_id": ride_id,
            "distance_km": float(distance_km),
            "vehicle_type": "gasoline",
            "passengers": int(data.get("total_seats", 1)),
            "from_location": data.get("from_location"),
            "to_location": data.get("to_location"),
            "driver_id": data.get("user_id")
        }
        
        # Invoke Lambda B (RUCarpool_CalculateEmissions)
        response = lambda_client.invoke(
            FunctionName="RUGroqCalCO2Emissions",  # Name of the target Lambda function
            InvocationType="RequestResponse",  # Synchronous invocation
            Payload=json.dumps(payload).encode("utf-8")
        )
        
        # Read and parse response from Lambda B
        response_payload = json.loads(response["Payload"].read().decode("utf-8"))
        print("From CO2Emissions ", response_payload)
        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "Carbon Emissions Caluclated",
                "ride_id": ride_id,
                "lambda_b_response": response_payload
            })
        }
        
        return {
            "statusCode": 201, 
            "body": json.dumps({
                "ride_id": ride_id,
                "geohash_count": len(route_geohashes)
            })
        }
        
        
        
        
    except json.JSONDecodeError:
        return {"statusCode": 400, "body": json.dumps({"error": "Invalid JSON format"})}
    except json.JSONDecodeError:
        return {"statusCode": 400, "body": json.dumps({"error": "Invalid JSON format"})}
    except Exception as e:
        error_message = str(e)
        stack_trace = traceback.format_exc()
        print(f"❌ Error: {error_message}")
        print(f"❌ Stack Trace:\n{stack_trace}")
        return {"statusCode": 500, "body": json.dumps({"error": error_message, "stack_trace": stack_trace})}
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
    
def get_all_rides(event, context):
    try:
        table = dynamodb.Table(TABLE_NAME)
        response = table.scan()
        return {"statusCode": 200, "body": json.dumps({"car_rides": decimal_to_float(response.get("Items", []))})}
    except Exception as e:
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}

def get_ride_by_id(event, context):
    try:
        ride_id = event["pathParameters"]["ride_id"]
        
        table = dynamodb.Table(TABLE_NAME)
        response = table.get_item(Key={"ride_id": ride_id})
        
        if "Item" in response:
            return {"statusCode": 200, "body": json.dumps({"car_rides": decimal_to_float(response["Item"])})}
        else:
            return {"statusCode": 404, "body": json.dumps({"error": "Ride not found"})}
    except Exception as e:
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}

def get_rides_by_user(event, context):
    try:
        user_id = event["pathParameters"]["user_id"]
        
        table = dynamodb.Table(TABLE_NAME)
        response = table.query(
            IndexName="user_id-index",
            KeyConditionExpression=Key("user_id").eq(user_id)
        )
        
        return {"statusCode": 200, "body": json.dumps({"car_rides": decimal_to_float(response.get("Items", []))})}
    except Exception as e:
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}

def update_ride(event, context):
    try:
        ride_id = event["pathParameters"]["ride_id"]
        data = json.loads(event["body"])
        
        table = dynamodb.Table(TABLE_NAME)
        update_expression = "SET " + ", ".join(f"{k} = :{k}" for k in data.keys())
        expression_values = {f":{k}": v for k, v in data.items()}
        expression_values[":updated_at"] = data.get("updated_at", "")
        
        table.update_item(
            Key={"ride_id": ride_id},
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_values,
            ReturnValues="UPDATED_NEW"
        )
        
        return {"statusCode": 200, "body": json.dumps({"message": "Ride updated successfully"})}
    except Exception as e:
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}

def delete_ride(event, context):
    try:
        ride_id = event["pathParameters"]["ride_id"]
        
        table = dynamodb.Table(TABLE_NAME)
        table.delete_item(Key={"ride_id": ride_id})
        
        return {"statusCode": 200, "body": json.dumps({"message": "Ride deleted successfully"})}
    except Exception as e:
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}

# zip function.zip car_rides.py

    
# aws lambda update-function-code \
#     --function-name RUCreateRide \
#     --zip-file fileb://function.zip \
#     --region us-east-1
    
# aws lambda update-function-code \
#     --function-name RUGetAllRides \
#     --zip-file fileb://function.zip \
#     --region us-east-1

# aws lambda update-function-code \
#     --function-name RUGetRideById \
#     --zip-file fileb://function.zip \
#     --region us-east-1

# aws lambda update-function-code \
#     --function-name RUGetRidesByUser \
#     --zip-file fileb://function.zip \
#     --region us-east-1

# aws lambda update-function-code \
#     --function-name RUUpdateRide \
#     --zip-file fileb://function.zip \
#     --region us-east-1

# aws lambda update-function-code \
#     --function-name RUDeleteRide \
#     --zip-file fileb://function.zip \
#     --region us-east-1





# aws lambda update-function-configuration \
#     --function-name RUCreateRide \
#     --handler car_rides.create_ride \
#     --region us-east-1

# aws lambda update-function-configuration \
#     --function-name RUGetAllRides \
#     --handler car_rides.get_all_rides \
#     --region us-east-1

# aws lambda update-function-configuration \
#     --function-name RUGetRideById \
#     --handler car_rides.get_ride_by_id \
#     --region us-east-1

# aws lambda update-function-configuration \
#     --function-name RUGetRidesByUser \
#     --handler car_rides.get_rides_by_user \
#     --region us-east-1

# aws lambda update-function-configuration \
#     --function-name RUUpdateRide \
#     --handler car_rides.update_ride \
#     --region us-east-1

# aws lambda update-function-configuration \
#     --function-name RUDeleteRide \
#     --handler car_rides.delete_ride \
#     --region us-east-1

