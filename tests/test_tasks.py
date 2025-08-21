import pytest
from uuid import UUID, uuid4
from fastapi.testclient import TestClient
from fastapi import status

from app import schemas


def test_create_task(test_client: TestClient):
    task_data = {
        "title": "Test Task",
        "description": "Test Description",
        "status": schemas.TaskStatus.CREATED
    }
    
    response = test_client.post("/tasks/", json=task_data)
    assert response.status_code == status.HTTP_201_CREATED
    
    data = response.json()
    assert data["success"] is True
    assert data["data"]["title"] == task_data["title"]
    assert data["data"]["description"] == task_data["description"]
    assert data["data"]["status"] == task_data["status"]
    assert UUID(data["data"]["id"])  # Should be valid UUID


def test_search_tasks(test_client: TestClient):
    # Create test tasks
    tasks_data = [
        {"title": "Important task", "description": "Very important"},
        {"title": "Another task", "description": "Not important"},
    ]
    
    for task_data in tasks_data:
        test_client.post("/tasks/", json=task_data)
    
    # Search for "important"
    response = test_client.get("/tasks/search/?q=important")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["success"] is True
    assert data["count"] >= 1
    assert any("important" in task["title"].lower() or "important" in (task["description"] or "").lower() 
               for task in data["data"])


def test_get_stats(test_client: TestClient):
    # Create test tasks with different statuses
    tasks_data = [
        {"title": "Task 1", "status": schemas.TaskStatus.CREATED},
        {"title": "Task 2", "status": schemas.TaskStatus.IN_PROGRESS},
        {"title": "Task 3", "status": schemas.TaskStatus.COMPLETED},
    ]
    
    for task_data in tasks_data:
        test_client.post("/tasks/", json=task_data)
    
    response = test_client.get("/stats")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["success"] is True
    assert data["data"]["total"] == 3
    assert data["data"]["by_status"]["created"] == 1
    assert data["data"]["by_status"]["in_progress"] == 1
    assert data["data"]["by_status"]["completed"] == 1