from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2
from fastapi.openapi.models import OAuthFlows as OAuthFlowsModel
from fastapi.security.utils import get_authorization_scheme_param
import os
from dotenv import load_dotenv
import logging

from app.schemas.token import TokenData
from app.services.user_service import UserService
from app.models.user import User, UserRole

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Security configuration
SECRET_KEY = os.getenv("SECRET_KEY", "YOUR_SECRET_KEY_HERE")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# Initialize password hashing with bcrypt and proper settings
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12,
    bcrypt__default_rounds=12
)

# OAuth2 password bearer authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/token")

def verify_password(plain_password, hashed_password):
    """Verify a password against a hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    """Generate a password hash"""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create a JWT access token"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

class OAuth2PasswordBearerWithCookie(OAuth2):
    """Custom OAuth2 password bearer that can extract token from both header and cookie"""
    def __init__(
        self,
        tokenUrl: str,
        scheme_name: str = None,
        scopes: dict = None,
        auto_error: bool = True,
    ):
        if not scopes:
            scopes = {}
        flows = OAuthFlowsModel(password={"tokenUrl": tokenUrl, "scopes": scopes})
        super().__init__(flows=flows, scheme_name=scheme_name, auto_error=auto_error)

    async def __call__(self, request: Request) -> Optional[str]:
        """
        Extract the token from the request.
        Checks Authorization header first, then cookies.
        """
        # Try to get token from header first
        authorization = request.headers.get("Authorization")
        scheme, param = get_authorization_scheme_param(authorization)
        
        # For debugging
        client = f"{request.client.host}:{request.client.port}" if request.client else "Unknown"
        url = str(request.url)
        
        if authorization:
            # If Authorization header is present
            logger.debug(f"Auth header found for {client} requesting {url}: {scheme}")
            if scheme.lower() == "bearer":
                # Return token whether or not it has a Bearer prefix (we'll handle that in get_current_user)
                return param
            else:
                # If it's not Bearer scheme, just return the whole authorization string
                # This handles cases where the token is sent without a scheme
                logger.debug(f"Non-Bearer auth scheme detected: {scheme}")
                return authorization
        else:
            # If not in header, try to get from cookie
            logger.debug(f"No Auth header for {client} requesting {url}, checking cookies")
            token = request.cookies.get("access_token")
            if token:
                logger.debug("Auth cookie found")
            
            if not token and self.auto_error:
                logger.warning(f"No authentication found for {client} requesting {url}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Not authenticated",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            return token

# Use the custom bearer for token extraction
oauth2_scheme = OAuth2PasswordBearerWithCookie(tokenUrl="/api/auth/token")

async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """Get the current user from the token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Remove 'Bearer ' prefix if it exists in the token
        original_token = token  # Save for logging
        if token and token.startswith("Bearer "):
            token = token[7:]  # Remove "Bearer " prefix
            logger.debug(f"Removed 'Bearer ' prefix from token: {original_token[:15]}...")
        
        # Log token length for debugging (don't log the full token for security)
        token_length = len(token) if token else 0
        logger.debug(f"Validating token of length {token_length}")
            
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        
        if email is None:
            logger.warning("Token missing 'sub' claim")
            raise credentials_exception
        
        logger.debug(f"Token validated for email: {email}")
        
        # Create token data
        token_data = TokenData(
            email=email,
            user_id=payload.get("user_id"),
            role=payload.get("role")
        )
    except JWTError as e:
        logger.error(f"JWT Error: {str(e)}")
        raise credentials_exception
    except Exception as e:
        logger.error(f"Token validation error: {str(e)}")
        raise credentials_exception
    
    # Get user from database
    user = await UserService.find_by_email(token_data.email)
    if user is None:
        logger.warning(f"User not found for email: {token_data.email}")
        raise credentials_exception
    
    logger.debug(f"Successfully authenticated user: {user.email}")
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get the current active user"""
    return current_user

async def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """Check if the current user is an admin"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to perform this action"
        )
    return current_user 