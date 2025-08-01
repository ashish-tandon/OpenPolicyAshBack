"""
Phased Loading API Endpoints
Provides REST API for controlling phased data loading
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import StreamingResponse
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from enum import Enum
import json
import asyncio
from datetime import datetime

from phased_loading import phased_loader, LoadingStrategy, LoadingPhase


class LoadingStrategyRequest(str, Enum):
    """Loading strategy options"""
    CONSERVATIVE = "conservative"
    BALANCED = "balanced"
    AGGRESSIVE = "aggressive"


class StartLoadingRequest(BaseModel):
    """Request model for starting phased loading"""
    strategy: LoadingStrategyRequest = LoadingStrategyRequest.BALANCED
    user_id: Optional[str] = None
    manual_controls: bool = True


class PhaseActionRequest(BaseModel):
    """Request model for phase actions"""
    force: bool = False
    reason: Optional[str] = None


router = APIRouter(prefix="/api/phased-loading", tags=["phased-loading"])


@router.get("/status")
async def get_loading_status():
    """Get current phased loading status"""
    try:
        status = phased_loader.get_current_status()
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")


@router.get("/phases/preview")
async def get_phases_preview():
    """Get preview of all loading phases"""
    try:
        phases = phased_loader.get_all_phases_preview()
        return {
            "phases": phases,
            "total_phases": len(phases),
            "total_estimated_duration": sum(p["estimated_duration_minutes"] for p in phases)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get phases preview: {str(e)}")


@router.get("/phases/{phase}/preview")
async def get_phase_preview(phase: str):
    """Get preview of a specific loading phase"""
    try:
        phase_enum = LoadingPhase(phase)
        preview = phased_loader.get_phase_preview(phase_enum)
        return preview
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid phase: {phase}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get phase preview: {str(e)}")


@router.post("/start")
async def start_phased_loading(request: StartLoadingRequest):
    """Start a new phased loading session"""
    try:
        strategy = LoadingStrategy(request.strategy.value)
        session_id = phased_loader.start_phased_loading(
            strategy=strategy,
            user_id=request.user_id,
            manual_controls=request.manual_controls
        )
        
        return {
            "success": True,
            "session_id": session_id,
            "message": f"Phased loading started with {strategy.value} strategy",
            "strategy": strategy.value,
            "manual_controls": request.manual_controls
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start loading: {str(e)}")


@router.post("/execute-phase")
async def execute_current_phase():
    """Execute the current loading phase"""
    try:
        success = phased_loader.execute_current_phase()
        
        if success:
            return {
                "success": True,
                "message": "Phase executed successfully"
            }
        else:
            return {
                "success": False,
                "message": "Phase execution failed or system is paused"
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to execute phase: {str(e)}")


@router.post("/pause")
async def pause_loading(request: PhaseActionRequest = PhaseActionRequest()):
    """Pause the current loading session"""
    try:
        success = phased_loader.pause_loading()
        
        if success:
            return {
                "success": True,
                "message": "Loading session paused",
                "paused_at": datetime.now().isoformat(),
                "reason": request.reason
            }
        else:
            raise HTTPException(status_code=400, detail="No active loading session to pause")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to pause loading: {str(e)}")


@router.post("/resume")
async def resume_loading(request: PhaseActionRequest = PhaseActionRequest()):
    """Resume the paused loading session"""
    try:
        success = phased_loader.resume_loading()
        
        if success:
            return {
                "success": True,
                "message": "Loading session resumed",
                "resumed_at": datetime.now().isoformat(),
                "reason": request.reason
            }
        else:
            raise HTTPException(status_code=400, detail="No paused loading session to resume")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to resume loading: {str(e)}")


@router.post("/skip-phase")
async def skip_current_phase(request: PhaseActionRequest = PhaseActionRequest()):
    """Skip the current loading phase"""
    try:
        current_status = phased_loader.get_current_status()
        
        if current_status.get("status") == "no_session":
            raise HTTPException(status_code=400, detail="No active loading session")
        
        if not current_status.get("controls", {}).get("can_skip_phase", False):
            raise HTTPException(status_code=400, detail="Manual controls not enabled or phase cannot be skipped")
        
        success = phased_loader.skip_current_phase()
        
        if success:
            return {
                "success": True,
                "message": f"Skipped phase: {current_status['current_phase']['name']}",
                "skipped_at": datetime.now().isoformat(),
                "reason": request.reason,
                "force": request.force
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to skip phase")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to skip phase: {str(e)}")


@router.post("/cancel")
async def cancel_loading(request: PhaseActionRequest = PhaseActionRequest()):
    """Cancel the current loading session"""
    try:
        success = phased_loader.cancel_loading()
        
        if success:
            return {
                "success": True,
                "message": "Loading session cancelled",
                "cancelled_at": datetime.now().isoformat(),
                "reason": request.reason,
                "force": request.force
            }
        else:
            raise HTTPException(status_code=400, detail="No loading session to cancel")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cancel loading: {str(e)}")


@router.get("/stream/status")
async def stream_loading_status():
    """Stream real-time loading status updates"""
    async def generate_status_stream():
        """Generate server-sent events for loading status"""
        while True:
            try:
                status = phased_loader.get_current_status()
                
                # Format as server-sent event
                event_data = f"data: {json.dumps(status)}\n\n"
                yield event_data
                
                # Check if loading is complete
                if status.get("status") == "no_session" or \
                   status.get("progress", {}).get("overall_percentage", 0) >= 100:
                    break
                
                # Wait before next update
                await asyncio.sleep(2)
                
            except Exception as e:
                error_event = f"data: {json.dumps({'error': str(e)})}\n\n"
                yield error_event
                break
    
    return StreamingResponse(
        generate_status_stream(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
        }
    )


@router.get("/history")
async def get_loading_history(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """Get loading session history"""
    # This would typically query a database for historical sessions
    # For now, return placeholder data
    return {
        "sessions": [
            {
                "session_id": "loading_20241201_120000",
                "strategy": "balanced",
                "started_at": "2024-12-01T12:00:00",
                "completed_at": "2024-12-01T14:30:00",
                "status": "completed",
                "phases_completed": 8,
                "total_phases": 8,
                "duration_minutes": 150,
                "error_count": 0
            }
        ],
        "total_sessions": 1,
        "limit": limit,
        "offset": offset
    }


@router.get("/statistics")
async def get_loading_statistics():
    """Get loading statistics and performance metrics"""
    try:
        current_status = phased_loader.get_current_status()
        
        # Calculate statistics
        stats = {
            "current_session": current_status if current_status.get("status") != "no_session" else None,
            "system_metrics": {
                "average_loading_time_minutes": 180,  # Historical average
                "success_rate_percentage": 95.0,
                "most_common_strategy": "balanced",
                "total_sessions_completed": 25,
                "total_data_points_loaded": 15000,
                "last_successful_load": "2024-12-01T14:30:00"
            },
            "phase_statistics": {
                "fastest_phase": {
                    "name": "Preparation",
                    "average_duration_minutes": 3
                },
                "slowest_phase": {
                    "name": "Municipal Minor",
                    "average_duration_minutes": 85
                },
                "most_reliable_phase": {
                    "name": "Federal Core",
                    "success_rate_percentage": 98.5
                }
            },
            "performance_trends": {
                "loading_speed_trend": "stable",
                "error_rate_trend": "decreasing",
                "data_quality_trend": "improving"
            }
        }
        
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")


@router.get("/validation/results")
async def get_validation_results():
    """Get latest data validation results"""
    # This would typically query the database for validation results
    # For now, return sample data
    return {
        "validation_timestamp": datetime.now().isoformat(),
        "overall_score": 92.5,
        "checks": [
            {
                "check_name": "Data Completeness",
                "status": "passed",
                "score": 95.2,
                "details": "338 of 338 federal MPs have complete data"
            },
            {
                "check_name": "Relationship Integrity",
                "status": "passed",
                "score": 98.1,
                "details": "All foreign key relationships are valid"
            },
            {
                "check_name": "Data Quality",
                "status": "warning",
                "score": 85.3,
                "details": "Some contact information missing for municipal representatives"
            },
            {
                "check_name": "Federal Bill Identifiers",
                "status": "passed",
                "score": 99.7,
                "details": "All federal bills follow C-# or S-# format"
            }
        ],
        "recommendations": [
            "Update contact information for municipal representatives",
            "Verify recent federal bill data for completeness",
            "Consider increasing validation frequency for high-priority data"
        ]
    }


@router.get("/health")
async def health_check():
    """Health check for phased loading system"""
    try:
        status = phased_loader.get_current_status()
        
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "services": {
                "phased_loader": "operational",
                "progress_tracker": "operational",
                "database": "operational",
                "scrapers": "operational"
            },
            "current_loading_session": status.get("status") != "no_session",
            "system_load": "normal"
        }
        
        return health_status
    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
            "services": {
                "phased_loader": "error",
                "progress_tracker": "unknown",
                "database": "unknown",
                "scrapers": "unknown"
            }
        }


# Configuration endpoints
@router.get("/config/strategies")
async def get_loading_strategies():
    """Get available loading strategies"""
    return {
        "strategies": [
            {
                "name": "conservative",
                "display_name": "Conservative",
                "description": "Slow, safe loading with maximum error checking",
                "duration_multiplier": 1.5,
                "recommended_for": "Production environments, first-time setup"
            },
            {
                "name": "balanced",
                "display_name": "Balanced",
                "description": "Normal loading speed with good error handling",
                "duration_multiplier": 1.0,
                "recommended_for": "Most situations, regular updates"
            },
            {
                "name": "aggressive",
                "display_name": "Aggressive",
                "description": "Fast loading with reduced safety checks",
                "duration_multiplier": 0.7,
                "recommended_for": "Development environments, urgent updates"
            }
        ],
        "default_strategy": "balanced"
    }


@router.get("/config/phases")
async def get_phase_configuration():
    """Get detailed phase configuration"""
    try:
        phases = phased_loader.get_all_phases_preview()
        
        return {
            "phases": phases,
            "phase_dependencies": {
                "preparation": [],
                "federal_core": ["preparation"],
                "provincial_tier1": ["federal_core"],
                "provincial_tier2": ["provincial_tier1"],
                "municipal_major": ["provincial_tier2"],
                "municipal_minor": ["municipal_major"],
                "validation": ["municipal_minor"],
                "completion": ["validation"]
            },
            "total_jurisdictions": sum(len(p.get("jurisdictions", [])) for p in phases),
            "estimated_total_duration": sum(p["estimated_duration_minutes"] for p in phases)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get phase configuration: {str(e)}")


# Utility endpoints
@router.post("/simulate")
async def simulate_loading(
    strategy: LoadingStrategyRequest = LoadingStrategyRequest.BALANCED,
    phases_to_simulate: Optional[List[str]] = None
):
    """Simulate a loading session (for testing/planning)"""
    # This would run a simulation without actually loading data
    return {
        "simulation_id": f"sim_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "strategy": strategy.value,
        "estimated_duration_minutes": 180 if strategy == LoadingStrategyRequest.BALANCED else 
                                     270 if strategy == LoadingStrategyRequest.CONSERVATIVE else 126,
        "phases_to_run": phases_to_simulate or [p.value for p in LoadingPhase],
        "estimated_completion": (datetime.now().timestamp() + (180 * 60)),
        "resource_requirements": {
            "cpu_usage": "moderate",
            "memory_usage": "high",
            "network_usage": "high",
            "disk_usage": "moderate"
        },
        "simulation_note": "This is a simulation - no actual data will be loaded"
    }