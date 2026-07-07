import smtplib
from email.message import EmailMessage

from app.core.config import settings


class EmailService:

    @staticmethod
    def send_email(
        to_email: str,
        subject: str,
        body: str,
    ):
        """
        Send an email using Gmail SMTP.
        """

        message = EmailMessage()

        message["Subject"] = subject
        message["From"] = settings.EMAIL_FROM
        message["To"] = to_email

        message.set_content(body)

        with smtplib.SMTP(
            settings.EMAIL_HOST,
            settings.EMAIL_PORT,
        ) as smtp:

            smtp.starttls()

            smtp.login(
                settings.EMAIL_USERNAME,
                settings.EMAIL_PASSWORD,
            )

            smtp.send_message(message)
    @staticmethod
    def send_meeting_invitation(
        to_email: str,
        meeting_title: str,
        start_time,
        end_time,
        location: str,
    ):
        body = f"""
    You have been invited to a meeting.

    Title: {meeting_title}

    Start: {start_time}

    End: {end_time}

    Location: {location}

    Please join on time.

    Regards,
    AI Meeting Scheduler
    """

        EmailService.send_email(
            to_email=to_email,
            subject=f"Meeting Invitation: {meeting_title}",
            body=body,
        )