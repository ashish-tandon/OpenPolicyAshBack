"""
Phased Loading System for OpenPolicy Database
Provides controlled, gradual data loading with manual UI controls
"""

import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
from enum import Enum
from dataclasses import dataclass, asdict
from pathlib import Path

from progress_tracker import progress_tracker, TaskType, TaskStatus
from database import get_session_factory, get_database_config, create_engine_from_config
from scrapers.manager import ScraperManager


class LoadingPhase(Enum):
    """Loading phases for gradual rollout"""
    PREPARATION = "preparation"
    FEDERAL_CORE = "federal_core"
    PROVINCIAL_TIER1 = "provincial_tier1"
    PROVINCIAL_TIER2 = "provincial_tier2"
    MUNICIPAL_MAJOR = "municipal_major"
    MUNICIPAL_MINOR = "municipal_minor"
    VALIDATION = "validation"
    COMPLETION = "completion"


class LoadingStrategy(Enum):
    """Loading strategies for different scenarios"""
    CONSERVATIVE = "conservative"  # Slow, safe loading
    BALANCED = "balanced"         # Normal loading speed
    AGGRESSIVE = "aggressive"     # Fast loading


@dataclass
class PhaseConfig:
    """Configuration for a loading phase"""
    name: str
    description: str
    jurisdictions: List[str]
    estimated_duration: int  # minutes
    max_concurrent_tasks: int
    retry_attempts: int
    cooldown_period: int  # seconds between batches
    dependencies: List[str]  # Previous phases required
    validation_checks: List[str]


@dataclass
class LoadingSession:
    """Represents a loading session"""
    session_id: str
    strategy: LoadingStrategy
    current_phase: LoadingPhase
    started_at: datetime
    phases_completed: List[str]
    total_estimated_duration: int
    user_id: Optional[str] = None
    paused_at: Optional[datetime] = None
    error_count: int = 0
    manual_controls_enabled: bool = True


