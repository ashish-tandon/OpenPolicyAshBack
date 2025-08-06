"""
OpenPolicy Merge - Unified Database Models

This module defines the comprehensive database schema for the OpenPolicy Merge platform,
combining and enhancing models from:
- OpenParliament (parliamentary data structures)
- OpenPolicyAshBack (modern SQLAlchemy foundation)
- Represent API (standardized civic data)
- Additional enhancements for comprehensive Canadian civic data

Database: PostgreSQL 16+ with PostGIS for geographic data
ORM: SQLAlchemy with declarative base
"""

from sqlalchemy import (
    create_engine, Column, Integer, String, Text, DateTime, Boolean,
    ForeignKey, JSON, Enum, UniqueConstraint, Index, Date, Float,
    ARRAY, Table
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.dialects.postgresql import UUID, JSONB, TSVECTOR
from sqlalchemy.sql import func
from datetime import datetime
import uuid
import enum

Base = declarative_base()

# =============================================================================
# Enums - Comprehensive type definitions
# =============================================================================

class JurisdictionType(enum.Enum):
    """Canadian jurisdiction types"""
    FEDERAL = "federal"
    PROVINCIAL = "provincial" 
    TERRITORIAL = "territorial"
    MUNICIPAL = "municipal"
    REGIONAL = "regional"          # Regional municipalities
    INDIGENOUS = "indigenous"      # First Nations, etc.

class RepresentativeRole(enum.Enum):
    """All types of elected and appointed officials"""
    # Federal
    MP = "mp"                      # Member of Parliament
    SENATOR = "senator"
    GOVERNOR_GENERAL = "governor_general"
    
    # Provincial/Territorial
    MLA = "mla"                    # Member of Legislative Assembly
    MPP = "mpp"                    # Member of Provincial Parliament (ON)
    MNA = "mna"                    # Member of National Assembly (QC)
    PREMIER = "premier"
    LIEUTENANT_GOVERNOR = "lieutenant_governor"
    
    # Municipal
    MAYOR = "mayor"
    COUNCILLOR = "councillor"
    DEPUTY_MAYOR = "deputy_mayor"
    REEVE = "reeve"               # Rural municipalities
    WARDEN = "warden"             # Counties
    
    # Regional
    REGIONAL_COUNCILLOR = "regional_councillor"
    REGIONAL_CHAIR = "regional_chair"

class BillStatus(enum.Enum):
    """Comprehensive bill status tracking (from OpenParliament)"""
    # Introduced
    INTRODUCED = "introduced"
    PRO_FORMA = "pro_forma"
    
    # Readings
    FIRST_READING_HOUSE = "first_reading_house"
    FIRST_READING_SENATE = "first_reading_senate"
    SECOND_READING_HOUSE = "second_reading_house"
    SECOND_READING_SENATE = "second_reading_senate"
    THIRD_READING_HOUSE = "third_reading_house"
    THIRD_READING_SENATE = "third_reading_senate"
    
    # Committee stages
    IN_COMMITTEE_HOUSE = "in_committee_house"
    IN_COMMITTEE_SENATE = "in_committee_senate"
    COMMITTEE_REPORT_HOUSE = "committee_report_house"
    COMMITTEE_REPORT_SENATE = "committee_report_senate"
    
    # Report stages
    REPORT_STAGE_HOUSE = "report_stage_house"
    REPORT_STAGE_SENATE = "report_stage_senate"
    
    # Cross-chamber
    HOUSE_BILL_WAITING_SENATE = "house_bill_waiting_senate"
    SENATE_BILL_WAITING_HOUSE = "senate_bill_waiting_house"
    
    # Amendments
    HOUSE_CONSIDERING_SENATE_AMENDMENTS = "house_considering_senate_amendments"
    SENATE_CONSIDERING_HOUSE_AMENDMENTS = "senate_considering_house_amendments"
    
    # Final stages
    ROYAL_ASSENT_AWAITING = "royal_assent_awaiting"
    ROYAL_ASSENT_GIVEN = "royal_assent_given"
    
    # Failed/withdrawn
    DEFEATED = "defeated"
    WITHDRAWN = "withdrawn"
    NOT_ACTIVE = "not_active"
    WILL_NOT_PROCEED = "will_not_proceed"
    
    # Private members
    OUTSIDE_ORDER_PRECEDENCE = "outside_order_precedence"

class EventType(enum.Enum):
    """Types of political events and meetings"""
    # Parliamentary
    PARLIAMENTARY_SESSION = "parliamentary_session"
    HOUSE_SITTING = "house_sitting"
    SENATE_SITTING = "senate_sitting"
    COMMITTEE_MEETING = "committee_meeting"
    
    # Votes
    RECORDED_VOTE = "recorded_vote"
    VOICE_VOTE = "voice_vote"
    
    # Debates
    DEBATE = "debate"
    QUESTION_PERIOD = "question_period"
    MEMBERS_STATEMENTS = "members_statements"
    
    # Municipal
    COUNCIL_MEETING = "council_meeting"
    PUBLIC_HEARING = "public_hearing"
    COMMITTEE_MEETING_MUNICIPAL = "committee_meeting_municipal"
    
    # Elections
    ELECTION = "election"
    BY_ELECTION = "by_election"
    
    # Other
    ANNOUNCEMENT = "announcement"
    PRESS_CONFERENCE = "press_conference"

class VoteResult(enum.Enum):
    """Individual vote results"""
    YES = "yes"
    NO = "no"
    ABSTAIN = "abstain"
    ABSENT = "absent"
    PAIRED = "paired"              # Paired with opposing vote

class DocumentType(enum.Enum):
    """Types of parliamentary and government documents"""
    HANSARD_DEBATE = "hansard_debate"
    HANSARD_EVIDENCE = "hansard_evidence"
    BILL_TEXT = "bill_text"
    COMMITTEE_REPORT = "committee_report"
    COMMITTEE_TRANSCRIPT = "committee_transcript"
    ORDER_PAPER = "order_paper"
    NOTICE_PAPER = "notice_paper"
    GOVERNMENT_RESPONSE = "government_response"
    PETITION = "petition"
    MUNICIPAL_BYLAW = "municipal_bylaw"
    MUNICIPAL_AGENDA = "municipal_agenda"
    MUNICIPAL_MINUTES = "municipal_minutes"

class CommitteeType(enum.Enum):
    """Types of committees"""
    STANDING = "standing"
    SPECIAL = "special"
    JOINT = "joint"
    LEGISLATIVE = "legislative"
    SUBCOMMITTEE = "subcommittee"
    MUNICIPAL_COMMITTEE = "municipal_committee"
    REGIONAL_COMMITTEE = "regional_committee"

# =============================================================================
# Association Tables - Many-to-many relationships
# =============================================================================

# Committee membership association
committee_memberships = Table(
    'committee_memberships',
    Base.metadata,
    Column('committee_id', UUID(as_uuid=True), ForeignKey('committees.id')),
    Column('representative_id', UUID(as_uuid=True), ForeignKey('representatives.id')),
    Column('role', String(50), nullable=False, default='member'),  # chair, vice-chair, member
    Column('start_date', Date),
    Column('end_date', Date),
    Column('created_at', DateTime, default=datetime.utcnow),
    UniqueConstraint('committee_id', 'representative_id', 'start_date')
)

# Bill sponsorship and involvement
bill_representatives = Table(
    'bill_representatives',
    Base.metadata,
    Column('bill_id', UUID(as_uuid=True), ForeignKey('bills.id')),
    Column('representative_id', UUID(as_uuid=True), ForeignKey('representatives.id')),
    Column('role', String(50), nullable=False),  # sponsor, co-sponsor, critic
    Column('created_at', DateTime, default=datetime.utcnow)
)

# =============================================================================
# Core Models - Jurisdiction and Representatives
# =============================================================================

class Jurisdiction(Base):
    """Enhanced jurisdiction model covering all Canadian government levels"""
    __tablename__ = 'jurisdictions'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    name_en = Column(String(255), nullable=False)
    name_fr = Column(String(255))
    jurisdiction_type = Column(Enum(JurisdictionType), nullable=False)
    code = Column(String(50), unique=True, nullable=False)  # e.g., 'CA-ON', 'CA-QC-MTL'
    parent_jurisdiction_id = Column(UUID(as_uuid=True), ForeignKey('jurisdictions.id'))
    
    # Geographic and administrative info
    website = Column(String(500))
    population = Column(Integer)
    area_km2 = Column(Float)
    capital_city = Column(String(255))
    
    # Data source tracking
    represent_boundary_set = Column(String(255))  # From Represent API
    external_id = Column(String(255))  # External system ID
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    data_source = Column(String(100))  # Source of this data
    data_quality_score = Column(Float, default=1.0)  # 0-1 quality score
    
    # Relationships
    parent_jurisdiction = relationship("Jurisdiction", remote_side=[id])
    child_jurisdictions = relationship("Jurisdiction", back_populates="parent_jurisdiction")
    representatives = relationship("Representative", back_populates="jurisdiction")
    bills = relationship("Bill", back_populates="jurisdiction")
    committees = relationship("Committee", back_populates="jurisdiction")
    events = relationship("Event", back_populates="jurisdiction")
    scraping_runs = relationship("ScrapingRun", back_populates="jurisdiction")

class Representative(Base):
    """Comprehensive representative model for all levels of government"""
    __tablename__ = 'representatives'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    jurisdiction_id = Column(UUID(as_uuid=True), ForeignKey('jurisdictions.id'), nullable=False)
    
    # Basic information
    name = Column(String(255), nullable=False)
    name_given = Column(String(100))
    name_family = Column(String(100))
    name_display = Column(String(255))  # Preferred display name
    
    # Role and position
    role = Column(Enum(RepresentativeRole), nullable=False)
    party = Column(String(255))
    party_short = Column(String(50))
    riding = Column(String(255))  # Electoral district
    district_name = Column(String(255))  # Alternative to riding
    
    # Contact information
    email = Column(String(255))
    phone = Column(String(50))
    fax = Column(String(50))
    website = Column(String(500))
    twitter = Column(String(100))
    facebook = Column(String(500))
    
    # Physical details
    photo_url = Column(String(500))
    gender = Column(String(1))  # M, F, O, or NULL
    
    # Status tracking
    active = Column(Boolean, default=True)
    start_date = Column(Date)
    end_date = Column(Date)
    
    # External system IDs (from OpenParliament)
    parl_affiliation_id = Column(Integer)  # Parliament affiliation ID
    parl_person_id = Column(Integer)       # Parliament person ID
    represent_id = Column(String(100))     # Represent API ID
    external_id = Column(String(255))      # Other external system ID
    
    # Offices (stored as JSON for flexibility)
    offices = Column(JSONB)  # Array of office objects with type, address, phone, etc.
    
    # Search and metadata
    search_vector = Column(TSVECTOR)  # Full-text search
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    data_source = Column(String(100))
    data_quality_score = Column(Float, default=1.0)
    
    # Relationships
    jurisdiction = relationship("Jurisdiction", back_populates="representatives")
    electoral_memberships = relationship("ElectoralMembership", back_populates="representative")
    parliamentary_statements = relationship("ParliamentaryStatement", back_populates="politician")
    votes = relationship("Vote", back_populates="representative")
    
    # Many-to-many relationships
    committees = relationship("Committee", secondary=committee_memberships, back_populates="members")
    bills = relationship("Bill", secondary=bill_representatives, back_populates="representatives")
    
    # Indexes
    __table_args__ = (
        Index('ix_representative_name', 'name'),
        Index('ix_representative_party', 'party'),
        Index('ix_representative_riding', 'riding'),
        Index('ix_representative_search', 'search_vector', postgresql_using='gin'),
        Index('ix_representative_active', 'active'),
    )

# =============================================================================
# Parliamentary Models - Enhanced from OpenParliament
# =============================================================================

class ParliamentarySession(Base):
    """Parliamentary sessions with enhanced tracking"""
    __tablename__ = 'parliamentary_sessions'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    parliament = Column(Integer, nullable=False)
    session = Column(Integer, nullable=False)
    name = Column(String(255))  # e.g., "44th Parliament, 1st Session"
    start_date = Column(Date, nullable=False)
    end_date = Column(Date)
    dissolved_date = Column(Date)
    prorogued_date = Column(Date)
    
    # Status
    active = Column(Boolean, default=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    bills = relationship("Bill", back_populates="parliamentary_session")
    hansard_documents = relationship("HansardDocument", back_populates="session")
    electoral_memberships = relationship("ElectoralMembership", back_populates="session")
    
    __table_args__ = (
        UniqueConstraint('parliament', 'session'),
        Index('ix_session_active', 'active'),
    )

class ElectoralMembership(Base):
    """Electoral history and current positions"""
    __tablename__ = 'electoral_memberships'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    representative_id = Column(UUID(as_uuid=True), ForeignKey('representatives.id'), nullable=False)
    session_id = Column(UUID(as_uuid=True), ForeignKey('parliamentary_sessions.id'))
    
    # Electoral information
    riding = Column(String(255), nullable=False)
    party = Column(String(255))
    election_date = Column(Date)
    start_date = Column(Date)
    end_date = Column(Date)
    
    # Election results
    votes_received = Column(Integer)
    percentage = Column(Float)
    margin = Column(Integer)
    elected = Column(Boolean, default=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    representative = relationship("Representative", back_populates="electoral_memberships")
    session = relationship("ParliamentarySession", back_populates="electoral_memberships")

class Bill(Base):
    """Enhanced bill model combining OpenParliament and OpenPolicyAshBack features"""
    __tablename__ = 'bills'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    jurisdiction_id = Column(UUID(as_uuid=True), ForeignKey('jurisdictions.id'), nullable=False)
    parliamentary_session_id = Column(UUID(as_uuid=True), ForeignKey('parliamentary_sessions.id'))
    
    # Bill identification
    number = Column(String(50), nullable=False)  # C-11, S-5, Bill 101, etc.
    title = Column(Text, nullable=False)
    title_en = Column(Text)
    title_fr = Column(Text)
    summary = Column(Text)
    summary_en = Column(Text)
    summary_fr = Column(Text)
    
    # Status tracking
    status = Column(Enum(BillStatus), nullable=False)
    status_date = Column(Date)
    status_description = Column(Text)
    
    # Parliamentary tracking
    parliament = Column(Integer)  # Parliament number
    session = Column(Integer)     # Session number
    chamber = Column(String(10))  # House, Senate
    private_member = Column(Boolean, default=False)
    
    # Important dates
    introduction_date = Column(Date)
    first_reading_date = Column(Date)
    second_reading_date = Column(Date)
    third_reading_date = Column(Date)
    royal_assent_date = Column(Date)
    
    # External system IDs
    legisinfo_id = Column(Integer)  # LEGISinfo ID from OpenParliament
    external_id = Column(String(255))
    source_url = Column(String(500))
    
    # Bill text and documents
    bill_text = Column(Text)
    bill_text_url = Column(String(500))
    explanatory_notes = Column(Text)
    
    # Search and categorization
    search_vector = Column(TSVECTOR)
    tags = Column(ARRAY(String))  # Topic tags
    departments = Column(ARRAY(String))  # Responsible departments
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    data_source = Column(String(100))
    data_quality_score = Column(Float, default=1.0)
    
    # Relationships
    jurisdiction = relationship("Jurisdiction", back_populates="bills")
    parliamentary_session = relationship("ParliamentarySession", back_populates="bills")
    votes = relationship("Vote", back_populates="bill")
    statements = relationship("ParliamentaryStatement", back_populates="bill")
    status_changes = relationship("BillStatusChange", back_populates="bill")
    
    # Many-to-many relationships
    representatives = relationship("Representative", secondary=bill_representatives, back_populates="bills")
    
    __table_args__ = (
        Index('ix_bill_number', 'number'),
        Index('ix_bill_status', 'status'),
        Index('ix_bill_search', 'search_vector', postgresql_using='gin'),
        Index('ix_bill_parliament_session', 'parliament', 'session'),
        UniqueConstraint('number', 'parliament', 'session', name='uq_bill_session'),
    )

class BillStatusChange(Base):
    """Track bill status changes over time"""
    __tablename__ = 'bill_status_changes'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bill_id = Column(UUID(as_uuid=True), ForeignKey('bills.id'), nullable=False)
    
    old_status = Column(Enum(BillStatus))
    new_status = Column(Enum(BillStatus), nullable=False)
    change_date = Column(Date, nullable=False)
    description = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    bill = relationship("Bill", back_populates="status_changes")

class HansardDocument(Base):
    """Enhanced Hansard document model from OpenParliament"""
    __tablename__ = 'hansard_documents'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey('parliamentary_sessions.id'), nullable=False)
    
    # Document identification
    document_type = Column(Enum(DocumentType), nullable=False)
    date = Column(Date, nullable=False)
    number = Column(String(10))  # Document number
    sitting_number = Column(Integer)
    
    # Source information
    source_id = Column(Integer, unique=True)  # External source ID
    source_url = Column(String(500))
    xml_source_url = Column(String(500))
    
    # Processing status
    downloaded = Column(Boolean, default=False)
    processed = Column(Boolean, default=False)
    skip_parsing = Column(Boolean, default=False)
    
    # Content metadata
    language = Column(String(2), default='en')  # en, fr
    multilingual = Column(Boolean, default=False)
    word_count = Column(Integer)
    most_frequent_word = Column(String(50))
    
    # Timestamps
    first_imported = Column(DateTime)
    last_imported = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    session = relationship("ParliamentarySession", back_populates="hansard_documents")
    statements = relationship("ParliamentaryStatement", back_populates="document")
    
    __table_args__ = (
        Index('ix_hansard_date', 'date'),
        Index('ix_hansard_type', 'document_type'),
        Index('ix_hansard_processed', 'processed'),
    )

class ParliamentaryStatement(Base):
    """Individual statements/speeches from Hansard"""
    __tablename__ = 'parliamentary_statements'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey('hansard_documents.id'), nullable=False)
    politician_id = Column(UUID(as_uuid=True), ForeignKey('representatives.id'))
    bill_id = Column(UUID(as_uuid=True), ForeignKey('bills.id'))
    
    # Statement content
    sequence = Column(Integer, nullable=False)  # Order within document
    content = Column(Text, nullable=False)
    content_en = Column(Text)
    content_fr = Column(Text)
    
    # Statement metadata
    statement_type = Column(String(50))  # speech, question, response, etc.
    time_offset = Column(Integer)  # Seconds from start of sitting
    who = Column(String(255))  # Speaker name as recorded
    
    # Processing
    search_vector = Column(TSVECTOR)
    word_count = Column(Integer)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    document = relationship("HansardDocument", back_populates="statements")
    politician = relationship("Representative", back_populates="parliamentary_statements")
    bill = relationship("Bill", back_populates="statements")
    
    __table_args__ = (
        Index('ix_statement_search', 'search_vector', postgresql_using='gin'),
        Index('ix_statement_sequence', 'document_id', 'sequence'),
        Index('ix_statement_politician', 'politician_id'),
    )

# =============================================================================
# Committee Models
# =============================================================================

class Committee(Base):
    """Enhanced committee model for all levels of government"""
    __tablename__ = 'committees'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    jurisdiction_id = Column(UUID(as_uuid=True), ForeignKey('jurisdictions.id'), nullable=False)
    parent_committee_id = Column(UUID(as_uuid=True), ForeignKey('committees.id'))
    
    # Basic information
    name = Column(String(255), nullable=False)
    name_en = Column(String(255))
    name_fr = Column(String(255))
    short_name = Column(String(100))
    acronym = Column(String(20))
    
    # Committee details
    committee_type = Column(Enum(CommitteeType), nullable=False)
    mandate = Column(Text)
    description = Column(Text)
    
    # Status
    active = Column(Boolean, default=True)
    start_date = Column(Date)
    end_date = Column(Date)
    
    # External IDs
    external_id = Column(String(255))
    source_url = Column(String(500))
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    data_source = Column(String(100))
    
    # Relationships
    jurisdiction = relationship("Jurisdiction", back_populates="committees")
    parent_committee = relationship("Committee", remote_side=[id])
    subcommittees = relationship("Committee", back_populates="parent_committee")
    meetings = relationship("CommitteeMeeting", back_populates="committee")
    
    # Many-to-many relationships
    members = relationship("Representative", secondary=committee_memberships, back_populates="committees")
    
    __table_args__ = (
        Index('ix_committee_name', 'name'),
        Index('ix_committee_active', 'active'),
    )

class CommitteeMeeting(Base):
    """Committee meetings and hearings"""
    __tablename__ = 'committee_meetings'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    committee_id = Column(UUID(as_uuid=True), ForeignKey('committees.id'), nullable=False)
    
    # Meeting details
    meeting_number = Column(Integer)
    date = Column(Date, nullable=False)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    location = Column(String(255))
    
    # Meeting content
    agenda = Column(Text)
    transcript = Column(Text)
    transcript_url = Column(String(500))
    
    # Status
    public = Column(Boolean, default=True)
    cancelled = Column(Boolean, default=False)
    
    # External tracking
    external_id = Column(String(255))
    source_url = Column(String(500))
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    committee = relationship("Committee", back_populates="meetings")

# =============================================================================
# Voting Models
# =============================================================================

class Vote(Base):
    """Parliamentary and municipal votes"""
    __tablename__ = 'votes'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bill_id = Column(UUID(as_uuid=True), ForeignKey('bills.id'))
    event_id = Column(UUID(as_uuid=True), ForeignKey('events.id'))
    representative_id = Column(UUID(as_uuid=True), ForeignKey('representatives.id'))
    
    # Vote details
    result = Column(Enum(VoteResult), nullable=False)
    vote_date = Column(Date, nullable=False)
    chamber = Column(String(20))  # House, Senate, Council
    
    # Vote description
    description = Column(Text)
    motion_text = Column(Text)
    vote_number = Column(Integer)
    
    # Results summary (for recorded votes)
    yeas = Column(Integer)
    nays = Column(Integer)
    abstentions = Column(Integer)
    absent = Column(Integer)
    
    # External tracking
    external_id = Column(String(255))
    source_url = Column(String(500))
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    bill = relationship("Bill", back_populates="votes")
    event = relationship("Event", back_populates="votes")
    representative = relationship("Representative", back_populates="votes")
    
    __table_args__ = (
        Index('ix_vote_date', 'vote_date'),
        Index('ix_vote_bill', 'bill_id'),
        Index('ix_vote_representative', 'representative_id'),
    )

# =============================================================================
# Event Models
# =============================================================================

class Event(Base):
    """Political events, meetings, and sessions"""
    __tablename__ = 'events'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    jurisdiction_id = Column(UUID(as_uuid=True), ForeignKey('jurisdictions.id'), nullable=False)
    
    # Event details
    title = Column(String(500), nullable=False)
    description = Column(Text)
    event_type = Column(Enum(EventType), nullable=False)
    
    # Timing
    date = Column(Date, nullable=False)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    timezone = Column(String(50), default='America/Toronto')
    
    # Location
    location = Column(String(255))
    address = Column(Text)
    room = Column(String(100))
    
    # Status
    public = Column(Boolean, default=True)
    cancelled = Column(Boolean, default=False)
    rescheduled = Column(Boolean, default=False)
    
    # External tracking
    external_id = Column(String(255))
    source_url = Column(String(500))
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    data_source = Column(String(100))
    
    # Relationships
    jurisdiction = relationship("Jurisdiction", back_populates="events")
    votes = relationship("Vote", back_populates="event")
    
    __table_args__ = (
        Index('ix_event_date', 'date'),
        Index('ix_event_type', 'event_type'),
        Index('ix_event_jurisdiction', 'jurisdiction_id'),
    )

# =============================================================================
# Data Quality and Audit Models
# =============================================================================

class ScrapingRun(Base):
    """Track scraper execution and results"""
    __tablename__ = 'scraping_runs'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    jurisdiction_id = Column(UUID(as_uuid=True), ForeignKey('jurisdictions.id'))
    
    # Run details
    scraper_type = Column(String(100), nullable=False)  # parliament, municipal, etc.
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime)
    duration_seconds = Column(Integer)
    
    # Results
    status = Column(String(50), nullable=False)  # running, completed, failed, partial
    records_found = Column(Integer, default=0)
    records_new = Column(Integer, default=0)
    records_updated = Column(Integer, default=0)
    records_deleted = Column(Integer, default=0)
    errors = Column(Integer, default=0)
    
    # Error details
    error_message = Column(Text)
    error_traceback = Column(Text)
    
    # Configuration
    config = Column(JSONB)  # Scraper configuration used
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    jurisdiction = relationship("Jurisdiction", back_populates="scraping_runs")
    data_quality_issues = relationship("DataQualityIssue", back_populates="scraping_run")

