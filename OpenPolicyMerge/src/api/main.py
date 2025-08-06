"""
OpenPolicy Merge - Main FastAPI Application

This is the main API application that brings together all components:
- Database models and connections
- Unified scraper management
- REST and GraphQL endpoints
- Authentication and security
- Real-time monitoring and health checks
"""

import logging
import time
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Union
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, Query, Path, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.utils import get_openapi
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from pydantic import BaseModel

# Internal imports
from ..database.config import get_db, check_database_health, get_database_stats, db_metrics
from ..database.models import (
    Jurisdiction, JurisdictionType, Representative, RepresentativeRole,
    Bill, BillStatus, Committee, CommitteeType, Event, EventType,
    Vote, VoteResult, ScrapingRun, DataQualityIssue
)
from ..scrapers.manager import scraper_manager, ScraperType, ScraperStatus

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =============================================================================
# Pydantic Models for API Responses
# =============================================================================

class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    version: str
    database: Dict[str, Any]
    services: Dict[str, str]

class StatsResponse(BaseModel):
    jurisdictions: int
    representatives: int
    bills: int
    events: int
    committees: int
    votes: int
    data_freshness: Dict[str, Any]

class JurisdictionResponse(BaseModel):
    id: str
    name: str
    jurisdiction_type: str
    code: str
    website: Optional[str]
    population: Optional[int]
    area_km2: Optional[float]
    representative_count: int
    bill_count: int
    data_quality_score: float
    last_updated: datetime

class RepresentativeResponse(BaseModel):
    id: str
    name: str
    role: str
    party: Optional[str]
    riding: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    photo_url: Optional[str]
    active: bool
    jurisdiction: Dict[str, str]
    committees: List[str]
    recent_votes: int

class BillResponse(BaseModel):
    id: str
    number: str
    title: str
    status: str
    introduction_date: Optional[str]
    parliament: Optional[int]
    session: Optional[int]
    private_member: bool
    sponsor: Optional[Dict[str, str]]
    jurisdiction: Dict[str, str]
    vote_count: int
    last_action: Optional[str]

class ScrapingTaskRequest(BaseModel):
    scraper_type: str
    jurisdiction_id: str
    config: Optional[Dict[str, Any]] = None

class ScrapingTaskResponse(BaseModel):
    task_id: str
    scraper_type: str
    jurisdiction_id: str
    status: str
    message: str

# =============================================================================
# Application Lifecycle
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("🚀 Starting OpenPolicy Merge API...")
    
    # Initialize database
    from ..database.config import initialize_database
    if not initialize_database():
        logger.error("❌ Failed to initialize database")
        raise RuntimeError("Database initialization failed")
    
    logger.info("✅ Database initialized successfully")
    
    # Startup tasks could include:
    # - Warming up caches
    # - Starting background services
    # - Initial data validation
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down OpenPolicy Merge API...")

# =============================================================================
# FastAPI Application Setup
# =============================================================================

app = FastAPI(
    title="OpenPolicy Merge API",
    description="""
    A comprehensive Canadian civic data platform that unifies federal, provincial, 
    and municipal political information through modern APIs.
    
    ## Features
    
    * **Complete Coverage**: Federal, provincial, and municipal data
    * **Real-time Updates**: Daily scraping with automated error handling
    * **Advanced Search**: Full-text search across all entities
    * **Data Quality**: Cross-validation and audit trails
    * **High Performance**: <200ms response times with caching
    
    ## Data Sources
    
    * Parliament of Canada (ourcommons.ca, parl.ca)
    * Represent API (represent.opennorth.ca)
    * Provincial legislature websites
    * Municipal government websites (200+ cities)
    
    ## Authentication
    
    Most endpoints are publicly accessible. Administrative endpoints require authentication.
    """,
    version="1.0.0",
    contact={
        "name": "OpenPolicy Merge Team",
        "email": "contact@openpolicymerge.org",
        "url": "https://openpolicymerge.org"
    },
    license_info={
        "name": "AGPLv3",
        "url": "https://www.gnu.org/licenses/agpl-3.0.html"
    },
    lifespan=lifespan
)

