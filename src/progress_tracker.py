"""
OpenPolicy Progress Tracking System
Comprehensive progress tracking with pause/skip functionality for scraping operations
"""

import json
import time
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, asdict
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    PAUSED = "paused"
    SKIPPED = "skipped"
    FAILED = "failed"
    CANCELLED = "cancelled"

class TaskType(Enum):
    DATABASE_INIT = "database_init"
    REGION_SCRAPE = "region_scrape"
    FEDERAL_SCRAPE = "federal_scrape"
    VALIDATION = "validation"
    CLEANUP = "cleanup"

@dataclass
class TaskProgress:
    """Individual task progress tracking"""
    task_id: str
    task_type: TaskType
    name: str
    status: TaskStatus
    progress: float  # 0.0 to 100.0
    current_step: str
    total_steps: int
    completed_steps: int
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    @property
    def duration(self) -> Optional[timedelta]:
        if self.start_time:
            end = self.end_time or datetime.now()
            return end - self.start_time
        return None
    
    @property
    def eta(self) -> Optional[datetime]:
        if self.start_time and self.progress > 0:
            elapsed = (datetime.now() - self.start_time).total_seconds()
            total_estimated = elapsed / (self.progress / 100)
            remaining = total_estimated - elapsed
            return datetime.now() + timedelta(seconds=remaining)
        return None

@dataclass
class RegionProgress:
    """Regional scraping progress"""
    region_code: str
    region_name: str
    status: TaskStatus
    progress: float
    tasks: List[TaskProgress]
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    can_skip: bool = True
    
    @property
    def duration(self) -> Optional[timedelta]:
        if self.start_time:
            end = self.end_time or datetime.now()
            return end - self.start_time
        return None

