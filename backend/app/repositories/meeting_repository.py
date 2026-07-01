from sqlalchemy.orm import Session
from sqlalchemy import or_,func
from datetime import date


from app.models.meeting import Meeting


class MeetingRepository:

    @staticmethod
    def create(db: Session, meeting: Meeting):
        db.add(meeting)
        db.commit()
        db.refresh(meeting)
        return meeting

    @staticmethod
    def get_all(db: Session, owner_id: int):
        return (
            db.query(Meeting)
            .filter(Meeting.owner_id == owner_id)
            .all()
        )

    @staticmethod
    def get_by_id(db: Session, meeting_id: int):
        return (
            db.query(Meeting)
            .filter(Meeting.id == meeting_id)
            .first()
        )

    @staticmethod
    def update(db: Session, meeting: Meeting):
        db.commit()
        db.refresh(meeting)
        return meeting

    @staticmethod
    def delete(db: Session, meeting: Meeting):
        db.delete(meeting)
        db.commit()

    @staticmethod
    def get_user_meetings(
        db: Session,
        owner_id: int,
    ):
        return (
            db.query(Meeting)
            .filter(Meeting.owner_id == owner_id)
            .all()
        )
    
    @staticmethod
    def search_meetings(
        db: Session,
        owner_id: int,
        keyword: str,
    ):
        return (
            db.query(Meeting)
            .filter(
                Meeting.owner_id == owner_id,
                or_(
                    Meeting.title.ilike(f"%{keyword}%"),
                    Meeting.description.ilike(f"%{keyword}%"),
                ),
            )
            .all()
        )
    
    @staticmethod
    def filter_by_status(
        db: Session,
        owner_id: int,
        status: str,
    ):
        return (
            db.query(Meeting)
            .filter(
                Meeting.owner_id == owner_id,
                Meeting.status == status,
            )
            .all()
        )
    
    @staticmethod
    def filter_by_date(
        db: Session,
        owner_id: int,
        meeting_date: date,
    ):
        return (
            db.query(Meeting)
            .filter(
                Meeting.owner_id == owner_id,
                func.date(Meeting.start_time) == meeting_date,
            )
            .all()
        )
    
    @staticmethod
    def filter_by_date_range(
        db: Session,
        owner_id: int,
        start_date: date,
        end_date: date,
    ):
        return (
            db.query(Meeting)
            .filter(
                Meeting.owner_id == owner_id,
                func.date(Meeting.start_time) >= start_date,
                func.date(Meeting.start_time) <= end_date,
            )
            .all()
        )
    