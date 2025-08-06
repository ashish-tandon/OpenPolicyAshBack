# OpenPolicy Merge - System Architecture

## Overview

OpenPolicy Merge is a comprehensive Canadian civic data platform built on a modern microservices architecture. The system integrates data from federal, provincial, and municipal sources to provide unified access to Canadian political and legislative information.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          OpenPolicy Merge Platform                             │
├─────────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐                │
│  │   Web Client    │  │  Mobile Client  │  │   Admin Panel   │                │
│  │    (React)      │  │ (React Native)  │  │ (React + TS)    │                │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘                │
│           │                     │                     │                        │
│  ┌─────────────────────────────────────────────────────────────────────────────┤
│  │                          Nginx Reverse Proxy                               │
│  └─────────────────────────────────────────────────────────────────────────────┤
│           │                                                                    │
│  ┌─────────────────────────────────────────────────────────────────────────────┤
│  │                            API Gateway                                     │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │
│  │  │   REST API  │  │  GraphQL    │  │ WebSocket   │  │  Swagger    │      │
│  │  │  (FastAPI)  │  │ (Strawberry)│  │  Events     │  │    Docs     │      │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘      │
│  └─────────────────────────────────────────────────────────────────────────────┤
│           │                                                                    │
│  ┌─────────────────────────────────────────────────────────────────────────────┤
│  │                         Business Logic Layer                               │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │
│  │  │ Parliament  │  │   Scraper   │  │    Data     │  │    Auth     │      │
│  │  │  Service    │  │   Manager   │  │ Validation  │  │  Service    │      │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘      │
│  └─────────────────────────────────────────────────────────────────────────────┤
│           │                                                                    │
│  ┌─────────────────────────────────────────────────────────────────────────────┤
│  │                          Data Access Layer                                 │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │
│  │  │ PostgreSQL  │  │    Redis    │  │   Celery    │  │    File     │      │
│  │  │  Database   │  │   Cache     │  │   Workers   │  │   Storage   │      │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘      │
│  └─────────────────────────────────────────────────────────────────────────────┤
│           │                                                                    │
│  ┌─────────────────────────────────────────────────────────────────────────────┤
│  │                          External Integrations                             │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │
│  │  │ Parliament  │  │ Represent   │  │ Municipal   │  │  Provincial │      │
│  │  │   APIs      │  │    API      │  │  Websites   │  │   APIs      │      │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘      │
│  └─────────────────────────────────────────────────────────────────────────────┤
└─────────────────────────────────────────────────────────────────────────────────┘
```

## Data Flow Architecture

### 1. Data Ingestion Pipeline

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                             Data Sources                                       │
├─────────────────────────────────────────────────────────────────────────────────┤
│  Federal Sources          │  Provincial Sources      │  Municipal Sources       │
│  ┌─────────────────┐     │  ┌─────────────────┐     │  ┌─────────────────┐    │
│  │ ourcommons.ca   │     │  │ legislature.    │     │  │ toronto.ca      │    │
│  │ parl.ca         │     │  │ websites        │     │  │ montreal.ca     │    │
│  │ elections.ca    │     │  │ (13 provinces)  │     │  │ vancouver.ca    │    │
│  │ represent API   │     │  │                 │     │  │ (200+ cities)   │    │
│  └─────────────────┘     │  └─────────────────┘     │  └─────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────────┘
           │                         │                         │
           ▼                         ▼                         ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                             Scraper Layer                                      │
├─────────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐          │
│  │ Parliamentary   │     │ Provincial      │     │ Municipal       │          │
│  │ Scrapers        │     │ Scrapers        │     │ Scrapers        │          │
│  │ - Bills         │     │ - Legislation   │     │ - Councils      │          │
│  │ - Hansard       │     │ - MLAs/MPPs     │     │ - Bylaws        │          │
│  │ - Committees    │     │ - Committees    │     │ - Meetings      │          │
│  │ - MPs           │     │ - Sessions      │     │ - Representatives│         │
│  └─────────────────┘     └─────────────────┘     └─────────────────┘          │
└─────────────────────────────────────────────────────────────────────────────────┘
           │                         │                         │
           ▼                         ▼                         ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          Data Processing                                       │
├─────────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐          │
│  │ Data Validation │     │ Normalization   │     │ Deduplication   │          │
│  │ - Schema check  │     │ - Name cleanup  │     │ - Cross-source  │          │
│  │ - Required      │     │ - Address std   │     │ - Entity match  │          │
│  │   fields        │     │ - Phone format  │     │ - Conflict res  │          │
│  │ - Format check  │     │ - Title cleanup │     │ - Data merge    │          │
│  └─────────────────┘     └─────────────────┘     └─────────────────┘          │
└─────────────────────────────────────────────────────────────────────────────────┘
           │                         │                         │
           └─────────────────────────┼─────────────────────────┘
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        Data Storage (PostgreSQL 16+)                          │
├─────────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐          │
│  │ Core Tables     │     │ Parliamentary   │     │ Audit & Logs    │          │
│  │ - jurisdictions │     │ - sessions      │     │ - scraping_runs │          │
│  │ - representatives│     │ - hansard_docs  │     │ - data_quality  │          │
│  │ - bills         │     │ - statements    │     │ - change_log    │          │
│  │ - committees    │     │ - votes         │     │ - error_log     │          │
│  │ - events        │     │ - memberships   │     │ - metrics       │          │
│  └─────────────────┘     └─────────────────┘     └─────────────────┘          │
└─────────────────────────────────────────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                             API Layer                                          │
├─────────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐          │
│  │ REST Endpoints  │     │ GraphQL Schema  │     │ WebSocket       │          │
│  │ - CRUD ops      │     │ - Complex       │     │ - Real-time     │          │
│  │ - Filtering     │     │   queries       │     │ - Push updates  │          │
│  │ - Pagination    │     │ - Relationships │     │ - Notifications │          │
│  │ - Sorting       │     │ - Mutations     │     │ - Live stats    │          │
│  └─────────────────┘     └─────────────────┘     └─────────────────┘          │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 2. Real-time Data Processing

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          Scheduler (Celery Beat)                               │
├─────────────────────────────────────────────────────────────────────────────────┤
│  Daily: 6:00 AM EST                    │  Hourly: Federal Priority             │
│  ┌─────────────────┐                   │  ┌─────────────────┐                 │
│  │ Full Scrape     │                   │  │ Parliament      │                 │
│  │ - All jurisdic. │                   │  │ - Active bills  │                 │
│  │ - All data      │                   │  │ - Today's votes │                 │
│  │ - Validation    │                   │  │ - New statements│                 │
│  │ - Reports       │                   │  │ - Committees    │                 │
│  └─────────────────┘                   │  └─────────────────┘                 │
└─────────────────────────────────────────────────────────────────────────────────┘
           │                                         │
           ▼                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           Celery Workers                                       │
├─────────────────────────────────────────────────────────────────────────────────┤
│  Worker Pool 1            │  Worker Pool 2            │  Worker Pool 3          │
│  ┌─────────────────┐     │  ┌─────────────────┐     │  ┌─────────────────┐    │
│  │ Federal Tasks   │     │  │ Provincial      │     │  │ Municipal       │    │
│  │ - Parliament    │     │  │ - Legislatures  │     │  │ - City councils │    │
│  │ - Elections     │     │  │ - Premiers      │     │  │ - Mayors        │    │
│  │ - Represent API │     │  │ - Committees    │     │  │ - Bylaws        │    │
│  └─────────────────┘     │  └─────────────────┘     │  └─────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────────┘
           │                         │                         │
           ▼                         ▼                         ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          Redis Message Queue                                   │
├─────────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐          │
│  │ Task Queue      │     │ Result Store    │     │ Cache Layer     │          │
│  │ - Pending jobs  │     │ - Job results   │     │ - API responses │          │
│  │ - Retry queue   │     │ - Error logs    │     │ - Query cache   │          │
│  │ - Priority      │     │ - Metrics       │     │ - Session data  │          │
│  └─────────────────┘     └─────────────────┘     └─────────────────┘          │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## Database Schema Design

### Core Entity Relationships

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         PostgreSQL 16+ Database Schema                         │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐           │
│  │  Jurisdictions  │────▶│ Representatives │◀────│      Bills      │           │
│  │  - id (UUID)    │     │  - id (UUID)    │     │  - id (UUID)    │           │
│  │  - name         │     │  - name         │     │  - number       │           │
│  │  - type         │     │  - role         │     │  - title        │           │
│  │  - code         │     │  - party        │     │  - status       │           │
│  │  - website      │     │  - email        │     │  - intro_date   │           │
│  └─────────────────┘     │  - phone        │     │  - parliament   │           │
│           │               │  - riding       │     │  - session      │           │
│           │               └─────────────────┘     └─────────────────┘           │
│           │                        │                       │                   │
│           │                        ▼                       ▼                   │
│           │               ┌─────────────────┐     ┌─────────────────┐           │
│           └──────────────▶│   Committees    │     │ Parliamentary   │           │
│                           │  - id (UUID)    │     │   Sessions      │           │
│                           │  - name         │     │  - id (UUID)    │           │
│                           │  - type         │     │  - parliament   │           │
│                           │  - chair_id     │     │  - session      │           │
│                           │  - members      │     │  - start_date   │           │
│                           └─────────────────┘     │  - end_date     │           │
│                                    │               └─────────────────┘           │
│                                    ▼                       │                   │
│           ┌─────────────────┐     ┌─────────────────┐     ▼                   │
│           │     Events      │     │ Committee       │ ┌─────────────────┐     │
│           │  - id (UUID)    │     │   Meetings      │ │ Hansard         │     │
│           │  - title        │     │  - id (UUID)    │ │ Documents       │     │
│           │  - date         │     │  - committee_id │ │  - id (UUID)    │     │
│           │  - type         │     │  - date         │ │  - type         │     │
│           │  - jurisdiction │     │  - agenda       │ │  - date         │     │
│           └─────────────────┘     │  - transcript   │ │  - session_id   │     │
│                    │               └─────────────────┘ │  - source_url   │     │
│                    ▼                       │           │  - processed    │     │
│           ┌─────────────────┐             ▼           └─────────────────┘     │
│           │     Votes       │    ┌─────────────────┐           │               │
│           │  - id (UUID)    │    │ Parliamentary   │           ▼               │
│           │  - bill_id      │    │  Statements     │  ┌─────────────────┐     │
│           │  - event_id     │    │  - id (UUID)    │  │ Electoral       │     │
│           │  - result       │    │  - document_id  │  │ Memberships     │     │
│           │  - date         │    │  - politician_id│  │  - id (UUID)    │     │
│           │  - chamber      │    │  - content      │  │  - rep_id       │     │
│           └─────────────────┘    │  - sequence     │  │  - riding       │     │
│                                  │  - type         │  │  - party        │     │
│                                  └─────────────────┘  │  - start_date   │     │
│                                                       │  - end_date     │     │
│                                                       │  - session_id   │     │
│                                                       └─────────────────┘     │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Data Quality & Audit Schema

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         Audit & Quality Assurance                              │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐           │
│  │ Scraping_Runs   │     │ Data_Quality    │     │ Change_Log      │           │
│  │  - id (UUID)    │────▶│   _Issues       │◀────│  - id (UUID)    │           │
│  │  - jurisdiction │     │  - id (UUID)    │     │  - table_name   │           │
│  │  - scraper_type │     │  - run_id       │     │  - record_id    │           │
│  │  - start_time   │     │  - issue_type   │     │  - field_name   │           │
│  │  - end_time     │     │  - description  │     │  - old_value    │           │
│  │  - status       │     │  - severity     │     │  - new_value    │           │
│  │  - records_found│     │  - resolved     │     │  - changed_by   │           │
│  │  - records_new  │     └─────────────────┘     │  - changed_at   │           │
│  │  - records_upd  │              │               └─────────────────┘           │
│  │  - errors       │              ▼                        │                  │
│  └─────────────────┘     ┌─────────────────┐              ▼                  │
│           │               │ Error_Log       │     ┌─────────────────┐           │
│           ▼               │  - id (UUID)    │     │ Performance     │           │
│  ┌─────────────────┐     │  - run_id       │     │   Metrics       │           │
│  │ Source_Metadata │     │  - error_type   │     │  - id (UUID)    │           │
│  │  - id (UUID)    │     │  - message      │     │  - endpoint     │           │
│  │  - source_name  │     │  - stack_trace  │     │  - response_time│           │
│  │  - last_updated │     │  - timestamp    │     │  - query_count  │           │
│  │  - url          │     │  - resolved     │     │  - cache_hits   │           │
│  │  - checksum     │     └─────────────────┘     │  - timestamp    │           │
│  │  - status       │                             └─────────────────┘           │
│  └─────────────────┘                                                           │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## API Architecture

### REST API Endpoints

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              REST API Structure                                │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  /api/v1/                                                                      │
│  ├── health                     # Health check                                 │
│  ├── stats                      # System statistics                            │
│  ├── auth/                                                                     │
│  │   ├── login                  # User authentication                          │
│  │   ├── logout                 # User logout                                  │
│  │   └── refresh                # Token refresh                               │
│  │                                                                             │
│  ├── jurisdictions/             # Canadian jurisdictions                       │
│  │   ├── GET    /               # List all jurisdictions                      │
│  │   ├── GET    /{id}           # Get specific jurisdiction                    │
│  │   ├── GET    /{id}/reps      # Representatives by jurisdiction              │
│  │   └── GET    /{id}/bills     # Bills by jurisdiction                       │
│  │                                                                             │
│  ├── representatives/           # Elected officials                            │
│  │   ├── GET    /               # List with filtering                         │
│  │   ├── GET    /{id}           # Individual representative                    │
│  │   ├── GET    /{id}/bills     # Bills sponsored/involved                    │
│  │   ├── GET    /{id}/statements # Parliamentary statements                   │
│  │   ├── GET    /{id}/committees # Committee memberships                       │
│  │   └── GET    /{id}/votes     # Voting record                               │
│  │                                                                             │
│  ├── bills/                     # Legislation                                  │
│  │   ├── GET    /               # List with filtering                         │
│  │   ├── GET    /{id}           # Individual bill                             │
│  │   ├── GET    /{id}/votes     # Votes on bill                               │
│  │   ├── GET    /{id}/statements # Debate statements                           │
│  │   └── GET    /{id}/timeline  # Status history                              │
│  │                                                                             │
│  ├── committees/                # Parliamentary committees                      │
│  │   ├── GET    /               # List committees                             │
│  │   ├── GET    /{id}           # Committee details                           │
│  │   ├── GET    /{id}/members   # Committee members                           │
│  │   ├── GET    /{id}/meetings  # Committee meetings                          │
│  │   └── GET    /{id}/reports   # Committee reports                           │
│  │                                                                             │
│  ├── parliamentary/             # Parliamentary-specific data                  │
│  │   ├── sessions/              # Parliamentary sessions                       │
│  │   │   ├── GET  /             # List sessions                               │
│  │   │   └── GET  /{id}         # Session details                             │
│  │   ├── hansard/               # Hansard documents                           │
│  │   │   ├── GET  /             # List documents                              │
│  │   │   ├── GET  /{id}         # Document content                            │
│  │   │   └── GET  /{id}/search  # Search within document                      │
│  │   └── votes/                 # Parliamentary votes                          │
│  │       ├── GET  /             # List votes                                  │
│  │       └── GET  /{id}         # Vote details                                │
│  │                                                                             │
│  ├── events/                    # Political events                             │
│  │   ├── GET    /               # List events                                 │
│  │   ├── GET    /{id}           # Event details                               │
│  │   └── GET    /upcoming       # Upcoming events                             │
│  │                                                                             │
│  ├── search/                    # Global search                               │
│  │   ├── GET    /               # Search across all entities                  │
│  │   ├── GET    /representatives # Search representatives                     │
│  │   ├── GET    /bills          # Search bills                               │
│  │   └── GET    /statements     # Search statements                           │
│  │                                                                             │
│  └── admin/                     # Administrative endpoints                     │
│      ├── scraping/              # Scraper management                          │
│      │   ├── GET    /status     # Scraper status                              │
│      │   ├── POST   /run        # Trigger scraper                             │
│      │   └── GET    /logs       # Scraper logs                                │
│      ├── data-quality/          # Data quality reports                        │
│      │   ├── GET    /issues     # Data quality issues                         │
│      │   └── GET    /reports    # Quality reports                             │
│      └── metrics/               # System metrics                              │
│          ├── GET    /performance # Performance metrics                        │
│          └── GET    /usage      # API usage statistics                        │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### GraphQL Schema

```graphql
# Core Types
type Jurisdiction {
    id: ID!
    name: String!
    type: JurisdictionType!
    code: String!
    website: String
    representatives(
        role: RepresentativeRole
        party: String
        active: Boolean
    ): [Representative!]!
    bills(status: BillStatus, session: Int): [Bill!]!
    committees: [Committee!]!
    stats: JurisdictionStats!
}

