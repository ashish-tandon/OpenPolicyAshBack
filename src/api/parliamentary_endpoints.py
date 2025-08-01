"""
Parliamentary API Endpoints - Enhanced OpenParliament Integration
Provides access to parliamentary data including Hansard debates, committee meetings, and speeches
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from sqlalchemy.orm import Session
from pydantic import BaseModel

from src.database.connection import get_db_session
from src.database.models import (
    ParliamentarySession, HansardRecord, Speech, CommitteeMeeting, Bill
)
from src.scrapers.parliamentary_scraper import (
    ParliamentaryScraper, run_parliamentary_data_collection
)
from src.validation.parliamentary_validator import (
    ParliamentaryValidator, validate_federal_bill, validate_bills_batch
)
from src.policy_engine.opa_client import OPAClient

router = APIRouter(prefix="/api/parliamentary", tags=["parliamentary"])

# Response models
class ParliamentarySessionResponse(BaseModel):
    id: int
    parliament_number: int
    session_number: int
    start_date: date
    end_date: Optional[date]
    hansard_records_count: int
    committee_meetings_count: int
    
    class Config:
        from_attributes = True

class HansardRecordResponse(BaseModel):
    id: int
    date: date
    sitting_number: Optional[int]
    document_url: Optional[str]
    pdf_url: Optional[str]
    xml_url: Optional[str]
    processed: bool
    speech_count: int
    
    class Config:
        from_attributes = True

class SpeechResponse(BaseModel):
    id: int
    speaker_name: Optional[str]
    speaker_title: Optional[str]
    content: str
    time_spoken: Optional[datetime]
    speech_type: Optional[str]
    hansard_id: int
    
    class Config:
        from_attributes = True

class CommitteeMeetingResponse(BaseModel):
    id: int
    committee_name: str
    meeting_date: date
    meeting_number: Optional[int]
    evidence_url: Optional[str]
    transcript_url: Optional[str]
    processed: bool
    
    class Config:
        from_attributes = True

class ValidationResultResponse(BaseModel):
    bill_id: Optional[int]
    identifier: Optional[str]
    title: Optional[str]
    passes: bool
    warnings: List[str]
    errors: List[str]
    quality_score: int
    is_critical: bool
    is_government_bill: bool
    recommendations: List[str]

class DataCollectionResultResponse(BaseModel):
    parliamentary_session: Optional[str]
    hansard_records: int
    speeches_processed: int
    committee_meetings: int
    errors: List[str]

# Dependency for policy validation
def get_opa_client():
    return OPAClient()

def check_parliamentary_access(request: Request):
    """Check if user has access to parliamentary endpoints"""
    # This uses the policy middleware context
    if hasattr(request.state, 'policy_context'):
        policy_context = request.state.policy_context
        if not policy_context.get('access_result', {}).get('allowed', False):
            raise HTTPException(status_code=403, detail="Access denied to parliamentary endpoints")
    # For development/testing without policy middleware
    return True

# Parliamentary Sessions
@router.get("/sessions", response_model=List[ParliamentarySessionResponse])
async def get_parliamentary_sessions(
    db: Session = Depends(get_db_session),
    _access_check = Depends(check_parliamentary_access)
):
    """Get all parliamentary sessions with summary statistics"""
    sessions = db.query(ParliamentarySession).order_by(
        ParliamentarySession.parliament_number.desc(),
        ParliamentarySession.session_number.desc()
    ).all()
    
    result = []
    for session in sessions:
        hansard_count = db.query(HansardRecord).filter_by(session_id=session.id).count()
        committee_count = db.query(CommitteeMeeting).filter_by(session_id=session.id).count()
        
        result.append(ParliamentarySessionResponse(
            id=session.id,
            parliament_number=session.parliament_number,
            session_number=session.session_number,
            start_date=session.start_date,
            end_date=session.end_date,
            hansard_records_count=hansard_count,
            committee_meetings_count=committee_count
        ))
    
    return result

@router.get("/sessions/{session_id}", response_model=ParliamentarySessionResponse)
async def get_parliamentary_session(
    session_id: int,
    db: Session = Depends(get_db_session),
    _access_check = Depends(check_parliamentary_access)
):
    """Get specific parliamentary session details"""
    session = db.query(ParliamentarySession).filter_by(id=session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Parliamentary session not found")
    
    hansard_count = db.query(HansardRecord).filter_by(session_id=session.id).count()
    committee_count = db.query(CommitteeMeeting).filter_by(session_id=session.id).count()
    
    return ParliamentarySessionResponse(
        id=session.id,
        parliament_number=session.parliament_number,
        session_number=session.session_number,
        start_date=session.start_date,
        end_date=session.end_date,
        hansard_records_count=hansard_count,
        committee_meetings_count=committee_count
    )

# Hansard Records
@router.get("/hansard", response_model=List[HansardRecordResponse])
async def get_hansard_records(
    session_id: Optional[int] = Query(None, description="Filter by parliamentary session"),
    processed: Optional[bool] = Query(None, description="Filter by processing status"),
    limit: int = Query(50, le=500, description="Maximum number of records"),
    offset: int = Query(0, description="Number of records to skip"),
    db: Session = Depends(get_db_session),
    _access_check = Depends(check_parliamentary_access)
):
    """Get Hansard debate records"""
    query = db.query(HansardRecord)
    
    if session_id:
        query = query.filter(HansardRecord.session_id == session_id)
    
    if processed is not None:
        query = query.filter(HansardRecord.processed == processed)
    
    records = query.order_by(HansardRecord.date.desc()).offset(offset).limit(limit).all()
    
    return [HansardRecordResponse.from_orm(record) for record in records]

@router.get("/hansard/{hansard_id}", response_model=HansardRecordResponse)
async def get_hansard_record(
    hansard_id: int,
    db: Session = Depends(get_db_session),
    _access_check = Depends(check_parliamentary_access)
):
    """Get specific Hansard record details"""
    record = db.query(HansardRecord).filter_by(id=hansard_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Hansard record not found")
    
    return HansardRecordResponse.from_orm(record)

@router.get("/hansard/{hansard_id}/speeches", response_model=List[SpeechResponse])
async def get_hansard_speeches(
    hansard_id: int,
    speaker_name: Optional[str] = Query(None, description="Filter by speaker name"),
    speech_type: Optional[str] = Query(None, description="Filter by speech type"),
    limit: int = Query(100, le=1000, description="Maximum number of speeches"),
    db: Session = Depends(get_db_session),
    _access_check = Depends(check_parliamentary_access)
):
    """Get speeches from a specific Hansard record"""
    # Verify Hansard record exists
    hansard = db.query(HansardRecord).filter_by(id=hansard_id).first()
    if not hansard:
        raise HTTPException(status_code=404, detail="Hansard record not found")
    
    query = db.query(Speech).filter(Speech.hansard_id == hansard_id)
    
    if speaker_name:
        query = query.filter(Speech.speaker_name.ilike(f"%{speaker_name}%"))
    
    if speech_type:
        query = query.filter(Speech.speech_type == speech_type)
    
    speeches = query.order_by(Speech.time_spoken).limit(limit).all()
    
    return [SpeechResponse.from_orm(speech) for speech in speeches]

# Committee Meetings
@router.get("/committees/meetings", response_model=List[CommitteeMeetingResponse])
async def get_committee_meetings(
    committee_name: Optional[str] = Query(None, description="Filter by committee name"),
    session_id: Optional[int] = Query(None, description="Filter by parliamentary session"),
    processed: Optional[bool] = Query(None, description="Filter by processing status"),
    limit: int = Query(50, le=500, description="Maximum number of meetings"),
    offset: int = Query(0, description="Number of meetings to skip"),
    db: Session = Depends(get_db_session),
    _access_check = Depends(check_parliamentary_access)
):
    """Get committee meeting records"""
    query = db.query(CommitteeMeeting)
    
    if committee_name:
        query = query.filter(CommitteeMeeting.committee_name.ilike(f"%{committee_name}%"))
    
    if session_id:
        query = query.filter(CommitteeMeeting.session_id == session_id)
    
    if processed is not None:
        query = query.filter(CommitteeMeeting.processed == processed)
    
    meetings = query.order_by(CommitteeMeeting.meeting_date.desc()).offset(offset).limit(limit).all()
    
    return [CommitteeMeetingResponse.from_orm(meeting) for meeting in meetings]

@router.get("/committees/{committee_name}/meetings", response_model=List[CommitteeMeetingResponse])
async def get_committee_meetings_by_name(
    committee_name: str,
    limit: int = Query(50, le=500, description="Maximum number of meetings"),
    db: Session = Depends(get_db_session),
    _access_check = Depends(check_parliamentary_access)
):
    """Get meetings for a specific committee"""
    meetings = db.query(CommitteeMeeting).filter(
        CommitteeMeeting.committee_name.ilike(f"%{committee_name}%")
    ).order_by(CommitteeMeeting.meeting_date.desc()).limit(limit).all()
    
    return [CommitteeMeetingResponse.from_orm(meeting) for meeting in meetings]

# Data Validation Endpoints
@router.get("/validation/federal-bills", response_model=List[ValidationResultResponse])
async def validate_federal_bills(
    limit: int = Query(20, le=100, description="Maximum number of bills to validate"),
    include_critical_only: bool = Query(False, description="Only validate critical bills"),
    db: Session = Depends(get_db_session),
    opa_client: OPAClient = Depends(get_opa_client),
    _access_check = Depends(check_parliamentary_access)
):
    """Validate federal bills using enhanced parliamentary validation"""
    # Get federal bills
    query = db.query(Bill).filter(Bill.jurisdiction_type == "federal")
    
    if include_critical_only:
        # This would require implementing critical bill detection in the database
        # For now, we'll validate all federal bills
        pass
    
    bills = query.order_by(Bill.updated_at.desc()).limit(limit).all()
    
    validator = ParliamentaryValidator()
    results = []
    
    for bill in bills:
        validation = validator.validate_federal_bill(bill)
        results.append(ValidationResultResponse(**validation))
    
    return results

@router.post("/validation/federal-bills/batch", response_model=Dict[str, Any])
async def validate_federal_bills_batch(
    bill_ids: List[int],
    db: Session = Depends(get_db_session),
    opa_client: OPAClient = Depends(get_opa_client),
    _access_check = Depends(check_parliamentary_access)
):
    """Batch validate multiple federal bills"""
    if len(bill_ids) > 100:
        raise HTTPException(status_code=400, detail="Maximum 100 bills per batch")
    
    bills = db.query(Bill).filter(
        Bill.id.in_(bill_ids),
        Bill.jurisdiction_type == "federal"
    ).all()
    
    if len(bills) != len(bill_ids):
        raise HTTPException(status_code=404, detail="Some bills not found or not federal")
    
    validator = ParliamentaryValidator()
    return validator.validate_bulk_bills(bills)

@router.get("/validation/bill/{bill_id}", response_model=ValidationResultResponse)
async def validate_single_bill(
    bill_id: int,
    db: Session = Depends(get_db_session),
    opa_client: OPAClient = Depends(get_opa_client),
    _access_check = Depends(check_parliamentary_access)
):
    """Validate a single bill with detailed results"""
    bill = db.query(Bill).filter_by(id=bill_id).first()
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")
    
    validator = ParliamentaryValidator()
    validation = validator.validate_federal_bill(bill)
    
    return ValidationResultResponse(**validation)

# Data Collection Endpoints
@router.post("/collection/run", response_model=DataCollectionResultResponse)
async def run_parliamentary_data_collection_endpoint(
    request: Request,
    opa_client: OPAClient = Depends(get_opa_client),
    _access_check = Depends(check_parliamentary_access)
):
    """Trigger parliamentary data collection (admin only)"""
    # Check if user has admin privileges
    if hasattr(request.state, 'policy_context'):
        user_data = request.state.policy_context.get('user', {})
        if user_data.get('role') != 'admin':
            raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        results = run_parliamentary_data_collection()
        return DataCollectionResultResponse(**results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Collection failed: {str(e)}")

@router.post("/collection/hansard/{hansard_id}/process")
async def process_hansard_record(
    hansard_id: int,
    request: Request,
    db: Session = Depends(get_db_session),
    _access_check = Depends(check_parliamentary_access)
):
    """Process a specific Hansard record to extract speeches"""
    # Check if user has appropriate privileges
    if hasattr(request.state, 'policy_context'):
        user_data = request.state.policy_context.get('user', {})
        if user_data.get('role') not in ['admin', 'researcher']:
            raise HTTPException(status_code=403, detail="Insufficient privileges")
    
    hansard = db.query(HansardRecord).filter_by(id=hansard_id).first()
    if not hansard:
        raise HTTPException(status_code=404, detail="Hansard record not found")
    
    if hansard.processed:
        return {"message": "Hansard record already processed", "speech_count": hansard.speech_count}
    
    scraper = ParliamentaryScraper()
    try:
        speech_count = scraper.process_hansard_xml(hansard.xml_url, hansard.id)
        return {"message": "Hansard record processed successfully", "speech_count": speech_count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

# Search and Analysis Endpoints
@router.get("/search/speeches")
async def search_speeches(
    query: str = Query(..., description="Search query for speech content"),
    speaker_name: Optional[str] = Query(None, description="Filter by speaker name"),
    speech_type: Optional[str] = Query(None, description="Filter by speech type"),
    date_from: Optional[date] = Query(None, description="Start date filter"),
    date_to: Optional[date] = Query(None, description="End date filter"),
    limit: int = Query(50, le=200, description="Maximum number of results"),
    db: Session = Depends(get_db_session),
    _access_check = Depends(check_parliamentary_access)
):
    """Search speeches by content and metadata"""
    query_obj = db.query(Speech).join(HansardRecord)
    
    # Text search in content
    query_obj = query_obj.filter(Speech.content.ilike(f"%{query}%"))
    
    if speaker_name:
        query_obj = query_obj.filter(Speech.speaker_name.ilike(f"%{speaker_name}%"))
    
    if speech_type:
        query_obj = query_obj.filter(Speech.speech_type == speech_type)
    
    if date_from:
        query_obj = query_obj.filter(HansardRecord.date >= date_from)
    
    if date_to:
        query_obj = query_obj.filter(HansardRecord.date <= date_to)
    
    speeches = query_obj.order_by(HansardRecord.date.desc()).limit(limit).all()
    
    return [SpeechResponse.from_orm(speech) for speech in speeches]

@router.get("/analytics/summary")
async def get_parliamentary_analytics_summary(
    db: Session = Depends(get_db_session),
    _access_check = Depends(check_parliamentary_access)
):
    """Get summary analytics for parliamentary data"""
    
    # Count statistics
    total_sessions = db.query(ParliamentarySession).count()
    total_hansard = db.query(HansardRecord).count()
    processed_hansard = db.query(HansardRecord).filter_by(processed=True).count()
    total_speeches = db.query(Speech).count()
    total_committees = db.query(CommitteeMeeting).count()
    
    # Recent activity
    recent_hansard = db.query(HansardRecord).order_by(
        HansardRecord.created_at.desc()
    ).limit(5).all()
    
    return {
        "statistics": {
            "total_sessions": total_sessions,
            "total_hansard_records": total_hansard,
            "processed_hansard_records": processed_hansard,
            "total_speeches": total_speeches,
            "total_committee_meetings": total_committees,
            "processing_rate": round((processed_hansard / total_hansard * 100), 2) if total_hansard > 0 else 0
        },
        "recent_hansard": [HansardRecordResponse.from_orm(record) for record in recent_hansard],
        "timestamp": datetime.utcnow().isoformat()
    }

# Policy Integration Endpoints
@router.get("/policy/health")
async def get_policy_health(
    opa_client: OPAClient = Depends(get_opa_client)
):
    """Get policy engine health status"""
    return opa_client.health_check()

@router.post("/policy/validate-access")
async def validate_policy_access(
    request: Request,
    endpoint: str,
    method: str = "GET",
    opa_client: OPAClient = Depends(get_opa_client)
):
    """Test policy-based access validation"""
    # Extract user data from request
    user_data = {"role": "anonymous", "authenticated": False}
    if hasattr(request.state, 'policy_context'):
        user_data = request.state.policy_context.get('user', user_data)
    
    request_data = {
        "endpoint": endpoint,
        "method": method,
        "requests_per_hour": 10,  # Example
        "country_code": "CA"
    }
    
    result = opa_client.check_api_access(user_data, request_data)
    return result