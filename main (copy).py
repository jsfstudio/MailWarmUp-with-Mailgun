'''import requests
import os
import time
import threading
import logging
from flask import Flask, jsonify

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Constants (these should be loaded from Replit Secrets)
MAILGUN_API_KEY = os.environ['MAILGUN_API_KEY']
SENDING_DOMAIN = 'mail.fundingfinder.world'
RECEIVING_DOMAIN = 'fundingfinder.info'
FORWARD_EMAIL = 'connect@jsfstudio.co'
SENDER_NAME = 'Funding Finder'

def send_email():
    try:
        logger.info(f"Attempting to send email from {SENDING_DOMAIN} to inbox@{RECEIVING_DOMAIN}")
        response = requests.post(
            f"https://api.mailgun.net/v3/{SENDING_DOMAIN}/messages",
            auth=("api", MAILGUN_API_KEY),
            data={"from": f"{SENDER_NAME} <mailgun@{SENDING_DOMAIN}>",
                  "to": [f"inbox@{RECEIVING_DOMAIN}"],
                  "subject": "Automated Email from Flask App - FF-WARMUP - V2",
                  "text": "This is an automated test email sent via Mailgun!"})
        response.raise_for_status()
        logger.info(f"Email sent successfully! Response: {response.text}")
        # Log the Message-ID for tracking
        message_id = response.json().get('id', 'Unknown')
        logger.info(f"Message-ID: {message_id}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to send email. Error: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            logger.error(f"Response content: {e.response.text}")

def check_domain_status(domain):
    try:
        response = requests.get(
            f"https://api.mailgun.net/v3/domains/{domain}",
            auth=("api", MAILGUN_API_KEY))
        response.raise_for_status()
        logger.info(f"Domain {domain} status: {response.json()}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to check domain status for {domain}. Error: {str(e)}")

def email_scheduler():
    check_domain_status(SENDING_DOMAIN)
    check_domain_status(RECEIVING_DOMAIN)
    send_email()  # Send first email immediately
    while True:
        time.sleep(1800)  # Wait for 30 minutes (1800 seconds)
        send_email()

@app.route('/')
def home():
    return "Email sending app is running. Emails are being sent automatically."

@app.route('/status')
def status():
    return jsonify({"status": "running", "message": "Emails are being sent every 30 minutes"}), 200

if __name__ == '__main__':
    # Start the email scheduler in a separate thread
    email_thread = threading.Thread(target=email_scheduler)
    email_thread.daemon = True
    email_thread.start()

    # Run the Flask app
    app.run(host='0.0.0.0', port=8080)

    '''