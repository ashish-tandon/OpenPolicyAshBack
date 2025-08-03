"""
Federal-specific API endpoints for MPs, bills, and committees
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from database import get_session_factory, create_engine_from_config, get_database_config
from database.models import (
    Representative, Bill, Jurisdiction, Committee, 
    BillSponsorship, CommitteeMembership, Vote,
    JurisdictionType, RepresentativeRole
)
from api.models import RepresentativeResponse, BillResponse, CommitteeResponse, VoteResponse

router = APIRouter(prefix="/api/federal", tags=["federal"])

# Database setup
config = get_database_config()
engine = create_engine_from_config(config.get_url())
SessionLocal = get_session_factory(engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/mps", response_model=List[RepresentativeResponse])
async def get_federal_mps(
    province: Optional[str] = Query(None, description="Filter by province code"),
    party: Optional[str] = Query(None, description="Filter by party"),
    search: Optional[str] = Query(None, description="Search by name or riding"),
    limit: int = Query(338, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """Get all federal MPs with optional filtering"""
    query = db.query(Representative).join(Jurisdiction).filter(
        Jurisdiction.jurisdiction_type == JurisdictionType.FEDERAL,
        Representative.role == RepresentativeRole.MP
    )
    
    if province:
        query = query.filter(Jurisdiction.province == province)
    
    if party:
        query = query.filter(Representative.party == party)
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (Representative.name.ilike(search_term)) |
            (Representative.district.ilike(search_term))
        )
    
    total = query.count()
    mps = query.offset(offset).limit(limit).all()
    
    return [RepresentativeResponse.from_orm(mp) for mp in mps]

@router.get("/mps/{mp_id}", response_model=RepresentativeResponse)
async def get_federal_mp(mp_id: UUID, db: Session = Depends(get_db)):
    """Get detailed information about a specific MP"""
    mp = db.query(Representative).filter(Representative.id == mp_id).first()
    
    if not mp:
        raise HTTPException(status_code=404, detail="MP not found")
    
    if mp.role != RepresentativeRole.MP:
        raise HTTPException(status_code=400, detail="Representative is not an MP")
    
    return RepresentativeResponse.from_orm(mp)

@router.get("/mps/{mp_id}/bills", response_model=List[BillResponse])
async def get_mp_bills(
    mp_id: UUID,
    status: Optional[str] = Query(None, description="Filter by bill status"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """Get bills sponsored by a specific MP"""
    query = db.query(Bill).join(BillSponsorship).filter(
        BillSponsorship.representative_id == mp_id
    )
    
    if status:
        query = query.filter(Bill.status == status)
    
    bills = query.offset(offset).limit(limit).all()
    
    return [BillResponse.from_orm(bill) for bill in bills]

@router.get("/mps/{mp_id}/votes", response_model=List[VoteResponse])
async def get_mp_votes(
    mp_id: UUID,
    bill_id: Optional[UUID] = Query(None, description="Filter by specific bill"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """Get voting record for a specific MP"""
    query = db.query(Vote).filter(Vote.representative_id == mp_id)
    
    if bill_id:
        query = query.filter(Vote.bill_id == bill_id)
    
    votes = query.order_by(Vote.date.desc()).offset(offset).limit(limit).all()
    
    return [VoteResponse.from_orm(vote) for vote in votes]

@router.get("/mps/{mp_id}/committees", response_model=List[CommitteeResponse])
async def get_mp_committees(
    mp_id: UUID,
    active_only: bool = Query(True, description="Show only active memberships"),
    db: Session = Depends(get_db)
):
    """Get committee memberships for a specific MP"""
    query = db.query(Committee).join(CommitteeMembership).filter(
        CommitteeMembership.representative_id == mp_id
    )
    
    if active_only:
        query = query.filter(CommitteeMembership.end_date.is_(None))
    
    committees = query.all()
    
    return [CommitteeResponse.from_orm(committee) for committee in committees]

@router.get("/bills", response_model=List[BillResponse])
async def get_federal_bills(
    status: Optional[str] = Query(None, description="Filter by status"),
    search: Optional[str] = Query(None, description="Search in title or identifier"),
    session: Optional[int] = Query(None, description="Parliamentary session number"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """Get all federal bills with filtering"""
    query = db.query(Bill).join(Jurisdiction).filter(
        Jurisdiction.jurisdiction_type == JurisdictionType.FEDERAL
    )
    
    if status:
        query = query.filter(Bill.status == status)
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (Bill.title.ilike(search_term)) |
            (Bill.identifier.ilike(search_term))
        )
    
    bills = query.order_by(Bill.introduced_date.desc()).offset(offset).limit(limit).all()
    
    return [BillResponse.from_orm(bill) for bill in bills]

@router.get("/committees", response_model=List[CommitteeResponse])
async def get_federal_committees(
    committee_type: Optional[str] = Query(None, description="Filter by committee type"),
    active_only: bool = Query(True, description="Show only active committees"),
    db: Session = Depends(get_db)
):
    """Get all federal committees"""
    query = db.query(Committee).join(Jurisdiction).filter(
        Jurisdiction.jurisdiction_type == JurisdictionType.FEDERAL
    )
    
    if committee_type:
        query = query.filter(Committee.committee_type == committee_type)
    
    committees = query.all()
    
    return [CommitteeResponse.from_orm(committee) for committee in committees]

@router.get("/stats")
async def get_federal_stats(db: Session = Depends(get_db)):
    """Get statistics about federal data"""
    mp_count = db.query(Representative).join(Jurisdiction).filter(
        Jurisdiction.jurisdiction_type == JurisdictionType.FEDERAL,
        Representative.role == RepresentativeRole.MP
    ).count()
    
    bill_count = db.query(Bill).join(Jurisdiction).filter(
        Jurisdiction.jurisdiction_type == JurisdictionType.FEDERAL
    ).count()
    
    committee_count = db.query(Committee).join(Jurisdiction).filter(
        Jurisdiction.jurisdiction_type == JurisdictionType.FEDERAL
    ).count()
    
    # Party breakdown
    party_counts = db.query(
        Representative.party,
        db.func.count(Representative.id).label('count')
    ).join(Jurisdiction).filter(
        Jurisdiction.jurisdiction_type == JurisdictionType.FEDERAL,
        Representative.role == RepresentativeRole.MP
    ).group_by(Representative.party).all()
    
    return {
        "total_mps": mp_count,
        "total_bills": bill_count,
        "total_committees": committee_count,
        "party_breakdown": {party: count for party, count in party_counts if party}
    }