class ProgressTracker:
    """Central progress tracking system with persistence and control"""
    
    def __init__(self, progress_file: str = "storage/progress.json"):
        self.progress_file = Path(progress_file)
        self.progress_file.parent.mkdir(exist_ok=True)
        
        # Main progress state
        self.overall_progress: float = 0.0
        self.current_phase: str = "Initializing"
        self.start_time: Optional[datetime] = None
        self.is_paused: bool = False
        self.is_cancelled: bool = False
        
        # Task tracking
        self.tasks: Dict[str, TaskProgress] = {}
        self.regions: Dict[str, RegionProgress] = {}
        self.current_task: Optional[str] = None
        
        # Control flags
        self.pause_requested: bool = False
        self.skip_requested: Dict[str, bool] = {}  # task_id -> skip
        self.cancel_requested: bool = False
        
        # Callbacks
        self.progress_callbacks: List[Callable] = []
        self.status_callbacks: List[Callable] = []
        
        # Threading
        self._lock = threading.RLock()
        self._auto_save = True
        
        # Load existing progress
        self.load_progress()
        
        # Setup logging
        self._setup_logging()
    
    def _setup_logging(self):
        """Setup detailed logging for progress tracking"""
        log_file = self.progress_file.parent / "scraping.log"
        
        # Create file handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        
        # Create console handler  
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Add handlers to logger
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        logger.setLevel(logging.DEBUG)
    
    def start_operation(self, operation_name: str):
        """Start a new operation"""
        with self._lock:
            self.start_time = datetime.now()
            self.current_phase = operation_name
            self.overall_progress = 0.0
            self.is_paused = False
            self.is_cancelled = False
            
            logger.info(f"🚀 Starting operation: {operation_name}")
            self._notify_callbacks()
            self.save_progress()
    
    def add_task(self, task_id: str, task_type: TaskType, name: str, 
                 total_steps: int = 100, metadata: Dict[str, Any] = None) -> TaskProgress:
        """Add a new task to track"""
        with self._lock:
            task = TaskProgress(
                task_id=task_id,
                task_type=task_type,
                name=name,
                status=TaskStatus.PENDING,
                progress=0.0,
                current_step="Initializing",
                total_steps=total_steps,
                completed_steps=0,
                metadata=metadata or {}
            )
            self.tasks[task_id] = task
            
            logger.info(f"📋 Added task: {name} ({task_id})")
            self._notify_callbacks()
            return task
    
    def add_region(self, region_code: str, region_name: str, 
                   tasks: List[str] = None) -> RegionProgress:
        """Add a region to track"""
        with self._lock:
            region_tasks = []
            if tasks:
                region_tasks = [self.tasks[t] for t in tasks if t in self.tasks]
            
            region = RegionProgress(
                region_code=region_code,
                region_name=region_name,
                status=TaskStatus.PENDING,
                progress=0.0,
                tasks=region_tasks
            )
            self.regions[region_code] = region
            
            logger.info(f"🌍 Added region: {region_name} ({region_code})")
            self._notify_callbacks()
            return region
    
    def start_task(self, task_id: str, step_description: str = None):
        """Start a task"""
        with self._lock:
            if task_id not in self.tasks:
                raise ValueError(f"Task {task_id} not found")
            
            task = self.tasks[task_id]
            task.status = TaskStatus.RUNNING
            task.start_time = datetime.now()
            task.current_step = step_description or "Starting"
            self.current_task = task_id
            
            logger.info(f"▶️ Starting task: {task.name}")
            if step_description:
                logger.info(f"   Step: {step_description}")
            
            self._notify_callbacks()
            self.save_progress()
    
    def update_task_progress(self, task_id: str, progress: float, 
                           step_description: str = None, 
                           completed_steps: int = None):
        """Update task progress"""
        with self._lock:
            if task_id not in self.tasks:
                return
            
            task = self.tasks[task_id]
            task.progress = min(100.0, max(0.0, progress))
            
            if step_description:
                task.current_step = step_description
            
            if completed_steps is not None:
                task.completed_steps = completed_steps
            
            # Log significant progress milestones
            if int(progress) % 10 == 0 and progress != task.progress:
                logger.info(f"📊 {task.name}: {progress:.1f}%")
                if step_description:
                    logger.info(f"   Current: {step_description}")
            
            self._update_overall_progress()
            self._notify_callbacks()
            
            # Auto-save every 5%
            if int(progress) % 5 == 0:
                self.save_progress()
    
    def complete_task(self, task_id: str, success: bool = True, 
                     error_message: str = None):
        """Complete a task"""
        with self._lock:
            if task_id not in self.tasks:
                return
            
            task = self.tasks[task_id]
            task.end_time = datetime.now()
            task.progress = 100.0
            
            if success:
                task.status = TaskStatus.COMPLETED
                task.current_step = "Completed"
                logger.info(f"✅ Completed task: {task.name} in {task.duration}")
            else:
                task.status = TaskStatus.FAILED
                task.error_message = error_message
                task.current_step = f"Failed: {error_message}" if error_message else "Failed"
                logger.error(f"❌ Failed task: {task.name} - {error_message}")
            
            # Update region progress if applicable
            self._update_region_progress(task_id)
            self._update_overall_progress()
            self._notify_callbacks()
            self.save_progress()
    
    def pause_operation(self):
        """Pause the entire operation"""
        with self._lock:
            self.pause_requested = True
            self.is_paused = True
            logger.info("⏸️ Operation paused by user")
            self._notify_callbacks()
            self.save_progress()
    
    def resume_operation(self):
        """Resume the operation"""
        with self._lock:
            self.pause_requested = False
            self.is_paused = False
            logger.info("▶️ Operation resumed by user")
            self._notify_callbacks()
            self.save_progress()
    
    def skip_task(self, task_id: str):
        """Skip a specific task"""
        with self._lock:
            self.skip_requested[task_id] = True
            
            if task_id in self.tasks:
                task = self.tasks[task_id]
                task.status = TaskStatus.SKIPPED
                task.end_time = datetime.now()
                task.current_step = "Skipped by user"
                task.progress = 100.0
                
                logger.info(f"⏭️ Skipped task: {task.name}")
                self._update_region_progress(task_id)
                self._update_overall_progress()
                self._notify_callbacks()
                self.save_progress()
    
    def skip_region(self, region_code: str):
        """Skip an entire region"""
        with self._lock:
            if region_code in self.regions:
                region = self.regions[region_code]
                region.status = TaskStatus.SKIPPED
                region.end_time = datetime.now()
                
                # Skip all tasks in this region
                for task in region.tasks:
                    self.skip_task(task.task_id)
                
                logger.info(f"⏭️ Skipped region: {region.region_name}")
                self._notify_callbacks()
                self.save_progress()
    
    def cancel_operation(self):
        """Cancel the entire operation"""
        with self._lock:
            self.cancel_requested = True
            self.is_cancelled = True
            
            # Mark all running tasks as cancelled
            for task in self.tasks.values():
                if task.status == TaskStatus.RUNNING:
                    task.status = TaskStatus.CANCELLED
                    task.end_time = datetime.now()
                    task.current_step = "Cancelled by user"
            
            logger.info("🛑 Operation cancelled by user")
            self._notify_callbacks()
            self.save_progress()
    
    def should_pause(self) -> bool:
        """Check if operation should pause"""
        return self.pause_requested or self.is_paused
    
    def should_skip_task(self, task_id: str) -> bool:
        """Check if task should be skipped"""
        return self.skip_requested.get(task_id, False)
    
    def should_cancel(self) -> bool:
        """Check if operation should be cancelled"""
        return self.cancel_requested or self.is_cancelled
    
    def _update_region_progress(self, task_id: str):
        """Update region progress based on task completion"""
        with self._lock:
            for region in self.regions.values():
                region_task_ids = [t.task_id for t in region.tasks]
                if task_id in region_task_ids:
                    completed_tasks = sum(1 for t in region.tasks 
                                        if t.status in [TaskStatus.COMPLETED, TaskStatus.SKIPPED])
                    total_tasks = len(region.tasks)
                    
                    region.progress = (completed_tasks / total_tasks) * 100 if total_tasks > 0 else 0
                    
                    if completed_tasks == total_tasks:
                        region.status = TaskStatus.COMPLETED
                        region.end_time = datetime.now()
                        logger.info(f"🌍 Completed region: {region.region_name}")
    
    def _update_overall_progress(self):
        """Update overall progress based on all tasks"""
        with self._lock:
            if not self.tasks:
                self.overall_progress = 0.0
                return
            
            total_progress = sum(task.progress for task in self.tasks.values())
            self.overall_progress = total_progress / len(self.tasks)
    
    def get_progress_summary(self) -> Dict[str, Any]:
        """Get comprehensive progress summary"""
        with self._lock:
            completed_tasks = sum(1 for t in self.tasks.values() 
                                if t.status in [TaskStatus.COMPLETED, TaskStatus.SKIPPED])
            failed_tasks = sum(1 for t in self.tasks.values() if t.status == TaskStatus.FAILED)
            running_tasks = sum(1 for t in self.tasks.values() if t.status == TaskStatus.RUNNING)
            
            eta = None
            if self.start_time and self.overall_progress > 0:
                elapsed = (datetime.now() - self.start_time).total_seconds()
                total_estimated = elapsed / (self.overall_progress / 100)
                remaining = total_estimated - elapsed
                eta = datetime.now() + timedelta(seconds=remaining)
            
            return {
                'overall_progress': self.overall_progress,
                'current_phase': self.current_phase,
                'is_paused': self.is_paused,
                'is_cancelled': self.is_cancelled,
                'start_time': self.start_time.isoformat() if self.start_time else None,
                'duration': str(datetime.now() - self.start_time) if self.start_time else None,
                'eta': eta.isoformat() if eta else None,
                'tasks': {
                    'total': len(self.tasks),
                    'completed': completed_tasks,
                    'failed': failed_tasks,
                    'running': running_tasks,
                    'pending': len(self.tasks) - completed_tasks - failed_tasks - running_tasks
                },
                'regions': {
                    'total': len(self.regions),
                    'completed': sum(1 for r in self.regions.values() 
                                   if r.status == TaskStatus.COMPLETED),
                    'running': sum(1 for r in self.regions.values() 
                                 if r.status == TaskStatus.RUNNING),
                    'pending': sum(1 for r in self.regions.values() 
                                 if r.status == TaskStatus.PENDING)
                },
                'current_task': self.tasks[self.current_task].name if self.current_task else None
            }
    
    def get_detailed_status(self) -> Dict[str, Any]:
        """Get detailed status of all tasks and regions"""
        with self._lock:
            return {
                'summary': self.get_progress_summary(),
                'tasks': {task_id: asdict(task) for task_id, task in self.tasks.items()},
                'regions': {region_code: asdict(region) for region_code, region in self.regions.items()}
            }
    
    def add_progress_callback(self, callback: Callable):
        """Add a callback to be called on progress updates"""
        self.progress_callbacks.append(callback)
    
    def add_status_callback(self, callback: Callable):
        """Add a callback to be called on status changes"""
        self.status_callbacks.append(callback)
    
    def _notify_callbacks(self):
        """Notify all registered callbacks"""
        try:
            summary = self.get_progress_summary()
            for callback in self.progress_callbacks:
                try:
                    callback(summary)
                except Exception as e:
                    logger.error(f"Error in progress callback: {e}")
            
            for callback in self.status_callbacks:
                try:
                    callback(self.get_detailed_status())
                except Exception as e:
                    logger.error(f"Error in status callback: {e}")
        except Exception as e:
            logger.error(f"Error notifying callbacks: {e}")
    
    def save_progress(self):
        """Save progress to file"""
        if not self._auto_save:
            return
        
        try:
            data = {
                'overall_progress': self.overall_progress,
                'current_phase': self.current_phase,
                'start_time': self.start_time.isoformat() if self.start_time else None,
                'is_paused': self.is_paused,
                'is_cancelled': self.is_cancelled,
                'tasks': {task_id: asdict(task) for task_id, task in self.tasks.items()},
                'regions': {region_code: asdict(region) for region_code, region in self.regions.items()},
                'current_task': self.current_task,
                'skip_requested': self.skip_requested,
                'saved_at': datetime.now().isoformat()
            }
            
            # Convert datetime objects to strings for JSON serialization
            def serialize_datetime(obj):
                if isinstance(obj, datetime):
                    return obj.isoformat()
                return obj
            
            with open(self.progress_file, 'w') as f:
                json.dump(data, f, indent=2, default=serialize_datetime)
                
        except Exception as e:
            logger.error(f"Error saving progress: {e}")
    
    def load_progress(self):
        """Load progress from file"""
        if not self.progress_file.exists():
            return
        
        try:
            with open(self.progress_file, 'r') as f:
                data = json.load(f)
            
            self.overall_progress = data.get('overall_progress', 0.0)
            self.current_phase = data.get('current_phase', 'Initializing')
            self.is_paused = data.get('is_paused', False)
            self.is_cancelled = data.get('is_cancelled', False)
            self.current_task = data.get('current_task')
            self.skip_requested = data.get('skip_requested', {})
            
            if data.get('start_time'):
                self.start_time = datetime.fromisoformat(data['start_time'])
            
            # Reconstruct tasks
            for task_id, task_data in data.get('tasks', {}).items():
                # Convert datetime strings back to datetime objects
                if task_data.get('start_time'):
                    task_data['start_time'] = datetime.fromisoformat(task_data['start_time'])
                if task_data.get('end_time'):
                    task_data['end_time'] = datetime.fromisoformat(task_data['end_time'])
                
                # Convert enum strings back to enums
                task_data['task_type'] = TaskType(task_data['task_type'])
                task_data['status'] = TaskStatus(task_data['status'])
                
                self.tasks[task_id] = TaskProgress(**task_data)
            
            # Reconstruct regions
            for region_code, region_data in data.get('regions', {}).items():
                if region_data.get('start_time'):
                    region_data['start_time'] = datetime.fromisoformat(region_data['start_time'])
                if region_data.get('end_time'):
                    region_data['end_time'] = datetime.fromisoformat(region_data['end_time'])
                
                region_data['status'] = TaskStatus(region_data['status'])
                
                # Reconstruct task references
                region_data['tasks'] = [self.tasks[t['task_id']] for t in region_data['tasks'] 
                                      if t['task_id'] in self.tasks]
                
                self.regions[region_code] = RegionProgress(**region_data)
            
            logger.info(f"📂 Loaded progress from {self.progress_file}")
            
        except Exception as e:
            logger.error(f"Error loading progress: {e}")

# Global progress tracker instance
progress_tracker = ProgressTracker()