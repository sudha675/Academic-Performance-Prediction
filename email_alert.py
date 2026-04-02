import smtplib
from email.mime.text import MIMEText
import os
import logging

logger = logging.getLogger(__name__)

def send_email(to_email: str, subject: str, message: str) -> bool:
    """Send email alert"""
    sender = os.getenv("SENDER_EMAIL", "sudharaju6143@gmail.com")
    password = os.getenv("EMAIL_PASSWORD", "oqjdslcxveqyilwz")
    
    try:
        msg = MIMEText(message)
        msg["Subject"] = subject
        msg["From"] = sender
        msg["To"] = to_email
        
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender, password)
        server.sendmail(sender, to_email, msg.as_string())
        server.quit()
        
        logger.info(f"📧 Email sent to {to_email}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Email failed for {to_email}: {str(e)}")
        return False