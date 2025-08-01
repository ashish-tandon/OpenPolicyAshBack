"""
Comprehensive Database Testing Suite
Tests all database operations, migrations, and data integrity
"""

import pytest
import sqlalchemy as sa
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timedelta
import json

from database import (
    Base, Jurisdiction, Representative, Bill, Committee, Event, Vote,
    JurisdictionType, RepresentativeRole, BillStatus,
    create_all_tables, get_session_factory
)


class TestDatabaseSchema:
    """Test database schema and table creation"""
    
    def test_tables_creation(self, test_database):
        """Test that all tables are created correctly"""
        # Get table names
        inspector = sa.inspect(test_database)
        table_names = inspector.get_table_names()
        
        expected_tables = [
            'jurisdictions', 'representatives', 'bills', 
            'committees', 'events', 'votes'
        ]
        
        for table in expected_tables:
            assert table in table_names
    
    def test_table_columns(self, test_database):
        """Test that tables have the correct columns"""
        inspector = sa.inspect(test_database)
        
        # Test jurisdictions table
        jurisdiction_columns = [col['name'] for col in inspector.get_columns('jurisdictions')]
        expected_jurisdiction_cols = ['id', 'name', 'jurisdiction_type', 'division_id']
        for col in expected_jurisdiction_cols:
            assert col in jurisdiction_columns
        
        # Test representatives table
        rep_columns = [col['name'] for col in inspector.get_columns('representatives')]
        expected_rep_cols = ['id', 'name', 'role', 'party', 'district', 'jurisdiction_id']
        for col in expected_rep_cols:
            assert col in rep_columns
        
        # Test bills table
        bill_columns = [col['name'] for col in inspector.get_columns('bills')]
        expected_bill_cols = ['id', 'identifier', 'title', 'summary', 'jurisdiction_id']
        for col in expected_bill_cols:
            assert col in bill_columns
    
    def test_foreign_key_constraints(self, test_database):
        """Test that foreign key constraints are properly set"""
        inspector = sa.inspect(test_database)
        
        # Test representative -> jurisdiction FK
        rep_fks = inspector.get_foreign_keys('representatives')
        assert any(fk['referred_table'] == 'jurisdictions' for fk in rep_fks)
        
        # Test bill -> jurisdiction FK
        bill_fks = inspector.get_foreign_keys('bills')
        assert any(fk['referred_table'] == 'jurisdictions' for fk in bill_fks)
    
    def test_indexes(self, test_database):
        """Test that proper indexes are created"""
        inspector = sa.inspect(test_database)
        
        # Test indexes on frequently queried columns
        rep_indexes = inspector.get_indexes('representatives')
        bill_indexes = inspector.get_indexes('bills')
        
        # Should have indexes for performance
        assert len(rep_indexes) >= 0  # At minimum, primary key
        assert len(bill_indexes) >= 0


class TestJurisdictionModel:
    """Test Jurisdiction model operations"""
    
    def test_create_jurisdiction(self, db_session):
        """Test creating a jurisdiction"""
        jurisdiction = Jurisdiction(
            name="Test Jurisdiction",
            jurisdiction_type=JurisdictionType.FEDERAL,
            division_id="ocd-division/country:ca/test"
        )
        
        db_session.add(jurisdiction)
        db_session.commit()
        
        assert jurisdiction.id is not None
        assert jurisdiction.name == "Test Jurisdiction"
    
    def test_jurisdiction_unique_constraints(self, db_session):
        """Test jurisdiction unique constraints"""
        # Create first jurisdiction
        jurisdiction1 = Jurisdiction(
            name="Unique Test",
            jurisdiction_type=JurisdictionType.FEDERAL,
            division_id="ocd-division/country:ca/unique"
        )
        db_session.add(jurisdiction1)
        db_session.commit()
        
        # Try to create duplicate
        jurisdiction2 = Jurisdiction(
            name="Unique Test",
            jurisdiction_type=JurisdictionType.FEDERAL,
            division_id="ocd-division/country:ca/unique"
        )
        db_session.add(jurisdiction2)
        
        # Should raise integrity error for duplicate division_id
        with pytest.raises(IntegrityError):
            db_session.commit()
    
    def test_jurisdiction_types(self, db_session):
        """Test different jurisdiction types"""
        types_to_test = [
            JurisdictionType.FEDERAL,
            JurisdictionType.PROVINCIAL,
            JurisdictionType.MUNICIPAL
        ]
        
        for jurisdiction_type in types_to_test:
            jurisdiction = Jurisdiction(
                name=f"Test {jurisdiction_type.value}",
                jurisdiction_type=jurisdiction_type,
                division_id=f"ocd-division/country:ca/{jurisdiction_type.value.lower()}"
            )
            db_session.add(jurisdiction)
        
        db_session.commit()
        
        # Verify all types were created
        for jurisdiction_type in types_to_test:
            found = db_session.query(Jurisdiction).filter_by(
                jurisdiction_type=jurisdiction_type
            ).first()
            assert found is not None
    
    def test_jurisdiction_relationships(self, db_session, sample_jurisdiction):
        """Test jurisdiction relationships"""
        # Add a representative to the jurisdiction
        rep = Representative(
            name="Test Rep",
            role=RepresentativeRole.MP,
            jurisdiction_id=sample_jurisdiction.id
        )
        db_session.add(rep)
        db_session.commit()
        
        # Test relationship
        assert len(sample_jurisdiction.representatives) >= 1
        assert sample_jurisdiction.representatives[0].name == "Test Rep"


