from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from database import SessionLocal
from models import AuditLog, User
from jose import jwt, JWTError
import os

SECRET_KEY = os.getenv("SECRET_KEY", "fallback-key")
ALGORITHM = "HS256"

#Not needed paths
EXCLUDED_PATHS = ["/docs", "/openapi.json", "/redoc", "/favicon.ico", "/metadata"]


def get_action_from_method(method: str) -> str:
    mapping = {
        "GET": "READ",
        "POST": "CREATE",
        "PUT": "UPDATE",
        "PATCH": "UPDATE",
        "DELETE": "DELETE"
    }
    return mapping.get(method, "UNKNOWN")


def extract_user_from_token(auth_header: str | None) -> tuple[str | None, str | None]:
    if not auth_header or not auth_header.startswith("Bearer "):
        return None, None
    
    token = auth_header.replace("Bearer ", "")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
    except JWTError:
        return None, None
    
    if not email:
        return None, None
    
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if user:
            return user.email, user.role
        return None, None
    finally:
        db.close()


class AuditLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next): 
        response = await call_next(request)
        
        if any(request.url.path.startswith(p) for p in EXCLUDED_PATHS):
            return response
        
        
        auth_header = request.headers.get("Authorization")
        user_email, user_role = extract_user_from_token(auth_header)
        
        
        db = SessionLocal()
        try:
            log = AuditLog(
                user_email=user_email,
                user_role=user_role,
                action=get_action_from_method(request.method),
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                ip_address=request.client.host if request.client else None )
            db.add(log)
            db.commit()
        except Exception as e:
            print(f"Audit log failed: {e}")
            db.rollback()
        finally:
            db.close()
        
        return response