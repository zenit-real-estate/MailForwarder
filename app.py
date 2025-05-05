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

# Configuration
IMAP_SERVER = 'imap.gmail.com'
SMTP_SERVER = 'smtp.gmail.com'
EMAIL_ADDRESS = 'info@zenitrealestate.com'
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
SMTP_PORT = 465

objects = db.load_objects()


def update_requests_count(miogest_code):
    global objects
    
    if miogest_code in objects:
        objects[miogest_code].requests_count += 1
        print(f"Updated requests for {miogest_code}: {objects[miogest_code].requests_count}")
    else:
        obj = miogest.find_miogest_object(miogest_code)
        if obj != None:
            objects[miogest_code] = obj
            db.save_request_counts(objects)


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
    if source.startswith('SMG'):
        server.add_gmail_labels(email_id, ['Annunci Homegate.ch'])
        print('Homegate')
    elif source.startswith('idealista'):
        server.add_gmail_labels(email_id, ['Annunci Idealista'])
        print('Idealista')
    elif source.endswith('Immobiliare.it') or source.startswith('Utente da Immobiliare.it'):
        server.add_gmail_labels(email_id, ['Annunci Immobiliare.it'])
        print('Immobiliare.it')
    elif 'newhome' in source:
        server.add_gmail_labels(email_id, ['Annunci NewHome'])
        print('NewHome')
    elif 'deliver@geoticino.ch' in source:
        server.add_gmail_labels(email_id, ['GeoTicino'])
        print('GeoTicino')
    print("Email classified successfully")


def decode_email_subject(encoded_subject):
    decoded_parts = decode_header(encoded_subject)
    decoded_subject = "".join(
        part.decode(encoding or "utf-8") if isinstance(part, bytes) else part
        for part, encoding in decoded_parts
    )
    return decoded_subject


def mark_read_email_as_to_read(server, email_id):
    """
    Marks an email as DA LEGGERE by adding the 'A. DA LEGGERE' label.
    :param server: IMAPClient connection object.
    :param email_id: The unique ID of the email to mark to read.
    """
    try:
        server.add_gmail_labels(email_id, ['A. DA LEGGERE'])
        print(f"Email with ID {email_id} marked as to read.")
    except Exception as e:
        print(f"Failed to mark email as to read: {e}")


def forward_raw_email(raw_email, recipients, cc=None):
    """
    Forward an email as-is without modifying its content.
    :param raw_email: The raw MIME content of the email.
    :param recipient: The recipient to whom the email should be forwarded.
    """
    all_recipients = recipients
    if cc!=None:
        all_recipients = recipients + [cc]
    try:
        with smtplib.SMTP_SSL(SMTP_SERVER, 465) as server:
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            print("Successfully logged in to the email.")
            server.sendmail(from_addr=EMAIL_ADDRESS, msg=raw_email, to_addrs=all_recipients)
            print(f"Email successfully forwarded to {all_recipients}.")
    except Exception as e:
        print(f"Failed to forward email: {e}")


def process_email(raw_message, msg_id, imap_server):
    """
    Process the incoming email and forward it.
    :param raw_message: The raw email message.
    """
    try:
        msg = message_from_bytes(raw_message)

        # Extract details
        subject = msg["subject"]
        sender = msg["from"]
        body = msg["body"]

        print(f'Sender: {sender}')
        print(f'Subject: {subject}')
        print(f'Body: {body}')
        email_date = parsedate_to_datetime(msg["Date"])
        print(f'Date: {email_date}')

        # 1. preprocess email subject if coming from newhome to convert it to a human readable string
        if sender.startswith('"newhome"'):
            subject = decode_email_subject(subject)
            print(subject)
        
        # 2. extract miogest code from the email subject
        miogest_code = extract_miogest_code(subject)

        # 3. If a code is a found, we proceed to process it otherwise print it's not found and mark the email "to read"
        if miogest_code:
            print(f'Miogest Code {miogest_code} found in the object of the email!')

            # 4. Identify the sender
            classify_source(imap_server, sender, msg_id)
            
            # 5. Update the request count for the miogest code
            update_requests_count(miogest_code)

            # 6. Get all the recipients for the email
            recipients = miogest.get_agent_emails_from_list(objects[miogest_code].sellers)
            print(f'Recipients: {recipients}')

            if recipients == None:
                print("No recipient found for miogest_code")
            elif isinstance(recipients, list):
                forward_raw_email(raw_message, recipients)
                # print(f"Imagine forwarding to {recipients}")
            else:
                forward_raw_email(raw_message, recipients[0], recipients[1])
                # print(f"Imagine forwarding to {recipients}")
        else:
            print('Miogest Code not Found')
            mark_read_email_as_to_read(imap_server, msg_id)
    except Exception as e:
        print(f"Error processing email: {e}")

def monitor_inbox():
    """
    Monitor the inbox for new emails using IMAP IDLE.
    """
    with IMAPClient(IMAP_SERVER) as server:
        # Login to the IMAP server
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.select_folder('INBOX')

        print("Monitoring inbox for new emails...")

        while True:
            # Wait for new emails
            try:
                # IMAP IDLE to listen for new emails
                server.idle()
                print("IDLE mode enabled. Waiting for new emails...")
                server.idle_check(timeout=10)  # Check for new emails every 60 seconds
                server.idle_done()

                # Fetch new emails
                messages = server.search(['UNSEEN'])
                for msg_id in messages:
                    try:
                        # Fetch the raw email message
                        raw_message = server.fetch(msg_id, ['RFC822'])[msg_id][b'RFC822']
                        process_email(raw_message, msg_id, server)
                        print("\n")
                    except Exception as e:
                        print(f"Error processing email with ID {msg_id}: {e}")
                        continue  # Continue to the next email
                break
            except Exception as e:
                print(f"Error: {e}")
                time.sleep(5)  # Wait and retry on error

if __name__ == "__main__":
    monitor_inbox()
