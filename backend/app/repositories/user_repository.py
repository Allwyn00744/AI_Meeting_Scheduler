from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate


class UserRepository:

    @staticmethod
    def create_user(db: Session, user: UserCreate):
        new_user = User(
            name=user.name,
            email=user.email
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        return new_user

    @staticmethod
    def get_all_users(db: Session):
        return db.query(User).all()

    @staticmethod
    def get_user_by_id(db: Session, user_id: int):
        return db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def get_user_by_email(db: Session, email: str):
        return db.query(User).filter(User.email == email).first()

    @staticmethod
    def update_user(db: Session, user_id: int, user: UserUpdate):

        existing_user = db.query(User).filter(User.id == user_id).first()

        if not existing_user:
            return None

        if user.name is not None:
            existing_user.name = user.name

        if user.email is not None:
            existing_user.email = user.email

        db.commit()
        db.refresh(existing_user)

        return existing_user

    @staticmethod
    def delete_user(db: Session, user_id: int):

        existing_user = db.query(User).filter(User.id == user_id).first()

        if not existing_user:
            return None

        db.delete(existing_user)
        db.commit()

        return existing_user