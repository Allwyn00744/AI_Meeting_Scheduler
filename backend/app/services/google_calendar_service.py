from sqlalchemy.orm import Session

from app.models.google_credential import GoogleCredential
from app.repositories.google_credential_repository import GoogleCredentialRepository
from fastapi import HTTPException, status

from app.calendar.google_calendar import GoogleCalendarAPI


class GoogleCalendarService:

    @staticmethod
    def save_google_credentials(
        db: Session,
        user_id: int,
        credentials,
    ):
        existing = GoogleCredentialRepository.get_by_user_id(
            db,
            user_id,
        )

        if existing:
            existing.access_token = credentials.token
            existing.refresh_token = credentials.refresh_token
            existing.token_uri = credentials.token_uri
            existing.scopes = ",".join(credentials.scopes)
            existing.expiry = credentials.expiry

            return GoogleCredentialRepository.update(
                db,
                existing,
            )

        credential = GoogleCredential(
            user_id=user_id,
            access_token=credentials.token,
            refresh_token=credentials.refresh_token,
            token_uri=credentials.token_uri,
            scopes=",".join(credentials.scopes),
            expiry=credentials.expiry,
        )

        return GoogleCredentialRepository.create(
            db,
            credential,
        )
    @staticmethod
    def create_google_calendar_event(
        db: Session,
        user_id: int,
        title: str,
        description: str,
        start_time,
        end_time,
        location: str | None = None,
    ):
        credential = (
            GoogleCredentialRepository.get_by_user_id(
                db,
                user_id,
            )
        )

        if credential is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Google account not connected.",
            )

        event = GoogleCalendarAPI.create_calendar_event(
            credential=credential,
            title=title,
            description=description,
            start_time=start_time,
            end_time=end_time,
            location=location,
        )

        return event