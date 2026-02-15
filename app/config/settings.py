

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
     SECRET_KEY: str
     OPENAI_API_KEY: str
     MONGODB_URL: str
     DB_NAME: str
     
     class Config:
          env_file = ".env"


settings = Settings()
