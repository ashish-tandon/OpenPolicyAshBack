"""
GraphQL Schema for OpenPolicy Backend Ash Aug 2025

Provides a powerful GraphQL interface for complex queries and data relationships.
"""

import strawberry
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session

from database import (
    Jurisdiction, Representative, Bill, Committee, Event, Vote,
    JurisdictionType, RepresentativeRole, BillStatus,
    get_session_factory, get_database_config, create_engine_from_config
)
from federal_priority import federal_monitor
from ai_services import ai_analyzer, data_enricher

# Database setup
config = get_database_config()
engine = create_engine_from_config(config.get_url())
SessionLocal = get_session_factory(engine)

def get_db():
    """Get database session"""
    return SessionLocal()

# GraphQL Types
@strawberry.type
class JurisdictionType_GQL:
    id: str
    name: str
    jurisdiction_type: str
    province: Optional[str]
    url: Optional[str]
    api_url: Optional[str]
    created_at: datetime
    updated_at: datetime

@strawberry.type
class RepresentativeType_GQL:
    id: str
    name: str
    role: str
    party: Optional[str]
    district: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    jurisdiction_id: str
    created_at: datetime
    updated_at: datetime

@strawberry.type
class BillType_GQL:
    id: str
    identifier: str
    title: str
    summary: Optional[str]
    status: str
    jurisdiction_id: str
    created_at: datetime
    updated_at: datetime

@strawberry.type
class CommitteeType_GQL:
    id: str
    name: str
    description: Optional[str]
    committee_type: Optional[str]
    jurisdiction_id: str
    created_at: datetime
    updated_at: datetime

@strawberry.type
class EventType_GQL:
    id: str
    name: str
    event_type: Optional[str]
    description: Optional[str]
    date: Optional[datetime]
    jurisdiction_id: str
    bill_id: Optional[str]
    committee_id: Optional[str]
    created_at: datetime
    updated_at: datetime

@strawberry.type
class VoteType_GQL:
    id: str
    vote_type: str
    result: Optional[str]
    date: Optional[datetime]
    event_id: str
    bill_id: Optional[str]
    representative_id: str
    created_at: datetime
    updated_at: datetime

@strawberry.type
class FederalMonitoringType_GQL:
    total_federal_bills: int
    recent_updates_7d: int
    active_bills: int
    monitoring_enabled: bool
    last_check: str
    priority_status: str

@strawberry.type
class AIAnalysisType_GQL:
    bill_id: str
    executive_summary: Optional[str]
    key_provisions: List[str]
    impact_analysis: Optional[str]
    controversy_level: Optional[str]
    public_interest: Optional[str]
    confidence_score: Optional[float]
    generated_at: str

@strawberry.type
class DataEnrichmentType_GQL:
    bill_id: str
    parliamentary_link: Optional[str]
    openparliament_link: Optional[str]
    stakeholders: List[str]
    sources: List[str]
    enriched_at: str

@strawberry.type
class StatsType_GQL:
    total_jurisdictions: int
    federal_jurisdictions: int
    provincial_jurisdictions: int
    municipal_jurisdictions: int
    total_representatives: int
    total_bills: int
    total_committees: int
    total_events: int
    total_votes: int

# Input Types
@strawberry.input
class JurisdictionFilterInput:
    jurisdiction_type: Optional[str] = None
    province: Optional[str] = None

@strawberry.input
class RepresentativeFilterInput:
    jurisdiction_id: Optional[str] = None
    jurisdiction_type: Optional[str] = None
    province: Optional[str] = None
    party: Optional[str] = None
    role: Optional[str] = None
    search: Optional[str] = None

@strawberry.input
class BillFilterInput:
    jurisdiction_id: Optional[str] = None
    jurisdiction_type: Optional[str] = None
    status: Optional[str] = None
    search: Optional[str] = None
    federal_only: Optional[bool] = None

@strawberry.input
class PaginationInput:
    limit: int = 100
    offset: int = 0