type Representative {
    id: ID!
    name: String!
    role: RepresentativeRole!
    party: String
    riding: String
    email: String
    phone: String
    photoUrl: String
    gender: String
    jurisdiction: Jurisdiction!
    bills: [Bill!]!
    committees: [Committee!]!
    statements(limit: Int, offset: Int): [ParliamentaryStatement!]!
    votes: [Vote!]!
    electoralHistory: [ElectoralMembership!]!
}

type Bill {
    id: ID!
    number: String!
    title: String!
    summary: String
    status: BillStatus!
    statusDate: Date
    introductionDate: Date
    privateMember: Boolean!
    parliament: Int
    session: Int
    jurisdiction: Jurisdiction!
    sponsor: Representative
    votes: [Vote!]!
    statements: [ParliamentaryStatement!]!
    timeline: [BillStatusChange!]!
}

type Committee {
    id: ID!
    name: String!
    type: CommitteeType!
    chair: Representative
    members: [Representative!]!
    jurisdiction: Jurisdiction!
    meetings: [CommitteeMeeting!]!
    reports: [CommitteeReport!]!
}

type ParliamentarySession {
    id: ID!
    parliament: Int!
    session: Int!
    startDate: Date!
    endDate: Date
    dissolvedDate: Date
    bills: [Bill!]!
    hansardDocuments: [HansardDocument!]!
}

