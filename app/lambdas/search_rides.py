import traceback
import requests
import json
import geohash2
import boto3
from datetime import datetime, timedelta
from math import radians, sin, cos, sqrt, atan2
from decimal import Decimal

def get_osrm_route(start_lat: float, start_lng: float, end_lat: float, end_lng: float):
    """Get actual driving route using OSRM"""
    base_url = "http://router.project-osrm.org/route/v1/driving"
    url = f"{base_url}/{start_lng},{start_lat};{end_lng},{end_lat}"
    
    params = {
        "overview": "full",
        "geometries": "geojson",
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

def calculate_geohash_similarity(user_geohashes, ride_geohashes):
    """Calculate similarity score based on overlapping geohashes."""
    # Convert both to sets to remove any duplicates
    user_set = set(user_geohashes)
    ride_set = set(ride_geohashes)
    
    # Find common geohashes
    common_geohashes = user_set & ride_set
    
    # Calculate Jaccard similarity
    union_size = len(user_set | ride_set)
    intersection_size = len(common_geohashes)
    
    if union_size == 0:
        return 0.0
    
    similarity_score = intersection_size / union_size
    
    print("Similarity calculation:")
    print(f"- User unique geohashes: {len(user_set)}")
    print(f"- Ride unique geohashes: {len(ride_set)}")
    print(f"- Common geohashes: {len(common_geohashes)}")
    print(f"- Similarity score: {similarity_score}")
    
    return similarity_score


def to_float(value):
    """Recursively convert Decimal to float if needed"""
    if isinstance(value, Decimal):
        return float(value)
    elif isinstance(value, dict):
        return {k: to_float(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [to_float(v) for v in value]
    return value

def lambda_handler(event, context):
    """Lambda function to search for matching rides"""
    try:
        body = json.loads(event['body'])

        # 1️⃣ Get the user's planned route
        user_route_data = get_osrm_route(
            body['from_lat'], 
            body['from_long'],
            body['to_lat'], 
            body['to_long']
        )
        
        if not user_route_data:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Could not calculate route'})
            }

        # Convert route to geohashes
        distance_km = user_route_data['distance'] / 1000
        user_geohashes = convert_route_to_geohashes(user_route_data['route'], distance_km)

        # 2️⃣ Calculate time window for ride matches
        departure_time = datetime.fromisoformat(body['departure_time'])
        time_window_start = (departure_time - timedelta(hours=2)).isoformat()
        time_window_end = (departure_time + timedelta(hours=2)).isoformat()

        # 3️⃣ Query potential matches from DynamoDB
        dynamodb = boto3.resource('dynamodb')
        rides_table = dynamodb.Table('RUCarRides')
        
        filter_expression = [
            'departure_time BETWEEN :start AND :end',
            '(ride_status = :scheduled OR ride_status = :active)',
            'available_seats >= :min_seats'
        ]

        expression_attribute_values = {
            ':start': time_window_start,
            ':end': time_window_end,
            ':scheduled': 'scheduled',
            ':active': 'active',
            ':min_seats': body["seats_requested"]
        }
        
        # Optional boolean filters (only add if True)
        optional_filters = ['pet_friendly', 'trunk_space', 'wheelchair_access']

        for key in optional_filters:
            if body.get(key) is True:  # Only filter if explicitly True
                placeholder = f":{key}"
                filter_expression.append(f"{key} = {placeholder}")
                expression_attribute_values[placeholder] = True  # Ensure it's True in DB

        # Execute the scan operation
        response = rides_table.scan(
            FilterExpression=" AND ".join(filter_expression),
            ExpressionAttributeValues=expression_attribute_values
        )
        
        print(json.dumps(response, indent=2, default=str))
        

        # 4️⃣ Score and rank matches
        scored_rides = []
        scored_rides = []
        for ride in response['Items']:
            print("\n=== Processing Ride ===")
            print(f"Ride ID: {ride['ride_id']}")
            print(f"From: {ride['from_location']}")
            print(f"To: {ride['to_location']}")
            
            # Debug geohash comparison
            ride_geohashes = set(ride['route_geohashes'])
            user_geohashes_set = set(user_geohashes)
            
            print(f"Number of geohashes:")
            print(f"- User route: {len(user_geohashes_set)}")
            print(f"- Ride route: {len(ride_geohashes)}")
            
            route_similarity = calculate_geohash_similarity(user_geohashes, ride['route_geohashes'])
            
            ride_time = datetime.fromisoformat(ride['departure_time'])
            time_diff = abs((departure_time - ride_time).total_seconds() / 3600)
            time_score = max(0, 1 - (time_diff / 2) ** 0.5)
            # Consider using a more lenient time scoring
            time_score = max(0, 1 - (time_diff / 4))  # Linear decay over 4 hours
            
            print(f"Scores:")
            print(f"- Route similarity: {route_similarity:.3f}")
            print(f"- Time score: {time_score:.3f}")
            print(f"- Seat availability: {ride['available_seats']}/{ride['total_seats']}")
            
            score = (
                float(route_similarity) * 0.5 +  # Convert route_similarity to float
                float(time_score) * 0.3 +  # Convert time_score to float
                (float(ride['available_seats']) / float(ride['total_seats'])) * 0.1  # Convert both values to float
            )

            if route_similarity > 0.15:  # Only include rides with at least 30% similarity
                scored_rides.append({
                    **ride,
                    'score': score,
                    'route_similarity': route_similarity,
                    'time_difference_hours': time_diff
                })

            print(f"Final score: {score:.3f}")
            
        for ride in scored_rides:
            ride['score'] = float(ride['score'])
            ride['available_seats'] = float(ride['available_seats'])
            ride['total_seats'] = float(ride['total_seats'])
            ride['time_difference_hours'] = float(ride['time_difference_hours'])

    
        print("Final Score", scored_rides)
        # 5️⃣ Sort by highest match score
        scored_rides.sort(key=lambda x: x['score'], reverse=True)

        # 6️⃣ Return results with optional debugging info
        response_body = {
            'rides': scored_rides,
            'total': len(scored_rides),
            'route_info': {
                'distance_km': distance_km,
                'duration_minutes': user_route_data['duration'] / 60
            }
        }

        if 'debug' in body and body['debug']:
            response_body['debug'] = {
                'searched_geohash': user_geohashes[0][:5],
                'departure_time_window': (time_window_start, time_window_end),
                'user_route_geohashes': user_geohashes
            }

        return {
            'statusCode': 200,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps(to_float(response_body)) 
        }

    except Exception as e:
        error_message = str(e)
        stack_trace = traceback.format_exc()
        print(f"❌ Error: {error_message}")
        print(f"❌ Stack Trace:\n{stack_trace}")
        # return {"statusCode": 500, "body": json.dumps({"error": error_message, "stack_trace": stack_trace})}
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

# Upload the Zip File to AWS Lambda
# zip function.zip search_rides.py
# aws lambda update-function-code \
#     --function-name RUSearchRides \
#     --zip-file fileb://function.zip \
#     --region us-east-1