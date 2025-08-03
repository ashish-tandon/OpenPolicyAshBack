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

from src.database.config import engine, SessionLocal, get_db
from src.database.models import (
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

# Create FastAPI app
app = FastAPI(
    title="OpenPolicy Database API",
    description="REST API for accessing Canadian civic data",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include scheduling router
app.include_router(scheduling_router, tags=["scheduling"])

# Include progress tracking router
from api.progress_api import router as progress_router
app.include_router(progress_router, tags=["progress"])

# Include phased loading router
from api.phased_loading_api import router as phased_loading_router
app.include_router(phased_loading_router, tags=["phased-loading"])

# Include GraphQL
from strawberry.fastapi import GraphQLRouter
graphql_app = GraphQLRouter(schema)
app.include_router(graphql_app, prefix="/graphql", tags=["graphql"])

# Rate limiting middleware
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    return await rate_limit_middleware(request, call_next)

# Security headers middleware
@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    return await add_security_headers(request, call_next)

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "OpenPolicy Database API"}

# Stats endpoint
@app.get("/stats", response_model=StatsResponse)
async def get_stats(db: Session = Depends(get_db)):
    """Get system statistics"""
    try:
        jurisdiction_count = db.query(Jurisdiction).count()
        representative_count = db.query(Representative).count()
        bill_count = db.query(Bill).count()
        event_count = db.query(Event).count()
        
        return StatsResponse(
            jurisdictions=jurisdiction_count,
            representatives=representative_count,
            bills=bill_count,
            events=event_count
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# Jurisdictions endpoints
@app.get("/jurisdictions", response_model=List[JurisdictionResponse])
async def get_jurisdictions(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    jurisdiction_type: Optional[JurisdictionType] = Query(None),
    db: Session = Depends(get_db)
):
    """Get jurisdictions with optional filtering"""
    try:
        query = db.query(Jurisdiction)
        
        if jurisdiction_type:
            query = query.filter(Jurisdiction.jurisdiction_type == jurisdiction_type)
        
        jurisdictions = query.offset(skip).limit(limit).all()
        return [JurisdictionResponse.from_orm(j) for j in jurisdictions]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/jurisdictions/{jurisdiction_id}", response_model=JurisdictionResponse)
async def get_jurisdiction(
    jurisdiction_id: str = Path(..., description="Jurisdiction ID"),
    db: Session = Depends(get_db)
):
    """Get a specific jurisdiction by ID"""
    try:
        jurisdiction = db.query(Jurisdiction).filter(Jurisdiction.id == jurisdiction_id).first()
        if not jurisdiction:
            raise HTTPException(status_code=404, detail="Jurisdiction not found")
        return JurisdictionResponse.from_orm(jurisdiction)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# Representatives endpoints
@app.get("/representatives", response_model=List[RepresentativeResponse])
async def get_representatives(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    jurisdiction_id: Optional[str] = Query(None),
    party: Optional[str] = Query(None),
    role: Optional[RepresentativeRole] = Query(None),
    db: Session = Depends(get_db)
):
    """Get representatives with optional filtering"""
    try:
        query = db.query(Representative)
        
        if jurisdiction_id:
            query = query.filter(Representative.jurisdiction_id == jurisdiction_id)
        if party:
            query = query.filter(Representative.party.ilike(f"%{party}%"))
        if role:
            query = query.filter(Representative.role == role)
        
        representatives = query.offset(skip).limit(limit).all()
        return [RepresentativeResponse.from_orm(r) for r in representatives]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/representatives/{representative_id}", response_model=RepresentativeResponse)
async def get_representative(
    representative_id: str = Path(..., description="Representative ID"),
    db: Session = Depends(get_db)
):
    """Get a specific representative by ID"""
    try:
        representative = db.query(Representative).filter(Representative.id == representative_id).first()
        if not representative:
            raise HTTPException(status_code=404, detail="Representative not found")
        return RepresentativeResponse.from_orm(representative)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# Bills endpoints
@app.get("/bills", response_model=List[BillResponse])
async def get_bills(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    jurisdiction_id: Optional[str] = Query(None),
    status: Optional[BillStatus] = Query(None),
    db: Session = Depends(get_db)
):
    """Get bills with optional filtering"""
    try:
        query = db.query(Bill)
        
        if jurisdiction_id:
            query = query.filter(Bill.jurisdiction_id == jurisdiction_id)
        if status:
            query = query.filter(Bill.status == status)
        
        bills = query.offset(skip).limit(limit).all()
        return [BillResponse.from_orm(b) for b in bills]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/bills/{bill_id}", response_model=BillResponse)
async def get_bill(
    bill_id: str = Path(..., description="Bill ID"),
    db: Session = Depends(get_db)
):
    """Get a specific bill by ID"""
    try:
        bill = db.query(Bill).filter(Bill.id == bill_id).first()
        if not bill:
            raise HTTPException(status_code=404, detail="Bill not found")
        return BillResponse.from_orm(bill)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# Committees endpoints
@app.get("/committees", response_model=List[CommitteeResponse])
async def get_committees(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    jurisdiction_id: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Get committees with optional filtering"""
    try:
        query = db.query(Committee)
        
        if jurisdiction_id:
            query = query.filter(Committee.jurisdiction_id == jurisdiction_id)
        
        committees = query.offset(skip).limit(limit).all()
        return [CommitteeResponse.from_orm(c) for c in committees]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/committees/{committee_id}", response_model=CommitteeResponse)
async def get_committee(
    committee_id: str = Path(..., description="Committee ID"),
    db: Session = Depends(get_db)
):
    """Get a specific committee by ID"""
    try:
        committee = db.query(Committee).filter(Committee.id == committee_id).first()
        if not committee:
            raise HTTPException(status_code=404, detail="Committee not found")
        return CommitteeResponse.from_orm(committee)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# Events endpoints
@app.get("/events", response_model=List[EventResponse])
async def get_events(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    jurisdiction_id: Optional[str] = Query(None),
    event_type: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Get events with optional filtering"""
    try:
        query = db.query(Event)
        
        if jurisdiction_id:
            query = query.filter(Event.jurisdiction_id == jurisdiction_id)
        if event_type:
            query = query.filter(Event.event_type == event_type)
        
        events = query.offset(skip).limit(limit).all()
        return [EventResponse.from_orm(e) for e in events]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# Votes endpoints
@app.get("/votes", response_model=List[VoteResponse])
async def get_votes(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    event_id: Optional[str] = Query(None),
    bill_id: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Get votes with optional filtering"""
    try:
        query = db.query(Vote)
        
        if event_id:
            query = query.filter(Vote.event_id == event_id)
        if bill_id:
            query = query.filter(Vote.bill_id == bill_id)
        
        votes = query.offset(skip).limit(limit).all()
        return [VoteResponse.from_orm(v) for v in votes]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# AI Analysis endpoints
@app.post("/ai/analyze-bill/{bill_id}")
async def analyze_bill(
    bill_id: str = Path(..., description="Bill ID"),
    db: Session = Depends(get_db)
):
    """Analyze a bill using AI"""
    try:
        bill = db.query(Bill).filter(Bill.id == bill_id).first()
        if not bill:
            raise HTTPException(status_code=404, detail="Bill not found")
        
        # TODO: Implement AI analysis
        return {"message": "AI analysis endpoint - implementation pending"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis error: {str(e)}")

@app.post("/ai/federal-briefing")
async def generate_federal_briefing():
    """Generate federal briefing using AI"""
    try:
        # TODO: Implement federal briefing generation
        return {"message": "Federal briefing endpoint - implementation pending"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Briefing error: {str(e)}")

# Data enrichment endpoints
@app.post("/enrich/bill/{bill_id}")
async def enrich_bill(
    bill_id: str = Path(..., description="Bill ID"),
    db: Session = Depends(get_db)
):
    """Enrich bill data with additional information"""
    try:
        bill = db.query(Bill).filter(Bill.id == bill_id).first()
        if not bill:
            raise HTTPException(status_code=404, detail="Bill not found")
        
        # TODO: Implement bill enrichment
        return {"message": "Bill enrichment endpoint - implementation pending"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Enrichment error: {str(e)}")

# Federal priority endpoints
@app.get("/federal/priority-metrics")
async def get_federal_priority_metrics():
    """Get federal priority metrics"""
    try:
        # TODO: Implement federal priority metrics
        return {"message": "Federal priority metrics endpoint - implementation pending"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Metrics error: {str(e)}")

@app.post("/federal/run-checks")
async def run_federal_checks():
    """Run federal priority checks"""
    try:
        # TODO: Implement federal checks
        return {"message": "Federal checks endpoint - implementation pending"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Checks error: {str(e)}")

# Authentication endpoints
@app.get("/auth/token")
async def get_auth_token():
    """Get authentication token"""
    # TODO: Implement proper authentication
    return {"message": "Authentication endpoint - implementation pending"}

# Search endpoint
@app.get("/search")
async def search(
    q: str = Query(..., description="Search query"),
    db: Session = Depends(get_db)
):
    """Search across all entities"""
    try:
        # TODO: Implement search functionality
        return {"message": "Search endpoint - implementation pending", "query": q}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)