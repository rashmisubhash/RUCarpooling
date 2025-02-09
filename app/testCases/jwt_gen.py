import base64
import hmac
import hashlib

# ✅ Replace these with your actual AWS Cognito details
CLIENT_ID = "1hf732i741jv10c5a1h7dpo1n9"  # Your Cognito App Client ID
CLIENT_SECRET = "ved07emp84cdsdni78cps3aqbldmkf9q2hoekq8t75ar0adshpn"  # Your Cognito App Client Secret
USERNAME = "annu"  # The Cognito Username

def generate_secret_hash(username, client_id, client_secret):
    message = username + client_id
    dig = hmac.new(client_secret.encode("utf-8"), message.encode("utf-8"), hashlib.sha256).digest()
    return base64.b64encode(dig).decode()

# Generate the Secret Hash
secret_hash = generate_secret_hash(USERNAME, CLIENT_ID, CLIENT_SECRET)
print("Generated Secret Hash:", secret_hash)
