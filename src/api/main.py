"""
OpenPolicy Database REST API

This module provides a FastAPI-based REST API for accessing Canadian civic data
from the OpenPolicy Database.
"""

from fastapi import FastAPI, HTTPException, Depends, Query, Path, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import sys
import time
from pathlib import Path as PathLib

# Add src to path
sys.path.insert(0, str(PathLib(__file__).parent.parent))

from database import (
    get_database_config, create_engine_from_config, get_session_factory,
    Jurisdiction, Representative, Bill, Committee, Event, Vote,
    JurisdictionType, RepresentativeRole, BillStatus
)
from api.models import (
    JurisdictionResponse, RepresentativeResponse, BillResponse,
    CommitteeResponse, EventResponse, VoteResponse, StatsResponse
)
from api.scheduling import router as scheduling_router
from api.rate_limiting import rate_limit_middleware, add_security_headers, get_current_user
from api.graphql_schema import schema
from api.progress_api import router as progress_router
from ai_services import ai_analyzer, data_enricher
import strawberry
from strawberry.fastapi import GraphQLRouter

# Create FastAPI app
app = FastAPI(
    title="OpenPolicy Database API",
    description="REST API for accessing Canadian civic data including representatives, bills, committees, and more.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include scheduling router
app.include_router(scheduling_router, tags=["scheduling"])

# Include progress tracking router
app.include_router(progress_router, tags=["progress"])

# Include phased loading router
from api.phased_loading_api import router as phased_loading_router
app.include_router(phased_loading_router, tags=["phased-loading"])

# Add GraphQL endpoint
graphql_app = GraphQLRouter(schema)
app.include_router(graphql_app, prefix="/graphql", tags=["graphql"])

# Add middleware for rate limiting and security
app.middleware("http")(add_security_headers)

@app.middleware("http")
async def rate_limiting_middleware(request: Request, call_next):
    await rate_limit_middleware(request)
    response = await call_next(request)
    return response

# Database setup
config = get_database_config()
engine = create_engine_from_config(config.get_url())
SessionLocal = get_session_factory(engine)

def get_db():
    """Database dependency"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "OpenPolicy Database API"}

# Statistics endpoint
@app.get("/stats", response_model=StatsResponse)
async def get_statistics(db: Session = Depends(get_db)):
    """Get database statistics"""
    try:
        stats = {
            "total_jurisdictions": db.query(Jurisdiction).count(),
            "federal_jurisdictions": db.query(Jurisdiction).filter_by(jurisdiction_type=JurisdictionType.FEDERAL).count(),
            "provincial_jurisdictions": db.query(Jurisdiction).filter_by(jurisdiction_type=JurisdictionType.PROVINCIAL).count(),
            "municipal_jurisdictions": db.query(Jurisdiction).filter_by(jurisdiction_type=JurisdictionType.MUNICIPAL).count(),
            "total_representatives": db.query(Representative).count(),
            "total_bills": db.query(Bill).count(),
            "total_committees": db.query(Committee).count(),
            "total_events": db.query(Event).count(),
            "total_votes": db.query(Vote).count()
        }
        
        # Representative breakdown by role
        for role in RepresentativeRole:
            count = db.query(Representative).filter_by(role=role).count()
            stats[f"representatives_{role.value.lower()}"] = count
        
        return StatsResponse(**stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching statistics: {str(e)}")

# Jurisdiction endpoints
@app.get("/jurisdictions", response_model=List[JurisdictionResponse])
async def get_jurisdictions(
    jurisdiction_type: Optional[JurisdictionType] = Query(None, description="Filter by jurisdiction type"),
    province: Optional[str] = Query(None, description="Filter by province code"),
    limit: int = Query(100, ge=1, le=1000, description="Number of results to return"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    db: Session = Depends(get_db)
):
    """Get list of jurisdictions"""
    query = db.query(Jurisdiction)
    
    if jurisdiction_type:
        query = query.filter(Jurisdiction.jurisdiction_type == jurisdiction_type)
    
    if province:
        query = query.filter(Jurisdiction.province == province.upper())
    
    jurisdictions = query.offset(offset).limit(limit).all()
    return [JurisdictionResponse.from_orm(j) for j in jurisdictions]

@app.get("/jurisdictions/{jurisdiction_id}", response_model=JurisdictionResponse)
async def get_jurisdiction(
    jurisdiction_id: str = Path(..., description="Jurisdiction ID"),
    db: Session = Depends(get_db)
):
    """Get a specific jurisdiction"""
    jurisdiction = db.query(Jurisdiction).filter(Jurisdiction.id == jurisdiction_id).first()
    if not jurisdiction:
        raise HTTPException(status_code=404, detail="Jurisdiction not found")
    return JurisdictionResponse.from_orm(jurisdiction)

# Representative endpoints
@app.get("/representatives", response_model=List[RepresentativeResponse])
async def get_representatives(
    jurisdiction_id: Optional[str] = Query(None, description="Filter by jurisdiction ID"),
    jurisdiction_type: Optional[JurisdictionType] = Query(None, description="Filter by jurisdiction type"),
    province: Optional[str] = Query(None, description="Filter by province"),
    party: Optional[str] = Query(None, description="Filter by political party"),
    role: Optional[RepresentativeRole] = Query(None, description="Filter by role"),
    district: Optional[str] = Query(None, description="Filter by district"),
    search: Optional[str] = Query(None, description="Search by name"),
    limit: int = Query(100, ge=1, le=1000, description="Number of results to return"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    db: Session = Depends(get_db)
):
    """Get list of representatives"""
    query = db.query(Representative).join(Jurisdiction)
    
    if jurisdiction_id:
        query = query.filter(Representative.jurisdiction_id == jurisdiction_id)
    
    if jurisdiction_type:
        query = query.filter(Jurisdiction.jurisdiction_type == jurisdiction_type)
    
    if province:
        query = query.filter(Jurisdiction.province == province.upper())
    
    if party:
        query = query.filter(Representative.party.ilike(f"%{party}%"))
    
    if role:
        query = query.filter(Representative.role == role)
    
    if district:
        query = query.filter(Representative.district.ilike(f"%{district}%"))
    
    if search:
        query = query.filter(Representative.name.ilike(f"%{search}%"))
    
    representatives = query.offset(offset).limit(limit).all()
    return [RepresentativeResponse.from_orm(r) for r in representatives]

@app.get("/representatives/{representative_id}", response_model=RepresentativeResponse)
async def get_representative(
    representative_id: str = Path(..., description="Representative ID"),
    db: Session = Depends(get_db)
):
    """Get a specific representative"""
    representative = db.query(Representative).filter(Representative.id == representative_id).first()
    if not representative:
        raise HTTPException(status_code=404, detail="Representative not found")
    return RepresentativeResponse.from_orm(representative)

# Bill endpoints
@app.get("/bills", response_model=List[BillResponse])
async def get_bills(
    jurisdiction_id: Optional[str] = Query(None, description="Filter by jurisdiction ID"),
    status: Optional[BillStatus] = Query(None, description="Filter by bill status"),
    search: Optional[str] = Query(None, description="Search in title and summary"),
    limit: int = Query(100, ge=1, le=1000, description="Number of results to return"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    db: Session = Depends(get_db)
):
    """Get list of bills"""
    query = db.query(Bill)
    
    if jurisdiction_id:
        query = query.filter(Bill.jurisdiction_id == jurisdiction_id)
    
    if status:
        query = query.filter(Bill.status == status)
    
    if search:
        query = query.filter(
            (Bill.title.ilike(f"%{search}%")) |
            (Bill.summary.ilike(f"%{search}%"))
        )
    
    bills = query.offset(offset).limit(limit).all()
    return [BillResponse.from_orm(b) for b in bills]

@app.get("/bills/{bill_id}", response_model=BillResponse)
async def get_bill(
    bill_id: str = Path(..., description="Bill ID"),
    db: Session = Depends(get_db)
):
    """Get a specific bill"""
    bill = db.query(Bill).filter(Bill.id == bill_id).first()
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")
    return BillResponse.from_orm(bill)

# Committee endpoints
@app.get("/committees", response_model=List[CommitteeResponse])
async def get_committees(
    jurisdiction_id: Optional[str] = Query(None, description="Filter by jurisdiction ID"),
    committee_type: Optional[str] = Query(None, description="Filter by committee type"),
    search: Optional[str] = Query(None, description="Search in name and description"),
    limit: int = Query(100, ge=1, le=1000, description="Number of results to return"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    db: Session = Depends(get_db)
):
    """Get list of committees"""
    query = db.query(Committee)
    
    if jurisdiction_id:
        query = query.filter(Committee.jurisdiction_id == jurisdiction_id)
    
    if committee_type:
        query = query.filter(Committee.committee_type.ilike(f"%{committee_type}%"))
    
    if search:
        query = query.filter(
            (Committee.name.ilike(f"%{search}%")) |
            (Committee.description.ilike(f"%{search}%"))
        )
    
    committees = query.offset(offset).limit(limit).all()
    return [CommitteeResponse.from_orm(c) for c in committees]

@app.get("/committees/{committee_id}", response_model=CommitteeResponse)
async def get_committee(
    committee_id: str = Path(..., description="Committee ID"),
    db: Session = Depends(get_db)
):
    """Get a specific committee"""
    committee = db.query(Committee).filter(Committee.id == committee_id).first()
    if not committee:
        raise HTTPException(status_code=404, detail="Committee not found")
    return CommitteeResponse.from_orm(committee)

# Event endpoints
@app.get("/events", response_model=List[EventResponse])
async def get_events(
    jurisdiction_id: Optional[str] = Query(None, description="Filter by jurisdiction ID"),
    bill_id: Optional[str] = Query(None, description="Filter by bill ID"),
    committee_id: Optional[str] = Query(None, description="Filter by committee ID"),
    limit: int = Query(100, ge=1, le=1000, description="Number of results to return"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    db: Session = Depends(get_db)
):
    """Get list of events"""
    query = db.query(Event)
    
    if jurisdiction_id:
        query = query.filter(Event.jurisdiction_id == jurisdiction_id)
    
    if bill_id:
        query = query.filter(Event.bill_id == bill_id)
    
    if committee_id:
        query = query.filter(Event.committee_id == committee_id)
    
    events = query.offset(offset).limit(limit).all()
    return [EventResponse.from_orm(e) for e in events]

# Vote endpoints
@app.get("/votes", response_model=List[VoteResponse])
async def get_votes(
    event_id: Optional[str] = Query(None, description="Filter by event ID"),
    bill_id: Optional[str] = Query(None, description="Filter by bill ID"),
    representative_id: Optional[str] = Query(None, description="Filter by representative ID"),
    limit: int = Query(100, ge=1, le=1000, description="Number of results to return"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    db: Session = Depends(get_db)
):
    """Get list of votes"""
    query = db.query(Vote)
    
    if event_id:
        query = query.filter(Vote.event_id == event_id)
    
    if bill_id:
        query = query.filter(Vote.bill_id == bill_id)
    
    if representative_id:
        query = query.filter(Vote.representative_id == representative_id)
    
    votes = query.offset(offset).limit(limit).all()
    return [VoteResponse.from_orm(v) for v in votes]

# AI and Data Enrichment Endpoints
@app.post("/ai/analyze-bill/{bill_id}")
async def analyze_bill_with_ai(
    bill_id: str = Path(..., description="Bill ID"),
    user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate AI analysis for a specific bill"""
    bill = db.query(Bill).filter(Bill.id == bill_id).first()
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")
    
    analysis = await ai_analyzer.summarize_bill(bill)
    return analysis

@app.post("/ai/federal-briefing")
async def get_federal_briefing(
    user: Dict[str, Any] = Depends(get_current_user)
):
    """Get daily AI briefing for federal parliamentary activity"""
    briefing = await ai_analyzer.generate_daily_briefing()
    return briefing

@app.post("/enrich/bill/{bill_id}")
async def enrich_bill_data(
    bill_id: str = Path(..., description="Bill ID"),
    user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Enrich bill data with external sources"""
    bill = db.query(Bill).filter(Bill.id == bill_id).first()
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")
    
    enrichment = await data_enricher.enrich_bill_data(bill)
    return enrichment

@app.get("/federal/priority-metrics")
async def get_federal_priority_metrics():
    """Get federal bills priority monitoring metrics"""
    from federal_priority import federal_monitor
    return federal_monitor.get_federal_priority_metrics()

@app.post("/federal/run-checks")
async def run_federal_checks():
    """Run comprehensive federal bills quality checks"""
    from federal_priority import federal_monitor
    report = federal_monitor.run_comprehensive_check()
    return {
        "report_id": f"federal_check_{int(time.time())}",
        "total_bills": report.total_bills,
        "checks_performed": report.checks_performed,
        "passed_checks": report.passed_checks,
        "warnings": report.warnings,
        "failures": report.failures,
        "recommendations": report.recommendations,
        "generated_at": report.checked_at.isoformat()
    }

@app.get("/auth/token")
async def get_auth_token(api_key: str = Query(..., description="API key for authentication")):
    """Get JWT token using API key"""
    from api.rate_limiting import authenticate_api_key
    return await authenticate_api_key(api_key)

# Enhanced search endpoint
@app.get("/search")
async def universal_search(
    q: str = Query(..., description="Search query"),
    type: Optional[str] = Query(None, description="Search type: jurisdictions, representatives, bills, all"),
    limit: int = Query(10, ge=1, le=100, description="Number of results per type"),
    db: Session = Depends(get_db)
):
    """Universal search across all data types"""
    results = {}
    
    if type is None or type == "all" or type == "jurisdictions":
        jurisdictions = db.query(Jurisdiction).filter(
            Jurisdiction.name.ilike(f"%{q}%")
        ).limit(limit).all()
        results["jurisdictions"] = [JurisdictionResponse.from_orm(j) for j in jurisdictions]
    
    if type is None or type == "all" or type == "representatives":
        representatives = db.query(Representative).filter(
            Representative.name.ilike(f"%{q}%")
        ).limit(limit).all()
        results["representatives"] = [RepresentativeResponse.from_orm(r) for r in representatives]
    
    if type is None or type == "all" or type == "bills":
        bills = db.query(Bill).filter(
            (Bill.title.ilike(f"%{q}%")) |
            (Bill.summary.ilike(f"%{q}%")) |
            (Bill.identifier.ilike(f"%{q}%"))
        ).limit(limit).all()
        results["bills"] = [BillResponse.from_orm(b) for b in bills]
    
    return {
        "query": q,
        "results": results,
        "total_results": sum(len(v) for v in results.values()) if isinstance(results, dict) else 0
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)