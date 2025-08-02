# OpenPolicy Backend - Canadian Civic Data Platform

[![Docker Pulls](https://img.shields.io/docker/pulls/ashishtandon9/openpolicyashback.svg)](https://hub.docker.com/r/ashishtandon9/openpolicyashback)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

## 🇨🇦 Comprehensive Canadian Parliamentary & Civic Data System

OpenPolicy Backend is an enterprise-grade platform for accessing and analyzing Canadian civic data across federal, provincial, and municipal jurisdictions. Enhanced with parliamentary data processing capabilities and policy-as-code governance.

## 🚀 Features

- **123 Canadian Jurisdictions**: Complete coverage of federal, provincial/territorial, and municipal governments
- **Parliamentary Data Processing**: Hansard debates, committee meetings, and speech analysis
- **Policy-as-Code Governance**: Open Policy Agent (OPA) integration for smart access control
- **Real-Time Monitoring**: Automated data collection and freshness tracking
- **AI-Powered Analysis**: OpenAI integration for legislative insights
- **Enterprise API**: GraphQL and REST APIs with intelligent rate limiting

## 📦 Available Images

### Main Application
```bash
docker pull ashishtandon9/openpolicyashback:latest
```

### Policy Validator Service
```bash
docker pull ashishtandon9/openpolicyashback-policy-validator:latest
```

### Celery Worker
```bash
docker pull ashishtandon9/openpolicyashback-celery:latest
```

## 🔧 Quick Start

### Using Docker Compose (Recommended)

1. **Create a new directory for your deployment:**
```bash
mkdir openpolicy-deployment
cd openpolicy-deployment
```

2. **Download the docker-compose file:**
```bash
wget https://raw.githubusercontent.com/ashish-tandon/OpenPolicyAshBack/main/docker-compose.dockerhub.yml -O docker-compose.yml
```

3. **Download the policy files:**
```bash
mkdir -p policies
wget https://raw.githubusercontent.com/ashish-tandon/OpenPolicyAshBack/main/policies/data_quality.rego -P policies/
wget https://raw.githubusercontent.com/ashish-tandon/OpenPolicyAshBack/main/policies/api_access.rego -P policies/
```

4. **Create .env file:**
```bash
cat > .env << EOF
POSTGRES_PASSWORD=your-secure-password
OPENAI_API_KEY=sk-your-openai-api-key
EOF
```

5. **Start the stack:**
```bash
docker-compose up -d
```

6. **Initialize the database:**
```bash
# Wait for services to start
sleep 30

# Run database migrations
docker-compose exec app python -c "
from src.database.connection import engine
from src.database.models import Base
Base.metadata.create_all(engine)
print('Database initialized!')
"

# Apply parliamentary models migration
docker-compose exec app psql $DATABASE_URL -f migrations/001_add_parliamentary_models.sql
```

### Using Individual Containers

```bash
# PostgreSQL Database
docker run -d --name openpolicy-db \
  -e POSTGRES_DB=opencivicdata \
  -e POSTGRES_USER=openpolicy \
  -e POSTGRES_PASSWORD=changeme \
  postgres:13

# Redis
docker run -d --name openpolicy-redis redis:7-alpine

# OPA Policy Engine
docker run -d --name openpolicy-opa \
  -p 8181:8181 \
  -v $(pwd)/policies:/policies:ro \
  openpolicyagent/opa:latest-debug \
  run --server /policies

# Main Application
docker run -d --name openpolicy-app \
  -p 8000:8000 \
  --link openpolicy-db:postgres \
  --link openpolicy-redis:redis \
  --link openpolicy-opa:opa \
  -e DATABASE_URL=postgresql://openpolicy:changeme@postgres:5432/opencivicdata \
  -e REDIS_URL=redis://redis:6379/0 \
  -e OPA_URL=http://opa:8181 \
  -e OPENAI_API_KEY=your-key \
  ashishtandon9/openpolicyashback:latest
```

## 🔑 Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `DATABASE_URL` | PostgreSQL connection string | Yes | - |
| `REDIS_URL` | Redis connection string | Yes | - |
| `OPENAI_API_KEY` | OpenAI API key for AI features | No | - |
| `OPA_URL` | Open Policy Agent URL | Yes | http://opa:8181 |
| `POSTGRES_PASSWORD` | Database password | Yes | - |

## 📡 API Endpoints

The application exposes the following ports:
- **8000**: Main API (FastAPI)
- **8181**: OPA Policy Engine
- **5555**: Flower (Celery monitoring)

### Key API Endpoints:
- `/docs` - Interactive API documentation
- `/api/bills` - Legislative bills data
- `/api/representatives` - Government representatives
- `/api/jurisdictions` - Canadian jurisdictions
- `/api/parliamentary/*` - Parliamentary data endpoints (NEW!)
- `/graphql` - GraphQL endpoint

### New Parliamentary Endpoints:
- `/api/parliamentary/sessions` - Parliamentary sessions
- `/api/parliamentary/hansard` - Hansard debate records
- `/api/parliamentary/search/speeches` - Search parliamentary speeches
- `/api/parliamentary/committees/meetings` - Committee meetings
- `/api/parliamentary/validation/federal-bills` - Validate federal bills

## 🏗️ Architecture

```
┌─────────────────┐     ┌──────────────┐     ┌─────────────┐
│   FastAPI App   │────▶│  PostgreSQL  │     │    Redis    │
└────────┬────────┘     └──────────────┘     └──────┬──────┘
         │                                            │
         │              ┌──────────────┐              │
         └─────────────▶│     OPA      │◀─────────────┘
                        └──────────────┘
                               │
                        ┌──────▼───────┐
                        │Policy Validator│
                        └──────────────┘
```

## 📊 Data Coverage

- **Federal**: Parliament of Canada, all federal ministries
- **Provincial/Territorial**: All 10 provinces and 3 territories
- **Municipal**: 108 major cities and municipalities
- **Parliamentary**: Hansard debates, committee meetings, speeches (NEW!)

## 🛡️ Security Features

- **Policy-as-Code**: OPA-based access control
- **Rate Limiting**: Role-based (1K-50K requests/hour)
- **API Key Authentication**: Multiple user roles
- **Audit Logging**: Comprehensive request tracking

## 📈 Monitoring

Access Flower monitoring UI at `http://localhost:5555` to monitor:
- Celery task execution
- Scraping job status
- Background process health

## 🚦 Health Checks

All services include health checks:
```bash
# Main API health
curl http://localhost:8000/health

# OPA health
curl http://localhost:8181/health

# Policy integration health
curl http://localhost:8000/api/parliamentary/policy/health
```

## 📚 Documentation

- Full API docs: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- GraphQL playground: `http://localhost:8000/graphql`

## 🤝 Contributing

Visit our [GitHub repository](https://github.com/ashish-tandon/OpenPolicyAshBack) for:
- Source code
- Issue tracking
- Contributing guidelines
- Policy files

## 📄 License

MIT License - see LICENSE file for details

## 🏷️ Tags

- `latest` - Most recent stable version
- `20250109` - Initial release with parliamentary features

---

Made with ❤️ for Canadian civic engagement