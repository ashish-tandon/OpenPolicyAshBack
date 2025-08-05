# OpenPolicy Enhancement Implementation Guide

## Quick Start: Priority Integrations

### 1. OpenParliament Integration (Week 1)

#### A. Enhanced Parliamentary Models

**File: `src/database/models.py`** - Add these models:

```python
# Add to existing models.py after line 250

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
```

#### B. Enhanced Federal Scraper

**File: `src/scrapers/parliamentary_scraper.py`** - New file:

```python
import xml.etree.ElementTree as ET
import requests
from datetime import datetime, date
from typing import List, Dict, Optional
import re
from sqlalchemy.orm import Session
from src.database.models import HansardRecord, ParliamentarySession, Speech, CommitteeMeeting
from src.database.connection import get_db_session

class ParliamentaryScraper:
    def __init__(self):
        self.base_url = "https://www.parl.gc.ca"
        self.hansard_base = f"{self.base_url}/HousePublications"
        self.committee_base = f"{self.base_url}/Committees"
        
    def get_current_session(self) -> ParliamentarySession:
        """Get or create the current parliamentary session"""
        with get_db_session() as db:
            # For now, using 44th Parliament, 1st Session (current as of 2024)
            session = db.query(ParliamentarySession).filter_by(
                parliament_number=44, 
                session_number=1
            ).first()
            
            if not session:
                session = ParliamentarySession(
                    parliament_number=44,
                    session_number=1,
                    start_date=date(2021, 11, 22)  # 44th Parliament start date
                )
                db.add(session)
                db.commit()
                db.refresh(session)
                
            return session
    
    def scrape_hansard_list(self, parliament: int = 44, session: int = 1) -> List[Dict]:
        """Scrape list of available Hansard debates"""
        url = f"{self.hansard_base}/Publication.aspx"
        params = {
            'Language': 'E',
            'Mode': '1',
            'Parl': parliament,
            'Ses': session
        }
        
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            # Parse HTML to extract debate list
            # This would need proper HTML parsing - simplified for example
            debates = []
            # Implementation would parse the publication list page
            return debates
            
        except Exception as e:
            print(f"Error scraping Hansard list: {e}")
            return []
    
    def process_hansard_xml(self, xml_url: str, hansard_id: int):
        """Process Hansard XML document to extract speeches"""
        try:
            response = requests.get(xml_url, timeout=30)
            response.raise_for_status()
            
            root = ET.fromstring(response.content)
            
            # XML namespace handling (Hansard XML uses specific namespaces)
            namespaces = {
                'hansard': 'http://www.parl.gc.ca/HousePublications/Hansard'
            }
            
            speeches = []
            
            # Extract speeches from XML
            for speech_elem in root.findall('.//hansard:speech', namespaces):
                speech_data = self.extract_speech_data(speech_elem, namespaces)
                if speech_data:
                    speech_data['hansard_id'] = hansard_id
                    speeches.append(speech_data)
            
            # Save speeches to database
            with get_db_session() as db:
                for speech_data in speeches:
                    speech = Speech(**speech_data)
                    db.add(speech)
                
                # Update hansard record
                hansard = db.query(HansardRecord).get(hansard_id)
                hansard.processed = True
                hansard.speech_count = len(speeches)
                
                db.commit()
                
            return len(speeches)
            
        except Exception as e:
            print(f"Error processing Hansard XML {xml_url}: {e}")
            return 0
    
    def extract_speech_data(self, speech_elem, namespaces: Dict) -> Optional[Dict]:
        """Extract individual speech data from XML element"""
        try:
            speaker_elem = speech_elem.find('.//hansard:speaker', namespaces)
            content_elem = speech_elem.find('.//hansard:content', namespaces)
            
            if speaker_elem is None or content_elem is None:
                return None
            
            # Extract speaker information
            speaker_name = speaker_elem.get('name', '')
            speaker_title = speaker_elem.get('title', '')
            
            # Extract content
            content = ET.tostring(content_elem, encoding='unicode', method='text').strip()
            
            # Extract time if available
            time_attr = speech_elem.get('time')
            time_spoken = None
            if time_attr:
                try:
                    time_spoken = datetime.fromisoformat(time_attr)
                except:
                    pass
            
            return {
                'speaker_name': speaker_name,
                'speaker_title': speaker_title,
                'content': content,
                'time_spoken': time_spoken,
                'speech_type': speech_elem.get('type', 'statement')
            }
            
        except Exception as e:
            print(f"Error extracting speech data: {e}")
            return None
    
    def scrape_committee_meetings(self, committee_acronym: str) -> List[Dict]:
        """Scrape committee meeting evidence"""
        url = f"{self.committee_base}/{committee_acronym}/Meetings"
        
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            # Parse committee meetings
            # Implementation would parse the committee meetings page
            meetings = []
            return meetings
            
        except Exception as e:
            print(f"Error scraping committee meetings for {committee_acronym}: {e}")
            return []
```

