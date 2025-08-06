# OpenPolicy Merge Project - Comprehensive Merge Plan

## Executive Summary

This document outlines the strategy for merging 9 repositories into a unified Canadian civic data platform called **OpenPolicy Merge**. The project will leverage OpenParliament's extensive legislative database, integrate comprehensive scrapers from multiple sources, and create a modern, scalable platform with PostgreSQL 16+ backend and React-based frontend.

## Repository Analysis & Status

### Successfully Cloned Repositories
1. ✅ **openparliament** - Django-based parliamentary system (main data source)
2. ✅ **open-policy-infra** - Infrastructure configurations 
3. ✅ **admin-open-policy** - React/TypeScript admin panel
4. ✅ **open-policy-app** - React Native mobile app
5. ✅ **scrapers-ca** - OpenCivicData Canadian scrapers (109 municipalities + provinces)
6. ✅ **civic-scraper** - BigLocalNews scraping framework
7. ✅ **OpenPolicyAshBack** - Existing comprehensive backend (already feature-rich)

### Unavailable Repositories
- ❌ **open-policy-web** - Repository not found (will use admin-open-policy as UI base)
- ❌ **open-policy** - Repository not found (functionality exists in OpenPolicyAshBack)

## Core Architecture Decision

**Base Platform**: OpenPolicyAshBack will serve as the foundation since it already contains:
- Modern FastAPI/SQLAlchemy architecture
- PostgreSQL database with comprehensive models
- GraphQL + REST APIs
- Docker containerization
- React dashboard
- 123 Canadian jurisdictions already mapped
- Advanced monitoring and scheduling systems

**Integration Strategy**: Enhance the existing platform by merging the best features from other repositories.

## Repository Integration Plan

### 1. OpenParliament (HIGH PRIORITY)
**Technology**: Django + PostgreSQL
**License**: AGPLv3 (compatible)
**Value**: Extensive parliamentary data and proven scraping techniques

#### Features to Integrate:
- **Enhanced Parliamentary Models**: 
  - Parliamentary sessions tracking
  - Hansard document processing
  - Committee evidence parsing
  - Voting record extraction
  - Bill status workflows (15+ status codes)
  
- **Advanced Scraping Capabilities**:
  - XML/OData parsing for ourcommons.ca
  - LEGISinfo integration
  - Politician biographical data
  - Electoral district mapping
  - Party management system

