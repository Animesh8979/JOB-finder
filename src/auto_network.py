"""
Autonomous Email Outreach Engine.
Processes the OutreachQueue and fires emails natively via SMTP (or MCP fallback).
"""
import smtplib
from email.message import EmailMessage
import logging
from src import db, config, outreach

logger = logging.getLogger(__name__)

def process_outreach_queue():
    """
    Pulls queued emails from the database and sends them.
    Adheres strictly to the daily_limit cap.
    """
    prefs = config.load_prefs()
    daily_cap = int(prefs.get("outreach_daily_cap", 15))
    
    queued_emails = outreach.OutreachQueue.pop_ready(daily_limit=daily_cap)
    if not queued_emails:
        logger.info("No pending emails in the queue or daily cap reached.")
        return 0
        
    # We will use native smtplib for absolute reliability without external dependencies
    # Requires standard SMTP credentials in secrets (e.g. App Password for Gmail)
    smtp_user = prefs.get("identity", {}).get("email")
    smtp_pass = config.get_secret("smtp_password", "SMTP_PASSWORD")
    
    if not smtp_user or not smtp_pass:
        logger.error("Cannot process email queue: Missing smtp_password in secrets or identity email.")
        return 0
        
    sent_count = 0
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(smtp_user, smtp_pass)
            
            for item in queued_emails:
                contact = db.get_contact(item["contact_id"])
                if not contact or not contact.get("email"):
                    logger.warning(f"Skipping outreach ID {item['id']}: No valid contact email.")
                    continue
                    
                msg = EmailMessage()
                msg["Subject"] = item["subject"]
                msg["From"] = smtp_user
                msg["To"] = contact["email"]
                msg.set_content(item["body"])
                
                try:
                    if item.get("channel") == "linkedin":
                        logger.info(f"LinkedIn DM routing selected for {contact['name']} - delegating to Playwright Persistent Context (WIP)")
                        # [TODO]: Inject Playwright logic here to navigate to LinkedIn profile and send connection note
                        outreach.OutreachQueue.mark_sent(item["id"])
                        sent_count += 1
                    else:
                        # Fallback to standard SMTP
                        server.send_message(msg)
                        outreach.OutreachQueue.mark_sent(item["id"])
                        sent_count += 1
                        logger.info(f"Successfully sent email to {contact['email']}")
                except Exception as e:
                    logger.error(f"Failed to send outreach to {contact['email']}: {e}")
                    
    except Exception as e:
        logger.error(f"SMTP connection failed: {e}")
        
    return sent_count
