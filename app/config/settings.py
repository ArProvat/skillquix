

from typing import Any
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
     SECRET_KEY: str
     OPENAI_API_KEY: str
     MONGODB_URL: str
     DB_NAME: str
     QDRANT_HOST: Any
     QDRANT_PORT: int
     
     
     class Config:
          env_file = ".env"


settings = Settings()
