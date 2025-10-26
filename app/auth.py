import os, time
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError

ALGO = "HS256"
bearer = HTTPBearer()

def create_token() -> str:
    exp = int(time.time()) + int(os.environ.get("JWT_EXPIRE_MIN", "43200"))*60
    return jwt.encode({"exp": exp, "sub": "admin"}, os.environ["JWT_SECRET"], algorithm=ALGO)

def verify_token(token: str):
    try:
        payload = jwt.decode(token, os.environ["JWT_SECRET"], algorithms=[ALGO])
        if payload.get("sub") != "admin":
            raise JWTError()
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

async def admin_required(creds: HTTPAuthorizationCredentials = Depends(bearer)):
    verify_token(creds.credentials)
