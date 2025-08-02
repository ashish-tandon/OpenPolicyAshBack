#!/bin/bash

# Build and Push OpenPolicy Docker Images to Docker Hub
# Usage: ./build-and-push-docker.sh [docker-hub-username]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get Docker Hub username from argument or prompt
if [ -z "$1" ]; then
    echo -e "${YELLOW}Enter your Docker Hub username:${NC}"
    read DOCKER_HUB_USERNAME
else
    DOCKER_HUB_USERNAME=$1
fi

# Repository name
REPO_NAME="openpolicy-backend"
TAG="latest"

echo -e "${BLUE}Building and pushing OpenPolicy Docker images to Docker Hub...${NC}"
echo -e "${BLUE}Docker Hub Username: ${DOCKER_HUB_USERNAME}${NC}"

# Check if logged in to Docker Hub
echo -e "${YELLOW}Checking Docker Hub login...${NC}"
if ! docker info | grep -q "Username: ${DOCKER_HUB_USERNAME}"; then
    echo -e "${YELLOW}Please log in to Docker Hub:${NC}"
    docker login
fi

# Build the main application image
echo -e "${GREEN}Building main OpenPolicy application image...${NC}"
docker build -t ${DOCKER_HUB_USERNAME}/${REPO_NAME}:${TAG} \
    -t ${DOCKER_HUB_USERNAME}/${REPO_NAME}:$(date +%Y%m%d) \
    -f Dockerfile .

# Build the policy validator image
echo -e "${GREEN}Building Policy Validator image...${NC}"
docker build -t ${DOCKER_HUB_USERNAME}/${REPO_NAME}-policy-validator:${TAG} \
    -t ${DOCKER_HUB_USERNAME}/${REPO_NAME}-policy-validator:$(date +%Y%m%d) \
    -f Dockerfile.policy-validator .

# Build the Celery worker image (using same Dockerfile)
echo -e "${GREEN}Building Celery worker image...${NC}"
docker build -t ${DOCKER_HUB_USERNAME}/${REPO_NAME}-celery:${TAG} \
    -t ${DOCKER_HUB_USERNAME}/${REPO_NAME}-celery:$(date +%Y%m%d) \
    -f Dockerfile .

# Push main application image
echo -e "${BLUE}Pushing main application image...${NC}"
docker push ${DOCKER_HUB_USERNAME}/${REPO_NAME}:${TAG}
docker push ${DOCKER_HUB_USERNAME}/${REPO_NAME}:$(date +%Y%m%d)

# Push policy validator image
echo -e "${BLUE}Pushing policy validator image...${NC}"
docker push ${DOCKER_HUB_USERNAME}/${REPO_NAME}-policy-validator:${TAG}
docker push ${DOCKER_HUB_USERNAME}/${REPO_NAME}-policy-validator:$(date +%Y%m%d)

# Push Celery worker image
echo -e "${BLUE}Pushing Celery worker image...${NC}"
docker push ${DOCKER_HUB_USERNAME}/${REPO_NAME}-celery:${TAG}
docker push ${DOCKER_HUB_USERNAME}/${REPO_NAME}-celery:$(date +%Y%m%d)

# Create and push a docker-compose file that uses the pushed images
echo -e "${GREEN}Creating production docker-compose file...${NC}"
cat > docker-compose.prod.yml << EOF
version: '3.8'

services:
  postgres:
    image: postgres:13
    environment:
      POSTGRES_DB: opencivicdata
      POSTGRES_USER: openpolicy
      POSTGRES_PASSWORD: \${POSTGRES_PASSWORD:-openpolicy123}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U openpolicy"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5

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

  app:
    image: ${DOCKER_HUB_USERNAME}/${REPO_NAME}:${TAG}
    depends_on:
      - postgres
      - redis
      - opa
    environment:
      - DATABASE_URL=postgresql://openpolicy:\${POSTGRES_PASSWORD:-openpolicy123}@postgres:5432/opencivicdata
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
      - OPENAI_API_KEY=\${OPENAI_API_KEY}
      - OPA_URL=http://opa:8181
    ports:
      - "8000:8000"
    volumes:
      - ./policies:/app/policies:ro
      - ./data:/app/data

  celery-worker:
    image: ${DOCKER_HUB_USERNAME}/${REPO_NAME}-celery:${TAG}
    command: celery -A src.scheduler.celery_app worker --loglevel=info
    depends_on:
      - postgres
      - redis
    environment:
      - DATABASE_URL=postgresql://openpolicy:\${POSTGRES_PASSWORD:-openpolicy123}@postgres:5432/opencivicdata
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
      - OPENAI_API_KEY=\${OPENAI_API_KEY}

  celery-beat:
    image: ${DOCKER_HUB_USERNAME}/${REPO_NAME}-celery:${TAG}
    command: celery -A src.scheduler.celery_app beat --loglevel=info
    depends_on:
      - postgres
      - redis
    environment:
      - DATABASE_URL=postgresql://openpolicy:\${POSTGRES_PASSWORD:-openpolicy123}@postgres:5432/opencivicdata
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0

  policy-validator:
    image: ${DOCKER_HUB_USERNAME}/${REPO_NAME}-policy-validator:${TAG}
    depends_on:
      - opa
      - postgres
      - redis
    environment:
      - OPA_URL=http://opa:8181
      - DATABASE_URL=postgresql://openpolicy:\${POSTGRES_PASSWORD:-openpolicy123}@postgres:5432/opencivicdata
      - REDIS_URL=redis://redis:6379/0
      - PYTHONPATH=/app
    volumes:
      - ./policies:/policies:ro

  flower:
    image: mher/flower:2.0
    ports:
      - "5555:5555"
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
      - FLOWER_PORT=5555
    depends_on:
      - redis

volumes:
  postgres_data:
  redis_data:

networks:
  default:
    name: openpolicy-network
EOF

echo -e "${GREEN}✅ Docker images built and pushed successfully!${NC}"
echo
echo -e "${YELLOW}Published Docker images:${NC}"
echo -e "  - ${BLUE}${DOCKER_HUB_USERNAME}/${REPO_NAME}:${TAG}${NC}"
echo -e "  - ${BLUE}${DOCKER_HUB_USERNAME}/${REPO_NAME}-policy-validator:${TAG}${NC}"
echo -e "  - ${BLUE}${DOCKER_HUB_USERNAME}/${REPO_NAME}-celery:${TAG}${NC}"
echo
echo -e "${YELLOW}To run the production stack:${NC}"
echo -e "  1. Copy ${GREEN}docker-compose.prod.yml${NC} to your production server"
echo -e "  2. Copy the ${GREEN}policies/${NC} directory to your production server"
echo -e "  3. Create a ${GREEN}.env${NC} file with:"
echo -e "     ${BLUE}POSTGRES_PASSWORD=<secure-password>${NC}"
echo -e "     ${BLUE}OPENAI_API_KEY=<your-api-key>${NC}"
echo -e "  4. Run: ${GREEN}docker-compose -f docker-compose.prod.yml up -d${NC}"
echo
echo -e "${YELLOW}To pull images on another machine:${NC}"
echo -e "  ${GREEN}docker pull ${DOCKER_HUB_USERNAME}/${REPO_NAME}:${TAG}${NC}"
echo -e "  ${GREEN}docker pull ${DOCKER_HUB_USERNAME}/${REPO_NAME}-policy-validator:${TAG}${NC}"
echo -e "  ${GREEN}docker pull ${DOCKER_HUB_USERNAME}/${REPO_NAME}-celery:${TAG}${NC}"