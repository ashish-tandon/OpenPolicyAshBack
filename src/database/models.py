"""
OpenPolicy Database Models

This module defines the database schema for storing Canadian civic data
including representatives, bills, committees, events, votes, and other civic information.
"""

from sqlalchemy import (
    create_engine, Column, Integer, String, Text, DateTime, Boolean,
    ForeignKey, JSON, Enum, UniqueConstraint, Index, Date
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
import enum

Base = declarative_base()

class JurisdictionType(enum.Enum):
    FEDERAL = "federal"
    PROVINCIAL = "provincial"
    MUNICIPAL = "municipal"

class RepresentativeRole(enum.Enum):
    MP = "MP"  # Member of Parliament
    MPP = "MPP"  # Member of Provincial Parliament
    MLA = "MLA"  # Member of Legislative Assembly
    MNA = "MNA"  # Member of National Assembly (Quebec)
    MAYOR = "Mayor"
    COUNCILLOR = "Councillor"
    REEVE = "Reeve"
    OTHER = "Other"

class BillStatus(enum.Enum):
    INTRODUCED = "introduced"
    FIRST_READING = "first_reading"
    SECOND_READING = "second_reading"
    COMMITTEE = "committee"
    THIRD_READING = "third_reading"
    PASSED = "passed"
    ROYAL_ASSENT = "royal_assent"
    FAILED = "failed"
    WITHDRAWN = "withdrawn"

class EventType(enum.Enum):
    MEETING = "meeting"
    VOTE = "vote"
    READING = "reading"
    COMMITTEE_MEETING = "committee_meeting"
    OTHER = "other"

class VoteResult(enum.Enum):
    YES = "yes"
    NO = "no"
    ABSTAIN = "abstain"
    ABSENT = "absent"

# Core Tables
class Jurisdiction(Base):
    __tablename__ = 'jurisdictions'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    jurisdiction_type = Column(Enum(JurisdictionType), nullable=False)
    division_id = Column(String(255), unique=True)  # OpenCivicData division ID
    province = Column(String(2))  # Province/territory code
    url = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    representatives = relationship("Representative", back_populates="jurisdiction")
    bills = relationship("Bill", back_populates="jurisdiction")
    committees = relationship("Committee", back_populates="jurisdiction")
    events = relationship("Event", back_populates="jurisdiction")
    
    __table_args__ = (
        Index('idx_jurisdiction_type', 'jurisdiction_type'),
        Index('idx_jurisdiction_province', 'province'),
    )

class Representative(Base):
    __tablename__ = 'representatives'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    jurisdiction_id = Column(UUID(as_uuid=True), ForeignKey('jurisdictions.id'), nullable=False)
    
    # Basic Information
    name = Column(String(255), nullable=False)
    first_name = Column(String(100))
    last_name = Column(String(100))
    role = Column(Enum(RepresentativeRole), nullable=False)
    party = Column(String(100))
    district = Column(String(255))
    
    # Contact Information
    email = Column(String(255))
    phone = Column(String(50))
    office_address = Column(Text)
    website = Column(String(500))
    
    # Social Media
    facebook_url = Column(String(500))
    twitter_url = Column(String(500))
    instagram_url = Column(String(500))
    linkedin_url = Column(String(500))
    
    # Term Information
    term_start = Column(DateTime)
    term_end = Column(DateTime)
    
    # Media
    photo_url = Column(String(500))
    biography = Column(Text)
    
    # Metadata
    source_url = Column(String(500))
    external_id = Column(String(100))  # ID from source system
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    jurisdiction = relationship("Jurisdiction", back_populates="representatives")
    bill_sponsorships = relationship("BillSponsorship", back_populates="representative")
    committee_memberships = relationship("CommitteeMembership", back_populates="representative")
    votes = relationship("Vote", back_populates="representative")
    
    __table_args__ = (
        Index('idx_representative_jurisdiction', 'jurisdiction_id'),
        Index('idx_representative_role', 'role'),
        Index('idx_representative_party', 'party'),
        Index('idx_representative_district', 'district'),
        UniqueConstraint('jurisdiction_id', 'external_id', name='uq_representative_external_id'),
    )

class Bill(Base):
    __tablename__ = 'bills'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    jurisdiction_id = Column(UUID(as_uuid=True), ForeignKey('jurisdictions.id'), nullable=False)
    
    # Bill Information
    bill_number = Column(String(50), nullable=False)
    title = Column(String(500), nullable=False)
    summary = Column(Text)
    full_text = Column(Text)
    status = Column(Enum(BillStatus), nullable=False)
    
    # Legislative Process
    introduced_date = Column(DateTime)
    first_reading_date = Column(DateTime)
    second_reading_date = Column(DateTime)
    third_reading_date = Column(DateTime)
    passed_date = Column(DateTime)
    royal_assent_date = Column(DateTime)
    
    # Legislative Body
    legislative_body = Column(String(100))  # House of Commons, Senate, Provincial Legislature, etc.
    
    # Metadata
    source_url = Column(String(500))
    external_id = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    jurisdiction = relationship("Jurisdiction", back_populates="bills")
    sponsorships = relationship("BillSponsorship", back_populates="bill")
    events = relationship("Event", back_populates="bill")
    votes = relationship("Vote", back_populates="bill")
    
    __table_args__ = (
        Index('idx_bill_jurisdiction', 'jurisdiction_id'),
        Index('idx_bill_status', 'status'),
        Index('idx_bill_number', 'bill_number'),
        UniqueConstraint('jurisdiction_id', 'bill_number', name='uq_bill_number'),
    )

class BillSponsorship(Base):
    __tablename__ = 'bill_sponsorships'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bill_id = Column(UUID(as_uuid=True), ForeignKey('bills.id'), nullable=False)
    representative_id = Column(UUID(as_uuid=True), ForeignKey('representatives.id'), nullable=False)
    
    is_primary_sponsor = Column(Boolean, default=False)
    sponsorship_type = Column(String(50))  # sponsor, co-sponsor, etc.
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    bill = relationship("Bill", back_populates="sponsorships")
    representative = relationship("Representative", back_populates="bill_sponsorships")
    
    __table_args__ = (
        Index('idx_bill_sponsorship_bill', 'bill_id'),
        Index('idx_bill_sponsorship_representative', 'representative_id'),
        UniqueConstraint('bill_id', 'representative_id', name='uq_bill_sponsorship'),
    )

class Committee(Base):
    __tablename__ = 'committees'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    jurisdiction_id = Column(UUID(as_uuid=True), ForeignKey('jurisdictions.id'), nullable=False)
    
    name = Column(String(255), nullable=False)
    description = Column(Text)
    committee_type = Column(String(100))  # standing, special, joint, etc.
    
    # Metadata
    source_url = Column(String(500))
    external_id = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    jurisdiction = relationship("Jurisdiction", back_populates="committees")
    memberships = relationship("CommitteeMembership", back_populates="committee")
    events = relationship("Event", back_populates="committee")
    
    __table_args__ = (
        Index('idx_committee_jurisdiction', 'jurisdiction_id'),
        UniqueConstraint('jurisdiction_id', 'name', name='uq_committee_name'),
    )

class CommitteeMembership(Base):
    __tablename__ = 'committee_memberships'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    committee_id = Column(UUID(as_uuid=True), ForeignKey('committees.id'), nullable=False)
    representative_id = Column(UUID(as_uuid=True), ForeignKey('representatives.id'), nullable=False)
    
    role = Column(String(100))  # chair, vice-chair, member, etc.
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    committee = relationship("Committee", back_populates="memberships")
    representative = relationship("Representative", back_populates="committee_memberships")
    
    __table_args__ = (
        Index('idx_committee_membership_committee', 'committee_id'),
        Index('idx_committee_membership_representative', 'representative_id'),
    )

class Event(Base):
    __tablename__ = 'events'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    jurisdiction_id = Column(UUID(as_uuid=True), ForeignKey('jurisdictions.id'), nullable=False)
    bill_id = Column(UUID(as_uuid=True), ForeignKey('bills.id'), nullable=True)
    committee_id = Column(UUID(as_uuid=True), ForeignKey('committees.id'), nullable=True)
    
    name = Column(String(255), nullable=False)
    description = Column(Text)
    event_type = Column(Enum(EventType), nullable=False)
    
    event_date = Column(DateTime, nullable=False)
    location = Column(String(255))
    
    # Metadata
    source_url = Column(String(500))
    external_id = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    jurisdiction = relationship("Jurisdiction", back_populates="events")
    bill = relationship("Bill", back_populates="events")
    committee = relationship("Committee", back_populates="events")
    votes = relationship("Vote", back_populates="event")
    
    __table_args__ = (
        Index('idx_event_jurisdiction', 'jurisdiction_id'),
        Index('idx_event_date', 'event_date'),
        Index('idx_event_type', 'event_type'),
    )

class Vote(Base):
    __tablename__ = 'votes'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id = Column(UUID(as_uuid=True), ForeignKey('events.id'), nullable=False)
    bill_id = Column(UUID(as_uuid=True), ForeignKey('bills.id'), nullable=True)
    representative_id = Column(UUID(as_uuid=True), ForeignKey('representatives.id'), nullable=False)
    
    vote_result = Column(Enum(VoteResult), nullable=False)
    vote_date = Column(DateTime, nullable=False)
    
    # Metadata
    source_url = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    event = relationship("Event", back_populates="votes")
    bill = relationship("Bill", back_populates="votes")
    representative = relationship("Representative", back_populates="votes")
    
    __table_args__ = (
        Index('idx_vote_event', 'event_id'),
        Index('idx_vote_bill', 'bill_id'),
        Index('idx_vote_representative', 'representative_id'),
        Index('idx_vote_date', 'vote_date'),
        UniqueConstraint('event_id', 'representative_id', name='uq_event_representative_vote'),
    )

# Additional Tables for Data Quality and System Management
class ScrapingRun(Base):
    __tablename__ = 'scraping_runs'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    jurisdiction_id = Column(UUID(as_uuid=True), ForeignKey('jurisdictions.id'), nullable=False)
    
    run_type = Column(String(50), nullable=False)  # 'scheduled', 'manual', 'test'
    status = Column(String(50), nullable=False)  # 'running', 'completed', 'failed'
    
    start_time = Column(DateTime, nullable=False, default=datetime.utcnow)
    end_time = Column(DateTime)
    
    records_processed = Column(Integer, default=0)
    records_created = Column(Integer, default=0)
    records_updated = Column(Integer, default=0)
    errors_count = Column(Integer, default=0)
    
    error_log = Column(JSON)  # Store detailed error information
    summary = Column(JSON)    # Store run summary information
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_scraping_run_jurisdiction', 'jurisdiction_id'),
        Index('idx_scraping_run_status', 'status'),
        Index('idx_scraping_run_start_time', 'start_time'),
    )

