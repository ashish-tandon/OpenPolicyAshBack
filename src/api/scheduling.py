"""
Scheduling endpoints for the OpenPolicy Database API
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
import uuid
from datetime import datetime

from database import get_session_factory, get_database_config, create_engine_from_config
from scheduler.tasks import (
    run_test_scrapers, run_federal_scrapers, 
    run_provincial_scrapers, run_municipal_scrapers
)

# Database setup
config = get_database_config()
engine = create_engine_from_config(config.get_url())
Session_factory = get_session_factory(engine)

def get_db():
    """Database dependency"""
    db = Session_factory()
    try:
        yield db
    finally:
        db.close()

router = APIRouter()

# Pydantic models
class ScheduleTaskRequest(BaseModel):
    task_type: str  # 'test', 'federal', 'provincial', 'municipal'

class ScheduleTaskResponse(BaseModel):
    task_id: str
    message: str

class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    result: dict = None
    error: str = None

class ScrapingRunResponse(BaseModel):
    id: str
    task_id: str
    jurisdiction_types: List[str]
    status: str
    records_created: int
    records_updated: int
    errors_count: int
    started_at: datetime = None
    completed_at: datetime = None
    error_message: str = None

@router.post("/schedule", response_model=ScheduleTaskResponse)
async def schedule_task(request: ScheduleTaskRequest):
    """Schedule a scraping task"""
    try:
        task_id = str(uuid.uuid4())
        
        # Map task types to functions
        task_map = {
            'test': run_test_scrapers,
            'federal': run_federal_scrapers,
            'provincial': run_provincial_scrapers,
            'municipal': run_municipal_scrapers
        }
        
        if request.task_type not in task_map:
            raise HTTPException(status_code=400, detail="Invalid task type")
        
        # Start the task asynchronously
        task_function = task_map[request.task_type]
        result = task_function.delay()
        
        return ScheduleTaskResponse(
            task_id=result.id,
            message=f"Task {request.task_type} scheduled successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to schedule task: {str(e)}")

@router.get("/tasks/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """Get the status of a specific task"""
    try:
        from celery.result import AsyncResult
        from scheduler.tasks import celery_app
        
        result = AsyncResult(task_id, app=celery_app)
        
        response = TaskStatusResponse(
            task_id=task_id,
            status=result.status,
        )
        
        if result.ready():
            if result.successful():
                response.result = result.result
            else:
                response.error = str(result.info)
        
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get task status: {str(e)}")

@router.delete("/tasks/{task_id}")
async def cancel_task(task_id: str):
    """Cancel a running task"""
    try:
        from celery.result import AsyncResult
        from scheduler.tasks import celery_app
        
        result = AsyncResult(task_id, app=celery_app)
        result.revoke(terminate=True)
        
        return {"success": True, "message": "Task cancelled successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cancel task: {str(e)}")

@router.get("/scraping-runs", response_model=List[ScrapingRunResponse])
async def get_scraping_runs(limit: int = 20, db: Session = Depends(get_db)):
    """Get recent scraping runs"""
    try:
        # This would typically query a scraping_runs table
        # For now, return mock data
        mock_runs = [
            ScrapingRunResponse(
                id=str(uuid.uuid4()),
                task_id=str(uuid.uuid4()),
                jurisdiction_types=["federal"],
                status="completed",
                records_created=150,
                records_updated=45,
                errors_count=2,
                started_at=datetime.now(),
                completed_at=datetime.now()
            ),
            ScrapingRunResponse(
                id=str(uuid.uuid4()),
                task_id=str(uuid.uuid4()),
                jurisdiction_types=["provincial"],
                status="running",
                records_created=89,
                records_updated=23,
                errors_count=0,
                started_at=datetime.now()
            )
        ]
        
        return mock_runs[:limit]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get scraping runs: {str(e)}")