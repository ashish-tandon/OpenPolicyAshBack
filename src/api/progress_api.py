"""
Progress Tracking API Endpoints
RESTful API for monitoring and controlling scraping operations
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from typing import Dict, Any
import json
import asyncio
from datetime import datetime

from ..progress_tracker import progress_tracker, TaskStatus, TaskType

router = APIRouter(prefix="/api/progress", tags=["progress"])

@router.get("/status")
async def get_progress_status():
    """Get comprehensive progress status"""
    try:
        return progress_tracker.get_detailed_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/summary")
async def get_progress_summary():
    """Get progress summary only"""
    try:
        return progress_tracker.get_progress_summary()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/pause")
async def pause_operation():
    """Pause the current operation"""
    try:
        progress_tracker.pause_operation()
        return {"message": "Operation paused", "status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/resume")
async def resume_operation():
    """Resume the paused operation"""
    try:
        progress_tracker.resume_operation()
        return {"message": "Operation resumed", "status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/cancel")
async def cancel_operation():
    """Cancel the entire operation"""
    try:
        progress_tracker.cancel_operation()
        return {"message": "Operation cancelled", "status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/skip-task/{task_id}")
async def skip_task(task_id: str):
    """Skip a specific task"""
    try:
        if task_id not in progress_tracker.tasks:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
        
        progress_tracker.skip_task(task_id)
        return {"message": f"Task {task_id} skipped", "status": "success"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/skip-region/{region_code}")
async def skip_region(region_code: str):
    """Skip an entire region"""
    try:
        if region_code not in progress_tracker.regions:
            raise HTTPException(status_code=404, detail=f"Region {region_code} not found")
        
        progress_tracker.skip_region(region_code)
        return {"message": f"Region {region_code} skipped", "status": "success"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stream")
async def stream_progress():
    """Stream real-time progress updates using Server-Sent Events"""
    
    async def generate_progress_stream():
        """Generate real-time progress updates"""
        last_update = None
        
        while True:
            try:
                # Get current status
                current_status = progress_tracker.get_progress_summary()
                
                # Only send update if something changed
                if current_status != last_update:
                    data = json.dumps(current_status)
                    yield f"data: {data}\n\n"
                    last_update = current_status
                
                # Check if operation is complete or cancelled
                if (current_status.get('overall_progress', 0) >= 100 or 
                    current_status.get('is_cancelled', False)):
                    yield f"data: {json.dumps({'type': 'complete'})}\n\n"
                    break
                
                await asyncio.sleep(1)  # Update every second
                
            except Exception as e:
                error_data = json.dumps({'type': 'error', 'message': str(e)})
                yield f"data: {error_data}\n\n"
                break
    
    return StreamingResponse(
        generate_progress_stream(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream"
        }
    )

@router.get("/logs")
async def get_recent_logs(lines: int = 100):
    """Get recent log entries"""
    try:
        log_file = progress_tracker.progress_file.parent / "scraping.log"
        
        if not log_file.exists():
            return {"logs": [], "message": "No log file found"}
        
        with open(log_file, 'r') as f:
            all_lines = f.readlines()
            recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
        
        return {
            "logs": [line.strip() for line in recent_lines],
            "total_lines": len(all_lines),
            "showing": len(recent_lines)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/logs/stream")
async def stream_logs():
    """Stream real-time log updates"""
    
    async def generate_log_stream():
        """Generate real-time log updates"""
        log_file = progress_tracker.progress_file.parent / "scraping.log"
        
        if not log_file.exists():
            yield f"data: {json.dumps({'type': 'error', 'message': 'Log file not found'})}\n\n"
            return
        
        # Start from end of file
        with open(log_file, 'r') as f:
            f.seek(0, 2)  # Seek to end
            
            while True:
                try:
                    line = f.readline()
                    if line:
                        log_data = json.dumps({
                            'type': 'log',
                            'message': line.strip(),
                            'timestamp': datetime.now().isoformat()
                        })
                        yield f"data: {log_data}\n\n"
                    else:
                        await asyncio.sleep(0.5)  # Wait for new lines
                        
                except Exception as e:
                    error_data = json.dumps({'type': 'error', 'message': str(e)})
                    yield f"data: {error_data}\n\n"
                    break
    
    return StreamingResponse(
        generate_log_stream(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream"
        }
    )

@router.post("/start/{operation_name}")
async def start_operation(operation_name: str, background_tasks: BackgroundTasks):
    """Start a new operation"""
    try:
        progress_tracker.start_operation(operation_name)
        
        # Start the actual operation in background
        if operation_name == "database_initialization":
            background_tasks.add_task(run_database_initialization)
        elif operation_name == "full_scrape":
            background_tasks.add_task(run_full_scrape)
        elif operation_name == "federal_priority_scrape":
            background_tasks.add_task(run_federal_priority_scrape)
        else:
            raise HTTPException(status_code=400, detail=f"Unknown operation: {operation_name}")
        
        return {"message": f"Started operation: {operation_name}", "status": "success"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Background task functions
async def run_database_initialization():
    """Run database initialization with progress tracking"""
    from ..database.init_db import initialize_database_with_progress
    
    try:
        await initialize_database_with_progress(progress_tracker)
    except Exception as e:
        progress_tracker.complete_task("db_init", success=False, error_message=str(e))

async def run_full_scrape():
    """Run full scraping operation with progress tracking"""
    from ..scrapers.enhanced_scraper import run_full_scrape_with_progress
    
    try:
        await run_full_scrape_with_progress(progress_tracker)
    except Exception as e:
        if progress_tracker.current_task:
            progress_tracker.complete_task(progress_tracker.current_task, success=False, error_message=str(e))

async def run_federal_priority_scrape():
    """Run federal priority scraping with progress tracking"""
    from ..scrapers.federal_priority_scraper import run_federal_scrape_with_progress
    
    try:
        await run_federal_scrape_with_progress(progress_tracker)
    except Exception as e:
        if progress_tracker.current_task:
            progress_tracker.complete_task(progress_tracker.current_task, success=False, error_message=str(e))

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "tracker_active": progress_tracker is not None,
        "has_tasks": len(progress_tracker.tasks) > 0 if progress_tracker else False
    }