#### C. Enhanced Federal Bill Validation

**File: `src/validation/parliamentary_validator.py`** - New file:

```python
import re
from typing import Dict, List, Tuple
from datetime import datetime, timedelta
from src.database.models import Bill, Representative

class ParliamentaryValidator:
    
    BILL_IDENTIFIER_PATTERNS = {
        'commons': r'^C-\d+$',  # House of Commons bills
        'senate': r'^S-\d+$',   # Senate bills
        'private_member': r'^[CS]-\d+$'  # Private member bills
    }
    
    VALID_BILL_STATUSES = [
        'First Reading',
        'Second Reading', 
        'Committee Stage',
        'Report Stage',
        'Third Reading',
        'Consideration by Senate',
        'Royal Assent',
        'Withdrawn',
        'Defeated'
    ]
    
    CRITICAL_BILL_KEYWORDS = [
        'budget', 'tax', 'taxation', 'healthcare', 'health care',
        'education', 'defence', 'defense', 'immigration',
        'employment', 'economy', 'trade', 'environment'
    ]
    
    def validate_federal_bill(self, bill: Bill) -> Dict:
        """Comprehensive validation of federal bill data"""
        validation_result = {
            'bill_id': bill.id,
            'identifier': bill.identifier,
            'passes': True,
            'warnings': [],
            'errors': [],
            'quality_score': 100,
            'is_critical': False,
            'recommendations': []
        }
        
        # Validate identifier format
        identifier_valid = self.validate_bill_identifier(bill.identifier)
        if not identifier_valid:
            validation_result['errors'].append(
                f"Invalid bill identifier format: {bill.identifier}"
            )
            validation_result['quality_score'] -= 20
            validation_result['passes'] = False
        
        # Validate title quality
        title_score = self.validate_title_quality(bill.title)
        validation_result['quality_score'] += title_score - 100  # Adjust score
        
        if title_score < 60:
            validation_result['warnings'].append(
                f"Low title quality score: {title_score}"
            )
        
        # Validate status progression
        status_valid = self.validate_status_progression(bill)
        if not status_valid:
            validation_result['warnings'].append(
                "Unusual status progression detected"
            )
            validation_result['quality_score'] -= 10
        
        # Check if bill is critical
        validation_result['is_critical'] = self.is_critical_bill(bill)
        
        # Data freshness check
        freshness_score = self.check_data_freshness(bill)
        validation_result['quality_score'] += freshness_score - 100
        
        if freshness_score < 80:
            validation_result['warnings'].append(
                f"Data may be stale (freshness score: {freshness_score})"
            )
        
        # Generate recommendations
        validation_result['recommendations'] = self.generate_recommendations(
            validation_result
        )
        
        return validation_result
    
    def validate_bill_identifier(self, identifier: str) -> bool:
        """Validate Canadian federal bill identifier format"""
        if not identifier:
            return False
        
        for pattern in self.BILL_IDENTIFIER_PATTERNS.values():
            if re.match(pattern, identifier):
                return True
        
        return False
    
    def validate_title_quality(self, title: str) -> int:
        """Score title quality (0-100)"""
        if not title:
            return 0
        
        score = 50  # Base score
        
        # Length check
        if 10 <= len(title) <= 200:
            score += 20
        elif len(title) < 10:
            score -= 30
        elif len(title) > 200:
            score -= 10
        
        # Completeness check
        if title.strip().endswith('.') or title.strip().endswith('Act'):
            score += 15
        
        # Avoid too generic titles
        generic_words = ['bill', 'act', 'legislation', 'law']
        if any(word.lower() == title.lower().strip() for word in generic_words):
            score -= 40
        
        # Check for meaningful content
        if len(title.split()) >= 3:
            score += 15
        
        return max(0, min(100, score))
    
    def validate_status_progression(self, bill: Bill) -> bool:
        """Validate logical bill status progression"""
        # This would check if the bill's status makes sense
        # given its history and timeline
        
        if not bill.status:
            return False
        
        if bill.status not in self.VALID_BILL_STATUSES:
            return False
        
        # Could add more sophisticated progression logic here
        return True
    
    def is_critical_bill(self, bill: Bill) -> bool:
        """Determine if bill deals with critical national issues"""
        if not bill.title and not bill.summary:
            return False
        
        text_to_check = f"{bill.title or ''} {bill.summary or ''}".lower()
        
        return any(keyword in text_to_check for keyword in self.CRITICAL_BILL_KEYWORDS)
    
    def check_data_freshness(self, bill: Bill) -> int:
        """Check how fresh the bill data is (0-100 score)"""
        if not bill.updated_at:
            return 50  # Neutral score if no update time
        
        age = datetime.utcnow() - bill.updated_at
        
        if age <= timedelta(hours=4):
            return 100  # Perfect freshness
        elif age <= timedelta(hours=24):
            return 90   # Good freshness
        elif age <= timedelta(days=3):
            return 70   # Acceptable freshness
        elif age <= timedelta(weeks=1):
            return 50   # Getting stale
        else:
            return 20   # Stale data
    
    def generate_recommendations(self, validation_result: Dict) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        if validation_result['quality_score'] < 70:
            recommendations.append(
                "Consider re-scraping this bill for updated information"
            )
        
        if validation_result['is_critical']:
            recommendations.append(
                "Critical bill detected - prioritize for frequent updates"
            )
        
        if validation_result['errors']:
            recommendations.append(
                "Fix data quality errors before publishing"
            )
        
        if len(validation_result['warnings']) > 2:
            recommendations.append(
                "Multiple warnings detected - review data source"
            )
        
        return recommendations
```

