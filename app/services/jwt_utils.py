import jwt
from datetime import datetime, timedelta
from app.core.config import settings

def generate_custom_jwt(username: str):
    payload = {"sub": username, "exp": datetime.utcnow() + timedelta(hours=1)}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")

def decode_jwt_token(token: str):
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")