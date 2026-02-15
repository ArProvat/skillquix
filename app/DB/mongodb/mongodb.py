from motor.motor_asyncio import AsyncIOMotorClient
from app.config.settings import settings

class MongoDB:
     def __init__(self):
          self.client = AsyncIOMotorClient(settings.MONGODB_URL)
          self.db = self.client[settings.DB_NAME]

     def get_db(self):
          return self.db
          