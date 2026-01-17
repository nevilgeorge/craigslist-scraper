"""
Email notifications via Resend.

Setup:
1. Sign up at https://resend.com
2. Get your API key from the dashboard
3. Set environment variables:
   - RESEND_API_KEY: Your Resend API key
   - NOTIFY_EMAIL: The email address to send notifications to
"""

import os

import requests


class EmailNotifier:
    """Send email notifications via Resend."""

    RESEND_URL = "https://api.resend.com/emails"

    def __init__(self, api_key=None, to_email=None):
        """
        Initialize the email notifier.

        Args:
            api_key: Resend API key. Falls back to RESEND_API_KEY env var.
            to_email: Email address to send notifications to.
                      Falls back to NOTIFY_EMAIL env var.
        """
        self.api_key = api_key or os.environ.get("RESEND_API_KEY")
        self.to_email = to_email or os.environ.get("NOTIFY_EMAIL")

        if not self.api_key or not self.to_email:
            raise ValueError(
                "Email notifications require RESEND_API_KEY and NOTIFY_EMAIL "
                "environment variables. See notifier.py for setup instructions."
            )

    def send(self, subject, body):
        """
        Send an email.

        Args:
            subject: Email subject line.
            body: Email body (plain text).

        Returns:
            True if successful, False otherwise.
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        data = {
            "from": "Craigslist Scraper <onboarding@resend.dev>",
            "to": [self.to_email],
            "subject": subject,
            "text": body,
        }

        try:
            response = requests.post(self.RESEND_URL, headers=headers, json=data, timeout=30)
            if response.status_code == 200:
                return True
            else:
                print(f"Email notification failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"Email notification error: {e}")
            return False

    def notify_matches(self, matches):
        """
        Send a summary notification for all matching listings.

        Args:
            matches: List of dicts with 'product_name' and 'listing' keys.

        Returns:
            True if successful, False otherwise.
        """
        if not matches:
            return True

        count = len(matches)
        subject = f"Craigslist Camera search -- {count} match{'es' if count > 1 else ''} found"

        body_parts = [f"Found {count} matching listing{'s' if count > 1 else ''}!\n"]

        for i, match in enumerate(matches, 1):
            product_name = match["product_name"]
            listing = match["listing"]
            title = listing.get("title", "N/A")
            price = listing.get("price", "N/A")
            url = listing.get("url", "N/A")
            confidence = listing.get("evaluation", {}).get("confidence", "N/A")
            reason = listing.get("evaluation", {}).get("reason", "N/A")

            body_parts.append(f"""
---
Match {i}: {product_name}

Title: {title}
Price: {price}
Confidence: {confidence}
Reason: {reason}

View listing: {url}
""")

        return self.send(subject, "\n".join(body_parts))