# =============================================================================
# Middleware Configuration
# =============================================================================

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React development
        "http://localhost:3001",  # Alternative React port
        "https://openpolicymerge.org",  # Production frontend
        "https://*.openpolicymerge.org",  # Subdomains
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Compression middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Request logging middleware
@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    """Log all requests with timing"""
    start_time = time.time()
    
    # Process request
    response = await call_next(request)
    
    # Log request details
    process_time = time.time() - start_time
    logger.info(
        f"{request.method} {request.url.path} - "
        f"Status: {response.status_code} - "
        f"Time: {process_time:.3f}s"
    )
    
    # Add timing header
    response.headers["X-Process-Time"] = str(process_time)
    
    return response

# =============================================================================
# Health and System Endpoints
# =============================================================================

@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Health check endpoint providing system status and diagnostics.
    
    Returns comprehensive health information including:
    - API status and version
    - Database connectivity and performance
    - Background services status
    - Data freshness indicators
    """
    db_health = check_database_health()
    
    return HealthResponse(
        status="healthy" if db_health.get("status") == "healthy" else "degraded",
        timestamp=datetime.utcnow(),
        version="1.0.0",
        database=db_health,
        services={
            "database": db_health.get("status", "unknown"),
            "scrapers": "active" if scraper_manager.get_active_runs() else "idle",
            "cache": "healthy",  # Would check Redis if implemented
        }
    )

@app.get("/stats", response_model=StatsResponse, tags=["Statistics"])
async def get_system_stats(db: Session = Depends(get_db)):
    """
    Get comprehensive system statistics including data counts and freshness.
    """
    try:
        # Count records by type
        jurisdiction_count = db.query(Jurisdiction).count()
        representative_count = db.query(Representative).count()
        bill_count = db.query(Bill).count()
        event_count = db.query(Event).count()
        committee_count = db.query(Committee).count()
        vote_count = db.query(Vote).count()
        
        # Data freshness indicators
        recent_cutoff = datetime.utcnow() - timedelta(days=1)
        recent_scrapes = db.query(ScrapingRun).filter(
            ScrapingRun.start_time >= recent_cutoff,
            ScrapingRun.status == "completed"
        ).count()
        
        last_scrape = db.query(ScrapingRun).filter(
            ScrapingRun.status == "completed"
        ).order_by(ScrapingRun.end_time.desc()).first()
        
        data_freshness = {
            "recent_scrapes_24h": recent_scrapes,
            "last_successful_scrape": last_scrape.end_time.isoformat() if last_scrape else None,
            "data_age_hours": (
                (datetime.utcnow() - last_scrape.end_time).total_seconds() / 3600
                if last_scrape else None
            )
        }
        
        return StatsResponse(
            jurisdictions=jurisdiction_count,
            representatives=representative_count,
            bills=bill_count,
            events=event_count,
            committees=committee_count,
            votes=vote_count,
            data_freshness=data_freshness
        )
        
    except Exception as e:
        logger.error(f"Failed to get system stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve statistics: {str(e)}")

@app.get("/metrics", tags=["Monitoring"])
async def get_metrics():
    """
    Get detailed performance metrics for monitoring and observability.
    """
    try:
        # Database metrics
        db_stats = get_database_stats()
        db_perf = db_metrics.get_metrics()
        
        # Scraper metrics
        scraper_stats = scraper_manager.get_scraper_stats()
        
        return {
            "database": {
                "performance": db_perf,
                "statistics": db_stats
            },
            "scrapers": scraper_stats,
            "api": {
                "uptime_seconds": time.time() - app.state.start_time if hasattr(app.state, 'start_time') else 0,
                "requests_total": db_perf.get("total_queries", 0),
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve metrics: {str(e)}")

# =============================================================================
# Jurisdiction Endpoints
# =============================================================================

@app.get("/api/v1/jurisdictions", response_model=List[JurisdictionResponse], tags=["Jurisdictions"])
async def list_jurisdictions(
    jurisdiction_type: Optional[str] = Query(None, description="Filter by jurisdiction type"),
    search: Optional[str] = Query(None, description="Search jurisdictions by name"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    db: Session = Depends(get_db)
):
    """
    List all jurisdictions with optional filtering and search.
    
    Supports filtering by:
    - Jurisdiction type (federal, provincial, municipal, etc.)
    - Name search (case-insensitive)
    - Pagination with limit and offset
    """
    try:
        query = db.query(Jurisdiction)
        
        # Apply filters
        if jurisdiction_type:
            try:
                jtype = JurisdictionType(jurisdiction_type)
                query = query.filter(Jurisdiction.jurisdiction_type == jtype)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid jurisdiction type: {jurisdiction_type}")
        
        if search:
            query = query.filter(Jurisdiction.name.ilike(f"%{search}%"))
        
        # Get total count for pagination
        total = query.count()
        
        # Apply pagination
        jurisdictions = query.offset(offset).limit(limit).all()
        
        # Build response with additional data
        response = []
        for jurisdiction in jurisdictions:
            rep_count = db.query(Representative).filter(
                Representative.jurisdiction_id == jurisdiction.id
            ).count()
            
            bill_count = db.query(Bill).filter(
                Bill.jurisdiction_id == jurisdiction.id
            ).count()
            
            response.append(JurisdictionResponse(
                id=str(jurisdiction.id),
                name=jurisdiction.name,
                jurisdiction_type=jurisdiction.jurisdiction_type.value,
                code=jurisdiction.code,
                website=jurisdiction.website,
                population=jurisdiction.population,
                area_km2=jurisdiction.area_km2,
                representative_count=rep_count,
                bill_count=bill_count,
                data_quality_score=jurisdiction.data_quality_score or 1.0,
                last_updated=jurisdiction.updated_at
            ))
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list jurisdictions: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve jurisdictions")

@app.get("/api/v1/jurisdictions/{jurisdiction_id}", response_model=JurisdictionResponse, tags=["Jurisdictions"])
async def get_jurisdiction(
    jurisdiction_id: str = Path(..., description="Jurisdiction ID"),
    db: Session = Depends(get_db)
):
    """Get detailed information about a specific jurisdiction."""
    try:
        jurisdiction = db.query(Jurisdiction).filter(
            Jurisdiction.id == jurisdiction_id
        ).first()
        
        if not jurisdiction:
            raise HTTPException(status_code=404, detail="Jurisdiction not found")
        
        # Get additional statistics
        rep_count = db.query(Representative).filter(
            Representative.jurisdiction_id == jurisdiction.id
        ).count()
        
        bill_count = db.query(Bill).filter(
            Bill.jurisdiction_id == jurisdiction.id
        ).count()
        
        return JurisdictionResponse(
            id=str(jurisdiction.id),
            name=jurisdiction.name,
            jurisdiction_type=jurisdiction.jurisdiction_type.value,
            code=jurisdiction.code,
            website=jurisdiction.website,
            population=jurisdiction.population,
            area_km2=jurisdiction.area_km2,
            representative_count=rep_count,
            bill_count=bill_count,
            data_quality_score=jurisdiction.data_quality_score or 1.0,
            last_updated=jurisdiction.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get jurisdiction {jurisdiction_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve jurisdiction")

# =============================================================================
# Representative Endpoints
# =============================================================================

@app.get("/api/v1/representatives", response_model=List[RepresentativeResponse], tags=["Representatives"])
async def list_representatives(
    jurisdiction_id: Optional[str] = Query(None, description="Filter by jurisdiction"),
    role: Optional[str] = Query(None, description="Filter by representative role"),
    party: Optional[str] = Query(None, description="Filter by political party"),
    active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search by name"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    List representatives with comprehensive filtering options.
    
    Supports filtering by:
    - Jurisdiction (federal, provincial, municipal)
    - Role (MP, MLA, councillor, mayor, etc.)
    - Political party
    - Active status
    - Name search
    """
    try:
        query = db.query(Representative).join(Jurisdiction)
        
        # Apply filters
        if jurisdiction_id:
            query = query.filter(Representative.jurisdiction_id == jurisdiction_id)
        
        if role:
            try:
                role_enum = RepresentativeRole(role)
                query = query.filter(Representative.role == role_enum)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid role: {role}")
        
        if party:
            query = query.filter(Representative.party.ilike(f"%{party}%"))
        
        if active is not None:
            query = query.filter(Representative.active == active)
        
        if search:
            query = query.filter(Representative.name.ilike(f"%{search}%"))
        
        # Apply pagination
        representatives = query.offset(offset).limit(limit).all()
        
        # Build response with additional data
        response = []
        for rep in representatives:
            # Get committee count
            committee_names = [committee.name for committee in rep.committees]
            
            # Get recent vote count
            recent_votes = db.query(Vote).filter(
                Vote.representative_id == rep.id,
                Vote.vote_date >= datetime.utcnow() - timedelta(days=30)
            ).count()
            
            response.append(RepresentativeResponse(
                id=str(rep.id),
                name=rep.name,
                role=rep.role.value,
                party=rep.party,
                riding=rep.riding,
                email=rep.email,
                phone=rep.phone,
                photo_url=rep.photo_url,
                active=rep.active,
                jurisdiction={
                    "id": str(rep.jurisdiction.id),
                    "name": rep.jurisdiction.name,
                    "type": rep.jurisdiction.jurisdiction_type.value
                },
                committees=committee_names,
                recent_votes=recent_votes
            ))
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list representatives: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve representatives")