type HansardDocument {
    id: ID!
    documentType: DocumentType!
    date: Date!
    number: String
    session: ParliamentarySession!
    sourceUrl: String
    processed: Boolean!
    statements: [ParliamentaryStatement!]!
}

type ParliamentaryStatement {
    id: ID!
    document: HansardDocument!
    politician: Representative
    sequence: Int!
    content: String!
    contentEn: String
    contentFr: String
    statementType: String
    timeOffset: Int
}

# Query Root
type Query {
    # Jurisdictions
    jurisdictions(type: JurisdictionType): [Jurisdiction!]!
    jurisdiction(id: ID!): Jurisdiction
    
    # Representatives
    representatives(
        jurisdiction: ID
        role: RepresentativeRole
        party: String
        active: Boolean
        search: String
    ): [Representative!]!
    representative(id: ID!): Representative
    
    # Bills
    bills(
        jurisdiction: ID
        status: BillStatus
        parliament: Int
        session: Int
        search: String
    ): [Bill!]!
    bill(id: ID!): Bill
    
    # Committees
    committees(jurisdiction: ID, type: CommitteeType): [Committee!]!
    committee(id: ID!): Committee
    
    # Parliamentary Data
    parliamentarySessions(parliament: Int): [ParliamentarySession!]!
    parliamentarySession(id: ID!): ParliamentarySession
    hansardDocuments(session: ID, date: Date): [HansardDocument!]!
    hansardDocument(id: ID!): HansardDocument
    
    # Search
    search(query: String!, type: SearchType): [SearchResult!]!
    
    # Statistics
    stats: GlobalStats!
}