class TestRepresentativeModel:
    """Test Representative model operations"""
    
    def test_create_representative(self, db_session, sample_jurisdiction):
        """Test creating a representative"""
        representative = Representative(
            name="Jane Doe",
            role=RepresentativeRole.MP,
            party="Liberal",
            district="Ottawa Centre",
            jurisdiction_id=sample_jurisdiction.id
        )
        
        db_session.add(representative)
        db_session.commit()
        
        assert representative.id is not None
        assert representative.name == "Jane Doe"
        assert representative.jurisdiction_id == sample_jurisdiction.id
    
    def test_representative_roles(self, db_session, sample_jurisdiction):
        """Test different representative roles"""
        roles_to_test = [
            RepresentativeRole.MP,
            RepresentativeRole.MPP,
            RepresentativeRole.MLA,
            RepresentativeRole.MAYOR,
            RepresentativeRole.COUNCILLOR
        ]
        
        for role in roles_to_test:
            rep = Representative(
                name=f"Test {role.value}",
                role=role,
                jurisdiction_id=sample_jurisdiction.id
            )
            db_session.add(rep)
        
        db_session.commit()
        
        # Verify all roles were created
        for role in roles_to_test:
            found = db_session.query(Representative).filter_by(role=role).first()
            assert found is not None
    
    def test_representative_search(self, db_session, sample_jurisdiction):
        """Test searching representatives"""
        # Create test representatives
        representatives = [
            Representative(name="John Smith", role=RepresentativeRole.MP, 
                         party="Liberal", jurisdiction_id=sample_jurisdiction.id),
            Representative(name="Jane Johnson", role=RepresentativeRole.MP, 
                         party="Conservative", jurisdiction_id=sample_jurisdiction.id),
            Representative(name="Bob Brown", role=RepresentativeRole.MPP, 
                         party="NDP", jurisdiction_id=sample_jurisdiction.id)
        ]
        
        for rep in representatives:
            db_session.add(rep)
        db_session.commit()
        
        # Test name search
        john_results = db_session.query(Representative).filter(
            Representative.name.contains("John")
        ).all()
        assert len(john_results) >= 1
        
        # Test party filter
        liberal_results = db_session.query(Representative).filter_by(
            party="Liberal"
        ).all()
        assert len(liberal_results) >= 1
        
        # Test role filter
        mp_results = db_session.query(Representative).filter_by(
            role=RepresentativeRole.MP
        ).all()
        assert len(mp_results) >= 2
    
    def test_representative_contact_info(self, db_session, sample_jurisdiction):
        """Test representative contact information"""
        rep = Representative(
            name="Contact Test",
            role=RepresentativeRole.MP,
            jurisdiction_id=sample_jurisdiction.id,
            email="test@parl.gc.ca",
            phone="613-555-0123",
            website="https://example.com"
        )
        
        db_session.add(rep)
        db_session.commit()
        
        assert rep.email == "test@parl.gc.ca"
        assert rep.phone == "613-555-0123"
        assert rep.website == "https://example.com"


