from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.schemas.user import UserCreate, UserUpdate
from app.repositories.user_repository import UserRepository


class UserService:

    @staticmethod
    def create_user(db: Session, user: UserCreate):

        existing_user = UserRepository.get_user_by_email(db, user.email)

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already exists."
            )

        return UserRepository.create_user(db, user)

    @staticmethod
    def get_all_users(db: Session):

        return UserRepository.get_all_users(db)

    @staticmethod
    def get_user_by_id(db: Session, user_id: int):

        user = UserRepository.get_user_by_id(db, user_id)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found."
            )

        return user

    @staticmethod
    def update_user(db: Session, user_id: int, user: UserUpdate):

        existing_user = UserRepository.get_user_by_id(db, user_id)

        if not existing_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found."
            )

        if user.email:

            email_exists = UserRepository.get_user_by_email(db, user.email)

            if email_exists and email_exists.id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already exists."
                )

        return UserRepository.update_user(db, user_id, user)

    @staticmethod
    def delete_user(db: Session, user_id: int):

        user = UserRepository.get_user_by_id(db, user_id)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found."
            )

        return UserRepository.delete_user(db, user_id)