# Mutation Root
type Mutation {
    # Administrative operations
    triggerScraper(jurisdiction: ID!, scraperType: String!): ScrapingRun!
    resolveDataQualityIssue(issueId: ID!): DataQualityIssue!
}

# Subscription Root
type Subscription {
    # Real-time updates
    scrapingStatus: ScrapingRun!
    newBill: Bill!
    newVote: Vote!
    dataQualityAlert: DataQualityIssue!
}
```

## Security Architecture

### Authentication & Authorization

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                            Security Layer                                      │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐           │
│  │   API Gateway   │────▶│  Rate Limiting  │────▶│  Load Balancer  │           │
│  │  - Request Val. │     │  - Per IP limit │     │  - Health checks│           │
│  │  - CORS headers │     │  - Per user     │     │  - Failover     │           │
│  │  - Request size │     │  - Per endpoint │     │  - SSL termination          │
│  └─────────────────┘     └─────────────────┘     └─────────────────┘           │
│           │                        │                        │                  │
│           ▼                        ▼                        ▼                  │
│  ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐           │
│  │ JWT Auth        │     │ Role-Based      │     │ Data Encryption │           │
│  │  - Token issue  │────▶│   Access        │────▶│  - At rest      │           │
│  │  - Token verify │     │  - Public read  │     │  - In transit   │           │
│  │  - Refresh      │     │  - Admin write  │     │  - Backup enc   │           │
│  │  - Expiration   │     │  - API quotas   │     │  - Key rotation │           │
│  └─────────────────┘     └─────────────────┘     └─────────────────┘           │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Data Protection

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           Data Protection Strategy                             │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  Input Validation          │  Data Sanitization        │  Output Protection     │
│  ┌─────────────────┐      │  ┌─────────────────┐      │  ┌─────────────────┐   │
│  │ Schema validate │      │  │ HTML cleaning   │      │  │ XSS protection  │   │
│  │ Type checking   │      │  │ SQL injection   │      │  │ CSRF tokens     │   │
│  │ Length limits   │      │  │   prevention    │      │  │ Content-Type    │   │
│  │ Format rules    │      │  │ Input encoding  │      │  │   headers       │   │
│  │ Required fields │      │  │ Special chars   │      │  │ Response encode │   │
│  └─────────────────┘      │  └─────────────────┘      │  └─────────────────┘   │
│                                                                                 │
│  Audit Logging             │  Privacy Controls         │  Compliance          │
│  ┌─────────────────┐      │  ┌─────────────────┐      │  ┌─────────────────┐   │
│  │ Access logs     │      │  │ PII identification │    │  │ PIPEDA compliance│   │
│  │ Change tracking │      │  │ Data minimization│      │  │ Data retention  │   │
│  │ Error logging   │      │  │ Consent tracking │      │  │ Right to forget │   │
│  │ Performance     │      │  │ Anonymization   │      │  │ Breach response │   │
│  └─────────────────┘      │  └─────────────────┘      │  └─────────────────┘   │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## Monitoring & Observability

### System Monitoring

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        Monitoring & Alerting Stack                             │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  Application Metrics      │  Infrastructure           │  Business Metrics       │
│  ┌─────────────────┐     │  ┌─────────────────┐     │  ┌─────────────────┐    │
│  │ API Response    │     │  │ CPU/Memory      │     │  │ Data freshness  │    │
│  │   times         │     │  │ Disk space      │     │  │ Scraper success │    │
│  │ Request counts  │     │  │ Network I/O     │     │  │ Data quality    │    │
│  │ Error rates     │     │  │ Database perf   │     │  │ User activity   │    │
│  │ Cache hit ratio │     │  │ Container       │     │  │ Coverage gaps   │    │
│  │ Queue lengths   │     │  │   health        │     │  │ Update frequency│    │
│  └─────────────────┘     │  └─────────────────┘     │  └─────────────────┘    │
│           │               │           │               │           │            │
│           ▼               │           ▼               │           ▼            │
│  ┌─────────────────┐     │  ┌─────────────────┐     │  ┌─────────────────┐    │
│  │ Prometheus      │     │  │ Node Exporter   │     │  │ Custom Metrics  │    │
│  │ - Time series   │◀────┼──│ - System stats  │◀────┼──│ - Domain KPIs   │    │
│  │ - Alerting      │     │  │ - Container     │     │  │ - Data quality  │    │
│  │ - Retention     │     │  │   metrics       │     │  │ - Business      │    │
│  └─────────────────┘     │  └─────────────────┘     │  │   intelligence  │    │
│           │               │                          │  └─────────────────┘    │
│           ▼               │                          │                         │
│  ┌─────────────────┐     │  ┌─────────────────┐     │  ┌─────────────────┐    │
│  │ Grafana         │     │  │ Alert Manager   │     │  │ Dashboard       │    │
│  │ - Dashboards    │◀────┼──│ - Notifications │────▶│  │ - Real-time     │    │
│  │ - Visualizations│     │  │ - Escalation    │     │  │ - Historical    │    │
│  │ - Annotations   │     │  │ - Routing       │     │  │ - Mobile view   │    │
│  └─────────────────┘     │  └─────────────────┘     │  └─────────────────┘    │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Logging Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                            Centralized Logging                                 │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  Application Logs         │  System Logs              │  Audit Logs            │
│  ┌─────────────────┐     │  ┌─────────────────┐     │  ┌─────────────────┐    │
│  │ FastAPI         │     │  │ Container logs  │     │  │ API access      │    │
│  │ Celery workers  │     │  │ Nginx access    │     │  │ Data changes    │    │
│  │ Scrapers        │     │  │ PostgreSQL      │     │  │ Admin actions   │    │
│  │ Database        │     │  │ Redis           │     │  │ Security events │    │
│  │ Authentication  │     │  │ System events   │     │  │ Error tracking  │    │
│  └─────────────────┘     │  └─────────────────┘     │  └─────────────────┘    │
│           │               │           │               │           │            │
│           ▼               │           ▼               │           ▼            │
│  ┌─────────────────┐     │  ┌─────────────────┐     │  ┌─────────────────┐    │
│  │ Structured      │     │  │ Syslog          │     │  │ Security logs   │    │
│  │   Logging       │     │  │ Journald        │     │  │ Compliance      │    │
│  │ - JSON format   │     │  │ File rotation   │     │  │ Retention       │    │
│  │ - Correlation   │     │  │ Compression     │     │  │ Encryption      │    │
│  │   IDs           │     │  └─────────────────┘     │  └─────────────────┘    │
│  └─────────────────┘     │                          │                         │
│           │               │                          │                         │
│           ▼               │                          │                         │
│  ┌─────────────────────────────────────────────────────────────────────────────┤
│  │                        Log Aggregation (ELK Stack)                         │
│  │  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐                  │
│  │  │ Filebeat    │────▶│ Logstash    │────▶│ Elasticsearch│                  │
│  │  │ - Log       │     │ - Parsing   │     │ - Indexing  │                  │
│  │  │   shipping  │     │ - Filtering │     │ - Search    │                  │
│  │  │ - Buffering │     │ - Transform │     │ - Analytics │                  │
│  │  └─────────────┘     └─────────────┘     └─────────────┘                  │
│  │                               │                  │                          │
│  │                               ▼                  ▼                          │
│  │  ┌─────────────┐     ┌─────────────────┐     ┌─────────────┐              │
│  │  │ Kibana      │     │ Alerting        │     │ Retention   │              │
│  │  │ - Search    │     │ - Error spikes  │     │ - 90 days   │              │
│  │  │ - Dashboards│     │ - Performance   │     │ - Archival  │              │
│  │  │ - Reports   │     │ - Security      │     │ - Cleanup   │              │
│  │  └─────────────┘     └─────────────────┘     └─────────────┘              │
│  └─────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## Deployment Architecture

### Container Strategy

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                       Single Container Architecture                             │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────────┐│
│  │                      OpenPolicy Merge Container                            ││
│  │  ┌─────────────────────────────────────────────────────────────────────────┤│
│  │  │                         Supervisor                                      ││
│  │  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐      ││
│  │  │  │   Nginx     │ │  FastAPI    │ │    React    │ │   Flower    │      ││
│  │  │  │   :80       │ │   :8000     │ │   :3000     │ │   :5555     │      ││
│  │  │  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘      ││
│  │  └─────────────────────────────────────────────────────────────────────────┤│
│  │  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐      ││
│  │  │  │ PostgreSQL  │ │    Redis    │ │   Celery    │ │   Celery    │      ││
│  │  │  │   :5432     │ │   :6379     │ │   Worker    │ │    Beat     │      ││
│  │  │  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘      ││
│  │  └─────────────────────────────────────────────────────────────────────────┤│
│  │  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐      ││
│  │  │  │ Log Rotate  │ │ Monitoring  │ │   Backup    │ │  Health     │      ││
│  │  │  │   Service   │ │   Agents    │ │   Scripts   │ │   Checks    │      ││
│  │  │  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘      ││
│  │  └─────────────────────────────────────────────────────────────────────────┤│
│  └─────────────────────────────────────────────────────────────────────────────┘│
│                                      │                                          │
│                                      ▼                                          │
│  ┌─────────────────────────────────────────────────────────────────────────────┐│
│  │                         Persistent Volumes                                 ││
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐          ││
│  │  │ PostgreSQL  │ │  App Logs   │ │   Scraped   │ │   Backups   │          ││
│  │  │    Data     │ │   Volume    │ │    Data     │ │   Volume    │          ││
│  │  │   /data     │ │   /logs     │ │  /storage   │ │  /backups   │          ││
│  │  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘          ││
│  └─────────────────────────────────────────────────────────────────────────────┘│
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Production Environment

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          Production Infrastructure                              │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  Internet                                                                       │
│      │                                                                          │
│      ▼                                                                          │
│  ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐           │
│  │   CloudFlare    │────▶│     HAProxy     │────▶│   Application   │           │
│  │   - CDN         │     │   - SSL Term    │     │     Server      │           │
│  │   - DDoS        │     │   - Load Bal    │     │   - Container   │           │
│  │   - WAF         │     │   - Health      │     │   - Monitoring  │           │
│  │   - Caching     │     │     Check       │     │   - Logging     │           │
│  └─────────────────┘     └─────────────────┘     └─────────────────┘           │
│                                   │                        │                   │
│                                   ▼                        ▼                   │
│                          ┌─────────────────┐     ┌─────────────────┐           │
│                          │   Monitoring    │     │     Backup      │           │
│                          │   - Prometheus  │     │   - Daily       │           │
│                          │   - Grafana     │     │   - Incremental │           │
│                          │   - AlertMgr    │     │   - Offsite     │           │
│                          └─────────────────┘     └─────────────────┘           │
│                                                                                 │
│  Disaster Recovery                                                              │
│  ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐           │
│  │   Failover      │     │   Data Repl     │     │   Config Mgmt   │           │
│  │   - Standby     │────▶│   - Streaming   │────▶│   - GitOps      │           │
│  │   - Auto        │     │   - Point-in    │     │   - Secrets     │           │
│  │   - Manual      │     │     -time       │     │   - Environment │           │
│  └─────────────────┘     └─────────────────┘     └─────────────────┘           │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## Performance Optimization

### Caching Strategy

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           Multi-Layer Caching                                  │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  Client Side              │  CDN Layer               │  Application Layer       │
│  ┌─────────────────┐     │  ┌─────────────────┐     │  ┌─────────────────┐    │
│  │ Browser Cache   │     │  │ CloudFlare      │     │  │ Redis Cache     │    │
│  │ - Static assets │     │  │ - Static files  │     │  │ - API responses │    │
│  │ - API responses │     │  │ - Images        │     │  │ - Query results │    │
│  │ - 1 hour TTL    │     │  │ - CSS/JS        │     │  │ - Session data  │    │
│  └─────────────────┘     │  │ - 24 hour TTL   │     │  │ - 15 min TTL    │    │
│                           │  └─────────────────┘     │  └─────────────────┘    │
│                           │                          │                         │
│  Database Layer           │  Query Optimization      │  Connection Pooling     │
│  ┌─────────────────┐     │  ┌─────────────────┐     │  ┌─────────────────┐    │
│  │ Query Cache     │     │  │ Prepared        │     │  │ Connection      │    │
│  │ - Result sets   │     │  │   Statements    │     │  │   Pooling       │    │
│  │ - Indexes       │     │  │ - Query plans   │     │  │ - Max 50 conn   │    │
│  │ - Statistics    │     │  │ - Index hints   │     │  │ - Idle timeout  │    │
│  │ - Auto expire   │     │  │ - Partitioning  │     │  │ - Health checks │    │
│  └─────────────────┘     │  └─────────────────┘     │  └─────────────────┘    │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Database Optimization

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        PostgreSQL 16+ Optimization                             │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  Indexing Strategy         │  Partitioning            │  Query Optimization     │
│  ┌─────────────────┐      │  ┌─────────────────┐      │  ┌─────────────────┐   │
│  │ Primary Keys    │      │  │ Date-based      │      │  │ Query analysis  │   │
│  │ Foreign Keys    │      │  │   partitions    │      │  │ Execution plans │   │
│  │ Search fields   │      │  │ - Bills by year │      │  │ Index usage     │   │
│  │ Composite       │      │  │ - Events by     │      │  │ Join strategies │   │
│  │   indexes       │      │  │   quarter       │      │  │ Materialized    │   │
│  │ GIN for JSON    │      │  │ - Logs by month │      │  │   views         │   │
│  │ Text search     │      │  └─────────────────┘      │  └─────────────────┘   │
│  └─────────────────┘      │                           │                        │
│                            │                           │                        │
│  Memory Tuning             │  Maintenance              │  Monitoring            │
│  ┌─────────────────┐      │  ┌─────────────────┐      │  ┌─────────────────┐   │
│  │ shared_buffers  │      │  │ Auto vacuum     │      │  │ Query stats     │   │
│  │ work_mem        │      │  │ Analyze         │      │  │ Lock monitoring │   │
│  │ maintenance_    │      │  │ Reindex         │      │  │ Connection      │   │
│  │   work_mem      │      │  │ Log rotation    │      │  │   tracking      │   │
│  │ effective_cache │      │  │ Backup          │      │  │ Performance     │   │
│  │   _size         │      │  │   scheduling    │      │  │   insights      │   │
│  └─────────────────┘      │  └─────────────────┘      │  └─────────────────┘   │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## Scalability Plan

### Horizontal Scaling Strategy

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           Future Scalability                                   │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  Phase 1: Single Container    │  Phase 2: Multi-Container   │  Phase 3: K8s    │
│  ┌─────────────────┐         │  ┌─────────────────┐         │  ┌─────────────┐ │
│  │ All services    │         │  │ Separate        │         │  │ Kubernetes  │ │
│  │ in one          │────────▶│  │   containers    │────────▶│  │ deployment  │ │
│  │ container       │         │  │ - API           │         │  │ - Auto      │ │
│  │ - Simple        │         │  │ - Database      │         │  │   scaling   │ │
│  │ - Fast deploy   │         │  │ - Workers       │         │  │ - Rolling   │ │
│  │ - Easy debug    │         │  │ - Better        │         │  │   updates   │ │
│  │ - Current       │         │  │   isolation     │         │  │ - Service   │ │
│  │   approach      │         │  │ - Independent   │         │  │   mesh      │ │
│  └─────────────────┘         │  │   scaling       │         │  │ - Advanced  │ │
│                               │  └─────────────────┘         │  │   monitoring│ │
│                               │                              │  └─────────────┘ │
│                               │                              │                  │
│  Load Triggers               │  Scaling Metrics             │  Resource Mgmt   │
│  ┌─────────────────┐         │  ┌─────────────────┐         │  ┌─────────────┐ │
│  │ CPU > 70%       │         │  │ Response time   │         │  │ CPU limits  │ │
│  │ Memory > 80%    │         │  │ Queue length    │         │  │ Memory      │ │
│  │ Queue > 1000    │         │  │ Error rate      │         │  │   quotas    │ │
│  │ Response > 1s   │         │  │ Throughput      │         │  │ Storage     │ │
│  │ Disk > 85%      │         │  │ Active users    │         │  │   classes   │ │
│  └─────────────────┘         │  └─────────────────┘         │  └─────────────┘ │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

This architecture provides a robust, scalable foundation for the OpenPolicy Merge platform, ensuring reliable data ingestion, efficient API performance, and comprehensive monitoring capabilities.