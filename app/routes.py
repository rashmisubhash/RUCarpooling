from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from passlib.context import CryptContext
import jwt
import datetime

# Create an instance of APIRouter
router = APIRouter()

# Password hashing setup
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT secret and algorithm
SECRET_KEY = "99ySHm25hfxUQI3MaSA3vKQcbHL1nCOzcEIdojc5"  # Use an environment variable in production
ALGORITHM = "HS256"

# Example data model for request body
class UserRegister(BaseModel):
    name: str
    email: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

# In-memory user "database" for demonstration
fake_users_db = {}

# Route for user registration
@router.post("/register")
async def register_user(user: UserRegister):
    if user.email in fake_users_db:
        raise HTTPException(status_code=400, detail="Email already registered")
    # Hash the password before storing it
    hashed_password = pwd_context.hash(user.password)
    fake_users_db[user.email] = {"name": user.name, "password": hashed_password}
    return {"message": f"User {user.name} registered successfully!"}

# Route for user login
@router.post("/login")
async def login_user(user: UserLogin):
    # Check if user exists
    db_user = fake_users_db.get(user.email)
    if not db_user or not pwd_context.verify(user.password, db_user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    # Generate JWT token
    token_data = {
        "sub": user.email,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=30)
    }
    token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)
    return {"access_token": token, "token_type": "bearer"}