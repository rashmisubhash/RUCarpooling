from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    CLIENT_ID: str
    CLIENT_SECRET: str
    REGION: str
    JWT_SECRET: str
    aws_secret_key: str
    aws_access_key: str
    aws_region: str
    COGNITO_USER_POOL_ID: str
    GROQ_API_KEY: str
    OPENAI_API_KEY: str
    REPLICATE_API_KEY: str
    DEEPAI_API_KEY: str

    class Config:
        env_file = ".env"

settings = Settings()
