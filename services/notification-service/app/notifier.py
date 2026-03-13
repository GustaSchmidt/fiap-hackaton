import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.config import settings

logger = logging.getLogger(__name__)


def send_email_notification(to_email: str, subject: str, body: str) -> bool:
    """Send an email notification to a user."""
    try:
        msg = MIMEMultipart()
        msg["From"] = settings.SMTP_FROM
        msg["To"] = to_email
        msg["Subject"] = subject

        html_body = f"""
        <html>
        <body style="font-family: 'Segoe UI', sans-serif; background-color: #0f172a; color: #f8fafc; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; background-color: #1e293b; border-radius: 10px; padding: 30px;">
                <h2 style="color: #ed145b;">FIAP X - Notification</h2>
                <p>{body}</p>
                <hr style="border-color: #475569;">
                <p style="color: #94a3b8; font-size: 12px;">
                    This is an automated message from the FIAP X system.
                </p>
            </div>
        </body>
        </html>
        """
        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.send_message(msg)

        logger.info(f"Email notification sent to {to_email}")
        return True

    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {e}")
        return False


def send_error_notification(to_email: str, video_name: str, error_message: str) -> bool:
    """Send a video processing error notification."""
    subject = f"FIAP X - Video processing error: {video_name}"
    body = f"""
    <p>Hello,</p>
    <p>An error occurred while processing your video:</p>
    <ul>
        <li><strong>File:</strong> {video_name}</li>
        <li><strong>Error:</strong> {error_message}</li>
    </ul>
    <p>Please try uploading the video again. If the problem persists,
    contact support.</p>
    """
    return send_email_notification(to_email, subject, body)