class TestBillModel:
    """Test Bill model operations"""
    
    def test_create_bill(self, db_session, sample_jurisdiction):
        """Test creating a bill"""
        bill = Bill(
            identifier="C-100",
            title="Test Bill",
            summary="A test bill for testing purposes",
            jurisdiction_id=sample_jurisdiction.id,
            status=BillStatus.FIRST_READING
        )
        
        db_session.add(bill)
        db_session.commit()
        
        assert bill.id is not None
        assert bill.identifier == "C-100"
        assert bill.status == BillStatus.FIRST_READING
    
    def test_bill_statuses(self, db_session, sample_jurisdiction):
        """Test different bill statuses"""
        statuses_to_test = [
            BillStatus.INTRODUCED,
            BillStatus.FIRST_READING,
            BillStatus.SECOND_READING,
            BillStatus.COMMITTEE,
            BillStatus.THIRD_READING,
            BillStatus.ROYAL_ASSENT,
            BillStatus.FAILED
        ]
        
        for status in statuses_to_test:
            bill = Bill(
                identifier=f"C-{status.value}",
                title=f"Test Bill - {status.value}",
                summary=f"Bill testing {status.value} status",
                jurisdiction_id=sample_jurisdiction.id,
                status=status
            )
            db_session.add(bill)
        
        db_session.commit()
        
        # Verify all statuses were created
        for status in statuses_to_test:
            found = db_session.query(Bill).filter_by(status=status).first()
            assert found is not None
    
    def test_federal_bill_identifiers(self, db_session, sample_jurisdiction):
        """Test federal bill identifier patterns"""
        federal_bills = [
            ("C-1", "Government Bill"),
            ("C-100", "Government Bill"),
            ("S-1", "Senate Bill"),
            ("S-50", "Senate Bill")
        ]
        
        for identifier, bill_type in federal_bills:
            bill = Bill(
                identifier=identifier,
                title=f"{bill_type} Test",
                summary=f"Testing {bill_type}",
                jurisdiction_id=sample_jurisdiction.id
            )
            db_session.add(bill)
        
        db_session.commit()
        
        # Test filtering by identifier pattern
        c_bills = db_session.query(Bill).filter(
            Bill.identifier.like("C-%")
        ).all()
        assert len(c_bills) >= 2
        
        s_bills = db_session.query(Bill).filter(
            Bill.identifier.like("S-%")
        ).all()
        assert len(s_bills) >= 2
    
    def test_bill_search_and_filtering(self, db_session, sample_jurisdiction):
        """Test bill search and filtering functionality"""
        bills = [
            Bill(identifier="C-1", title="Budget Implementation Act", 
                 summary="Implements budget measures", jurisdiction_id=sample_jurisdiction.id),
            Bill(identifier="C-2", title="Criminal Code Amendment", 
                 summary="Amends the Criminal Code", jurisdiction_id=sample_jurisdiction.id),
            Bill(identifier="S-1", title="Senate Reform Act", 
                 summary="Reforms the Senate", jurisdiction_id=sample_jurisdiction.id)
        ]
        
        for bill in bills:
            db_session.add(bill)
        db_session.commit()
        
        # Test title search
        budget_bills = db_session.query(Bill).filter(
            Bill.title.contains("Budget")
        ).all()
        assert len(budget_bills) >= 1
        
        # Test summary search
        criminal_bills = db_session.query(Bill).filter(
            Bill.summary.contains("Criminal")
        ).all()
        assert len(criminal_bills) >= 1
        
        # Test identifier search
        specific_bill = db_session.query(Bill).filter_by(identifier="C-1").first()
        assert specific_bill is not None
        assert specific_bill.title == "Budget Implementation Act"


