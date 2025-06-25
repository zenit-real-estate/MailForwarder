from datetime import datetime, timedelta
from dotenv import load_dotenv
from email import message_from_bytes
from email.header import decode_header
from email.message import EmailMessage
from email.utils import parsedate_to_datetime
from imapclient import IMAPClient
from MiogestObject import MiogestObject
import db
import email
import miogest
import os
import smtplib
import re
import time
import ssl
import signal
import sys
import threading
from logger import logger

# Load environment variables
load_dotenv()

# Configuration
IMAP_SERVER = 'imap.gmail.com'
SMTP_SERVER = 'smtp.gmail.com'
EMAIL_ADDRESS = 'info@zenitrealestate.com'
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
SMTP_PORT = 465

# Create SSL context
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

# Global flag for graceful shutdown
shutdown_requested = False
shutdown_event = threading.Event()
shutdown_start_time = None
SHUTDOWN_TIMEOUT = 10  # Force exit after 10 seconds

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    global shutdown_requested, shutdown_start_time
    if not shutdown_requested:
        shutdown_start_time = time.time()
        logger.log_warning(f"Received signal {signum}, initiating graceful shutdown")
        shutdown_requested = True
        shutdown_event.set()
    else:
        # Second Ctrl+C - force immediate exit
        logger.log_warning("Force shutdown requested - exiting immediately")
        sys.exit(1)

# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

objects = db.load_objects()
logger.log_startup()

def update_requests_count(miogest_code):
    global objects, shutdown_requested
    
    # Don't perform expensive operations during shutdown
    if shutdown_requested:
        logger.log_warning(f"Skipping database update for {miogest_code} - shutdown in progress")
        return
    
    if miogest_code in objects:
        old_count = objects[miogest_code].requests_count
        objects[miogest_code].requests_count += 1
        new_count = objects[miogest_code].requests_count
        logger.log_database_update(miogest_code, old_count, new_count)
        logger.main_logger.info(f"Updated requests for {miogest_code}: {new_count}")
    else:
        logger.log_warning(f"Miogest code {miogest_code} not found in database, attempting to fetch from Miogest")
        # Skip expensive Miogest lookup during shutdown
        if not shutdown_requested:
            obj = miogest.find_miogest_object(miogest_code)
            if obj != None:
                objects[miogest_code] = obj
                db.save_request_counts(objects)
                logger.log_database_update(miogest_code, 0, 1)
                logger.main_logger.info(f"Added new object {miogest_code} to database")
            else:
                logger.log_error(f"Failed to find Miogest object for code {miogest_code}", "update_requests_count")
        else:
            logger.log_warning(f"Skipping Miogest lookup for {miogest_code} - shutdown in progress")


def extract_miogest_code(subject):
    """
    Extract the announcement code from the email subject.
    :param subject: The subject line of the email.
    :return: The extracted code or None if not found.
    """
    # Regular expression to match the code
    code_pattern = r"\b[A|V]\d{6}\b"
    match = re.search(code_pattern, subject)
    return match.group(0) if match else None


def classify_source(server, source, email_id):
    try:
        if source.startswith('SMG'):
            server.add_gmail_labels(email_id, ['Annunci Homegate.ch'])
            logger.log_source_classified(email_id, source, 'Annunci Homegate.ch')
            logger.main_logger.info('Homegate')
        elif source.startswith('idealista'):
            server.add_gmail_labels(email_id, ['Annunci Idealista'])
            logger.log_source_classified(email_id, source, 'Annunci Idealista')
            logger.main_logger.info('Idealista')
        elif source.endswith('Immobiliare.it') or source.startswith('Utente da Immobiliare.it'):
            server.add_gmail_labels(email_id, ['Annunci Immobiliare.it'])
            logger.log_source_classified(email_id, source, 'Annunci Immobiliare.it')
            logger.main_logger.info('Immobiliare.it')
        elif 'newhome' in source:
            server.add_gmail_labels(email_id, ['Annunci NewHome'])
            logger.log_source_classified(email_id, source, 'Annunci NewHome')
            logger.main_logger.info('NewHome')
        elif 'deliver@geoticino.ch' in source:
            server.add_gmail_labels(email_id, ['GeoTicino'])
            logger.log_source_classified(email_id, source, 'GeoTicino')
            logger.main_logger.info('GeoTicino')
        else:
            logger.log_warning(f"Unknown email source: {source}", "classify_source")
            
        logger.main_logger.info("Email classified successfully")
    except Exception as e:
        logger.log_error(f"Failed to classify email source: {e}", "classify_source")


def decode_email_subject(encoded_subject):
    try:
        decoded_parts = decode_header(encoded_subject)
        decoded_subject = "".join(
            part.decode(encoding or "utf-8") if isinstance(part, bytes) else part
            for part, encoding in decoded_parts
        )
        return decoded_subject
    except Exception as e:
        logger.log_error(f"Failed to decode email subject: {e}", "decode_email_subject")
        return encoded_subject