class DataQualityIssue(Base):
    """Track data quality problems"""
    __tablename__ = 'data_quality_issues'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    jurisdiction_id = Column(UUID(as_uuid=True), ForeignKey('jurisdictions.id'))
    scraping_run_id = Column(UUID(as_uuid=True), ForeignKey('scraping_runs.id'))
    
    # Issue details
    issue_type = Column(String(100), nullable=False)  # missing_data, invalid_format, etc.
    severity = Column(String(20), nullable=False)     # low, medium, high, critical
    description = Column(Text, nullable=False)
    
    # Affected data
    table_name = Column(String(100))
    record_id = Column(String(255))
    field_name = Column(String(100))
    expected_value = Column(Text)
    actual_value = Column(Text)
    
    # Resolution
    resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime)
    resolved_by = Column(String(255))
    resolution_notes = Column(Text)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    jurisdiction = relationship("Jurisdiction")
    scraping_run = relationship("ScrapingRun", back_populates="data_quality_issues")

class ChangeLog(Base):
    """Audit trail for all data changes"""
    __tablename__ = 'change_log'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Change details
    table_name = Column(String(100), nullable=False)
    record_id = Column(String(255), nullable=False)
    operation = Column(String(20), nullable=False)  # INSERT, UPDATE, DELETE
    
    # Field changes (for UPDATE operations)
    field_changes = Column(JSONB)  # {field: {old: value, new: value}}
    
    # Context
    changed_by = Column(String(255))  # user_id or 'system'
    changed_via = Column(String(100))  # API, scraper, admin, etc.
    change_reason = Column(String(255))
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('ix_changelog_table_record', 'table_name', 'record_id'),
        Index('ix_changelog_created', 'created_at'),
    )

