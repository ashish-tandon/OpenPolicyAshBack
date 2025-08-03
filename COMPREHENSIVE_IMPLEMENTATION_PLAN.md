# Comprehensive Implementation Plan for OpenPolicy Backend

## 🎯 Objective
Ensure complete implementation of all features from referenced repositories with full access to federal MPs, provincial MPPs/MLAs, and municipal leaders with their bills through both UI and API.

## 📋 Current Status Review

### ✅ What's Already Implemented:
1. **Data Models**: Federal (MP), Provincial (MPP/MLA), Municipal (Mayor/Councillor)
2. **Bill Tracking**: Comprehensive bill model with status tracking
3. **Parliamentary Features**: Hansard, speeches, committee data
4. **API Endpoints**: REST and GraphQL interfaces
5. **UI Pages**: Dashboard, Database browser, Parliamentary viewer, Admin panel
6. **Policy Engine**: OPA integration for access control

### ⚠️ What's Missing or Needs Enhancement:

## 🔧 Implementation Tasks

### 1. **Enhanced Data Display in UI** 🎨

#### Federal MPs Page
```typescript
// dashboard/src/pages/FederalMPs.tsx
- Display all 338 MPs with photos, party, riding
- Show each MP's sponsored bills
- Display committee memberships
- Show voting records
- Link to speeches in Hansard
```

#### Provincial MPPs/MLAs Page
```typescript
// dashboard/src/pages/ProvincialMPPs.tsx
- Province selector (ON, BC, AB, etc.)
- Display MPPs/MLAs by province
- Show provincial bills
- Committee memberships
- Contact information
```

#### Municipal Leaders Page
```typescript
// dashboard/src/pages/MunicipalLeaders.tsx
- City/municipality search
- Display mayors and councillors
- Show local bylaws and resolutions
- Meeting attendance
- Contact details
```

### 2. **API Enhancements** 🚀

#### New Endpoints Needed:
```python
# Federal specific
GET /api/federal/mps
GET /api/federal/mps/{id}
GET /api/federal/mps/{id}/bills
GET /api/federal/mps/{id}/votes
GET /api/federal/mps/{id}/speeches

# Provincial specific
GET /api/provincial/mpps
GET /api/provincial/mpps?province={code}
GET /api/provincial/mpps/{id}/bills
GET /api/provincial/bills?province={code}

# Municipal specific
GET /api/municipal/leaders
GET /api/municipal/leaders?city={name}
GET /api/municipal/bylaws
```

### 3. **Data Collection & Scraping** 🔍

#### Federal Data Sources:
- **House of Commons**: ourcommons.ca
- **LEGISinfo**: parl.ca/legisinfo
- **OpenParliament**: openparliament.ca API

#### Provincial Data Sources:
- **Ontario**: ola.org
- **British Columbia**: leg.bc.ca
- **Alberta**: assembly.ab.ca
- **Quebec**: assnat.qc.ca

#### Municipal Data Sources:
- **Toronto**: toronto.ca/council
- **Vancouver**: vancouver.ca/your-government
- **Montreal**: ville.montreal.qc.ca
- **Calgary**: calgary.ca/council

### 4. **Scraper Implementation** 🛠️

```python
# src/scrapers/federal_scraper.py
class FederalMPScraper:
    def scrape_all_mps(self):
        # Scrape from ourcommons.ca
        # Get MP details, photos, contact info
        
    def scrape_federal_bills(self):
        # Scrape from parl.ca/legisinfo
        # Get bill text, status, sponsors
        
    def scrape_committee_data(self):
        # Scrape committee memberships
        # Get meeting schedules, reports

# src/scrapers/provincial_scraper.py
class ProvincialMPPScraper:
    def scrape_ontario_mpps(self):
        # Scrape from ola.org
        
    def scrape_bc_mlas(self):
        # Scrape from leg.bc.ca
        
    def scrape_alberta_mlas(self):
        # Scrape from assembly.ab.ca

# src/scrapers/municipal_scraper.py
class MunicipalLeaderScraper:
    def scrape_toronto_council(self):
        # Scrape Toronto city councillors
        
    def scrape_vancouver_council(self):
        # Scrape Vancouver city councillors
```

