from fastapi import APIRouter

from app.services.email_service import EmailService

router = APIRouter(
    prefix="/email",
    tags=["Email"],
)


@router.post("/test")
def send_test_email():

    EmailService.send_email(
        to_email="f92080377@gmail.com",
        subject="AI Meeting Scheduler",
        body="Congratulations! Your email service is working.",
    )

    return {
        "message": "Email sent successfully"
    }