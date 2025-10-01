"""
Email processing service for automated commission email handling.

NOTE: This module is OPTIONAL when using n8n for email processing (recommended).
      n8n provides a visual workflow interface with better monitoring and flexibility.
      See docs/N8N_INTEGRATION_GUIDE.md for n8n setup instructions.

This module provides functionality to:
- Connect to email servers via IMAP
- Fetch unread commission-related emails
- Parse and extract commission data
- Store processed data in the database

Use this module if:
- You prefer code-based automation
- You need batch processing capabilities
- You want a backup/fallback email processor
- You're running scheduled scripts
"""

import imaplib
import email
from email.header import decode_header
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime

from .email_parser import AIEmailParser
from ..database.repository import CommissionRepository
from ..database.models import DatabaseManager

logger = logging.getLogger(__name__)


class EmailProcessor:
    """
    Service for processing commission emails from an IMAP mailbox.
    
    Connects to an email server, fetches commission-related emails,
    parses them using AI, and stores the results in the database.
    """
    
    def __init__(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        api_key: str,
        use_ssl: bool = True,
        folder: str = 'INBOX',
        search_criteria: str = 'UNSEEN SUBJECT "commission"',
        db_manager: Optional[DatabaseManager] = None
    ):
        """
        Initialize email processor.
        
        Args:
            host: IMAP server hostname
            port: IMAP server port
            username: Email account username
            password: Email account password
            api_key: OpenAI API key for parsing
            use_ssl: Whether to use SSL (default: True)
            folder: Email folder to monitor (default: INBOX)
            search_criteria: IMAP search criteria (default: UNSEEN SUBJECT "commission")
            db_manager: Database manager instance (creates default if None)
        """
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.use_ssl = use_ssl
        self.folder = folder
        self.search_criteria = search_criteria
        
        # Initialize parser and repository
        self.parser = AIEmailParser(api_key=api_key)
        self.repository = CommissionRepository(db_manager or DatabaseManager())
        
        logger.info(f"EmailProcessor initialized for {username}@{host}")
    
    def connect(self) -> imaplib.IMAP4_SSL:
        """
        Connect to the IMAP server.
        
        Returns:
            IMAP connection object
            
        Raises:
            imaplib.IMAP4.error: If connection fails
        """
        try:
            if self.use_ssl:
                mail = imaplib.IMAP4_SSL(self.host, self.port)
            else:
                mail = imaplib.IMAP4(self.host, self.port)
            
            mail.login(self.username, self.password)
            logger.info(f"Connected to {self.host} as {self.username}")
            return mail
            
        except Exception as e:
            logger.error(f"Failed to connect to email server: {e}")
            raise
    
    def process_new_emails(self) -> Dict[str, Any]:
        """
        Process all new commission emails.
        
        Connects to the email server, fetches unread commission emails,
        parses them, and stores the data in the database.
        
        Returns:
            Dictionary with processing results:
            {
                "processed": 5,
                "failed": 1,
                "skipped": 2,
                "details": [...]
            }
        """
        results = {
            "processed": 0,
            "failed": 0,
            "skipped": 0,
            "details": []
        }
        
        try:
            mail = self.connect()
            mail.select(self.folder)
            
            # Search for emails matching criteria
            logger.info(f"Searching for emails: {self.search_criteria}")
            status, message_ids = mail.search(None, self.search_criteria)
            
            if status != 'OK':
                logger.error(f"Email search failed: {status}")
                return results
            
            # Get list of message IDs
            msg_ids = message_ids[0].split()
            logger.info(f"Found {len(msg_ids)} emails to process")
            
            # Process each email
            for msg_id in msg_ids:
                result = self._process_single_email(mail, msg_id)
                
                if result['status'] == 'success':
                    results['processed'] += 1
                elif result['status'] == 'skipped':
                    results['skipped'] += 1
                else:
                    results['failed'] += 1
                
                results['details'].append(result)
            
            mail.close()
            mail.logout()
            
            logger.info(
                f"Email processing complete: "
                f"{results['processed']} processed, "
                f"{results['failed']} failed, "
                f"{results['skipped']} skipped"
            )
            
        except Exception as e:
            logger.error(f"Error processing emails: {e}")
            results['error'] = str(e)
        
        return results
    
    def _process_single_email(self, mail: imaplib.IMAP4_SSL, msg_id: bytes) -> Dict[str, Any]:
        """
        Process a single email.
        
        Args:
            mail: IMAP connection
            msg_id: Email message ID
            
        Returns:
            Dictionary with processing result
        """
        result = {
            "msg_id": msg_id.decode(),
            "status": "failed",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        try:
            # Fetch email
            status, msg_data = mail.fetch(msg_id, '(RFC822)')
            if status != 'OK':
                result['error'] = f"Failed to fetch email: {status}"
                return result
            
            # Parse email
            email_message = email.message_from_bytes(msg_data[0][1])
            
            # Extract metadata
            subject = self._decode_header(email_message.get('Subject', ''))
            from_addr = self._decode_header(email_message.get('From', ''))
            
            result['subject'] = subject
            result['from'] = from_addr
            
            # Extract email content
            content = self._extract_email_content(email_message)
            
            if not content or len(content.strip()) < 50:
                result['status'] = 'skipped'
                result['error'] = 'Email content too short or empty'
                logger.warning(f"Skipping email {msg_id}: content too short")
                return result
            
            # Parse with AI
            logger.info(f"Parsing email {msg_id}: {subject}")
            commission_data = self.parser.parse_commission_email(
                email_content=content,
                email_subject=subject,
                email_source=from_addr
            )
            
            # Validate
            validation = self.parser.validate_extraction(commission_data)
            result['validation'] = validation
            
            # Save to database
            commission = self.repository.save_commission(commission_data)
            
            result['status'] = 'success'
            result['commission_id'] = commission.id
            result['transaction_id'] = commission.transaction_id
            
            logger.info(
                f"Successfully processed email {msg_id}: "
                f"Transaction {commission.transaction_id}"
            )
            
        except ValueError as e:
            # Validation or duplicate error
            result['error'] = str(e)
            result['status'] = 'skipped' if 'already exists' in str(e) else 'failed'
            logger.warning(f"Validation error for email {msg_id}: {e}")
            
        except Exception as e:
            result['error'] = str(e)
            logger.error(f"Error processing email {msg_id}: {e}")
        
        return result
    
    def _extract_email_content(self, email_message: email.message.Message) -> str:
        """
        Extract text content from email message.
        
        Handles both plain text and HTML emails, extracting the most
        relevant content for parsing.
        
        Args:
            email_message: Email message object
            
        Returns:
            Extracted text content
        """
        content = ""
        
        if email_message.is_multipart():
            # Handle multipart emails
            for part in email_message.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition", ""))
                
                # Skip attachments
                if "attachment" in content_disposition:
                    continue
                
                # Get text content
                if content_type == "text/plain":
                    try:
                        payload = part.get_payload(decode=True)
                        if payload:
                            content += payload.decode('utf-8', errors='ignore')
                    except Exception as e:
                        logger.warning(f"Error decoding email part: {e}")
                
                elif content_type == "text/html" and not content:
                    # Use HTML as fallback if no plain text
                    try:
                        payload = part.get_payload(decode=True)
                        if payload:
                            html_content = payload.decode('utf-8', errors='ignore')
                            # Basic HTML stripping (for better parsing, use BeautifulSoup)
                            content += self._strip_html(html_content)
                    except Exception as e:
                        logger.warning(f"Error decoding HTML part: {e}")
        else:
            # Handle simple emails
            try:
                payload = email_message.get_payload(decode=True)
                if payload:
                    content = payload.decode('utf-8', errors='ignore')
            except Exception as e:
                logger.warning(f"Error decoding email: {e}")
        
        return content.strip()
    
    def _strip_html(self, html: str) -> str:
        """
        Basic HTML tag stripping.
        
        For production, consider using BeautifulSoup for better HTML parsing.
        """
        import re
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', ' ', html)
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def _decode_header(self, header: str) -> str:
        """
        Decode email header (handles encoded subjects/addresses).
        
        Args:
            header: Raw header string
            
        Returns:
            Decoded header string
        """
        if not header:
            return ""
        
        decoded_parts = decode_header(header)
        decoded_str = ""
        
        for part, encoding in decoded_parts:
            if isinstance(part, bytes):
                decoded_str += part.decode(encoding or 'utf-8', errors='ignore')
            else:
                decoded_str += part
        
        return decoded_str.strip()