### 5. **Database Schema Enhancements** 📊

```sql
-- Add missing indexes for performance
CREATE INDEX idx_representative_name ON representatives(name);
CREATE INDEX idx_bill_title ON bills(title);
CREATE INDEX idx_bill_introduced_date ON bills(introduced_date);

-- Add full-text search
CREATE INDEX idx_bill_fulltext ON bills USING gin(to_tsvector('english', title || ' ' || summary));
CREATE INDEX idx_representative_search ON representatives USING gin(to_tsvector('english', name || ' ' || COALESCE(district, '')));

-- Add materialized views for performance
CREATE MATERIALIZED VIEW federal_mp_summary AS
SELECT 
    r.*,
    COUNT(DISTINCT bs.bill_id) as sponsored_bills_count,
    COUNT(DISTINCT cm.committee_id) as committees_count,
    COUNT(DISTINCT v.id) as votes_count
FROM representatives r
JOIN jurisdictions j ON r.jurisdiction_id = j.id
LEFT JOIN bill_sponsorships bs ON bs.representative_id = r.id
LEFT JOIN committee_memberships cm ON cm.representative_id = r.id
LEFT JOIN votes v ON v.representative_id = r.id
WHERE j.jurisdiction_type = 'federal' AND r.role = 'MP'
GROUP BY r.id;
```

### 6. **Phased Loading Implementation** ⏳

```python
# src/phased_loading_manager.py
class PhasedLoadingManager:
    """Manages phased data loading to prevent overwhelming the system"""
    
    PHASES = [
        {
            'name': 'Federal Core',
            'duration': '2 hours',
            'tasks': [
                'Load all 338 MPs',
                'Load current federal bills',
                'Load House committees'
            ]
        },
        {
            'name': 'Provincial Core',
            'duration': '4 hours',
            'tasks': [
                'Load Ontario MPPs',
                'Load BC MLAs',
                'Load Alberta MLAs',
                'Load Quebec MNAs'
            ]
        },
        {
            'name': 'Municipal Leaders',
            'duration': '6 hours',
            'tasks': [
                'Load top 20 cities mayors',
                'Load city councillors',
                'Load recent bylaws'
            ]
        },
        {
            'name': 'Historical Data',
            'duration': '12 hours',
            'tasks': [
                'Load Hansard archives',
                'Load historical bills',
                'Load past representatives'
            ]
        }
    ]
```

### 7. **UI Components Implementation** 🎨

```typescript
// dashboard/src/components/RepresentativeCard.tsx
interface RepresentativeCardProps {
    representative: Representative
    showDetails?: boolean
    onViewBills?: () => void
    onViewVotes?: () => void
}

// dashboard/src/components/BillCard.tsx
interface BillCardProps {
    bill: Bill
    showSponsor?: boolean
    showVotes?: boolean
    onViewDetails?: () => void
}

// dashboard/src/components/JurisdictionFilter.tsx
interface JurisdictionFilterProps {
    selectedType?: 'federal' | 'provincial' | 'municipal'
    selectedProvince?: string
    selectedCity?: string
    onChange: (filters: FilterState) => void
}
```

### 8. **Testing Strategy** 🧪