# =============================================================================
# Search and Performance Models
# =============================================================================

class SearchIndex(Base):
    """Global search index for all entities"""
    __tablename__ = 'search_index'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Entity reference
    entity_type = Column(String(50), nullable=False)  # representative, bill, etc.
    entity_id = Column(String(255), nullable=False)
    
    # Search content
    title = Column(String(500), nullable=False)
    content = Column(Text)
    search_vector = Column(TSVECTOR, nullable=False)
    
    # Metadata for ranking
    jurisdiction_type = Column(String(50))
    entity_date = Column(Date)
    popularity_score = Column(Float, default=1.0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('ix_search_vector', 'search_vector', postgresql_using='gin'),
        Index('ix_search_entity', 'entity_type', 'entity_id'),
        UniqueConstraint('entity_type', 'entity_id'),
    )

# =============================================================================
# Configuration and Performance
# =============================================================================

# Database engine configuration for optimal performance
def create_optimized_engine(database_url: str):
    """Create a PostgreSQL engine with optimal settings"""
    return create_engine(
        database_url,
        echo=False,  # Set to True for SQL debugging
        pool_size=20,
        max_overflow=30,
        pool_pre_ping=True,
        pool_recycle=3600,
        connect_args={
            "options": "-c timezone=America/Toronto"
        }
    )

