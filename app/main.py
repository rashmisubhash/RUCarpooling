import sys
import os

# Add dependencies path manually
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../dependencies")

from fastapi import FastAPI
from app.api.routes import router
from mangum import Mangum
import pydantic

app = FastAPI()

# Include the router
app.include_router(router)

@app.get("/")
def read_root():
    return {"message": "Welcome to the CarPooling API!"}

# Define the handler for AWS Lambda
handler = Mangum(app)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
