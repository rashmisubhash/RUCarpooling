from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordBearer
from app.models.user import User, ConfirmUser
from app.services.auth import signup, confirm_signup, signin, logout
from app.services.jwt_utils import decode_jwt_token

router = APIRouter()

# Define the OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@router.post("/signup", response_model=dict)
def signup_route(user: User):
    return signup(user)

@router.post("/confirm", response_model=dict)
def confirm_signup_route(user: ConfirmUser):
    return confirm_signup(user)

@router.post("/signin", response_model=dict)
def signin_route(user: User):
    return signin(user)

@router.post("/logout", response_model=dict)
def logout_route(token: str = Depends(oauth2_scheme)):
    return logout(token)

@router.get("/LandingPage", response_model=dict)
def landing_page_route(token: str = Depends(oauth2_scheme)):  # Use oauth2_scheme explicitly
    decode_jwt_token(token)  # Verify token
    return {"message": "This is a demo page"}

# Do resend code here