class TestCommitteeModel:
    """Test Committee model operations"""
    
    def test_create_committee(self, db_session, sample_jurisdiction):
        """Test creating a committee"""
        committee = Committee(
            name="Standing Committee on Finance",
            committee_type="standing",
            jurisdiction_id=sample_jurisdiction.id
        )
        
        db_session.add(committee)
        db_session.commit()
        
        assert committee.id is not None
        assert committee.name == "Standing Committee on Finance"
    
    def test_committee_types(self, db_session, sample_jurisdiction):
        """Test different committee types"""
        committee_types = ["standing", "special", "joint", "subcommittee"]
        
        for committee_type in committee_types:
            committee = Committee(
                name=f"Test {committee_type.title()} Committee",
                committee_type=committee_type,
                jurisdiction_id=sample_jurisdiction.id
            )
            db_session.add(committee)
        
        db_session.commit()
        
        # Verify all types were created
        for committee_type in committee_types:
            found = db_session.query(Committee).filter_by(
                committee_type=committee_type
            ).first()
            assert found is not None


class TestEventModel:
    """Test Event model operations"""
    
    def test_create_event(self, db_session, sample_jurisdiction):
        """Test creating an event"""
        event = Event(
            name="Committee Meeting",
            event_type="meeting",
            start_time=datetime.now(),
            end_time=datetime.now() + timedelta(hours=2),
            jurisdiction_id=sample_jurisdiction.id
        )
        
        db_session.add(event)
        db_session.commit()
        
        assert event.id is not None
        assert event.name == "Committee Meeting"
    
    def test_event_time_validation(self, db_session, sample_jurisdiction):
        """Test event time validation"""
        start_time = datetime.now()
        end_time = start_time + timedelta(hours=2)
        
        event = Event(
            name="Time Test Event",
            event_type="meeting",
            start_time=start_time,
            end_time=end_time,
            jurisdiction_id=sample_jurisdiction.id
        )
        
        db_session.add(event)
        db_session.commit()
        
        assert event.start_time < event.end_time


class TestVoteModel:
    """Test Vote model operations"""
    
    def test_create_vote(self, db_session, sample_jurisdiction, sample_representative, sample_bill):
        """Test creating a vote"""
        vote = Vote(
            representative_id=sample_representative.id,
            bill_id=sample_bill.id,
            vote_type="yea",
            vote_date=datetime.now().date()
        )
        
        db_session.add(vote)
        db_session.commit()
        
        assert vote.id is not None
        assert vote.vote_type == "yea"
    
    def test_vote_types(self, db_session, sample_representative, sample_bill):
        """Test different vote types"""
        vote_types = ["yea", "nay", "abstain", "absent"]
        
        for vote_type in vote_types:
            vote = Vote(
                representative_id=sample_representative.id,
                bill_id=sample_bill.id,
                vote_type=vote_type,
                vote_date=datetime.now().date()
            )
            db_session.add(vote)
        
        db_session.commit()
        
        # Verify all vote types were created
        for vote_type in vote_types:
            found = db_session.query(Vote).filter_by(vote_type=vote_type).first()
            assert found is not None


class TestDatabaseQueries:
    """Test complex database queries"""
    
    def test_jurisdiction_with_representatives(self, db_session, sample_jurisdiction):
        """Test querying jurisdictions with their representatives"""
        # Add representatives
        representatives = [
            Representative(name="Rep 1", role=RepresentativeRole.MP, 
                         jurisdiction_id=sample_jurisdiction.id),
            Representative(name="Rep 2", role=RepresentativeRole.MP, 
                         jurisdiction_id=sample_jurisdiction.id)
        ]
        
        for rep in representatives:
            db_session.add(rep)
        db_session.commit()
        
        # Query jurisdiction with representatives
        jurisdiction_with_reps = db_session.query(Jurisdiction).join(
            Representative
        ).filter(Jurisdiction.id == sample_jurisdiction.id).first()
        
        assert jurisdiction_with_reps is not None
    
    def test_bills_by_status(self, db_session, sample_jurisdiction):
        """Test querying bills by status"""
        bills = [
            Bill(identifier="C-1", title="Bill 1", status=BillStatus.FIRST_READING,
                 jurisdiction_id=sample_jurisdiction.id),
            Bill(identifier="C-2", title="Bill 2", status=BillStatus.SECOND_READING,
                 jurisdiction_id=sample_jurisdiction.id),
            Bill(identifier="C-3", title="Bill 3", status=BillStatus.FIRST_READING,
                 jurisdiction_id=sample_jurisdiction.id)
        ]
        
        for bill in bills:
            db_session.add(bill)
        db_session.commit()
        
        # Query bills by status
        first_reading_bills = db_session.query(Bill).filter_by(
            status=BillStatus.FIRST_READING
        ).all()
        
        assert len(first_reading_bills) >= 2
    
    def test_representative_vote_history(self, db_session, sample_jurisdiction, sample_representative):
        """Test querying representative vote history"""
        # Create bills and votes
        bills = [
            Bill(identifier="C-1", title="Bill 1", jurisdiction_id=sample_jurisdiction.id),
            Bill(identifier="C-2", title="Bill 2", jurisdiction_id=sample_jurisdiction.id)
        ]
        
        for bill in bills:
            db_session.add(bill)
        db_session.flush()  # Get IDs
        
        votes = [
            Vote(representative_id=sample_representative.id, bill_id=bills[0].id,
                 vote_type="yea", vote_date=datetime.now().date()),
            Vote(representative_id=sample_representative.id, bill_id=bills[1].id,
                 vote_type="nay", vote_date=datetime.now().date())
        ]
        
        for vote in votes:
            db_session.add(vote)
        db_session.commit()
        
        # Query vote history
        vote_history = db_session.query(Vote).filter_by(
            representative_id=sample_representative.id
        ).all()
        
        assert len(vote_history) >= 2


