import requests
import os
import time
import threading
import logging
import random
import hashlib
from flask import Flask, jsonify
from datetime import datetime, timedelta

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Function to safely get environment variables
def get_env_variable(var_name):
    value = os.environ.get(var_name)
    if value is None:
        logger.error(f"Environment variable {var_name} is not set!")
        raise ValueError(f"Missing required environment variable: {var_name}")
    return value

# Constants
MAILGUN_API_KEY = get_env_variable('MAILGUN_API_KEY')
DOMAINS = ['mail.fundingfinder.world', 'fundingfinder.info']
FORWARD_EMAIL = 'connect@jsfstudio.co'
SENDER_NAME = 'Funding Finder'

# Track email sends for each domain
email_counts = {domain: 0 for domain in DOMAINS}

# Email bodies and subject lines
EMAIL_CONTENT = [
    {
        "subject": "Quick question about the project EMAIL-READINESS",
        "body": "Hey, I was wondering if you had a moment to discuss the latest project updates. Can we schedule a quick call?"
    },
    {
        "subject": "RE: Project timeline EMAIL-READINESS",
        "body": "Thanks for your last email. I've reviewed the timeline and I think we might need to adjust a few deadlines. Let's discuss this in our next meeting."
    },
    {
        "subject": "New feature idea EMAIL-READINESS",
        "body": "I just had a brainstorm about a potential new feature for our app. It's a bit out there, but I think it could really set us apart from the competition. Let me know if you want me to flesh it out more and we can discuss it."
    },
    {
        "subject": "Weekly report EMAIL-READINESS",
        "body": "Here's a quick summary of this week's progress:\n\n1. Completed the user authentication module\n2. Started work on the dashboard redesign\n3. Fixed 3 critical bugs in the backend\n\nLet me know if you need any more details!"
    }
]

def generate_hash():
    return hashlib.md5(str(time.time()).encode()).hexdigest()[:5]

def send_email(sender_domain, receiver_domain, is_start_email=False, pair_number=None):
    try:
        email_hash = generate_hash()
        if is_start_email:
            subject = f"{pair_number} Pair {sender_domain[-1]}: System Start Notification EMAIL-READINESS"
            body = f"This email confirms that the email warmup system has started successfully.\n\n" \
                   f"Sending Domain: {sender_domain}\n" \
                   f"Receiving Domain: {receiver_domain}\n" \
                   f"Unique Hash: {email_hash}"
        else:
            email_content = random.choice(EMAIL_CONTENT)
            subject = email_content["subject"]
            body = f"{email_content['body']}\n\n" \
                   f"Sending Domain: {sender_domain}\n" \
                   f"Receiving Domain: {receiver_domain}\n" \
                   f"Unique Hash: {email_hash}"

        logger.info(f"Attempting to send email from {sender_domain} to inbox@{receiver_domain}")
        response = requests.post(
            f"https://api.mailgun.net/v3/{sender_domain}/messages",
            auth=("api", MAILGUN_API_KEY),
            data={"from": f"{SENDER_NAME} <mailgun@{sender_domain}>",
                  "to": [f"inbox@{receiver_domain}"],
                  "subject": subject,
                  "text": body})
        response.raise_for_status()
        logger.info(f"Email sent successfully! Response: {response.text}")
        # Log the Message-ID for tracking
        message_id = response.json().get('id', 'Unknown')
        logger.info(f"Message-ID: {message_id}, Hash: {email_hash}")
        # Update email count for sender domain
        email_counts[sender_domain] += 1
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to send email. Error: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            logger.error(f"Response content: {e.response.text}")

def get_random_domains():
    sender = random.choice(DOMAINS)
    receiver = random.choice([d for d in DOMAINS if d != sender])
    return sender, receiver

def email_scheduler():
    # Send start emails
    for i in range(0, len(DOMAINS), 2):
        if i+1 < len(DOMAINS):
            send_email(DOMAINS[i], DOMAINS[i+1], is_start_email=True, pair_number="1/2")
            send_email(DOMAINS[i+1], DOMAINS[i], is_start_email=True, pair_number="2/2")

    while True:
        # Calculate next send time (random, but at least 5 minutes from now)
        next_send = datetime.now() + timedelta(minutes=random.randint(5, 15))
        logger.info(f"Next email scheduled for: {next_send}")

        # Sleep until next send time
        time.sleep((next_send - datetime.now()).total_seconds())

        # Choose domains with priority for those with fewer sends
        sender = min(email_counts, key=email_counts.get)
        receiver = random.choice([d for d in DOMAINS if d != sender])

        # Send email
        send_email(sender, receiver)

@app.route('/')
def home():
    return "Email sending app is running. Emails are being sent automatically."

@app.route('/status')
def status():
    return jsonify({
        "status": "running",
        "message": "Emails are being sent at random intervals",
        "email_counts": email_counts,
        "configured_domains": DOMAINS
    }), 200

if __name__ == '__main__':
    # Start the email scheduler in a separate thread
    email_thread = threading.Thread(target=email_scheduler)
    email_thread.daemon = True
    email_thread.start()

    # Run the Flask app
    app.run(host='0.0.0.0', port=8080)