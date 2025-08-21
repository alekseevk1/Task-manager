from sqlalchemy.orm import Session
from sqlalchemy import select, func
from uuid import UUID
from typing import List, Optional
from . import models, schemas


def get_task(db: Session, task_id: UUID) -> Optional[models.Task]:
    return db.execute(
        select(models.Task).where(models.Task.id == task_id)
    ).scalar_one_or_none()


def get_tasks(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    status: Optional[schemas.TaskStatus] = None
) -> List[models.Task]:
    query = select(models.Task)
    
    if status:
        query = query.where(models.Task.status == status)
    
    query = query.offset(skip).limit(limit)
    
    result = db.execute(query)
    return result.scalars().all()


def create_task(db: Session, task: schemas.TaskCreate) -> models.Task:
    db_task = models.Task(
        title=task.title,
        description=task.description,
        status=task.status
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task


def update_task(
    db: Session, 
    task_id: UUID, 
    task_update: schemas.TaskUpdate
) -> Optional[models.Task]:
    db_task = get_task(db, task_id)
    if not db_task:
        return None
    
    update_data = task_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_task, field, value)
    
    db.commit()
    db.refresh(db_task)
    return db_task


def delete_task(db: Session, task_id: UUID) -> bool:
    db_task = get_task(db, task_id)
    if not db_task:
        return False
    
    db.delete(db_task)
    db.commit()
    return True


def get_tasks_count(db: Session, status: Optional[schemas.TaskStatus] = None) -> int:
    query = select(func.count()).select_from(models.Task)
    
    if status:
        query = query.where(models.Task.status == status)
    
    return db.execute(query).scalar()


def search_tasks(db: Session, search_term: str, limit: int = 50) -> List[models.Task]:
    query = select(models.Task).where(
        (models.Task.title.like(f"%{search_term}%")) |
        (models.Task.description.like(f"%{search_term}%"))
    ).limit(limit)
    
    result = db.execute(query)
    return result.scalars().all()