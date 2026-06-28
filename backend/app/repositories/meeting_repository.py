from sqlalchemy.orm import Session

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