def mark_read_email_as_to_read(server, email_id):
    """
    Marks an email as DA LEGGERE by adding the 'A. DA LEGGERE' label.
    :param server: IMAPClient connection object.
    :param email_id: The unique ID of the email to mark to read.
    """
    try:
        server.add_gmail_labels(email_id, ['A. DA LEGGERE'])
        logger.main_logger.info(f"Email with ID {email_id} marked as to read.")
    except Exception as e:
        logger.log_error(f"Failed to mark email as to read: {e}", "mark_read_email_as_to_read")


def forward_raw_email(raw_email, recipients, cc=None):
    """
    Forward an email as-is without modifying its content.
    :param raw_email: The raw MIME content of the email.
    :param recipients: The recipients to whom the email should be forwarded.
    """
    start_time = time.time()
    all_recipients = recipients
    if cc != None:
        all_recipients = recipients + [cc]
        
    try:
        with smtplib.SMTP_SSL(SMTP_SERVER, 465) as server:
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            logger.main_logger.info("Successfully logged in to the email server.")
            server.sendmail(from_addr=EMAIL_ADDRESS, msg=raw_email, to_addrs=all_recipients)
            
            duration = int((time.time() - start_time) * 1000)
            logger.log_performance("email_forward", duration)
            logger.log_email_forwarded("N/A", all_recipients, success=True)
            logger.main_logger.info(f"Email successfully forwarded to {all_recipients}.")
    except Exception as e:
        duration = int((time.time() - start_time) * 1000)
        logger.log_performance("email_forward_failed", duration)
        logger.log_email_forwarded("N/A", all_recipients, success=False)
        logger.log_error(f"Failed to forward email: {e}", "forward_raw_email")


def process_email(raw_message, msg_id, imap_server):
    """
    Process the incoming email and forward it.
    :param raw_message: The raw email message.
    """
    global shutdown_requested
    
    # Skip processing if shutdown is requested
    if shutdown_requested:
        logger.log_warning(f"Skipping email processing - shutdown in progress")
        return
        
    start_time = time.time()
    
    try:
        msg = message_from_bytes(raw_message)

        # Extract details
        subject = msg["subject"]
        sender = msg["from"]
        body = msg.get("body", "No body")

        logger.log_email_received(msg_id, sender, subject)
        logger.main_logger.info(f'Sender: {sender}')
        logger.main_logger.info(f'Subject: {subject}')
        logger.main_logger.info(f'Body: {body}')
        
        email_date = parsedate_to_datetime(msg["Date"])
        logger.main_logger.info(f'Date: {email_date}')

        # 1. preprocess email subject if coming from newhome to convert it to a human readable string
        if sender.startswith('"newhome"'):
            subject = decode_email_subject(subject)
            logger.main_logger.info(f"Decoded subject: {subject}")
        
        # 2. extract miogest code from the email subject
        miogest_code = extract_miogest_code(subject)

        # 3. If a code is a found, we proceed to process it otherwise print it's not found and mark the email "to read"
        if miogest_code:
            logger.log_miogest_code_extracted(msg_id, miogest_code)
            logger.main_logger.info(f'Miogest Code {miogest_code} found in the object of the email!')

            # 4. Identify the sender
            classify_source(imap_server, sender, msg_id)
            
            # 5. Update the request count for the miogest code
            update_requests_count(miogest_code)

            # 6. Get all the recipients for the email
            recipients = miogest.get_agent_emails_from_list(objects[miogest_code].sellers)
            logger.main_logger.info(f'Recipients: {recipients}')

            if recipients == None:
                logger.log_warning(f"No recipient found for miogest_code {miogest_code}", "process_email")
            elif isinstance(recipients, list):
                forward_raw_email(raw_message, recipients)
                # logger.log_warning(f"Not forwarded but it could {miogest_code}", "process_email")
            else:
                forward_raw_email(raw_message, recipients[0], recipients[1])
                # logger.log_warning(f"Not forwarded but it could {miogest_code}", "process_email")
                
            logger.log_email_processed(msg_id, miogest_code, recipients)
        else:
            logger.log_miogest_code_not_found(msg_id, subject)
            logger.main_logger.info('Miogest Code not Found')
            mark_read_email_as_to_read(imap_server, msg_id)
            
        duration = int((time.time() - start_time) * 1000)
        logger.log_performance("email_processing", duration)
        
    except Exception as e:
        duration = int((time.time() - start_time) * 1000)
        logger.log_performance("email_processing_failed", duration)
        logger.log_error(f"Error processing email: {e}", "process_email")


