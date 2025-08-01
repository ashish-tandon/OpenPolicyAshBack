"""
API Models

Pydantic models for request/response serialization in the OpenPolicy Database API.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid
from enum import Enum

# Enum definitions
class JurisdictionTypeEnum(str, Enum):
    FEDERAL = "federal"
    PROVINCIAL = "provincial"
    MUNICIPAL = "municipal"

class RepresentativeRoleEnum(str, Enum):
    MP = "MP"
    MPP = "MPP"
    MLA = "MLA"
    MNA = "MNA"
    MAYOR = "Mayor"
    COUNCILLOR = "Councillor"
    REEVE = "Reeve"
    OTHER = "Other"

class BillStatusEnum(str, Enum):
    INTRODUCED = "introduced"
    FIRST_READING = "first_reading"
    SECOND_READING = "second_reading"
    COMMITTEE = "committee"
    THIRD_READING = "third_reading"
    PASSED = "passed"
    ROYAL_ASSENT = "royal_assent"
    FAILED = "failed"
    WITHDRAWN = "withdrawn"

class EventTypeEnum(str, Enum):
    MEETING = "meeting"
    VOTE = "vote"
    READING = "reading"
    COMMITTEE_MEETING = "committee_meeting"
    OTHER = "other"

class VoteResultEnum(str, Enum):
    YES = "yes"
    NO = "no"
    ABSTAIN = "abstain"
    ABSENT = "absent"

# Base response models
class JurisdictionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    name: str
    jurisdiction_type: JurisdictionTypeEnum
    division_id: Optional[str] = None
    province: Optional[str] = None
    url: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class RepresentativeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    jurisdiction_id: uuid.UUID
    name: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: RepresentativeRoleEnum
    party: Optional[str] = None
    district: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    office_address: Optional[str] = None
    website: Optional[str] = None
    facebook_url: Optional[str] = None
    twitter_url: Optional[str] = None
    instagram_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    term_start: Optional[datetime] = None
    term_end: Optional[datetime] = None
    photo_url: Optional[str] = None
    biography: Optional[str] = None
    source_url: Optional[str] = None
    external_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class BillResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    jurisdiction_id: uuid.UUID
    bill_number: str
    title: str
    summary: Optional[str] = None
    full_text: Optional[str] = None
    status: BillStatusEnum
    introduced_date: Optional[datetime] = None
    first_reading_date: Optional[datetime] = None
    second_reading_date: Optional[datetime] = None
    third_reading_date: Optional[datetime] = None
    passed_date: Optional[datetime] = None
    royal_assent_date: Optional[datetime] = None
    legislative_body: Optional[str] = None
    source_url: Optional[str] = None
    external_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class CommitteeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    jurisdiction_id: uuid.UUID
    name: str
    description: Optional[str] = None
    committee_type: Optional[str] = None
    source_url: Optional[str] = None
    external_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class EventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    jurisdiction_id: uuid.UUID
    bill_id: Optional[uuid.UUID] = None
    committee_id: Optional[uuid.UUID] = None
    name: str
    description: Optional[str] = None
    event_type: EventTypeEnum
    event_date: datetime
    location: Optional[str] = None
    source_url: Optional[str] = None
    external_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class VoteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    event_id: uuid.UUID
    bill_id: Optional[uuid.UUID] = None
    representative_id: uuid.UUID
    vote_result: VoteResultEnum
    vote_date: datetime
    source_url: Optional[str] = None
    created_at: datetime

class StatsResponse(BaseModel):
    """Statistics about the database"""
    total_jurisdictions: int = 0
    federal_jurisdictions: int = 0
    provincial_jurisdictions: int = 0
    municipal_jurisdictions: int = 0
    total_representatives: int = 0
    total_bills: int = 0
    total_committees: int = 0
    total_events: int = 0
    total_votes: int = 0
    
    # Representative breakdown by role
    representatives_mp: int = 0
    representatives_mpp: int = 0
    representatives_mla: int = 0
    representatives_mna: int = 0
    representatives_mayor: int = 0
    representatives_councillor: int = 0
    representatives_reeve: int = 0
    representatives_other: int = 0

# Detailed responses with relationships
class RepresentativeDetailResponse(RepresentativeResponse):
    """Detailed representative response with jurisdiction info"""
    jurisdiction: JurisdictionResponse

class BillDetailResponse(BillResponse):
    """Detailed bill response with sponsors and jurisdiction"""
    jurisdiction: JurisdictionResponse
    sponsors: List[RepresentativeResponse] = []

class CommitteeDetailResponse(CommitteeResponse):
    """Detailed committee response with members"""
    jurisdiction: JurisdictionResponse
    members: List[RepresentativeResponse] = []

# Request models for creating/updating data
class JurisdictionCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    jurisdiction_type: JurisdictionTypeEnum
    division_id: Optional[str] = Field(None, max_length=255)
    province: Optional[str] = Field(None, max_length=2)
    url: Optional[str] = Field(None, max_length=500)

class RepresentativeCreate(BaseModel):
    jurisdiction_id: uuid.UUID
    name: str = Field(..., min_length=1, max_length=255)
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    role: RepresentativeRoleEnum
    party: Optional[str] = Field(None, max_length=100)
    district: Optional[str] = Field(None, max_length=255)
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)
    office_address: Optional[str] = None
    website: Optional[str] = Field(None, max_length=500)
    facebook_url: Optional[str] = Field(None, max_length=500)
    twitter_url: Optional[str] = Field(None, max_length=500)
    instagram_url: Optional[str] = Field(None, max_length=500)
    linkedin_url: Optional[str] = Field(None, max_length=500)
    term_start: Optional[datetime] = None
    term_end: Optional[datetime] = None
    photo_url: Optional[str] = Field(None, max_length=500)
    biography: Optional[str] = None
    source_url: Optional[str] = Field(None, max_length=500)
    external_id: Optional[str] = Field(None, max_length=100)

class BillCreate(BaseModel):
    jurisdiction_id: uuid.UUID
    bill_number: str = Field(..., min_length=1, max_length=50)
    title: str = Field(..., min_length=1, max_length=500)
    summary: Optional[str] = None
    full_text: Optional[str] = None
    status: BillStatusEnum
    introduced_date: Optional[datetime] = None
    first_reading_date: Optional[datetime] = None
    second_reading_date: Optional[datetime] = None
    third_reading_date: Optional[datetime] = None
    passed_date: Optional[datetime] = None
    royal_assent_date: Optional[datetime] = None
    legislative_body: Optional[str] = Field(None, max_length=100)
    source_url: Optional[str] = Field(None, max_length=500)
    external_id: Optional[str] = Field(None, max_length=100)

# Search and filter models
class RepresentativeFilter(BaseModel):
    jurisdiction_id: Optional[uuid.UUID] = None
    jurisdiction_type: Optional[JurisdictionTypeEnum] = None
    province: Optional[str] = Field(None, max_length=2)
    party: Optional[str] = Field(None, max_length=100)
    role: Optional[RepresentativeRoleEnum] = None
    district: Optional[str] = Field(None, max_length=255)
    search: Optional[str] = Field(None, max_length=255, description="Search in name")

class BillFilter(BaseModel):
    jurisdiction_id: Optional[uuid.UUID] = None
    status: Optional[BillStatusEnum] = None
    search: Optional[str] = Field(None, max_length=255, description="Search in title and summary")

# Pagination models
class PaginationParams(BaseModel):
    limit: int = Field(100, ge=1, le=1000, description="Number of results to return")
    offset: int = Field(0, ge=0, description="Number of results to skip")

class PaginatedResponse(BaseModel):
    """Base model for paginated responses"""
    total: int
    limit: int
    offset: int
    has_next: bool
    has_prev: bool

class PaginatedJurisdictionsResponse(PaginatedResponse):
    items: List[JurisdictionResponse]

class PaginatedRepresentativesResponse(PaginatedResponse):
    items: List[RepresentativeResponse]

class PaginatedBillsResponse(PaginatedResponse):
    items: List[BillResponse]

class PaginatedCommitteesResponse(PaginatedResponse):
    items: List[CommitteeResponse]

# Error response models
class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    code: Optional[str] = None

class ValidationErrorResponse(BaseModel):
    error: str = "Validation Error"
    details: List[Dict[str, Any]]