"""
Microsoft Graph Service for creating draft emails
"""

import requests
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class MicrosoftGraphService:
    """Service for interacting with Microsoft Graph API"""
    
    def __init__(self):
        self.graph_endpoint = "https://graph.microsoft.com/v1.0"
    
    def create_draft_email(
        self, 
        access_token: str, 
        subject: str, 
        html_body: str,
        to_recipients: Optional[list] = None
    ) -> Dict[str, Any]:
        """
        Create draft email in user's mailbox with formatted HTML content
        
        Args:
            access_token: Valid OAuth access token
            subject: Email subject
            html_body: HTML content for email body (with formatting)
            to_recipients: Optional list of recipient email addresses
            
        Returns:
            Dict with draft_id and web_link to the draft
            
        Raises:
            Exception: If draft creation fails
        """
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        # Prepare draft data
        draft_data = {
            "subject": subject,
            "body": {
                "contentType": "HTML",
                "content": html_body
            },
            "importance": "normal"
        }
        
        # Add recipients if provided
        if to_recipients:
            draft_data["toRecipients"] = [
                {"emailAddress": {"address": email}} 
                for email in to_recipients
            ]
        
        # Create draft using Graph API
        response = requests.post(
            f"{self.graph_endpoint}/me/messages",
            headers=headers,
            json=draft_data
        )
        
        if response.status_code == 201:
            draft = response.json()
            draft_id = draft["id"]
            web_link = draft.get("webLink", "")
            
            logger.info(f"Successfully created draft email with ID: {draft_id}")
            
            return {
                "draft_id": draft_id,
                "web_link": web_link,
                "subject": draft.get("subject"),
                "created_at": draft.get("createdDateTime")
            }
        else:
            error_msg = f"Failed to create draft: {response.status_code} - {response.text}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    def get_draft_email(self, access_token: str, draft_id: str) -> Dict[str, Any]:
        """
        Get draft email details
        
        Args:
            access_token: Valid OAuth access token
            draft_id: ID of the draft email
            
        Returns:
            Draft email details
        """
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(
            f"{self.graph_endpoint}/me/messages/{draft_id}",
            headers=headers
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            error_msg = f"Failed to get draft: {response.status_code} - {response.text}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    def update_draft_email(
        self,
        access_token: str,
        draft_id: str,
        subject: Optional[str] = None,
        html_body: Optional[str] = None,
        to_recipients: Optional[list] = None
    ) -> Dict[str, Any]:
        """
        Update existing draft email
        
        Args:
            access_token: Valid OAuth access token
            draft_id: ID of the draft to update
            subject: Optional new subject
            html_body: Optional new HTML body
            to_recipients: Optional new recipient list
            
        Returns:
            Updated draft details
        """
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        update_data = {}
        
        if subject:
            update_data["subject"] = subject
        
        if html_body:
            update_data["body"] = {
                "contentType": "HTML",
                "content": html_body
            }
        
        if to_recipients:
            update_data["toRecipients"] = [
                {"emailAddress": {"address": email}}
                for email in to_recipients
            ]
        
        response = requests.patch(
            f"{self.graph_endpoint}/me/messages/{draft_id}",
            headers=headers,
            json=update_data
        )
        
        if response.status_code == 200:
            logger.info(f"Successfully updated draft: {draft_id}")
            return response.json()
        else:
            error_msg = f"Failed to update draft: {response.status_code} - {response.text}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    def delete_draft_email(self, access_token: str, draft_id: str) -> bool:
        """
        Delete draft email
        
        Args:
            access_token: Valid OAuth access token
            draft_id: ID of the draft to delete
            
        Returns:
            True if deleted successfully
        """
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        response = requests.delete(
            f"{self.graph_endpoint}/me/messages/{draft_id}",
            headers=headers
        )
        
        if response.status_code == 204:
            logger.info(f"Successfully deleted draft: {draft_id}")
            return True
        else:
            error_msg = f"Failed to delete draft: {response.status_code} - {response.text}"
            logger.error(error_msg)
            return False
    
    def list_drafts(self, access_token: str, top: int = 10) -> list:
        """
        List user's draft emails
        
        Args:
            access_token: Valid OAuth access token
            top: Number of drafts to retrieve (max 100)
            
        Returns:
            List of draft emails
        """
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(
            f"{self.graph_endpoint}/me/mailFolders/drafts/messages?$top={top}",
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            return data.get("value", [])
        else:
            error_msg = f"Failed to list drafts: {response.status_code} - {response.text}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    def get_user_profile(self, access_token: str) -> Dict[str, Any]:
        """
        Get authenticated user's profile information
        
        Args:
            access_token: Valid OAuth access token
            
        Returns:
            User profile including email, displayName, etc.
        """
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(
            f"{self.graph_endpoint}/me",
            headers=headers
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            error_msg = f"Failed to get user profile: {response.status_code} - {response.text}"
            logger.error(error_msg)
            raise Exception(error_msg)