def monitor_inbox():
    """
    Monitor the inbox for new emails using IMAP IDLE.
    """
    global shutdown_requested, shutdown_start_time
    
    while not shutdown_requested:
        try:
            logger.log_connection_attempt("IMAP", IMAP_SERVER)
            with IMAPClient(IMAP_SERVER, ssl_context=ssl_context) as server:
                # Login to the IMAP server
                server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
                server.select_folder('INBOX')
                logger.log_connection_success("IMAP", IMAP_SERVER)
                logger.main_logger.info("Monitoring inbox for new emails...")

                while not shutdown_requested:
                    # Check shutdown timeout
                    if shutdown_start_time and (time.time() - shutdown_start_time) > SHUTDOWN_TIMEOUT:
                        logger.log_warning(f"Shutdown timeout reached ({SHUTDOWN_TIMEOUT}s), forcing exit")
                        return
                        
                    # Wait for new emails
                    try:
                        # IMAP IDLE to listen for new emails
                        server.idle()
                        logger.log_idle_mode(True)
                        
                        # Use a shorter timeout and check shutdown flag
                        timeout = 10  # 10 seconds instead of 30
                        start_time = time.time()
                        
                        while not shutdown_requested and (time.time() - start_time) < timeout:
                            # Check shutdown timeout
                            if shutdown_start_time and (time.time() - shutdown_start_time) > SHUTDOWN_TIMEOUT:
                                logger.log_warning(f"Shutdown timeout reached ({SHUTDOWN_TIMEOUT}s), forcing exit")
                                return
                                
                            try:
                                server.idle_check(timeout=2)  # Check every 2 seconds
                                break  # If we get here, there was activity
                            except Exception as e:
                                if shutdown_requested:
                                    break
                                # Continue waiting
                                pass
                        
                        server.idle_done()
                        logger.log_idle_mode(False)

                        # Check if we should shutdown
                        if shutdown_requested:
                            logger.main_logger.info("Shutdown requested, stopping email monitoring")
                            return

                        # Fetch new emails
                        messages = server.search(['UNSEEN'])
                        if messages:
                            logger.main_logger.info(f"Found {len(messages)} new unread emails")
                            
                        for msg_id in messages:
                            if shutdown_requested:
                                return
                            try:
                                # Fetch the raw email message
                                raw_message = server.fetch(msg_id, ['RFC822'])[msg_id][b'RFC822']
                                process_email(raw_message, msg_id, server)
                                logger.main_logger.info("\n")
                            except Exception as e:
                                logger.log_error(f"Error processing email with ID {msg_id}: {e}", "monitor_inbox")
                                continue  # Continue to the next email
                                
                    except Exception as e:
                        if shutdown_requested:
                            return
                        logger.log_error(f"Error in IDLE mode: {e}", "monitor_inbox")
                        time.sleep(2)  # Wait and retry on error
                        
        except Exception as e:
            if shutdown_requested:
                return
            logger.log_connection_failure("IMAP", IMAP_SERVER, str(e))
            logger.main_logger.info("Waiting 5 seconds before retrying connection...")
            time.sleep(5)  # Wait before retrying connection


def graceful_shutdown(reason="Normal shutdown"):
    """Perform graceful shutdown operations."""
    global shutdown_start_time
    
    logger.log_warning("Starting graceful shutdown process")
    
    # Save any pending database changes
    try:
        db.save_request_counts(objects)
        logger.main_logger.info("Database changes saved during shutdown")
    except Exception as e:
        logger.log_error(f"Failed to save database during shutdown: {e}", "graceful_shutdown")
    
    # Cleanup old logs
    try:
        logger.cleanup_old_logs(30)
        logger.main_logger.info("Old logs cleaned up during shutdown")
    except Exception as e:
        logger.log_error(f"Failed to cleanup logs during shutdown: {e}", "graceful_shutdown")
    
    # Log shutdown
    logger.log_shutdown(reason)
    
    # Flush all log handlers to ensure logs are written
    for handler in logger.main_logger.handlers:
        handler.flush()
    for handler in logger.error_logger.handlers:
        handler.flush()
    for handler in logger.activity_logger.handlers:
        handler.flush()


if __name__ == "__main__":
    try:
        logger.main_logger.info("Starting MailForwarder application...")
        logger.main_logger.info("Press Ctrl+C to stop the application gracefully")
        logger.main_logger.info("Press Ctrl+C twice for immediate exit")
        monitor_inbox()
    except KeyboardInterrupt:
        logger.main_logger.info("Keyboard interrupt received")
        graceful_shutdown("Keyboard interrupt")
    except Exception as e:
        logger.log_error(f"Unexpected error: {e}", "main")
        graceful_shutdown("Unexpected error")
    finally:
        logger.main_logger.info("Application terminated")
        # Force exit to ensure we don't hang
        sys.exit(0)