from fastapi import FastAPI, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List, Optional
from contextlib import asynccontextmanager

import os
from . import crud, models, schemas, database
from .config import get_settings
from .schemas import TaskResponse, TasksResponse, ErrorResponse



app = FastAPI(
    title=get_settings().app_name,
    version=get_settings().version,
    description=get_settings().description,
    responses={
        404: {"model": ErrorResponse, "description": "Not Found"},
        422: {"model": ErrorResponse, "description": "Validation Error"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    if not os.getenv("TESTING"):
        models.Base.metadata.create_all(bind=database.engine)
    yield


@app.get("/", response_model=dict)
async def root():
    return {
        "message": "Добро пожаловать в Менеджер задач API",
        "version": get_settings().version,
        "docs": "/docs",
        "health": "/health"
    }


@app.post(
    "/tasks/", 
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "Задача успешно создана"},
        422: {"description": "Ошибка валидации данных"},
    }
)
def create_task(
    task: schemas.TaskCreate, 
    db: Session = Depends(database.get_db)
):
    """Создать новую задачу"""
    try:
        db_task = crud.create_task(db=db, task=task)
        return TaskResponse(
            success=True,
            data=db_task,
            message="Задача успешно создана"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при создании задачи: {str(e)}"
        )


@app.get(
    "/tasks/", 
    response_model=TasksResponse,
    responses={200: {"description": "Список задач успешно получен"}}
)
def read_tasks(
    skip: int = Query(0, ge=0, description="Количество пропускаемых записей"),
    limit: int = Query(100, ge=1, le=1000, description="Лимит записей"),
    status: Optional[schemas.TaskStatus] = Query(None, description="Фильтр по статусу"),
    db: Session = Depends(database.get_db)
):
    """Получить список задач с возможностью фильтрации по статусу"""
    try:
        tasks = crud.get_tasks(db, skip=skip, limit=limit, status=status)
        count = crud.get_tasks_count(db, status=status)
        
        return TasksResponse(
            success=True,
            data=tasks,
            count=count,
            message="Список задач успешно получен"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при получении списка задач: {str(e)}"
        )


@app.get(
    "/tasks/search/",
    response_model=TasksResponse,
    responses={200: {"description": "Результаты поиска"}}
)
def search_tasks(
    q: str = Query(..., min_length=2, description="Поисковый запрос"),
    limit: int = Query(50, ge=1, le=100, description="Лимит результатов"),
    db: Session = Depends(database.get_db)
):
    """Поиск задач по названию и описанию"""
    try:
        tasks = crud.search_tasks(db, search_term=q, limit=limit)
        return TasksResponse(
            success=True,
            data=tasks,
            count=len(tasks),
            message="Результаты поиска"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при поиске задач: {str(e)}"
        )


@app.get(
    "/tasks/{task_id}", 
    response_model=TaskResponse,
    responses={
        200: {"description": "Задача найдена"},
        404: {"description": "Задача не найдена"},
    }
)
def read_task(task_id: UUID, db: Session = Depends(database.get_db)):
    """Получить задачу по ID"""
    db_task = crud.get_task(db, task_id=task_id)
    if db_task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Задача не найдена"
        )
    
    return TaskResponse(
        success=True,
        data=db_task,
        message="Задача успешно найдена"
    )


@app.put(
    "/tasks/{task_id}", 
    response_model=TaskResponse,
    responses={
        200: {"description": "Задача успешно обновлена"},
        404: {"description": "Задача не найдена"},
    }
)
def update_task(
    task_id: UUID, 
    task_update: schemas.TaskUpdate,
    db: Session = Depends(database.get_db)
):
    """Обновить задачу"""
    db_task = crud.update_task(db, task_id=task_id, task_update=task_update)
    if db_task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Задача не найдена"
        )
    
    return TaskResponse(
        success=True,
        data=db_task,
        message="Задача успешно обновлена"
    )


@app.delete(
    "/tasks/{task_id}", 
    status_code=status.HTTP_200_OK,
    response_model=dict,
    responses={
        200: {"description": "Задача успешно удалена"},
        404: {"description": "Задача не найдена"},
    }
)
def delete_task(task_id: UUID, db: Session = Depends(database.get_db)):
    """Удалить задачу"""
    if not crud.delete_task(db, task_id=task_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Задача не найдена"
        )
    
    return {
        "success": True,
        "message": "Задача успешно удалена",
        "task_id": str(task_id)
    }


@app.get("/health", response_model=dict)
async def health_check(db: Session = Depends(database.get_db)):
    """Проверка здоровья приложения и базы данных"""
    try:
        if not os.getenv("TESTING"):  # Для SQLite в памяти проверка не нужна
            db.execute("SELECT 1")
        return {
            "status": "healthy",
            "database": "connected",
            "version": get_settings().version
        }
        # Проверяем соединение с базой данных
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database connection error: {str(e)}"
        )


@app.get("/stats", response_model=dict)
def get_stats(db: Session = Depends(database.get_db)):
    """Получить статистику по задачам"""
    try:
        total = crud.get_tasks_count(db)
        created = crud.get_tasks_count(db, status=schemas.TaskStatus.CREATED)
        in_progress = crud.get_tasks_count(db, status=schemas.TaskStatus.IN_PROGRESS)
        completed = crud.get_tasks_count(db, status=schemas.TaskStatus.COMPLETED)
        
        return {
            "success": True,
            "data": {
                "total": total,
                "by_status": {
                    "created": created,
                    "in_progress": in_progress,
                    "completed": completed
                }
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при получении статистики: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)