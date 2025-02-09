import json
import traceback
import boto3
import os
import groq
from decimal import Decimal
from dotenv import load_dotenv
import re

# Load environment variables
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Initialize AWS DynamoDB
dynamodb = boto3.resource('dynamodb', region_name="us-east-1")
TABLE_NAME = "RUCarpool_Emissions"
table = dynamodb.Table(TABLE_NAME)

# Initialize Groq Client
groq_client = groq.Client(api_key=GROQ_API_KEY)

def lambda_handler(event, context):
    """AWS Lambda function for calculating carbon emissions using Groq AI."""
    
    
    try:
        
        print("y evnet ", event)
        # 1️⃣ Parse incoming request directly from event (not using body)
        ride_id = event.get("ride_id")
        distance_km = Decimal(str(event.get("distance_km", 0)))  # ✅ Convert float to Decimal
        vehicle_type = event.get("vehicle_type", "").lower()
        passengers = int(event.get("passengers", 1))
        from_location = event.get("from_location", "")
        to_location = event.get("to_location", "")
        driver_id = event.get("driver_id", "")

        # 2️⃣ Validate input
        if not ride_id or not distance_km or not vehicle_type:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Missing required fields."})
            }

        prompt = (
            f"Estimate the total carbon emissions for a carpool ride of {distance_km} km "
            f"using a {vehicle_type} with {passengers} passengers.\n"
            "Follow these instructions carefully:\n"
            "1. DO NOT provide explanations.\n"
            "2. DO NOT include calculations.\n"
            "3. ONLY output results in the following format:\n"
            "\n"
            "Total CO₂ Emission: <NUMBER> kg CO₂\n"
            "Per Passenger Emission: <NUMBER> kg CO₂\n"
            "\n"
            "Example Output:\n"
            "Total CO₂ Emission: 9.3485 kg CO₂\n"
            "Per Passenger Emission: 2.3371 kg CO₂\n"
        )


        # 4️⃣ Call Groq AI model using chat API
        response = groq_client.chat.completions.create(
            model="mixtral-8x7b-32768",  # Adjust based on available Groq models
            messages=[{"role": "system", "content": prompt}],
            max_tokens=100
        )

        print("Groq response:", response)

        # 5️⃣ Extract text response from Groq API
        ai_response_text = response.choices[0].message.content.strip()
        print("AI Response:", ai_response_text)

        # 6️⃣ Extract AI-predicted CO₂ emissions
        total_emission, per_passenger_emission = extract_emission_values(ai_response_text)
        
        print("Total Emission:", total_emission)
        print("Per Passenger Emission:", per_passenger_emission)

        # 7️⃣ Store data in DynamoDB (Convert to Decimal)
        table.put_item(
            Item={
                "ride_id": ride_id,
                "driver_id": driver_id,
                "distance_km": Decimal(str(distance_km)),  # ✅ Convert float to Decimal
                "vehicle_type": vehicle_type,
                "passengers": passengers,
                "from_location": from_location,
                "to_location": to_location,
                "total_emission": Decimal(str(total_emission)),  # ✅ Convert float to Decimal
                "per_passenger_emission": Decimal(str(per_passenger_emission))  # ✅ Convert float to Decimal
            }
        )
        
        
        fun_summary_prompt = (
            f"Write a fun summary for a carpool ride where {passengers} passengers "
            f"traveled {distance_km:.1f} km using a {vehicle_type}. "
            f"The total CO₂ emission was {total_emission:.2f} kg, and the per passenger emission was {per_passenger_emission:.2f} kg. "
            "Keep it short, engaging, and add a fun fact at the end. "
            "Ensure it fits within 1-2 sentences.\n"
            "Example Output:\n"
            "\"🚗💨 You carpooled {distance_km} km with {passengers} friends and saved {savings} kg of CO₂! 🌱 That’s like planting a tree!\""
        )

        
        # Call Groq AI to generate the fun summary
        summary_response = groq_client.chat.completions.create(
            model="mixtral-8x7b-32768",
            messages=[{"role": "system", "content": fun_summary_prompt}],
            max_tokens=80  # Short response
        )

        # Extract AI-generated summary
        fun_summary = summary_response.choices[0].message.content.strip()

        # Print and return
        print("🎉 Fun AI Summary:", fun_summary)

        return {
            "statusCode": 200,
            "body": json.dumps({
                "ride_id": ride_id,
                "total_emission": float(total_emission),
                "per_passenger_emission": float(per_passenger_emission),
                "message": "Carbon footprint calculated successfully using Groq AI.",
                "fun_summary": fun_summary  # 🎉 Fun AI-generated message!
            })
        }


    except Exception as e:
        error_message = str(e)
        stack_trace = traceback.format_exc()
        print(f"❌ Error: {error_message}")
        print(f"❌ Stack Trace:\n{stack_trace}")
        return {"statusCode": 500, "body": json.dumps({"error": error_message, "stack_trace": stack_trace})}

def extract_emission_values(response_text):
    """
    Extracts emission values from the AI-generated response text.
    Uses regex to extract numbers and handles errors gracefully.
    """
    try:
        print("🔍 Raw AI Response for Parsing:", response_text)  # Debugging print

        # Use regex to extract numbers (including decimals)
        numbers = re.findall(r"[-+]?\d*\.\d+|\d+", response_text)

        if len(numbers) >= 2:
            total_emission = Decimal(numbers[0].strip())  # First number = total emission
            per_passenger_emission = Decimal(numbers[1].strip())  # Second number = per-passenger emission
            return total_emission, per_passenger_emission
        else:
            print("⚠️ AI response does not contain numeric values. Returning default 0 values.")
            return Decimal("0"), Decimal("0")  # Fallback values

    except Exception as e:
        print(f"⚠️ Error parsing AI response: {str(e)}")
        return Decimal("0"), Decimal("0")  # Fallback to zero
        
# zip function.zip groq_carbon_emissions.py
# aws lambda update-function-code \
#     --function-name RUGroqCalCO2Emissions \
#     --zip-file fileb://function.zip \
#     --region us-east-1