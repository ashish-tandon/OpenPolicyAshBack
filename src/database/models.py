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
    """Jurisdiction types"""
    FEDERAL = "federal"
    PROVINCIAL = "provincial"
    MUNICIPAL = "municipal"


class RepresentativeRole(enum.Enum):
    """Representative roles"""
    MP = "mp"
    MLA = "mla"
    MPP = "mpp"
    COUNCILLOR = "councillor"
    MAYOR = "mayor"
    PREMIER = "premier"
    PRIME_MINISTER = "prime_minister"


class BillStatus(enum.Enum):
    """Bill statuses"""
    INTRODUCED = "introduced"
    FIRST_READING = "first_reading"
    SECOND_READING = "second_reading"
    THIRD_READING = "third_reading"
    PASSED = "passed"
    DEFEATED = "defeated"
    WITHDRAWN = "withdrawn"


class EventType(enum.Enum):
    """Event types"""
    SESSION = "session"
    COMMITTEE_MEETING = "committee_meeting"
    VOTE = "vote"
    DEBATE = "debate"
    ANNOUNCEMENT = "announcement"


class VoteResult(enum.Enum):
    """Vote results"""
    YES = "yes"
    NO = "no"
    ABSTAIN = "abstain"
    ABSENT = "absent"


class Jurisdiction(Base):
    """Jurisdiction model (Federal, Provincial, Municipal)"""
    __tablename__ = 'jurisdictions'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    jurisdiction_type = Column(Enum(JurisdictionType), nullable=False)
    code = Column(String(50), unique=True, nullable=False)
    website = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    representatives = relationship("Representative", back_populates="jurisdiction")
    bills = relationship("Bill", back_populates="jurisdiction")
    committees = relationship("Committee", back_populates="jurisdiction")
    events = relationship("Event", back_populates="jurisdiction")
    scraping_runs = relationship("ScrapingRun", back_populates="jurisdiction")
    data_quality_issues = relationship("DataQualityIssue", back_populates="jurisdiction")


class Representative(Base):
    """Representative model (MPs, MLAs, Councillors, etc.)"""
    __tablename__ = 'representatives'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    jurisdiction_id = Column(UUID(as_uuid=True), ForeignKey('jurisdictions.id'), nullable=False)
    name = Column(String(255), nullable=False)
    role = Column(Enum(RepresentativeRole), nullable=False)
    party = Column(String(255))
    riding = Column(String(255))
    email = Column(String(255))
    phone = Column(String(50))
    website = Column(String(500))
    bio = Column(Text)
    image_url = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    jurisdiction = relationship("Jurisdiction", back_populates="representatives")
    bill_sponsorships = relationship("BillSponsorship", back_populates="representative")
    committee_memberships = relationship("CommitteeMembership", back_populates="representative")
    votes = relationship("Vote", back_populates="representative")
    
    # Indexes
    __table_args__ = (
        Index('idx_representative_jurisdiction', 'jurisdiction_id'),
        Index('idx_representative_party', 'party'),
        Index('idx_representative_riding', 'riding'),
    )


class Bill(Base):
    """Bill model"""
    __tablename__ = 'bills'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    jurisdiction_id = Column(UUID(as_uuid=True), ForeignKey('jurisdictions.id'), nullable=False)
    bill_number = Column(String(50), nullable=False)
    title = Column(String(500), nullable=False)
    summary = Column(Text)
    status = Column(Enum(BillStatus), nullable=False)
    introduced_date = Column(Date)
    passed_date = Column(Date)
    bill_text_url = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    jurisdiction = relationship("Jurisdiction", back_populates="bills")
    sponsorships = relationship("BillSponsorship", back_populates="bill")
    events = relationship("Event", back_populates="bill")
    votes = relationship("Vote", back_populates="bill")
    
    # Indexes
    __table_args__ = (
        Index('idx_bill_jurisdiction', 'jurisdiction_id'),
        Index('idx_bill_number', 'bill_number'),
        Index('idx_bill_status', 'status'),
        Index('idx_bill_introduced_date', 'introduced_date'),
        UniqueConstraint('jurisdiction_id', 'bill_number', name='uq_bill_jurisdiction_number'),
    )


class BillSponsorship(Base):
    """Bill sponsorship relationship"""
    __tablename__ = 'bill_sponsorships'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bill_id = Column(UUID(as_uuid=True), ForeignKey('bills.id'), nullable=False)
    representative_id = Column(UUID(as_uuid=True), ForeignKey('representatives.id'), nullable=False)
    is_primary_sponsor = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    bill = relationship("Bill", back_populates="sponsorships")
    representative = relationship("Representative", back_populates="bill_sponsorships")
    
    # Indexes
    __table_args__ = (
        Index('idx_sponsorship_bill', 'bill_id'),
        Index('idx_sponsorship_representative', 'representative_id'),
    )