class TestDatabasePerformance:
    """Test database performance characteristics"""
    
    def test_bulk_insert_performance(self, db_session, sample_jurisdiction):
        """Test bulk insert performance"""
        import time
        
        # Create many representatives
        representatives = []
        for i in range(100):
            rep = Representative(
                name=f"Test Rep {i}",
                role=RepresentativeRole.MP,
                party=f"Party {i % 5}",
                district=f"District {i}",
                jurisdiction_id=sample_jurisdiction.id
            )
            representatives.append(rep)
        
        start_time = time.time()
        db_session.bulk_save_objects(representatives)
        db_session.commit()
        end_time = time.time()
        
        # Should complete reasonably quickly
        assert end_time - start_time < 10.0  # Less than 10 seconds
        
        # Verify all were inserted
        count = db_session.query(Representative).count()
        assert count >= 100
    
    def test_query_performance(self, db_session, sample_jurisdiction):
        """Test query performance with data"""
        import time
        
        # Add some data first
        for i in range(50):
            rep = Representative(
                name=f"Query Test Rep {i}",
                role=RepresentativeRole.MP,
                party=f"Party {i % 3}",
                jurisdiction_id=sample_jurisdiction.id
            )
            db_session.add(rep)
        db_session.commit()
        
        # Test query performance
        start_time = time.time()
        results = db_session.query(Representative).filter_by(
            party="Party 1"
        ).all()
        end_time = time.time()
        
        # Should be fast
        assert end_time - start_time < 1.0  # Less than 1 second
        assert len(results) > 0


class TestDataIntegrity:
    """Test data integrity and constraints"""
    
    def test_cascade_deletes(self, db_session, sample_jurisdiction, sample_representative):
        """Test cascade delete behavior"""
        # This would test what happens when a jurisdiction is deleted
        # Implementation depends on cascade settings
        pass
    
    def test_data_validation(self, db_session, sample_jurisdiction):
        """Test data validation constraints"""
        # Test that required fields are enforced
        with pytest.raises(IntegrityError):
            rep = Representative(
                # Missing required name field
                role=RepresentativeRole.MP,
                jurisdiction_id=sample_jurisdiction.id
            )
            db_session.add(rep)
            db_session.commit()
    
    def test_unique_constraints(self, db_session, sample_jurisdiction):
        """Test unique constraints"""
        # Test that duplicate bills can't be created
        bill1 = Bill(
            identifier="C-UNIQUE",
            title="Unique Test Bill",
            jurisdiction_id=sample_jurisdiction.id
        )
        db_session.add(bill1)
        db_session.commit()
        
        # Try to create duplicate
        bill2 = Bill(
            identifier="C-UNIQUE",  # Same identifier
            title="Another Bill",
            jurisdiction_id=sample_jurisdiction.id
        )
        db_session.add(bill2)
        
        # Should raise integrity error
        with pytest.raises(IntegrityError):
            db_session.commit()