```python
# tests/test_federal_access.py
def test_federal_mp_list():
    """Test that all 338 MPs are accessible"""
    response = client.get("/api/federal/mps")
    assert response.status_code == 200
    assert len(response.json()) >= 338

def test_federal_bills_by_mp():
    """Test bills sponsored by specific MP"""
    # Get first MP
    mps = client.get("/api/federal/mps").json()
    mp_id = mps[0]['id']
    
    response = client.get(f"/api/federal/mps/{mp_id}/bills")
    assert response.status_code == 200

# tests/test_provincial_access.py
def test_provincial_mpp_by_province():
    """Test filtering MPPs by province"""
    response = client.get("/api/provincial/mpps?province=ON")
    assert response.status_code == 200
    assert all(mpp['province'] == 'ON' for mpp in response.json())

# tests/test_municipal_access.py
def test_municipal_leaders_by_city():
    """Test filtering municipal leaders by city"""
    response = client.get("/api/municipal/leaders?city=Toronto")
    assert response.status_code == 200
```

### 9. **Integration with External APIs** 🔗

```python
# src/integrations/openparliament_client.py
class OpenParliamentClient:
    """Client for OpenParliament.ca API"""
    BASE_URL = "https://api.openparliament.ca"
    
    def get_politicians(self):
        return requests.get(f"{self.BASE_URL}/politicians/").json()
    
    def get_bills(self):
        return requests.get(f"{self.BASE_URL}/bills/").json()
    
    def get_votes(self):
        return requests.get(f"{self.BASE_URL}/votes/").json()

# src/integrations/civic_info_client.py
class CivicInfoClient:
    """Client for various civic data sources"""
    
    def get_ontario_mpps(self):
        # Scrape or API call to ola.org
        pass
    
    def get_toronto_councillors(self):
        # API call to Toronto Open Data
        pass
```

### 10. **Performance Optimizations** ⚡

```python
# src/api/caching.py
from functools import lru_cache
import redis

redis_client = redis.Redis(host='redis', port=6379)

def cache_key(prefix: str, **kwargs):
    """Generate cache key from prefix and parameters"""
    parts = [prefix]
    for k, v in sorted(kwargs.items()):
        parts.append(f"{k}:{v}")
    return ":".join(parts)

def cached_endpoint(expire_time=3600):
    """Decorator for caching API responses"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            key = cache_key(func.__name__, **kwargs)
            cached = redis_client.get(key)
            if cached:
                return json.loads(cached)
            
            result = func(*args, **kwargs)
            redis_client.setex(key, expire_time, json.dumps(result))
            return result
        return wrapper
    return decorator
```

## 📊 Success Metrics

1. **Data Completeness**:
   - ✅ All 338 federal MPs loaded
   - ✅ All provincial MPPs/MLAs loaded (900+)
   - ✅ Major city mayors and councillors (1000+)
   - ✅ Current bills tracked (500+ federal, 2000+ provincial)

2. **API Performance**:
   - ✅ < 100ms response time for list endpoints
   - ✅ < 50ms for cached responses
   - ✅ Support for 1000+ concurrent users

3. **UI Functionality**:
   - ✅ All representatives searchable and filterable
   - ✅ Bill tracking with status updates
   - ✅ Export functionality working
   - ✅ Mobile responsive design

## 🚀 Deployment Checklist

- [ ] Run database migrations
- [ ] Load initial data (phased approach)
- [ ] Configure Redis caching
- [ ] Set up monitoring alerts
- [ ] Enable backup procedures
- [ ] Configure rate limiting
- [ ] Set up SSL certificates
- [ ] Configure CDN for static assets
- [ ] Enable error tracking (Sentry)
- [ ] Set up log aggregation

## 📅 Timeline

**Week 1**: UI Implementation
- Days 1-2: Federal MPs page
- Days 3-4: Provincial MPPs page  
- Days 5-7: Municipal leaders page

**Week 2**: API Development
- Days 1-3: New endpoints implementation
- Days 4-5: Testing and optimization
- Days 6-7: Documentation

**Week 3**: Data Collection
- Days 1-4: Scraper development
- Days 5-7: Initial data loading

**Week 4**: Testing & Deployment
- Days 1-3: Comprehensive testing
- Days 4-5: Performance optimization
- Days 6-7: Production deployment