### 2. Policy-as-Code Integration (Week 2)

#### A. Add OPA Service to Docker Compose

**File: `docker-compose.yml`** - Add this service:

```yaml
# Add after the existing services in docker-compose.yml

  opa:
    image: openpolicyagent/opa:latest-debug
    ports:
      - "8181:8181"
    command:
      - "run"
      - "--server"
      - "--log-level=debug"
      - "/policies"
    volumes:
      - ./policies:/policies:ro
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8181/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - openpolicy-network

  policy-validator:
    build:
      context: .
      dockerfile: Dockerfile.policy-validator
    depends_on:
      - opa
      - postgres
      - redis
    environment:
      - OPA_URL=http://opa:8181
      - DATABASE_URL=postgresql://openpolicy:openpolicy123@postgres:5432/opencivicdata
      - REDIS_URL=redis://redis:6379/0
    volumes:
      - ./policies:/policies:ro
    networks:
      - openpolicy-network
```

#### B. Create Policy Files

**Directory: `policies/`** - Create these files:

**File: `policies/data_quality.rego`**:

```rego
package openpolicy.data_quality

import future.keywords.if
import future.keywords.in

# Federal bill validation policy
federal_bill_valid[bill] if {
    bill.identifier
    regex.match(`^[CS]-\d+$`, bill.identifier)
    bill.title
    count(bill.title) > 10
    count(bill.title) < 300
    bill.status in valid_statuses
}

valid_statuses := [
    "First Reading",
    "Second Reading", 
    "Committee Stage",
    "Report Stage",
    "Third Reading",
    "Royal Assent",
    "Withdrawn",
    "Defeated"
]

# Provincial data completeness policy
provincial_data_complete[jurisdiction] if {
    jurisdiction.type == "provincial"
    jurisdiction.representatives
    count(jurisdiction.representatives) > 0
    jurisdiction.name
    jurisdiction.name != ""
}

# Municipal data quality policy  
municipal_data_quality[jurisdiction] if {
    jurisdiction.type == "municipal"
    jurisdiction.name
    jurisdiction.province
    jurisdiction.population
    jurisdiction.population > 0
}

# Data freshness policy
data_is_fresh[item] if {
    item.updated_at
    time.parse_rfc3339_ns(item.updated_at)
    now := time.now_ns()
    age_hours := (now - time.parse_rfc3339_ns(item.updated_at)) / 1000000000 / 3600
    age_hours < 24  # Data must be less than 24 hours old
}

# Critical bill detection
is_critical_bill[bill] if {
    bill.title
    lower_title := lower(bill.title)
    some keyword in critical_keywords
    contains(lower_title, keyword)
}

critical_keywords := [
    "budget", "tax", "taxation", "healthcare", "health care",
    "education", "defence", "defense", "immigration", 
    "employment", "economy", "trade", "environment"
]
```

**File: `policies/api_access.rego`**:

```rego
package openpolicy.api_access

import future.keywords.if
import future.keywords.in

# Rate limiting policy
allow_request if {
    input.user.authenticated
    input.requests_per_hour < user_rate_limit
}

allow_request if {
    not input.user.authenticated
    input.requests_per_hour < anonymous_rate_limit
}

user_rate_limit := 10000
anonymous_rate_limit := 1000

# API key validation
valid_api_key if {
    input.api_key
    input.api_key in valid_keys
}

valid_keys := [
    "dev-key-12345",
    "prod-key-67890"
]

# Federal priority data access
allow_federal_priority_data if {
    input.user.role in authorized_roles
}

allow_federal_priority_data if {
    input.user.authenticated
    input.user.verified_researcher
}

authorized_roles := ["researcher", "journalist", "admin", "government"]

# Data export permissions
allow_bulk_export if {
    input.user.authenticated
    input.user.role in ["admin", "researcher"]
    input.export_size < max_export_size
}

max_export_size := 10000  # Maximum records per export
```

#### C. OPA Client Integration

**File: `src/policy_engine/opa_client.py`** - New file:

```python
import requests
import json
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class OPAClient:
    def __init__(self, opa_url: str = "http://opa:8181"):
        self.opa_url = opa_url.rstrip('/')
        self.session = requests.Session()
    
    def evaluate_policy(self, policy_path: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate a policy with given input data"""
        url = f"{self.opa_url}/v1/data/{policy_path}"
        
        payload = {"input": input_data}
        
        try:
            response = self.session.post(
                url,
                json=payload,
                timeout=5.0
            )
            response.raise_for_status()
            
            result = response.json()
            return result.get("result", {})
            
        except requests.RequestException as e:
            logger.error(f"OPA policy evaluation failed: {e}")
            return {"error": str(e)}
    
    def validate_federal_bill(self, bill_data: Dict) -> bool:
        """Validate federal bill against data quality policies"""
        result = self.evaluate_policy(
            "openpolicy/data_quality/federal_bill_valid",
            bill_data
        )
        return bool(result)
    
    def check_api_access(self, user_data: Dict, request_data: Dict) -> bool:
        """Check if API request should be allowed"""
        input_data = {
            "user": user_data,
            **request_data
        }
        
        result = self.evaluate_policy(
            "openpolicy/api_access/allow_request",
            input_data
        )
        return bool(result)
    
    def validate_data_quality(self, jurisdiction_data: Dict) -> Dict:
        """Comprehensive data quality validation"""
        results = {}
        
        # Federal bill validation
        if jurisdiction_data.get("type") == "federal":
            for bill in jurisdiction_data.get("bills", []):
                bill_valid = self.evaluate_policy(
                    "openpolicy/data_quality/federal_bill_valid",
                    bill
                )
                results[f"bill_{bill.get('id')}"] = bill_valid
        
        # Provincial data validation
        elif jurisdiction_data.get("type") == "provincial":
            provincial_valid = self.evaluate_policy(
                "openpolicy/data_quality/provincial_data_complete",
                jurisdiction_data
            )
            results["provincial_complete"] = provincial_valid
        
        # Municipal data validation
        elif jurisdiction_data.get("type") == "municipal":
            municipal_valid = self.evaluate_policy(
                "openpolicy/data_quality/municipal_data_quality",
                jurisdiction_data
            )
            results["municipal_quality"] = municipal_valid
        
        return results
    
    def health_check(self) -> bool:
        """Check if OPA service is healthy"""
        try:
            response = self.session.get(f"{self.opa_url}/health", timeout=3.0)
            return response.status_code == 200
        except:
            return False
```

#### D. Policy Middleware for API

**File: `src/api/policy_middleware.py`** - New file:

```python
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from src.policy_engine.opa_client import OPAClient
import time
from typing import Dict

class PolicyMiddleware:
    def __init__(self):
        self.opa_client = OPAClient()
        self.request_counts = {}  # In production, use Redis
    
    async def __call__(self, request: Request, call_next):
        # Extract user information (if authenticated)
        user_data = await self.extract_user_data(request)
        
        # Check rate limiting
        client_ip = request.client.host
        if not await self.check_rate_limit(user_data, client_ip):
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "message": "Please reduce request frequency"
                }
            )
        
        # Check API access policies
        request_data = {
            "path": str(request.url.path),
            "method": request.method,
            "requests_per_hour": self.get_request_count(client_ip)
        }
        
        if not self.opa_client.check_api_access(user_data, request_data):
            return JSONResponse(
                status_code=403,
                content={
                    "error": "Access denied by policy",
                    "message": "Request violates access policies"
                }
            )
        
        # Track request
        self.track_request(client_ip)
        
        # Process request
        response = await call_next(request)
        return response
    
    async def extract_user_data(self, request: Request) -> Dict:
        """Extract user data from request (JWT, API key, etc.)"""
        # This would integrate with your existing auth system
        auth_header = request.headers.get("Authorization", "")
        api_key = request.headers.get("X-API-Key", "")
        
        if api_key:
            return {
                "authenticated": True,
                "api_key": api_key,
                "role": "api_user"  # Would be looked up from database
            }
        elif auth_header.startswith("Bearer "):
            # JWT token processing would go here
            return {
                "authenticated": True,
                "role": "user"
            }
        else:
            return {
                "authenticated": False,
                "role": "anonymous"
            }
    
    async def check_rate_limit(self, user_data: Dict, client_ip: str) -> bool:
        """Check if request should be rate limited"""
        current_count = self.get_request_count(client_ip)
        
        # Use OPA policy to determine limits
        policy_input = {
            "user": user_data,
            "requests_per_hour": current_count
        }
        
        return self.opa_client.evaluate_policy(
            "openpolicy/api_access/allow_request",
            policy_input
        )
    
    def get_request_count(self, client_ip: str) -> int:
        """Get current request count for IP (last hour)"""
        current_time = int(time.time())
        hour_ago = current_time - 3600
        
        if client_ip not in self.request_counts:
            self.request_counts[client_ip] = []
        
        # Remove old requests
        self.request_counts[client_ip] = [
            req_time for req_time in self.request_counts[client_ip]
            if req_time > hour_ago
        ]
        
        return len(self.request_counts[client_ip])
    
    def track_request(self, client_ip: str):
        """Track a new request"""
        current_time = int(time.time())
        
        if client_ip not in self.request_counts:
            self.request_counts[client_ip] = []
        
        self.request_counts[client_ip].append(current_time)
```

### 3. Integration with Existing API

**File: `src/api/main.py`** - Add these modifications:

```python
# Add these imports at the top
from src.policy_engine.opa_client import OPAClient
from src.api.policy_middleware import PolicyMiddleware
from src.validation.parliamentary_validator import ParliamentaryValidator

# Add after existing middleware
app.add_middleware(PolicyMiddleware)

# Add new endpoints
@app.get("/policy/health")
async def policy_health():
    """Check policy engine health"""
    opa_client = OPAClient()
    health = opa_client.health_check()
    
    return {
        "policy_engine_healthy": health,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/federal/validate-bill/{bill_id}")
async def validate_federal_bill(bill_id: int, db: Session = Depends(get_db)):
    """Validate a federal bill against quality policies"""
    bill = db.query(Bill).filter(Bill.id == bill_id).first()
    
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")
    
    validator = ParliamentaryValidator()
    validation_result = validator.validate_federal_bill(bill)
    
    return validation_result

@app.post("/federal/run-quality-checks")
async def run_federal_quality_checks(db: Session = Depends(get_db)):
    """Run comprehensive federal data quality checks"""
    federal_jurisdiction = db.query(Jurisdiction).filter(
        Jurisdiction.type == "federal"
    ).first()
    
    if not federal_jurisdiction:
        raise HTTPException(status_code=404, detail="Federal jurisdiction not found")
    
    opa_client = OPAClient()
    validator = ParliamentaryValidator()
    
    # Get all federal bills
    federal_bills = db.query(Bill).filter(
        Bill.jurisdiction_id == federal_jurisdiction.id
    ).limit(100).all()
    
    results = {
        "total_bills_checked": len(federal_bills),
        "validation_results": [],
        "summary": {
            "passed": 0,
            "warnings": 0,
            "errors": 0,
            "critical_bills": 0
        }
    }
    
    for bill in federal_bills:
        validation = validator.validate_federal_bill(bill)
        results["validation_results"].append(validation)
        
        if validation["passes"]:
            results["summary"]["passed"] += 1
        if validation["warnings"]:
            results["summary"]["warnings"] += 1
        if validation["errors"]:
            results["summary"]["errors"] += 1
        if validation["is_critical"]:
            results["summary"]["critical_bills"] += 1
    
    return results
```

## Next Steps

1. **Run database migrations** to add the new tables:
   ```bash
   # Add the new models and run
   python manage.py migrate
   ```

2. **Test the OPA integration**:
   ```bash
   # Start the enhanced system
   ./setup.sh
   
   # Test policy health
   curl http://localhost:8000/policy/health
   
   # Test federal bill validation
   curl -X POST http://localhost:8000/federal/run-quality-checks
   ```

3. **Add the enhanced scraping**:
   - The parliamentary scraper will automatically enhance federal data collection
   - Add periodic tasks to process Hansard and committee data

4. **Monitor and refine**:
   - Use the new quality metrics to improve data collection
   - Refine policies based on real-world data patterns

This implementation provides immediate value while being completely compatible with your existing system. The OPA integration adds enterprise-grade policy management, while the OpenParliament enhancements significantly improve the depth and quality of Canadian parliamentary data.