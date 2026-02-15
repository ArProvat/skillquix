from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.config.settings import settings
from jose import jwt


def verify_token(token: HTTPAuthorizationCredentials = Depends(HTTPBearer())):
     try:
          payload = jwt.decode(token.credentials, settings.SECRET_KEY, algorithms=["HS256"])
          return payload
     except jwt.JWTError:
          raise HTTPException(status_code=401, detail="Invalid authentication credentials")