@strawberry.type
class SearchResultType:
    jurisdictions: List[JurisdictionType_GQL]
    representatives: List[RepresentativeType_GQL]
    bills: List[BillType_GQL]
    committees: List[CommitteeType_GQL]

# Resolvers
@strawberry.type
class Query:
    
    @strawberry.field
    def jurisdictions(
        self, 
        filters: Optional[JurisdictionFilterInput] = None,
        pagination: Optional[PaginationInput] = None
    ) -> List[JurisdictionType_GQL]:
        """Get jurisdictions with filtering and pagination"""
        db = get_db()
        try:
            query = db.query(Jurisdiction)
            
            if filters:
                if filters.jurisdiction_type:
                    query = query.filter(Jurisdiction.jurisdiction_type == filters.jurisdiction_type)
                if filters.province:
                    query = query.filter(Jurisdiction.province == filters.province.upper())
            
            if pagination:
                query = query.offset(pagination.offset).limit(pagination.limit)
            
            jurisdictions = query.all()
            
            return [JurisdictionType_GQL(
                id=j.id,
                name=j.name,
                jurisdiction_type=j.jurisdiction_type.value,
                province=j.province,
                url=j.url,
                api_url=j.api_url,
                created_at=j.created_at,
                updated_at=j.updated_at
            ) for j in jurisdictions]
        finally:
            db.close()
    
    @strawberry.field
    def representatives(
        self,
        filters: Optional[RepresentativeFilterInput] = None,
        pagination: Optional[PaginationInput] = None
    ) -> List[RepresentativeType_GQL]:
        """Get representatives with advanced filtering"""
        db = get_db()
        try:
            query = db.query(Representative).join(Jurisdiction)
            
            if filters:
                if filters.jurisdiction_id:
                    query = query.filter(Representative.jurisdiction_id == filters.jurisdiction_id)
                if filters.jurisdiction_type:
                    query = query.filter(Jurisdiction.jurisdiction_type == filters.jurisdiction_type)
                if filters.province:
                    query = query.filter(Jurisdiction.province == filters.province.upper())
                if filters.party:
                    query = query.filter(Representative.party.ilike(f"%{filters.party}%"))
                if filters.role:
                    query = query.filter(Representative.role == filters.role)
                if filters.search:
                    query = query.filter(Representative.name.ilike(f"%{filters.search}%"))
            
            if pagination:
                query = query.offset(pagination.offset).limit(pagination.limit)
            
            representatives = query.all()
            
            return [RepresentativeType_GQL(
                id=r.id,
                name=r.name,
                role=r.role.value if hasattr(r.role, 'value') else r.role,
                party=r.party,
                district=r.district,
                email=r.email,
                phone=r.phone,
                jurisdiction_id=r.jurisdiction_id,
                created_at=r.created_at,
                updated_at=r.updated_at
            ) for r in representatives]
        finally:
            db.close()
    
    @strawberry.field
    def bills(
        self,
        filters: Optional[BillFilterInput] = None,
        pagination: Optional[PaginationInput] = None
    ) -> List[BillType_GQL]:
        """Get bills with comprehensive filtering"""
        db = get_db()
        try:
            query = db.query(Bill)
            
            if filters:
                if filters.jurisdiction_id:
                    query = query.filter(Bill.jurisdiction_id == filters.jurisdiction_id)
                if filters.jurisdiction_type:
                    query = query.join(Jurisdiction).filter(
                        Jurisdiction.jurisdiction_type == filters.jurisdiction_type
                    )
                if filters.status:
                    query = query.filter(Bill.status == filters.status)
                if filters.search:
                    query = query.filter(
                        (Bill.title.ilike(f"%{filters.search}%")) |
                        (Bill.summary.ilike(f"%{filters.search}%")) |
                        (Bill.identifier.ilike(f"%{filters.search}%"))
                    )
                if filters.federal_only:
                    query = query.join(Jurisdiction).filter(
                        Jurisdiction.jurisdiction_type == JurisdictionType.FEDERAL
                    )
            
            if pagination:
                query = query.offset(pagination.offset).limit(pagination.limit)
            
            bills = query.all()
            
            return [BillType_GQL(
                id=b.id,
                identifier=b.identifier,
                title=b.title,
                summary=b.summary,
                status=b.status.value if hasattr(b.status, 'value') else b.status,
                jurisdiction_id=b.jurisdiction_id,
                created_at=b.created_at,
                updated_at=b.updated_at
            ) for b in bills]
        finally:
            db.close()
    
    @strawberry.field
    def jurisdiction_by_id(self, id: str) -> Optional[JurisdictionType_GQL]:
        """Get jurisdiction by ID"""
        db = get_db()
        try:
            jurisdiction = db.query(Jurisdiction).filter(Jurisdiction.id == id).first()
            if not jurisdiction:
                return None
                
            return JurisdictionType_GQL(
                id=jurisdiction.id,
                name=jurisdiction.name,
                jurisdiction_type=jurisdiction.jurisdiction_type.value,
                province=jurisdiction.province,
                url=jurisdiction.url,
                api_url=jurisdiction.api_url,
                created_at=jurisdiction.created_at,
                updated_at=jurisdiction.updated_at
            )
        finally:
            db.close()
    
    @strawberry.field
    def bill_by_id(self, id: str) -> Optional[BillType_GQL]:
        """Get bill by ID"""
        db = get_db()
        try:
            bill = db.query(Bill).filter(Bill.id == id).first()
            if not bill:
                return None
                
            return BillType_GQL(
                id=bill.id,
                identifier=bill.identifier,
                title=bill.title,
                summary=bill.summary,
                status=bill.status.value if hasattr(bill.status, 'value') else bill.status,
                jurisdiction_id=bill.jurisdiction_id,
                created_at=bill.created_at,
                updated_at=bill.updated_at
            )
        finally:
            db.close()
    
    @strawberry.field
    async def federal_monitoring(self) -> FederalMonitoringType_GQL:
        """Get federal bills monitoring status"""
        metrics = federal_monitor.get_federal_priority_metrics()
        
        return FederalMonitoringType_GQL(
            total_federal_bills=metrics.get("total_federal_bills", 0),
            recent_updates_7d=metrics.get("recent_updates_7d", 0),
            active_bills=metrics.get("active_bills", 0),
            monitoring_enabled=metrics.get("monitoring_enabled", False),
            last_check=metrics.get("last_check", ""),
            priority_status=metrics.get("priority_status", "unknown")
        )
    
    @strawberry.field
    async def ai_analysis(self, bill_id: str) -> Optional[AIAnalysisType_GQL]:
        """Get AI analysis for a bill"""
        db = get_db()
        try:
            bill = db.query(Bill).filter(Bill.id == bill_id).first()
            if not bill:
                return None
            
            analysis = await ai_analyzer.summarize_bill(bill)
            if "error" in analysis:
                return None
            
            return AIAnalysisType_GQL(
                bill_id=bill_id,
                executive_summary=analysis.get("executive_summary"),
                key_provisions=analysis.get("key_provisions", []),
                impact_analysis=analysis.get("impact_analysis"),
                controversy_level=analysis.get("controversy_level"),
                public_interest=analysis.get("public_interest"),
                confidence_score=analysis.get("confidence_score"),
                generated_at=analysis.get("generated_at", "")
            )
        finally:
            db.close()
    
    @strawberry.field
    async def data_enrichment(self, bill_id: str) -> Optional[DataEnrichmentType_GQL]:
        """Get data enrichment for a bill"""
        db = get_db()
        try:
            bill = db.query(Bill).filter(Bill.id == bill_id).first()
            if not bill:
                return None
            
            enrichment = await data_enricher.enrich_bill_data(bill)
            if "error" in enrichment:
                return None
            
            return DataEnrichmentType_GQL(
                bill_id=bill_id,
                parliamentary_link=enrichment.get("parliamentary_link"),
                openparliament_link=enrichment.get("openparliament_link"),
                stakeholders=enrichment.get("stakeholders", []),
                sources=enrichment.get("sources", []),
                enriched_at=enrichment.get("enriched_at", "")
            )
        finally:
            db.close()
    
    @strawberry.field
    def stats(self) -> StatsType_GQL:
        """Get comprehensive database statistics"""
        db = get_db()
        try:
            return StatsType_GQL(
                total_jurisdictions=db.query(Jurisdiction).count(),
                federal_jurisdictions=db.query(Jurisdiction).filter_by(jurisdiction_type=JurisdictionType.FEDERAL).count(),
                provincial_jurisdictions=db.query(Jurisdiction).filter_by(jurisdiction_type=JurisdictionType.PROVINCIAL).count(),
                municipal_jurisdictions=db.query(Jurisdiction).filter_by(jurisdiction_type=JurisdictionType.MUNICIPAL).count(),
                total_representatives=db.query(Representative).count(),
                total_bills=db.query(Bill).count(),
                total_committees=db.query(Committee).count(),
                total_events=db.query(Event).count(),
                total_votes=db.query(Vote).count()
            )
        finally:
            db.close()
    
    @strawberry.field
    def search_all(
        self, 
        query: str, 
        pagination: Optional[PaginationInput] = None
    ) -> SearchResultType:
        """Universal search across all entities"""
        db = get_db()
        try:
            results = SearchResultType(
                jurisdictions=[],
                representatives=[],
                bills=[],
                committees=[]
            )
            
            # Search jurisdictions
            jurisdictions = db.query(Jurisdiction).filter(
                Jurisdiction.name.ilike(f"%{query}%")
            ).limit(10).all()
            
            results.jurisdictions = [JurisdictionType_GQL(
                id=j.id,
                name=j.name,
                jurisdiction_type=j.jurisdiction_type.value,
                province=j.province,
                url=j.url,
                api_url=j.api_url,
                created_at=j.created_at,
                updated_at=j.updated_at
            ) for j in jurisdictions]
            
            # Search representatives
            representatives = db.query(Representative).filter(
                Representative.name.ilike(f"%{query}%")
            ).limit(10).all()
            
            results.representatives = [RepresentativeType_GQL(
                id=r.id,
                name=r.name,
                role=r.role.value if hasattr(r.role, 'value') else r.role,
                party=r.party,
                district=r.district,
                email=r.email,
                phone=r.phone,
                jurisdiction_id=r.jurisdiction_id,
                created_at=r.created_at,
                updated_at=r.updated_at
            ) for r in representatives]
            
            # Search bills
            bills = db.query(Bill).filter(
                (Bill.title.ilike(f"%{query}%")) |
                (Bill.summary.ilike(f"%{query}%")) |
                (Bill.identifier.ilike(f"%{query}%"))
            ).limit(10).all()
            
            results.bills = [BillType_GQL(
                id=b.id,
                identifier=b.identifier,
                title=b.title,
                summary=b.summary,
                status=b.status.value if hasattr(b.status, 'value') else b.status,
                jurisdiction_id=b.jurisdiction_id,
                created_at=b.created_at,
                updated_at=b.updated_at
            ) for b in bills]
            
            # Search committees
            committees = db.query(Committee).filter(
                Committee.name.ilike(f"%{query}%")
            ).limit(10).all()
            
            results.committees = [CommitteeType_GQL(
                id=c.id,
                name=c.name,
                committee_type=c.committee_type.value if hasattr(c.committee_type, 'value') else c.committee_type,
                description=c.description,
                jurisdiction_id=c.jurisdiction_id,
                created_at=c.created_at,
                updated_at=c.updated_at
            ) for c in committees]
            
            return results
            
        finally:
            db.close()

# Create GraphQL schema
schema = strawberry.Schema(query=Query)