class Committee(Base):
    """Committee model"""
    __tablename__ = 'committees'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    jurisdiction_id = Column(UUID(as_uuid=True), ForeignKey('jurisdictions.id'), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    website = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    jurisdiction = relationship("Jurisdiction", back_populates="committees")
    memberships = relationship("CommitteeMembership", back_populates="committee")
    events = relationship("Event", back_populates="committee")
    
    # Indexes
    __table_args__ = (
        Index('idx_committee_jurisdiction', 'jurisdiction_id'),
        Index('idx_committee_name', 'name'),
    )


class CommitteeMembership(Base):
    """Committee membership relationship"""
    __tablename__ = 'committee_memberships'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    committee_id = Column(UUID(as_uuid=True), ForeignKey('committees.id'), nullable=False)
    representative_id = Column(UUID(as_uuid=True), ForeignKey('representatives.id'), nullable=False)
    role = Column(String(100))  # Chair, Vice-Chair, Member, etc.
    start_date = Column(Date)
    end_date = Column(Date)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    committee = relationship("Committee", back_populates="memberships")
    representative = relationship("Representative", back_populates="committee_memberships")
    
    # Indexes
    __table_args__ = (
        Index('idx_membership_committee', 'committee_id'),
        Index('idx_membership_representative', 'representative_id'),
    )


class Event(Base):
    """Event model (sessions, meetings, votes, etc.)"""
    __tablename__ = 'events'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    jurisdiction_id = Column(UUID(as_uuid=True), ForeignKey('jurisdictions.id'), nullable=False)
    bill_id = Column(UUID(as_uuid=True), ForeignKey('bills.id'), nullable=True)
    committee_id = Column(UUID(as_uuid=True), ForeignKey('committees.id'), nullable=True)
    event_type = Column(Enum(EventType), nullable=False)
    title = Column(String(500), nullable=False)
    description = Column(Text)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    location = Column(String(255))
    agenda_url = Column(String(500))
    minutes_url = Column(String(500))
    video_url = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    jurisdiction = relationship("Jurisdiction", back_populates="events")
    bill = relationship("Bill", back_populates="events")
    committee = relationship("Committee", back_populates="events")
    votes = relationship("Vote", back_populates="event")
    
    # Indexes
    __table_args__ = (
        Index('idx_event_jurisdiction', 'jurisdiction_id'),
        Index('idx_event_type', 'event_type'),
        Index('idx_event_start_time', 'start_time'),
        Index('idx_event_bill', 'bill_id'),
        Index('idx_event_committee', 'committee_id'),
    )


class Vote(Base):
    """Vote model"""
    __tablename__ = 'votes'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id = Column(UUID(as_uuid=True), ForeignKey('events.id'), nullable=False)
    bill_id = Column(UUID(as_uuid=True), ForeignKey('bills.id'), nullable=True)
    representative_id = Column(UUID(as_uuid=True), ForeignKey('representatives.id'), nullable=False)
    vote_result = Column(Enum(VoteResult), nullable=False)
    vote_time = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    event = relationship("Event", back_populates="votes")
    bill = relationship("Bill", back_populates="votes")
    representative = relationship("Representative", back_populates="votes")
    
    # Indexes
    __table_args__ = (
        Index('idx_vote_event', 'event_id'),
        Index('idx_vote_bill', 'bill_id'),
        Index('idx_vote_representative', 'representative_id'),
        Index('idx_vote_result', 'vote_result'),
        Index('idx_vote_time', 'vote_time'),
    )


class ScrapingRun(Base):
    """Scraping run tracking"""
    __tablename__ = 'scraping_runs'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    jurisdiction_id = Column(UUID(as_uuid=True), ForeignKey('jurisdictions.id'), nullable=False)
    scraper_name = Column(String(255), nullable=False)
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime)
    status = Column(String(50), nullable=False)  # running, completed, failed
    records_processed = Column(Integer, default=0)
    records_created = Column(Integer, default=0)
    records_updated = Column(Integer, default=0)
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    jurisdiction = relationship("Jurisdiction", back_populates="scraping_runs")
    
    # Indexes
    __table_args__ = (
        Index('idx_scraping_jurisdiction', 'jurisdiction_id'),
        Index('idx_scraping_status', 'status'),
        Index('idx_scraping_start_time', 'start_time'),
    )


class DataQualityIssue(Base):
    """Data quality issues tracking"""
    __tablename__ = 'data_quality_issues'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    jurisdiction_id = Column(UUID(as_uuid=True), ForeignKey('jurisdictions.id'), nullable=False)
    issue_type = Column(String(100), nullable=False)  # missing_data, invalid_format, etc.
    severity = Column(String(50), nullable=False)  # low, medium, high, critical
    description = Column(Text, nullable=False)
    affected_records = Column(Integer, default=0)
    resolved = Column(Boolean, default=False)
    resolution_notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime)
    
    # Relationships
    jurisdiction = relationship("Jurisdiction", back_populates="data_quality_issues")
    
    # Indexes
    __table_args__ = (
        Index('idx_quality_jurisdiction', 'jurisdiction_id'),
        Index('idx_quality_type', 'issue_type'),
        Index('idx_quality_severity', 'severity'),
        Index('idx_quality_resolved', 'resolved'),
    )


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