# OpenPolicy Backend - Canadian Civic Data Platform

[![Docker Pulls](https://img.shields.io/docker/pulls/yourusername/openpolicy-backend.svg)](https://hub.docker.com/r/yourusername/openpolicy-backend)
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
docker pull yourusername/openpolicy-backend:latest
```

### Policy Validator Service
```bash
docker pull yourusername/openpolicy-backend-policy-validator:latest
```

### Celery Worker
```bash
docker pull yourusername/openpolicy-backend-celery:latest
```

## 🔧 Quick Start

### Using Docker Compose (Recommended)

1. **Create docker-compose.yml**:
```yaml
version: '3.8'

services:
  postgres:
    image: postgres:13
    environment:
      POSTGRES_DB: opencivicdata
      POSTGRES_USER: openpolicy
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-changeme}
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

  opa:
    image: openpolicyagent/opa:latest-debug
    ports:
      - "8181:8181"
    command:
      - "run"
      - "--server"
      - "/policies"
    volumes:
      - ./policies:/policies:ro

  app:
    image: yourusername/openpolicy-backend:latest
    depends_on:
      - postgres
      - redis
      - opa
    environment:
      - DATABASE_URL=postgresql://openpolicy:${POSTGRES_PASSWORD:-changeme}@postgres:5432/opencivicdata
      - REDIS_URL=redis://redis:6379/0
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - OPA_URL=http://opa:8181
    ports:
      - "8000:8000"
    volumes:
      - ./policies:/app/policies:ro

  celery-worker:
    image: yourusername/openpolicy-backend-celery:latest
    command: celery -A src.scheduler.celery_app worker --loglevel=info
    depends_on:
      - postgres
      - redis
    environment:
      - DATABASE_URL=postgresql://openpolicy:${POSTGRES_PASSWORD:-changeme}@postgres:5432/opencivicdata
      - REDIS_URL=redis://redis:6379/0
      - OPENAI_API_KEY=${OPENAI_API_KEY}

  policy-validator:
    image: yourusername/openpolicy-backend-policy-validator:latest
    depends_on:
      - opa
    environment:
      - OPA_URL=http://opa:8181
      - DATABASE_URL=postgresql://openpolicy:${POSTGRES_PASSWORD:-changeme}@postgres:5432/opencivicdata

volumes:
  postgres_data:
  redis_data:
```

2. **Create .env file**:
```env
POSTGRES_PASSWORD=your-secure-password
OPENAI_API_KEY=your-openai-api-key
```

3. **Create policies directory** with OPA policies (download from repository)

4. **Start the stack**:
```bash
docker-compose up -d
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
  yourusername/openpolicy-backend:latest
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
- `/api/parliamentary/*` - Parliamentary data endpoints
- `/graphql` - GraphQL endpoint

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

- **Federal**: Parliament of Canada, all ministries
- **Provincial/Territorial**: All 10 provinces and 3 territories
- **Municipal**: 108 major cities and municipalities
- **Parliamentary**: Hansard debates, committee meetings, speeches

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

Visit our [GitHub repository](https://github.com/yourusername/openpolicy-backend) for:
- Source code
- Issue tracking
- Contributing guidelines
- Policy files

## 📄 License

MIT License - see LICENSE file for details

## 🏷️ Tags

- `latest` - Most recent stable version
- `YYYYMMDD` - Date-tagged versions for specific builds

---

Made with ❤️ for Canadian civic engagement