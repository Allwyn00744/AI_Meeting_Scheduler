from sqlalchemy.orm import Session
from app.core.config import settings

from app.models.google_credential import GoogleCredential
from app.repositories.google_credential_repository import GoogleCredentialRepository
from fastapi import HTTPException, status

from app.calendar.google_calendar import GoogleCalendarAPI

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from datetime import timezone

import logging

logger = logging.getLogger(__name__)


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
    def update_google_calendar_event(
        db: Session,
        meeting,
    ):
        credential = (
            GoogleCredentialRepository.get_by_user_id(
                db,
                meeting.owner_id,
            )
        )
        if credential is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Google account not connected.",
            )

        credential = GoogleCalendarService.refresh_google_token(
            db,
            credential,
        )

        if credential is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Google account not connected.",
            )

        if not meeting.google_event_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Google event not found.",
            )

        event = GoogleCalendarAPI.update_calendar_event(
            credential=credential,
            event_id=meeting.google_event_id,
            title=meeting.title,
            description=meeting.description or "",
            start_time=meeting.start_time,
            end_time=meeting.end_time,
            location=meeting.location,
        )
       
        logger.info(
            "Google Calendar event updated. meeting_id=%s event_id=%s",
            meeting.id,
            meeting.google_event_id,
        )
        return event
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

        credential = GoogleCalendarService.refresh_google_token(
            db,
            credential,
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
        logger.info(
            "Google Calendar event created. user_id=%s event_id=%s",
            user_id,
            event.get("id"),
        )

        return event
    @staticmethod
    def delete_google_calendar_event(
        db: Session,
        meeting,
    ):
        credential = (
            GoogleCredentialRepository.get_by_user_id(
                db,
                meeting.owner_id,
            )
        )
        if credential is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Google account not connected.",
            )

        credential = GoogleCalendarService.refresh_google_token(
            db,
            credential,
        )

        if credential is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Google account not connected.",
            )

        if not meeting.google_event_id:
            return

        GoogleCalendarAPI.delete_calendar_event(
            credential=credential,
            event_id=meeting.google_event_id,
        )
        logger.info(
            "Google Calendar event deleted. meeting_id=%s event_id=%s",
            meeting.id,
            meeting.google_event_id,
        )

    @staticmethod
    def refresh_google_token(
        db: Session,
        credential: GoogleCredential,
    ):
        expiry = credential.expiry

        if expiry is not None and expiry.tzinfo is not None:
            expiry = (
                expiry
                .astimezone(timezone.utc)
                .replace(tzinfo=None)
            )

        credentials = Credentials(
            token=credential.access_token,
            refresh_token=credential.refresh_token,
            token_uri=credential.token_uri,
            client_id=settings.GOOGLE_CLIENT_ID,
            client_secret=settings.GOOGLE_CLIENT_SECRET,
            scopes=credential.scopes.split(","),
            expiry=expiry,
        )

        if credentials.expired and credentials.refresh_token:
            logger.info(
                "Refreshing expired Google OAuth token. user_id=%s",
                credential.user_id,
            )

            credentials.refresh(Request())

            credential.access_token = credentials.token
            credential.expiry = credentials.expiry.replace(
                tzinfo=timezone.utc
            )

            credential = GoogleCredentialRepository.update(
                db,
                credential,
            )

            logger.info(
                "Google OAuth token refreshed successfully. user_id=%s",
                credential.user_id,
            )

        return credential