- **Data Quality Features**:
  - Bill identifier validation (C-#, S-# patterns)
  - Name normalization algorithms
  - Duplicate detection systems
  - Data integrity checks

#### Implementation Plan:
1. **Database Models Enhancement** (Week 1-2):
   ```python
   # Add to existing models.py
   class ParliamentarySession(Base):
       __tablename__ = 'parliamentary_sessions'
       parliament = Column(Integer, nullable=False)
       session = Column(Integer, nullable=False)
       start_date = Column(Date, nullable=False)
       end_date = Column(Date)
       
   class HansardDocument(Base):
       __tablename__ = 'hansard_documents'
       document_type = Column(Enum('DEBATE', 'EVIDENCE'))
       session_id = Column(ForeignKey('parliamentary_sessions.id'))
       source_url = Column(String(500))
       processed_at = Column(DateTime)
   ```

2. **Scraper Integration** (Week 2-3):
   - Port Django scraping logic to existing scraper framework
   - Integrate with current Celery task system
   - Add parliamentary-specific error handling

3. **API Enhancement** (Week 3):
   - Add parliamentary endpoints to existing FastAPI
   - Extend GraphQL schema for parliamentary data
   - Update Swagger documentation

#### Reference Storage:
- Django-specific code → `/reference/openparliament-django/`
- Deprecated HTML templates → `/reference/openparliament-templates/`
- Old migration files → `/reference/openparliament-migrations/`

### 2. Scrapers-CA (HIGH PRIORITY)
**Technology**: Python + Pupa framework
**Coverage**: Federal + 13 provinces + 109+ municipalities
**Value**: Comprehensive Canadian jurisdiction coverage

#### Features to Integrate:
- **Municipal Scraper Collection**:
  - 109+ municipal scrapers (Toronto, Montreal, Calgary, Ottawa, etc.)
  - Provincial legislature scrapers (all 13 provinces/territories)
  - Federal elections and candidacy data

- **Proven Scraping Infrastructure**:
  - PostGIS-enabled geographic data
  - Error handling and retry mechanisms
  - Data validation pipelines

#### Implementation Plan:
1. **Scraper Migration** (Week 2-3):
   ```python
   # Integrate into existing scraper manager
   class PupaScraperAdapter:
       def __init__(self, jurisdiction_code):
           self.jurisdiction = jurisdiction_code
           
       def run_scraper(self, scraper_type):
           # Adapt Pupa scrapers to current task system
           pass
   ```

2. **Database Integration**:
   - Map Pupa data models to existing SQLAlchemy models
   - Enhance jurisdiction coverage from 123 → 200+ jurisdictions

#### Reference Storage:
- Pupa framework dependencies → `/reference/scrapers-ca-pupa/`
- Obsolete scraper versions → `/reference/scrapers-ca-deprecated/`

### 3. Civic-Scraper (MEDIUM PRIORITY)
**Technology**: Python scraping framework
**Value**: Advanced scraping utilities and patterns

#### Features to Integrate:
- **Generic Scraping Tools**:
  - HTTP session management
  - Rate limiting utilities
  - Data cleaning pipelines
  - Error reporting systems

#### Implementation Plan:
- Extract utility classes and integrate into existing scraper manager
- Enhance error handling in current system

#### Reference Storage:
- Framework-specific code → `/reference/civic-scraper-framework/`

### 4. Admin-Open-Policy (MEDIUM PRIORITY)
**Technology**: React + TypeScript + Vite + Tailwind CSS
**Value**: Modern admin interface foundation

#### Features to Integrate:
- **Modern React Architecture**:
  - TypeScript for type safety
  - Tailwind CSS for styling
  - Component-based design
  - React Router for navigation

#### Implementation Plan:
1. **UI Enhancement** (Week 4-5):
   - Enhance existing React dashboard with admin-panel components
   - Integrate Tailwind CSS for improved styling
   - Add TypeScript for better type safety

2. **Component Integration**:
   ```typescript
   // Enhance existing dashboard with new components
   import { NavigationComponent } from './admin-components';
   import { DataManagementPanel } from './admin-components';
   ```

#### Reference Storage:
- Deprecated components → `/reference/admin-open-policy-old/`

### 5. Open-Policy-App (LOW PRIORITY)
**Technology**: React Native + Expo
**Value**: Mobile application capabilities

#### Features to Consider:
- **Mobile Interface**:
  - Cross-platform mobile app
  - Offline capabilities
  - Push notifications

#### Implementation Plan:
- **Phase 2 Enhancement**: After core platform is stable
- Create mobile API endpoints
- Develop Progressive Web App (PWA) alternative first

#### Reference Storage:
- Full mobile app → `/reference/open-policy-app/` (preserve for future development)

### 6. Open-Policy-Infra (LOW PRIORITY)
**Technology**: Laravel + PHP
**Value**: Infrastructure configurations and deployment scripts

#### Features to Integrate:
- **Deployment Configurations**:
  - Docker configurations
  - CI/CD pipeline setups
  - Infrastructure as Code (IaC)

#### Implementation Plan:
- Extract useful Docker and deployment configurations
- Integrate into existing deployment system

#### Reference Storage:
- Laravel-specific code → `/reference/open-policy-infra-laravel/`
- Obsolete configs → `/reference/open-policy-infra-deprecated/`

## External Data Integration

### Represent API (represent.opennorth.ca)
**Status**: Available and active
**Data Coverage**: 
- Federal MPs with contact information
- Provincial MLAs/MPPs 
- Municipal councillors and mayors
- Electoral boundary data
- Candidate information

#### Integration Plan:
1. **API Integration** (Week 3):
   ```python
   class RepresentAPIIntegrator:
       def sync_representatives(self, jurisdiction_type):
           # Fetch from represent.opennorth.ca/representatives/
           # Update existing database records
           pass
           
       def sync_boundaries(self):
           # Fetch electoral boundaries
           # Integrate with PostGIS geographic data
           pass
   ```

2. **Data Synchronization**:
   - Daily sync with Represent API
   - Cross-reference with scraped data
   - Handle data conflicts and duplicates

### OpenParliament Database Dump
**Status**: Available at openparliament.ca/data-download/
**Value**: Historical parliamentary data

#### Integration Plan:
- Download and analyze schema
- Import historical data to enhance current dataset
- Preserve data lineage and sources

## Enhanced Database Schema

### Unified PostgreSQL 16+ Schema
Building on existing OpenPolicyAshBack models, enhanced with OpenParliament features:

```sql
-- Enhanced parliamentary tracking
CREATE TABLE parliamentary_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    parliament INTEGER NOT NULL,
    session INTEGER NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE,
    dissolved_date DATE,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(parliament, session)
);

-- Enhanced bill tracking (extending existing bills table)
ALTER TABLE bills ADD COLUMN parliamentary_session_id UUID REFERENCES parliamentary_sessions(id);
ALTER TABLE bills ADD COLUMN legisinfo_id INTEGER UNIQUE;
ALTER TABLE bills ADD COLUMN private_member BOOLEAN DEFAULT FALSE;
ALTER TABLE bills ADD COLUMN royal_assent_date DATE;

-- Parliamentary documents
CREATE TABLE hansard_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_type VARCHAR(20) NOT NULL CHECK (document_type IN ('DEBATE', 'EVIDENCE')),
    date DATE NOT NULL,
    number VARCHAR(10),
    session_id UUID NOT NULL REFERENCES parliamentary_sessions(id),
    source_url TEXT,
    processed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Speeches and statements
CREATE TABLE parliamentary_statements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES hansard_documents(id),
    politician_id UUID REFERENCES representatives(id),
    sequence INTEGER NOT NULL,
    content TEXT NOT NULL,
    content_en TEXT,
    content_fr TEXT,
    statement_type VARCHAR(50),
    time_offset INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Enhanced representative tracking
ALTER TABLE representatives ADD COLUMN parl_affiliation_id INTEGER;
ALTER TABLE representatives ADD COLUMN parl_person_id INTEGER;
ALTER TABLE representatives ADD COLUMN gender CHAR(1);
ALTER TABLE representatives ADD COLUMN photo_url TEXT;

-- Electoral history
CREATE TABLE electoral_memberships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    representative_id UUID NOT NULL REFERENCES representatives(id),
    riding VARCHAR(255) NOT NULL,
    party VARCHAR(255),
    start_date DATE,
    end_date DATE,
    session_id UUID REFERENCES parliamentary_sessions(id),
    created_at TIMESTAMP DEFAULT NOW()
);
```

## API Enhancement Strategy

### Unified API Structure
Extend existing FastAPI with parliamentary features:

```python
# New parliamentary endpoints
@app.get("/api/v1/parliamentary-sessions")
async def get_parliamentary_sessions():
    pass

@app.get("/api/v1/hansard/{session_id}")
async def get_hansard_by_session(session_id: str):
    pass

@app.get("/api/v1/representatives/{rep_id}/statements")
async def get_representative_statements(rep_id: str):
    pass

# Enhanced existing endpoints
@app.get("/api/v1/bills")
async def get_bills(
    parliament: Optional[int] = None,
    session: Optional[int] = None,
    status: Optional[str] = None
):
    pass
```

### GraphQL Schema Enhancement
Extend existing GraphQL with parliamentary types:

```graphql
type ParliamentarySession {
    id: ID!
    parliament: Int!
    session: Int!
    startDate: Date!
    endDate: Date
    bills: [Bill!]!
    hansardDocuments: [HansardDocument!]!
}

type HansardDocument {
    id: ID!
    documentType: DocumentType!
    date: Date!
    session: ParliamentarySession!
    statements: [ParliamentaryStatement!]!
}

extend type Representative {
    parliamentaryStatements: [ParliamentaryStatement!]!
    electoralHistory: [ElectoralMembership!]!
}
```

## Scraper Architecture

### Unified Scraper Manager
Enhance existing scraper system:

```python
class UnifiedScraperManager:
    def __init__(self):
        self.federal_scrapers = {
            'parliament': ParliamentaryScraper(),
            'elections': ElectionsScraper(),
            'represent_api': RepresentAPIScraper()
        }
        
        self.provincial_scrapers = {}  # From scrapers-ca
        self.municipal_scrapers = {}   # From scrapers-ca
        
    async def run_comprehensive_scrape(self):
        """Run all scrapers for all jurisdictions"""
        # Federal data
        await self.scrape_federal_data()
        
        # Provincial data (13 provinces/territories)
        await self.scrape_provincial_data()
        
        # Municipal data (200+ municipalities)
        await self.scrape_municipal_data()
        
    async def validate_data_integrity(self):
        """Cross-validate data from multiple sources"""
        pass
```

## Frontend Architecture

### Enhanced React Dashboard
Build on existing dashboard with admin-panel features:

```typescript
// Enhanced component structure
interface DashboardProps {
    user: User;
    jurisdictions: Jurisdiction[];
    realtimeData: RealtimeStats;
}

const Dashboard: React.FC<DashboardProps> = () => {
    return (
        <div className="min-h-screen bg-gray-50">
            <Navigation />
            <main className="flex-1">
                <ParliamentaryOverview />
                <JurisdictionGrid />
                <RealtimeMonitoring />
                <DataQualityPanel />
            </main>
            <Footer />
        </div>
    );
};
```

### Component Integration Strategy
- **Keep**: Existing React dashboard foundation
- **Enhance**: Add TypeScript and Tailwind CSS from admin-panel
- **Add**: Parliamentary data visualization components
- **Add**: Advanced filtering and search capabilities

## Testing Strategy

### Comprehensive Test Coverage
Target: 90%+ API test coverage

```python
# Parliamentary API tests
class TestParliamentaryAPIs:
    async def test_get_parliamentary_sessions(self):
        pass
    
    async def test_hansard_document_creation(self):
        pass
        
    async def test_bill_status_updates(self):
        pass

# Data integrity tests
class TestDataIntegrity:
    async def test_representative_data_consistency(self):
        """Ensure Represent API data matches scraped data"""
        pass
        
    async def test_bill_identifier_validation(self):
        """Test C-# and S-# bill identifier patterns"""
        pass
```

## Deployment Architecture

### Enhanced Docker Configuration
Build on existing single-container design:

```dockerfile
# Enhanced Dockerfile
FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    postgis \
    gdal-bin \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application code
COPY . /app
WORKDIR /app

# Run services
CMD ["supervisord", "-c", "supervisord.conf"]
```

### Service Configuration
```yaml
# Enhanced docker-compose.yml
services:
  openpolicy-merge:
    build: .
    ports:
      - "80:80"      # Nginx
      - "8000:8000"  # FastAPI
      - "3000:3000"  # React Dashboard
      - "5555:5555"  # Flower (Celery monitoring)
    environment:
      - DATABASE_URL=postgresql://user:pass@localhost/openpolicy
      - REDIS_URL=redis://localhost:6379
      - REPRESENT_API_KEY=${REPRESENT_API_KEY}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - scraper_logs:/app/logs
```

## Data Sources & Quality

### Primary Data Sources
1. **Parliamentary Data**: openparliament.ca + ourcommons.ca
2. **Representative Data**: represent.opennorth.ca API
3. **Municipal Data**: Individual municipal websites (200+ scrapers)
4. **Provincial Data**: Provincial legislature websites
5. **Electoral Data**: Elections Canada + provincial election offices

### Data Quality Measures
1. **Cross-validation**: Compare multiple sources for same data
2. **Automated Testing**: Daily validation of critical data points
3. **Error Reporting**: Comprehensive logging of scraper failures
4. **Manual Review**: Flagging system for human verification

## Project Timeline

### Phase 1: Core Integration (Weeks 1-3)
- ✅ Repository analysis and planning
- 🔄 Database schema enhancement
- 🔄 OpenParliament model integration
- 🔄 Scraper framework unification

### Phase 2: Data Enhancement (Weeks 4-6)
- 🔄 Represent API integration
- 🔄 Parliamentary data import
- 🔄 Enhanced scraper deployment
- 🔄 Data validation systems

### Phase 3: Frontend & APIs (Weeks 7-9)
- 🔄 Enhanced React dashboard
- 🔄 Parliamentary API endpoints
- 🔄 GraphQL schema expansion
- 🔄 Comprehensive testing

### Phase 4: Production Deployment (Weeks 10-12)
- 🔄 Performance optimization
- 🔄 Security hardening
- 🔄 Monitoring enhancement
- 🔄 Documentation completion

## Success Metrics

### Data Coverage
- ✅ Federal: Parliament + Elections + Representatives
- ✅ Provincial: 13 provinces/territories
- ✅ Municipal: 200+ cities and towns
- ✅ Historical: 10+ years of parliamentary data

### API Performance
- 📊 Response time: <200ms for simple queries
- 📊 Availability: 99.9% uptime
- 📊 Test coverage: >90%
- 📊 Data freshness: <24 hours for most data

### Platform Features
- ✅ Real-time monitoring dashboard
- ✅ Automated daily scraping
- ✅ Comprehensive error handling
- ✅ GraphQL + REST APIs
- ✅ Mobile-responsive UI
- ✅ Docker containerization

## Risk Mitigation

### Technical Risks
1. **Data Source Changes**: Implement robust error handling and monitoring
2. **Performance Issues**: Use caching and database optimization
3. **Security Vulnerabilities**: Regular security audits and updates

### Operational Risks
1. **Data Quality**: Implement cross-validation and manual review processes
2. **Scraper Failures**: Automated retry logic and alerting systems
3. **Resource Constraints**: Scalable infrastructure with monitoring

## Conclusion

This merge plan leverages the existing robust OpenPolicyAshBack platform as the foundation while strategically integrating the best features from each repository. The focus is on enhancing parliamentary data capabilities, expanding scraper coverage, and improving the user interface while maintaining the proven architecture and deployment systems already in place.

The result will be a comprehensive Canadian civic data platform that provides unprecedented access to federal, provincial, and municipal political information through modern APIs and an intuitive web interface.