# RU Carpooling Backend

## Overview
The RU Carpooling backend is designed to support a carpooling service for Rutgers University students. It provides authentication, user profile management, and ride-sharing functionalities. The backend leverages AWS Cognito for authentication and DynamoDB for storing user profiles and ride details.

## Features
- User authentication using AWS Cognito
- Manages user accounts including creation, authentication, and profile updates
- Handles ride creation, updates, requests, and searching for available rides
- Fun metrics tracking (total rides given/taken)
- Provides real-time and stored notifications for ride-related activities
- Supports speech-to-text, avatar generation, carbon emissions estimation, and ride summary generation

## Tech Stack
- **Backend:** Python3, FastAPI with Boto3
- **Database:** AWS DynamoDB
- **Authentication:** AWS Cognito
- **Hosting:** AWS Lambda (Serverless)
- **Other AWS Services:** API Gateway, CloudWatch, IAM, Event Bridge, S3, Websockets

## Lambda Functions

### Cognito
- **Sign Up** (`POST /signup`): Registers a new student.
- **Confirm Signup** (`POST /confirm`): Confirm student registration using a confirmation code for their university mail.
- **Sign in** (`POST /signin`): Authenticates the user and generates an access token.

### Profile
- **Add User** (`POST /users`): Creates a new user profile.
- **Get User Details** (`GET /users/{user_id}`): Retrieves user profile details.
- **Edit User Details** (`PUT /users/{user_id}`): Updates user profile information.
- **Delete User** (`DELETE /users/{user_id}`): Deletes a user profile.

### Car Details
- **Add Car** (`POST /users/{user_id}/cars`): Allows users to add a new car.
- **Get User's Cars** (`GET /users/{user_id}/cars`): Retrieves all cars associated with a user.
- **Edit Car Details** (`PUT /users/{user_id}/cars/{car_id}`): Updates the details of a specific car.
- **Delete Car** (`DELETE /users/{user_id}/cars/{car_id}`): Removes a car from the user's profile.
- **Get Car by ID** (`GET /cars/{car_id}`): Fetches car details using a unique car ID.

### Post Ride and Search Ride
- **Post Ride** (`POST /rides/create`): Creates a new ride listing.
- **Update Ride** (`PUT /rides/{ride_id}`): Updates ride details.
- **Get All Rides** (`GET /rides`): Retrieves a list of all available rides.
- **Get Rides by User ID** (`GET /users/{user_id}/rides`): Fetches rides posted by a specific user.
- **Get Ride by Ride ID** (`GET /rides/{ride_id}`): Retrieves details of a specific ride.
- **Delete Ride** (`DELETE /rides/{ride_id}`): Deletes a ride entry.
- **Search Ride** (`POST /rides/search`): Searches for available rides based on user criteria.

### Book Ride
- **Request Ride** (`POST /rides/{ride_id}/request`): Allows a user to request a ride.
- **Get Ride Requests** (`GET /rides/{ride_id}/requests`): Retrieves all ride requests for a specific ride.
- **Update Ride Request** (`PUT /rides/{ride_id}/request/{request_id}`): Updates the status of a ride request (Accept, Reject, Cancel).
- **Delete Ride Request** (`DELETE /rides/{ride_id}/request/{request_id}`): Deletes a ride request.
- **Get Rides by Driver** (`GET /rides/{driver_id}`): Retrieves all rides posted by a specific driver.

### Notifications
- **Get Notifications** (`GET /notifications/{user_id}`): Retrieves all notifications for a user.
- **Mark Notification as Read** (`PATCH /notifications/mark-read`): Marks a specific notification as read.
- **WebSocket Notification** (`wss://sy3ppk7bnh.execute-api.us-east-1.amazonaws.com/dev`): Enables real-time notifications for ride updates.

### AI Integrations
- **Speech-to-Text** (`POST /speech-to-text`): Converts speech from a Base64-encoded `.wav` audio file into text.
- **Generate Avatar** (`POST /{user_id}/photo`): Creates an AI-generated avatar based on user preferences.
- **Carbon Emissions Estimation**: Uses AI to estimate total and per-passenger CO₂ emissions for a carpool ride.
- **Generate Fun Summary**: Creates a short and engaging summary of a carpool ride, including CO₂ savings.


## Setup Instructions
## 📌 Prerequisites

- **Python 3 (3.11 recommended)**
- **Node.js & npm** (for any frontend-related dependencies)
- **AWS CLI** configured with appropriate permissions
- **DynamoDB** table set up
- **Cognito User Pool** created
- **Docker** installed (for containerized deployments)

---

## 🛠️ Installation

### 1️⃣ Clone the Repository
```sh
git clone https://github.com/rashmisubhash/RUCarpooling-backend.git
cd RUCarpooling-backend
```

### 2️⃣ Create a Virtual Environment (Recommended)
```sh
python3 -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
```

### 3️⃣ Install Dependencies
```sh
pip install -r requirements.txt
```

### 4️⃣ Create a `.env` File
Create a `.env` file in the root directory and add the following:
```env
AWS_REGION=<your-region>
DYNAMODB_TABLE_NAME=<your-table-name>
COGNITO_USER_POOL_ID=<your-user-pool-id>
COGNITO_CLIENT_ID=<your-client-id>
AWS_ACCESS_KEY_ID=<your-access-key-id>
AWS_SECRET_ACCESS_KEY=<your-secret-key>
GROQ_API_KEY=<your-groq-api-key>
HUGGINGFACE_API_KEY=<your-huggingface-api-key>
```

### 5️⃣ Start the FastAPI Server with Uvicorn
```sh
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
The server will start at **http://localhost:8000**.

---

## 🚀 Running the FastAPI Backend Locally

### Test the API
Run the following command to check if the API is working:
```sh
curl -X 'GET' 'http://localhost:8000/' -H 'accept: application/json'
```
Alternatively, open **[http://localhost:8000/docs](http://localhost:8000/docs)** for the **Swagger UI**.

---

## 🐳 Running with Docker

### 1️⃣ Build the Docker Image
```sh
docker build -t ru-carpooling-backend .
```

### 2️⃣ Run the Container
```sh
docker run -p 8000:8000 --env-file .env ru-carpooling-backend
```

---

## 🌍 Deployment

To deploy the backend using **AWS Lambda**:
```sh
npm run deploy
```
Ensure **AWS SAM** or **Serverless Framework** is configured if using Lambda.

---

## 📜 License

This project is licensed under the **MIT License**.

---

## 📬 Contact

For questions, reach out to 📧 **rashmi.subhash@example.com** or create an **issue** in the repository.

---

### 🎯 Happy Coding! 🚀