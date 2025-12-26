"""
Microsoft Authentication Service for OAuth2 flow
"""

import os
import msal
import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from models.database import UserAuth

logger = logging.getLogger(__name__)

class MicrosoftAuthService:
    """Service for handling Microsoft OAuth2 authentication and token management"""
    
    def __init__(self, db=None):
        self.db = db
        self.client_id = os.getenv("MICROSOFT_CLIENT_ID")
        self.client_secret = os.getenv("MICROSOFT_CLIENT_SECRET")
        self.tenant_id = os.getenv("MICROSOFT_TENANT_ID", "common")
        self.redirect_uri = os.getenv("MICROSOFT_REDIRECT_URI")
        self.authority = f"https://login.microsoftonline.com/{self.tenant_id}"
        self.scopes = ["https://graph.microsoft.com/Mail.ReadWrite"]
        
        if not self.client_id or not self.client_secret:
            logger.warning("Microsoft Graph API credentials not configured")
    
    def get_auth_url(self, state: Optional[str] = None) -> str:
        """
        Generate Microsoft OAuth authorization URL
        
        Args:
            state: Optional state parameter for CSRF protection
            
        Returns:
            Authorization URL for user to visit
        """
        app = msal.ConfidentialClientApplication(
            self.client_id,
            authority=self.authority,
            client_credential=self.client_secret
        )
        
        auth_url = app.get_authorization_request_url(
            scopes=self.scopes,
            redirect_uri=self.redirect_uri,
            state=state
        )
        
        logger.info("Generated auth URL for Microsoft login")
        return auth_url
    
    def exchange_code_for_token(self, code: str) -> Dict[str, Any]:
        """
        Exchange authorization code for access token
        
        Args:
            code: Authorization code from OAuth callback
            
        Returns:
            Token data including access_token, refresh_token, and expires_in
        """
        app = msal.ConfidentialClientApplication(
            self.client_id,
            authority=self.authority,
            client_credential=self.client_secret
        )
        
        result = app.acquire_token_by_authorization_code(
            code,
            scopes=self.scopes,
            redirect_uri=self.redirect_uri
        )
        
        if "error" in result:
            logger.error(f"Error acquiring token: {result.get('error_description')}")
            raise Exception(f"Failed to acquire token: {result.get('error_description')}")
        
        logger.info("Successfully exchanged code for tokens")
        return result
    
    def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refresh expired access token using refresh token
        
        Args:
            refresh_token: Refresh token from previous authentication
            
        Returns:
            New token data including access_token and expires_in
        """
        app = msal.ConfidentialClientApplication(
            self.client_id,
            authority=self.authority,
            client_credential=self.client_secret
        )
        
        result = app.acquire_token_by_refresh_token(
            refresh_token,
            scopes=self.scopes
        )
        
        if "error" in result:
            logger.error(f"Error refreshing token: {result.get('error_description')}")
            raise Exception(f"Failed to refresh token: {result.get('error_description')}")
        
        logger.info("Successfully refreshed access token")
        return result
    
    def save_tokens(self, db: Session, user_email: str, token_data: Dict[str, Any]) -> UserAuth:
        """
        Save or update user tokens in database
        
        Args:
            db: Database session
            user_email: User's email address
            token_data: Token data from MSAL
            
        Returns:
            UserAuth object
        """
        expires_in = token_data.get("expires_in", 3600)
        expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
        
        # Check if user already exists
        user_auth = db.query(UserAuth).filter(UserAuth.user_email == user_email).first()
        
        if user_auth:
            # Update existing record
            user_auth.access_token = token_data["access_token"]
            user_auth.refresh_token = token_data.get("refresh_token", user_auth.refresh_token)
            user_auth.token_expires_at = expires_at
            user_auth.updated_at = datetime.utcnow()
            logger.info(f"Updated tokens for user: {user_email}")
        else:
            # Create new record
            user_auth = UserAuth(
                user_email=user_email,
                access_token=token_data["access_token"],
                refresh_token=token_data["refresh_token"],
                token_expires_at=expires_at
            )
            db.add(user_auth)
            logger.info(f"Created new auth record for user: {user_email}")
        
        db.commit()
        db.refresh(user_auth)
        return user_auth
    
    def get_valid_token(self, db: Session, user_email: str) -> str:
        """
        Get valid access token for user, refresh if expired
        
        Args:
            db: Database session
            user_email: User's email address
            
        Returns:
            Valid access token
            
        Raises:
            Exception: If user not authenticated or token refresh fails
        """
        user_auth = db.query(UserAuth).filter(UserAuth.user_email == user_email).first()
        
        if not user_auth:
            raise Exception(f"User {user_email} not authenticated. Please login first.")
        
        # Check if token is expired or will expire in next 5 minutes
        now = datetime.utcnow()
        buffer = timedelta(minutes=5)
        
        if user_auth.token_expires_at <= now + buffer:
            logger.info(f"Token expired for {user_email}, refreshing...")
            try:
                token_data = self.refresh_access_token(user_auth.refresh_token)
                self.save_tokens(db, user_email, token_data)
                return token_data["access_token"]
            except Exception as e:
                logger.error(f"Failed to refresh token: {e}")
                raise Exception("Token refresh failed. Please re-authenticate.")
        
        return user_auth.access_token
    
    def is_user_authenticated(self, db: Session, user_email: str) -> bool:
        """
        Check if user has valid authentication
        
        Args:
            db: Database session
            user_email: User's email address
            
        Returns:
            True if user is authenticated and has valid/refreshable token
        """
        user_auth = db.query(UserAuth).filter(UserAuth.user_email == user_email).first()
        return user_auth is not None
    
    # Alias methods for API compatibility
    def acquire_token_by_auth_code(self, code: str) -> Dict[str, Any]:
        """Alias for exchange_code_for_token"""
        return self.exchange_code_for_token(code)
    
    def get_user_auth(self, user_email: str):
        """Get user authentication record from database"""
        if not self.db:
            raise Exception("Database session not available")
        return self.db.query(UserAuth).filter(UserAuth.user_email == user_email).first()
    
    def acquire_token_silent(self, user_email: str):
        """Get valid token, refreshing if needed"""
        if not self.db:
            raise Exception("Database session not available")
        try:
            access_token = self.get_valid_token(self.db, user_email)
            return {"access_token": access_token}
        except:
            return None
    
    def _save_tokens(self, user_email: str, token_response: Dict[str, Any]):
        """Save tokens to database (uses self.db)"""
        if not self.db:
            raise Exception("Database session not available")
        self.save_tokens(self.db, user_email, token_response)
    
    def get_user_info_from_token(self, access_token: str) -> Dict[str, Any]:
        """
        Get user information from Microsoft Graph API using access token
        
        Args:
            access_token: Valid access token
            
        Returns:
            User information including email
        """
        import requests
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(
            "https://graph.microsoft.com/v1.0/me",
            headers=headers
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to get user info: {response.text}")