class PhasedLoader:
    """Main phased loading controller"""
    
    def __init__(self):
        self.config = self._load_phase_configurations()
        self.current_session: Optional[LoadingSession] = None
        self.session_file = Path("data/current_loading_session.json")
        self.logger = logging.getLogger(__name__)
        
        # Database setup
        db_config = get_database_config()
        self.engine = create_engine_from_config(db_config.get_url())
        self.session_factory = get_session_factory(self.engine)
        
        # Scraper manager
        self.scraper_manager = ScraperManager(self.session_factory())
        
        # Load existing session if any
        self._load_existing_session()
    
    def _load_phase_configurations(self) -> Dict[LoadingPhase, PhaseConfig]:
        """Load phase configurations"""
        return {
            LoadingPhase.PREPARATION: PhaseConfig(
                name="Preparation",
                description="Initialize database and validate system readiness",
                jurisdictions=[],
                estimated_duration=5,
                max_concurrent_tasks=1,
                retry_attempts=3,
                cooldown_period=0,
                dependencies=[],
                validation_checks=["database_connection", "scraper_availability"]
            ),
            LoadingPhase.FEDERAL_CORE: PhaseConfig(
                name="Federal Core Data",
                description="Load federal Parliament data (MPs, bills, committees)",
                jurisdictions=["ca"],
                estimated_duration=30,
                max_concurrent_tasks=3,
                retry_attempts=5,
                cooldown_period=10,
                dependencies=["preparation"],
                validation_checks=["federal_mps_count", "federal_bills_count"]
            ),
            LoadingPhase.PROVINCIAL_TIER1: PhaseConfig(
                name="Major Provinces",
                description="Load data for Ontario, Quebec, BC, Alberta",
                jurisdictions=["ca_on", "ca_qc", "ca_bc", "ca_ab"],
                estimated_duration=60,
                max_concurrent_tasks=2,
                retry_attempts=3,
                cooldown_period=15,
                dependencies=["federal_core"],
                validation_checks=["provincial_coverage_tier1"]
            ),
            LoadingPhase.PROVINCIAL_TIER2: PhaseConfig(
                name="Remaining Provinces",
                description="Load remaining provinces and territories",
                jurisdictions=[
                    "ca_sk", "ca_mb", "ca_ns", "ca_nb", "ca_pe", "ca_nl",
                    "ca_yt", "ca_nt", "ca_nu"
                ],
                estimated_duration=45,
                max_concurrent_tasks=3,
                retry_attempts=3,
                cooldown_period=10,
                dependencies=["provincial_tier1"],
                validation_checks=["provincial_coverage_complete"]
            ),
            LoadingPhase.MUNICIPAL_MAJOR: PhaseConfig(
                name="Major Cities",
                description="Load major city councils (Toronto, Montreal, Vancouver, etc.)",
                jurisdictions=[
                    "ca_on_toronto", "ca_qc_montreal", "ca_bc_vancouver",
                    "ca_ab_calgary", "ca_ab_edmonton", "ca_on_ottawa"
                ],
                estimated_duration=90,
                max_concurrent_tasks=2,
                retry_attempts=2,
                cooldown_period=20,
                dependencies=["provincial_tier2"],
                validation_checks=["major_cities_coverage"]
            ),
            LoadingPhase.MUNICIPAL_MINOR: PhaseConfig(
                name="Additional Municipalities",
                description="Load remaining municipal governments",
                jurisdictions=[],  # Dynamically populated
                estimated_duration=120,
                max_concurrent_tasks=4,
                retry_attempts=2,
                cooldown_period=5,
                dependencies=["municipal_major"],
                validation_checks=["municipal_coverage_target"]
            ),
            LoadingPhase.VALIDATION: PhaseConfig(
                name="Data Validation",
                description="Comprehensive data quality validation",
                jurisdictions=[],
                estimated_duration=20,
                max_concurrent_tasks=1,
                retry_attempts=1,
                cooldown_period=0,
                dependencies=["municipal_minor"],
                validation_checks=[
                    "data_completeness", "data_quality", "relationship_integrity"
                ]
            ),
            LoadingPhase.COMPLETION: PhaseConfig(
                name="Completion",
                description="Finalize loading and prepare for production",
                jurisdictions=[],
                estimated_duration=10,
                max_concurrent_tasks=1,
                retry_attempts=1,
                cooldown_period=0,
                dependencies=["validation"],
                validation_checks=["system_readiness"]
            )
        }
    
    def start_phased_loading(
        self, 
        strategy: LoadingStrategy = LoadingStrategy.BALANCED,
        user_id: Optional[str] = None,
        manual_controls: bool = True
    ) -> str:
        """Start a new phased loading session"""
        if self.current_session and self.current_session.current_phase != LoadingPhase.COMPLETION:
            raise ValueError("Loading session already in progress")
        
        session_id = f"loading_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Calculate total estimated duration
        total_duration = sum(
            config.estimated_duration for config in self.config.values()
        )
        
        # Adjust duration based on strategy
        if strategy == LoadingStrategy.CONSERVATIVE:
            total_duration = int(total_duration * 1.5)
        elif strategy == LoadingStrategy.AGGRESSIVE:
            total_duration = int(total_duration * 0.7)
        
        self.current_session = LoadingSession(
            session_id=session_id,
            strategy=strategy,
            current_phase=LoadingPhase.PREPARATION,
            started_at=datetime.now(),
            phases_completed=[],
            total_estimated_duration=total_duration,
            user_id=user_id,
            manual_controls_enabled=manual_controls
        )
        
        self._save_session()
        
        # Start progress tracking
        progress_tracker.start_operation(f"Phased Loading - {strategy.value.title()}")
        
        self.logger.info(f"Started phased loading session: {session_id}")
        return session_id
    
    def get_current_status(self) -> Dict:
        """Get current loading status"""
        if not self.current_session:
            return {
                "status": "no_session",
                "message": "No loading session in progress"
            }
        
        phase_config = self.config[self.current_session.current_phase]
        
        # Calculate overall progress
        completed_phases = len(self.current_session.phases_completed)
        total_phases = len(self.config)
        overall_progress = (completed_phases / total_phases) * 100
        
        # Calculate time estimates
        elapsed_time = datetime.now() - self.current_session.started_at
        if self.current_session.paused_at:
            elapsed_time = self.current_session.paused_at - self.current_session.started_at
        
        estimated_remaining = timedelta(
            minutes=self.current_session.total_estimated_duration
        ) - elapsed_time
        
        return {
            "session_id": self.current_session.session_id,
            "status": "paused" if self.current_session.paused_at else "running",
            "strategy": self.current_session.strategy.value,
            "current_phase": {
                "name": phase_config.name,
                "description": phase_config.description,
                "phase_key": self.current_session.current_phase.value
            },
            "progress": {
                "overall_percentage": round(overall_progress, 1),
                "phases_completed": completed_phases,
                "total_phases": total_phases,
                "completed_phase_names": self.current_session.phases_completed
            },
            "timing": {
                "started_at": self.current_session.started_at.isoformat(),
                "elapsed_minutes": int(elapsed_time.total_seconds() / 60),
                "estimated_remaining_minutes": max(0, int(estimated_remaining.total_seconds() / 60)),
                "paused_at": self.current_session.paused_at.isoformat() if self.current_session.paused_at else None
            },
            "controls": {
                "manual_controls_enabled": self.current_session.manual_controls_enabled,
                "can_pause": not self.current_session.paused_at,
                "can_resume": bool(self.current_session.paused_at),
                "can_skip_phase": self.current_session.manual_controls_enabled,
                "can_cancel": True
            },
            "error_count": self.current_session.error_count
        }
    
    def execute_current_phase(self) -> bool:
        """Execute the current loading phase"""
        if not self.current_session or self.current_session.paused_at:
            return False
        
        phase = self.current_session.current_phase
        phase_config = self.config[phase]
        
        self.logger.info(f"Executing phase: {phase_config.name}")
        
        try:
            # Add progress tasks for this phase
            phase_task_id = f"phase_{phase.value}"
            progress_tracker.add_task(
                phase_task_id,
                TaskType.SCRAPING,
                phase_config.description,
                len(phase_config.jurisdictions) or 1
            )
            
            progress_tracker.start_task(phase_task_id, f"Starting {phase_config.name}")
            
            # Execute phase-specific logic
            success = self._execute_phase_logic(phase, phase_config)
            
            if success:
                progress_tracker.complete_task(phase_task_id, success=True)
                self._complete_current_phase()
                return True
            else:
                progress_tracker.complete_task(
                    phase_task_id, 
                    success=False, 
                    error_message="Phase execution failed"
                )
                self.current_session.error_count += 1
                self._save_session()
                return False
                
        except Exception as e:
            self.logger.error(f"Error executing phase {phase.value}: {e}")
            self.current_session.error_count += 1
            self._save_session()
            return False
    
    def _execute_phase_logic(self, phase: LoadingPhase, config: PhaseConfig) -> bool:
        """Execute the logic for a specific phase"""
        if phase == LoadingPhase.PREPARATION:
            return self._execute_preparation_phase(config)
        elif phase == LoadingPhase.FEDERAL_CORE:
            return self._execute_federal_phase(config)
        elif phase in [LoadingPhase.PROVINCIAL_TIER1, LoadingPhase.PROVINCIAL_TIER2]:
            return self._execute_provincial_phase(config)
        elif phase in [LoadingPhase.MUNICIPAL_MAJOR, LoadingPhase.MUNICIPAL_MINOR]:
            return self._execute_municipal_phase(config)
        elif phase == LoadingPhase.VALIDATION:
            return self._execute_validation_phase(config)
        elif phase == LoadingPhase.COMPLETION:
            return self._execute_completion_phase(config)
        else:
            return False
    
    def _execute_preparation_phase(self, config: PhaseConfig) -> bool:
        """Execute preparation phase"""
        self.logger.info("Executing preparation phase")
        
        # Test database connection
        try:
            with self.engine.connect() as conn:
                result = conn.execute("SELECT 1").fetchone()
                if not result:
                    return False
        except Exception as e:
            self.logger.error(f"Database connection test failed: {e}")
            return False
        
        # Validate scraper availability
        try:
            available_scrapers = self.scraper_manager.get_available_scrapers()
            if len(available_scrapers) < 5:  # Minimum expected scrapers
                self.logger.warning(f"Only {len(available_scrapers)} scrapers available")
        except Exception as e:
            self.logger.error(f"Scraper validation failed: {e}")
            return False
        
        # Small delay for demonstration
        time.sleep(2)
        
        return True
    
    def _execute_federal_phase(self, config: PhaseConfig) -> bool:
        """Execute federal data loading phase"""
        self.logger.info("Executing federal core data loading")
        
        try:
            # Load federal data with rate limiting
            db_session = self.session_factory()
            
            # Federal MPs
            federal_task = progress_tracker.add_task(
                "federal_mps", TaskType.SCRAPING, "Federal MPs", 338  # Approx number of MPs
            )
            
            # Simulate federal scraping with progress updates
            for i in range(10):  # Simulated batches
                if self.current_session.paused_at:
                    return False
                
                progress_tracker.update_task_progress(
                    "federal_mps", 
                    (i + 1) * 10, 
                    f"Processing MP batch {i + 1}/10"
                )
                
                # Apply cooldown between batches
                time.sleep(config.cooldown_period)
            
            progress_tracker.complete_task("federal_mps", success=True)
            
            # Federal Bills
            bills_task = progress_tracker.add_task(
                "federal_bills", TaskType.SCRAPING, "Federal Bills", 100
            )
            
            # Simulate bills scraping
            for i in range(5):
                if self.current_session.paused_at:
                    return False
                
                progress_tracker.update_task_progress(
                    "federal_bills",
                    (i + 1) * 20,
                    f"Processing bills batch {i + 1}/5"
                )
                
                time.sleep(config.cooldown_period)
            
            progress_tracker.complete_task("federal_bills", success=True)
            
            db_session.close()
            return True
            
        except Exception as e:
            self.logger.error(f"Federal phase failed: {e}")
            return False
    
    def _execute_provincial_phase(self, config: PhaseConfig) -> bool:
        """Execute provincial data loading phase"""
        self.logger.info(f"Executing provincial phase: {config.name}")
        
        try:
            for jurisdiction in config.jurisdictions:
                if self.current_session.paused_at:
                    return False
                
                task_id = f"provincial_{jurisdiction}"
                progress_tracker.add_task(
                    task_id, TaskType.SCRAPING, f"Province: {jurisdiction}", 50
                )
                
                # Simulate provincial scraping
                for i in range(5):
                    if self.current_session.paused_at:
                        return False
                    
                    progress_tracker.update_task_progress(
                        task_id,
                        (i + 1) * 20,
                        f"Processing {jurisdiction} batch {i + 1}/5"
                    )
                    
                    time.sleep(config.cooldown_period)
                
                progress_tracker.complete_task(task_id, success=True)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Provincial phase failed: {e}")
            return False
    
    def _execute_municipal_phase(self, config: PhaseConfig) -> bool:
        """Execute municipal data loading phase"""
        self.logger.info(f"Executing municipal phase: {config.name}")
        
        try:
            jurisdictions = config.jurisdictions
            if not jurisdictions:  # For MUNICIPAL_MINOR, get remaining jurisdictions
                jurisdictions = self._get_remaining_municipal_jurisdictions()
            
            for jurisdiction in jurisdictions:
                if self.current_session.paused_at:
                    return False
                
                task_id = f"municipal_{jurisdiction}"
                progress_tracker.add_task(
                    task_id, TaskType.SCRAPING, f"Municipality: {jurisdiction}", 25
                )
                
                # Simulate municipal scraping (smaller datasets)
                for i in range(3):
                    if self.current_session.paused_at:
                        return False
                    
                    progress_tracker.update_task_progress(
                        task_id,
                        (i + 1) * 33,
                        f"Processing {jurisdiction} batch {i + 1}/3"
                    )
                    
                    time.sleep(config.cooldown_period)
                
                progress_tracker.complete_task(task_id, success=True)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Municipal phase failed: {e}")
            return False
    
    def _execute_validation_phase(self, config: PhaseConfig) -> bool:
        """Execute data validation phase"""
        self.logger.info("Executing validation phase")
        
        validation_task = progress_tracker.add_task(
            "validation", TaskType.VALIDATION, "Data Quality Validation", 100
        )
        
        try:
            # Simulate validation checks
            checks = [
                "Data completeness check",
                "Relationship integrity check", 
                "Data quality assessment",
                "Performance validation",
                "System readiness check"
            ]
            
            for i, check in enumerate(checks):
                if self.current_session.paused_at:
                    return False
                
                progress_tracker.update_task_progress(
                    "validation",
                    (i + 1) * 20,
                    check
                )
                
                time.sleep(3)  # Validation takes time
            
            progress_tracker.complete_task("validation", success=True)
            return True
            
        except Exception as e:
            self.logger.error(f"Validation phase failed: {e}")
            progress_tracker.complete_task("validation", success=False, error_message=str(e))
            return False
    
    def _execute_completion_phase(self, config: PhaseConfig) -> bool:
        """Execute completion phase"""
        self.logger.info("Executing completion phase")
        
        completion_task = progress_tracker.add_task(
            "completion", TaskType.COMPLETION, "Finalizing System", 100
        )
        
        try:
            # Finalization steps
            steps = [
                "Optimizing database indexes",
                "Clearing temporary data", 
                "Updating system status",
                "Preparing production mode",
                "Generating completion report"
            ]
            
            for i, step in enumerate(steps):
                progress_tracker.update_task_progress(
                    "completion",
                    (i + 1) * 20,
                    step
                )
                
                time.sleep(1)
            
            progress_tracker.complete_task("completion", success=True)
            return True
            
        except Exception as e:
            self.logger.error(f"Completion phase failed: {e}")
            return False
    
    def _get_remaining_municipal_jurisdictions(self) -> List[str]:
        """Get list of remaining municipal jurisdictions to process"""
        # This would query the database for remaining municipalities
        # For now, return a sample list
        return [
            "ca_on_mississauga", "ca_on_brampton", "ca_on_hamilton",
            "ca_qc_quebec", "ca_qc_laval", "ca_bc_burnaby",
            "ca_ab_red_deer", "ca_sk_saskatoon", "ca_mb_winnipeg"
        ]
    
    def _complete_current_phase(self):
        """Mark current phase as completed and advance to next"""
        current_phase = self.current_session.current_phase
        self.current_session.phases_completed.append(current_phase.value)
        
        # Get next phase
        phases = list(LoadingPhase)
        current_index = phases.index(current_phase)
        
        if current_index < len(phases) - 1:
            self.current_session.current_phase = phases[current_index + 1]
            self.logger.info(f"Advanced to phase: {self.current_session.current_phase.value}")
        else:
            self.logger.info("All phases completed")
        
        self._save_session()
    
    def pause_loading(self) -> bool:
        """Pause the current loading session"""
        if not self.current_session or self.current_session.paused_at:
            return False
        
        self.current_session.paused_at = datetime.now()
        self._save_session()
        
        # Pause progress tracker
        progress_tracker.pause_operation()
        
        self.logger.info("Loading session paused")
        return True
    
    def resume_loading(self) -> bool:
        """Resume the paused loading session"""
        if not self.current_session or not self.current_session.paused_at:
            return False
        
        self.current_session.paused_at = None
        self._save_session()
        
        # Resume progress tracker
        progress_tracker.resume_operation()
        
        self.logger.info("Loading session resumed")
        return True
    
    def skip_current_phase(self) -> bool:
        """Skip the current phase (manual control)"""
        if not self.current_session or not self.current_session.manual_controls_enabled:
            return False
        
        self.logger.info(f"Skipping phase: {self.current_session.current_phase.value}")
        self._complete_current_phase()
        return True
    
    def cancel_loading(self) -> bool:
        """Cancel the current loading session"""
        if not self.current_session:
            return False
        
        # Cancel progress tracker
        progress_tracker.cancel_operation()
        
        # Clear session
        self.current_session = None
        if self.session_file.exists():
            self.session_file.unlink()
        
        self.logger.info("Loading session cancelled")
        return True
    
    def get_phase_preview(self, phase: LoadingPhase) -> Dict:
        """Get preview information for a specific phase"""
        config = self.config[phase]
        
        return {
            "name": config.name,
            "description": config.description,
            "estimated_duration_minutes": config.estimated_duration,
            "jurisdiction_count": len(config.jurisdictions),
            "jurisdictions": config.jurisdictions[:10],  # Preview first 10
            "max_concurrent_tasks": config.max_concurrent_tasks,
            "dependencies": config.dependencies,
            "validation_checks": config.validation_checks
        }
    
    def get_all_phases_preview(self) -> List[Dict]:
        """Get preview of all loading phases"""
        return [
            {
                "phase": phase.value,
                **self.get_phase_preview(phase)
            }
            for phase in LoadingPhase
        ]
    
    def _save_session(self):
        """Save current session to file"""
        if not self.current_session:
            return
        
        self.session_file.parent.mkdir(parents=True, exist_ok=True)
        
        session_data = {
            **asdict(self.current_session),
            "started_at": self.current_session.started_at.isoformat(),
            "paused_at": self.current_session.paused_at.isoformat() if self.current_session.paused_at else None,
            "strategy": self.current_session.strategy.value,
            "current_phase": self.current_session.current_phase.value
        }
        
        with open(self.session_file, 'w') as f:
            json.dump(session_data, f, indent=2)
    
    def _load_existing_session(self):
        """Load existing session from file"""
        if not self.session_file.exists():
            return
        
        try:
            with open(self.session_file, 'r') as f:
                data = json.load(f)
            
            self.current_session = LoadingSession(
                session_id=data['session_id'],
                strategy=LoadingStrategy(data['strategy']),
                current_phase=LoadingPhase(data['current_phase']),
                started_at=datetime.fromisoformat(data['started_at']),
                phases_completed=data['phases_completed'],
                total_estimated_duration=data['total_estimated_duration'],
                user_id=data.get('user_id'),
                paused_at=datetime.fromisoformat(data['paused_at']) if data.get('paused_at') else None,
                error_count=data.get('error_count', 0),
                manual_controls_enabled=data.get('manual_controls_enabled', True)
            )
            
            self.logger.info(f"Loaded existing session: {self.current_session.session_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to load existing session: {e}")
            # Remove corrupted session file
            self.session_file.unlink()


# Global phased loader instance
phased_loader = PhasedLoader()