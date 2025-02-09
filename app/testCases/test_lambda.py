from app.lambdas.post_sign_up_lambda import lambda_handler

# Simulated Cognito Post Confirmation Event
test_event = {
    "userName": "test-user-123",
    "request": {
        "userAttributes": {
            "email": "testuser@example.com"
        }
    }
}

# Run locally
response = lambda_handler(test_event, None)
print(response)

# To Test
# python -m app.testCases.test_lambda