class DataQualityIssue(Base):
    __tablename__ = 'data_quality_issues'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    jurisdiction_id = Column(UUID(as_uuid=True), ForeignKey('jurisdictions.id'), nullable=False)
    
    issue_type = Column(String(100), nullable=False)  # 'missing_field', 'invalid_format', 'duplicate', etc.
    severity = Column(String(20), nullable=False)     # 'low', 'medium', 'high', 'critical'
    description = Column(Text, nullable=False)
    
    affected_table = Column(String(100))
    affected_record_id = Column(String(100))
    
    detected_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    resolved_at = Column(DateTime)
    resolution_notes = Column(Text)
    
    __table_args__ = (
        Index('idx_data_quality_jurisdiction', 'jurisdiction_id'),
        Index('idx_data_quality_type', 'issue_type'),
        Index('idx_data_quality_severity', 'severity'),
        Index('idx_data_quality_detected', 'detected_at'),
    )

# Enhanced Parliamentary Models - OpenParliament Integration
class ParliamentarySession(Base):
    __tablename__ = "parliamentary_sessions"
    
    id = Column(Integer, primary_key=True)
    parliament_number = Column(Integer, nullable=False)
    session_number = Column(Integer, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    hansard_records = relationship("HansardRecord", back_populates="session")
    committee_meetings = relationship("CommitteeMeeting", back_populates="session")
    
    def __repr__(self):
        return f"<ParliamentarySession {self.parliament_number}-{self.session_number}>"

class HansardRecord(Base):
    __tablename__ = "hansard_records"
    
    id = Column(Integer, primary_key=True)
    date = Column(Date, nullable=False)
    sitting_number = Column(Integer)
    document_url = Column(String(500))
    pdf_url = Column(String(500))
    xml_url = Column(String(500))
    processed = Column(Boolean, default=False)
    speech_count = Column(Integer, default=0)
    
    # Foreign Keys
    session_id = Column(Integer, ForeignKey("parliamentary_sessions.id"))
    
    # Relationships
    session = relationship("ParliamentarySession", back_populates="hansard_records")
    speeches = relationship("Speech", back_populates="hansard")
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<HansardRecord {self.date} Session {self.session_id}>"

class Speech(Base):
    __tablename__ = "speeches"
    
    id = Column(Integer, primary_key=True)
    speaker_name = Column(String(200))
    speaker_title = Column(String(200))
    content = Column(Text)
    time_spoken = Column(DateTime)
    speech_type = Column(String(50))  # 'statement', 'question', 'response', etc.
    
    # Foreign Keys
    hansard_id = Column(Integer, ForeignKey("hansard_records.id"))
    representative_id = Column(Integer, ForeignKey("representatives.id"), nullable=True)
    
    # Relationships
    hansard = relationship("HansardRecord", back_populates="speeches")
    representative = relationship("Representative")
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Speech by {self.speaker_name} in Hansard {self.hansard_id}>"

class CommitteeMeeting(Base):
    __tablename__ = "committee_meetings"
    
    id = Column(Integer, primary_key=True)
    committee_name = Column(String(200), nullable=False)
    meeting_date = Column(Date, nullable=False)
    meeting_number = Column(Integer)
    evidence_url = Column(String(500))
    transcript_url = Column(String(500))
    processed = Column(Boolean, default=False)
    
    # Foreign Keys  
    session_id = Column(Integer, ForeignKey("parliamentary_sessions.id"))
    
    # Relationships
    session = relationship("ParliamentarySession", back_populates="committee_meetings")
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<CommitteeMeeting {self.committee_name} on {self.meeting_date}>"

# Database utility functions
def create_engine_from_config(database_url: str):
    """Create database engine with optimal settings"""
    return create_engine(
        database_url,
        pool_size=10,
        max_overflow=20,
        pool_recycle=3600,
        echo=False  # Set to True for SQL debugging
    )

def create_all_tables(engine):
    """Create all tables in the database"""
    Base.metadata.create_all(engine)

def get_session_factory(engine):
    """Get a session factory for database operations"""
    return sessionmaker(bind=engine)