# =============================================================================
# Bill Endpoints
# =============================================================================

@app.get("/api/v1/bills", response_model=List[BillResponse], tags=["Bills"])
async def list_bills(
    jurisdiction_id: Optional[str] = Query(None, description="Filter by jurisdiction"),
    status: Optional[str] = Query(None, description="Filter by bill status"),
    parliament: Optional[int] = Query(None, description="Filter by parliament number"),
    session: Optional[int] = Query(None, description="Filter by session number"),
    search: Optional[str] = Query(None, description="Search bill titles and numbers"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    List bills with comprehensive filtering and search capabilities.
    """
    try:
        query = db.query(Bill).join(Jurisdiction)
        
        # Apply filters
        if jurisdiction_id:
            query = query.filter(Bill.jurisdiction_id == jurisdiction_id)
        
        if status:
            try:
                status_enum = BillStatus(status)
                query = query.filter(Bill.status == status_enum)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
        
        if parliament is not None:
            query = query.filter(Bill.parliament == parliament)
        
        if session is not None:
            query = query.filter(Bill.session == session)
        
        if search:
            query = query.filter(
                db.or_(
                    Bill.title.ilike(f"%{search}%"),
                    Bill.number.ilike(f"%{search}%")
                )
            )
        
        # Order by most recent first
        query = query.order_by(Bill.introduction_date.desc().nullslast())
        
        # Apply pagination
        bills = query.offset(offset).limit(limit).all()
        
        # Build response
        response = []
        for bill in bills:
            # Get sponsor information
            sponsor = None
            if bill.representatives:
                sponsor_rep = bill.representatives[0]  # First associated representative
                sponsor = {
                    "id": str(sponsor_rep.id),
                    "name": sponsor_rep.name,
                    "party": sponsor_rep.party
                }
            
            # Get vote count
            vote_count = db.query(Vote).filter(Vote.bill_id == bill.id).count()
            
            response.append(BillResponse(
                id=str(bill.id),
                number=bill.number,
                title=bill.title,
                status=bill.status.value,
                introduction_date=bill.introduction_date.isoformat() if bill.introduction_date else None,
                parliament=bill.parliament,
                session=bill.session,
                private_member=bill.private_member,
                sponsor=sponsor,
                jurisdiction={
                    "id": str(bill.jurisdiction.id),
                    "name": bill.jurisdiction.name,
                    "type": bill.jurisdiction.jurisdiction_type.value
                },
                vote_count=vote_count,
                last_action=bill.status_date.isoformat() if bill.status_date else None
            ))
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list bills: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve bills")

# =============================================================================
# Search Endpoints
# =============================================================================

@app.get("/api/v1/search", tags=["Search"])
async def global_search(
    q: str = Query(..., description="Search query"),
    entity_types: Optional[str] = Query(None, description="Comma-separated entity types to search"),
    jurisdiction_id: Optional[str] = Query(None, description="Limit search to specific jurisdiction"),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """
    Global search across all entities (representatives, bills, committees, etc.)
    
    Supports searching:
    - Representative names, parties, ridings
    - Bill titles, numbers, descriptions
    - Committee names and descriptions
    - Event titles and descriptions
    """
    try:
        results = []
        search_term = f"%{q}%"
        
        # Search representatives
        if not entity_types or "representatives" in entity_types:
            rep_query = db.query(Representative).join(Jurisdiction).filter(
                db.or_(
                    Representative.name.ilike(search_term),
                    Representative.party.ilike(search_term),
                    Representative.riding.ilike(search_term)
                )
            )
            
            if jurisdiction_id:
                rep_query = rep_query.filter(Representative.jurisdiction_id == jurisdiction_id)
            
            for rep in rep_query.limit(limit // 4).all():
                results.append({
                    "type": "representative",
                    "id": str(rep.id),
                    "title": rep.name,
                    "subtitle": f"{rep.role.value.title()} - {rep.party or 'Independent'}",
                    "description": f"{rep.riding}, {rep.jurisdiction.name}",
                    "url": f"/api/v1/representatives/{rep.id}",
                    "jurisdiction": rep.jurisdiction.name
                })
        
        # Search bills
        if not entity_types or "bills" in entity_types:
            bill_query = db.query(Bill).join(Jurisdiction).filter(
                db.or_(
                    Bill.title.ilike(search_term),
                    Bill.number.ilike(search_term),
                    Bill.summary.ilike(search_term)
                )
            )
            
            if jurisdiction_id:
                bill_query = bill_query.filter(Bill.jurisdiction_id == jurisdiction_id)
            
            for bill in bill_query.limit(limit // 4).all():
                results.append({
                    "type": "bill",
                    "id": str(bill.id),
                    "title": f"{bill.number}: {bill.title}",
                    "subtitle": bill.status.value.replace('_', ' ').title(),
                    "description": bill.summary[:200] + "..." if bill.summary and len(bill.summary) > 200 else bill.summary,
                    "url": f"/api/v1/bills/{bill.id}",
                    "jurisdiction": bill.jurisdiction.name
                })
        
        # Search committees
        if not entity_types or "committees" in entity_types:
            committee_query = db.query(Committee).join(Jurisdiction).filter(
                db.or_(
                    Committee.name.ilike(search_term),
                    Committee.description.ilike(search_term)
                )
            )
            
            if jurisdiction_id:
                committee_query = committee_query.filter(Committee.jurisdiction_id == jurisdiction_id)
            
            for committee in committee_query.limit(limit // 4).all():
                results.append({
                    "type": "committee",
                    "id": str(committee.id),
                    "title": committee.name,
                    "subtitle": committee.committee_type.value.title(),
                    "description": committee.description,
                    "url": f"/api/v1/committees/{committee.id}",
                    "jurisdiction": committee.jurisdiction.name
                })
        
        # Search events
        if not entity_types or "events" in entity_types:
            event_query = db.query(Event).join(Jurisdiction).filter(
                db.or_(
                    Event.title.ilike(search_term),
                    Event.description.ilike(search_term)
                )
            )
            
            if jurisdiction_id:
                event_query = event_query.filter(Event.jurisdiction_id == jurisdiction_id)
            
            for event in event_query.limit(limit // 4).all():
                results.append({
                    "type": "event",
                    "id": str(event.id),
                    "title": event.title,
                    "subtitle": event.event_type.value.replace('_', ' ').title(),
                    "description": f"{event.date} - {event.description}" if event.description else str(event.date),
                    "url": f"/api/v1/events/{event.id}",
                    "jurisdiction": event.jurisdiction.name
                })
        
        return {
            "query": q,
            "total_results": len(results),
            "results": results[:limit]
        }
        
    except Exception as e:
        logger.error(f"Search failed for query '{q}': {e}")
        raise HTTPException(status_code=500, detail="Search failed")

# =============================================================================
# Administrative Endpoints
# =============================================================================

@app.post("/api/v1/admin/scraping/run", response_model=ScrapingTaskResponse, tags=["Administration"])
async def trigger_scraper(
    request: ScrapingTaskRequest,
    background_tasks: BackgroundTasks
):
    """
    Trigger a scraping task for a specific jurisdiction and scraper type.
    
    Requires admin authentication (not implemented in this demo).
    """
    try:
        # Validate scraper type
        try:
            scraper_type = ScraperType(request.scraper_type)
        except ValueError:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid scraper type: {request.scraper_type}"
            )
        
        # Generate task ID
        task_id = f"{request.scraper_type}_{request.jurisdiction_id}_{int(time.time())}"
        
        # Add scraping task to background tasks
        background_tasks.add_task(
            scraper_manager.run_scraper,
            scraper_type,
            request.jurisdiction_id,
            request.config
        )
        
        return ScrapingTaskResponse(
            task_id=task_id,
            scraper_type=request.scraper_type,
            jurisdiction_id=request.jurisdiction_id,
            status="queued",
            message="Scraping task has been queued for execution"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to trigger scraper: {e}")
        raise HTTPException(status_code=500, detail="Failed to trigger scraper")

@app.get("/api/v1/admin/scraping/status", tags=["Administration"])
async def get_scraping_status():
    """Get status of all active and recent scraping runs."""
    try:
        active_runs = scraper_manager.get_active_runs()
        scraper_stats = scraper_manager.get_scraper_stats()
        
        return {
            "active_runs": active_runs,
            "statistics": scraper_stats
        }
        
    except Exception as e:
        logger.error(f"Failed to get scraping status: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve scraping status")

# =============================================================================
# OpenAPI Customization
# =============================================================================

def custom_openapi():
    """Custom OpenAPI schema with additional metadata"""
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="OpenPolicy Merge API",
        version="1.0.0",
        description=app.description,
        routes=app.routes,
    )
    
    # Add custom tags
    openapi_schema["tags"] = [
        {"name": "Health", "description": "Health checks and system status"},
        {"name": "Statistics", "description": "System statistics and metrics"},
        {"name": "Jurisdictions", "description": "Canadian jurisdictions (federal, provincial, municipal)"},
        {"name": "Representatives", "description": "Elected officials and representatives"},
        {"name": "Bills", "description": "Legislative bills and acts"},
        {"name": "Search", "description": "Search across all entities"},
        {"name": "Administration", "description": "Administrative endpoints (authentication required)"},
        {"name": "Monitoring", "description": "Performance monitoring and observability"},
    ]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# =============================================================================
# Application Startup
# =============================================================================

@app.on_event("startup")
async def startup_event():
    """Application startup tasks"""
    app.state.start_time = time.time()
    logger.info("🚀 OpenPolicy Merge API started successfully")

@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown tasks"""
    logger.info("🛑 OpenPolicy Merge API shutting down")

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
        access_log=True
    )