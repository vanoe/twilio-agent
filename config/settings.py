import os
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    APP_URL: str = Field(default="http://localhost:5050", env="APP_URL")
    PROJECT_NAME: str = "Solutions Two"
    ALLOW_ORIGINS: list[str] = Field(default_factory=lambda: ["*"])  # Allow all origins
    LOG_FILE: str = "logs/app.log"
    TWILIO_ACCOUNT_SID: str = Field(..., env="TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN: str = Field(..., env="TWILIO_AUTH_TOKEN")
    TWILIO_PHONE_NUMBER: str = Field(..., env="TWILIO_PHONE_NUMBER")
    GOOGLE_API_KEY: str = Field(..., env="GOOGLE_API_KEY")
    GOOGLE_CREDENTIALS_DIR: str = Field(default="config/google_credentials", env="GOOGLE_CREDENTIALS_DIR")
    OPENAI_API_KEY: str = Field(..., env="OPENAI_API_KEY")
    MONGO_URI: str = Field(..., env="MONGO_URI")
    MONGO_DATABASE_NAME: str = Field(..., env="MONGO_DATABASE_NAME")
    MONGO_COLLECTION_NAME_PRODUCTS: str = Field(..., env="MONGO_COLLECTION_NAME_PRODUCTS")
    MONGO_COLLECTION_NAME_SERVICES: str = Field(..., env="MONGO_COLLECTION_NAME_SERVICES")
    

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

settings = Settings()

# Constants for logging and debugging
SHOW_TIMING_MATH = False
