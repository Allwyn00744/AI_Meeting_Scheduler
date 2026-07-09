from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.resource import Resource
from app.models.user import User
from app.repositories.resource_repository import ResourceRepository
from app.schemas.resource import ResourceCreate, ResourceUpdate


class ResourceService:

    @staticmethod
    def create_resource(
        db: Session,
        resource: ResourceCreate,
        current_user: User,
    ):
        db_resource = Resource(
            name=resource.name,
            resource_type=resource.resource_type,
            description=resource.description,
            location=resource.location,
            created_by_id=current_user.id,
        )

        return ResourceRepository.create(db, db_resource)

    @staticmethod
    def list_active_resources(db: Session):
        return ResourceRepository.get_active(db)

    @staticmethod
    def get_resource(
        db: Session,
        resource_id: int,
    ):
        resource = ResourceRepository.get_by_id(db, resource_id)

        if resource is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resource not found",
            )

        return resource

    @staticmethod
    def update_resource(
        db: Session,
        resource_id: int,
        resource_data: ResourceUpdate,
        current_user: User,
    ):
        resource = ResourceRepository.get_by_id(db, resource_id)

        if resource is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resource not found",
            )

        if resource.created_by_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the resource creator can update this resource.",
            )

        update_data = resource_data.model_dump(exclude_unset=True)

        for key, value in update_data.items():
            setattr(resource, key, value)

        return ResourceRepository.update(db, resource)