# Session factory
def create_session_factory(engine):
    """Create a session factory with optimal settings"""
    return sessionmaker(
        bind=engine,
        autocommit=False,
        autoflush=False,
        expire_on_commit=False
    )

# Database initialization
def init_database(engine):
    """Initialize database with all tables and indexes"""
    Base.metadata.create_all(engine)
    
    # Create additional indexes for performance
    with engine.connect() as conn:
        # Full-text search indexes
        conn.execute("""
            CREATE INDEX IF NOT EXISTS ix_representatives_search_gin 
            ON representatives USING gin(search_vector)
        """)
        
        conn.execute("""
            CREATE INDEX IF NOT EXISTS ix_bills_search_gin 
            ON bills USING gin(search_vector)
        """)
        
        conn.execute("""
            CREATE INDEX IF NOT EXISTS ix_statements_search_gin 
            ON parliamentary_statements USING gin(search_vector)
        """)
        
        # Composite indexes for common queries
        conn.execute("""
            CREATE INDEX IF NOT EXISTS ix_bills_jurisdiction_status 
            ON bills(jurisdiction_id, status)
        """)
        
        conn.execute("""
            CREATE INDEX IF NOT EXISTS ix_representatives_jurisdiction_active 
            ON representatives(jurisdiction_id, active)
        """)
        
        conn.execute("""
            CREATE INDEX IF NOT EXISTS ix_events_jurisdiction_date 
            ON events(jurisdiction_id, date DESC)
        """)
        
        conn.commit()

if __name__ == "__main__":
    # Example usage
    import os
    
    database_url = os.getenv(
        "DATABASE_URL", 
        "postgresql://user:password@localhost/openpolicy_merge"
    )
    
    engine = create_optimized_engine(database_url)
    SessionLocal = create_session_factory(engine)
    
    # Initialize database
    init_database(engine)
    
    print("Database models and indexes created successfully!")