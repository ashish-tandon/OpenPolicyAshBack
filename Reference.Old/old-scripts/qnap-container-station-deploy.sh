#!/bin/bash

# QNAP Container Station Full Deployment for OpenPolicy
echo "🚀 Creating QNAP Container Station Deployment Package..."

QNAP_HOST="192.168.2.152"
QNAP_USER="ashish101"
QNAP_PATH="/share/Container/openpolicy"

# Create a comprehensive docker-compose file for Container Station
echo "📝 Creating Container Station configuration..."

cat > qnap-full-docker-compose.yml << 'EOF'
version: '3.8'

services:
  # PostgreSQL Database
  postgres:
    image: postgres:17
    container_name: openpolicy_postgres
    environment:
      POSTGRES_DB: opencivicdata
      POSTGRES_USER: openpolicy
      POSTGRES_PASSWORD: openpolicy123
      POSTGRES_HOST_AUTH_METHOD: trust
    volumes:
      - /share/Container/openpolicy/postgres_data:/var/lib/postgresql/data
      - /share/Container/openpolicy/init_db.sql:/docker-entrypoint-initdb.d/init_db.sql
    ports:
      - "5432:5432"
    restart: unless-stopped
    networks:
      - openpolicy_network

  # Redis for Celery
  redis:
    image: redis:7-alpine
    container_name: openpolicy_redis
    ports:
      - "6379:6379"
    volumes:
      - /share/Container/openpolicy/redis_data:/data
    restart: unless-stopped
    networks:
      - openpolicy_network

  # OpenPolicy API
  api:
    image: ashishtandon9/openpolicyashback:latest
    container_name: openpolicy_api
    environment:
      DB_HOST: postgres
      DB_PORT: 5432
      DB_NAME: opencivicdata
      DB_USER: openpolicy
      DB_PASSWORD: openpolicy123
      REDIS_URL: redis://redis:6379/0
      CORS_ORIGINS: "http://192.168.2.152:3000,http://localhost:3000,http://192.168.2.152:8080"
    ports:
      - "8000:8000"
    depends_on:
      - postgres
      - redis
    volumes:
      - /share/Container/openpolicy/regions_report.json:/app/regions_report.json:ro
      - /share/Container/openpolicy/scrapers:/app/scrapers:ro
    restart: unless-stopped
    networks:
      - openpolicy_network

  # Celery Worker
  celery_worker:
    image: ashishtandon9/openpolicyashback:latest
    container_name: openpolicy_worker
    environment:
      DB_HOST: postgres
      DB_PORT: 5432
      DB_NAME: opencivicdata
      DB_USER: openpolicy
      DB_PASSWORD: openpolicy123
      CELERY_BROKER_URL: redis://redis:6379/0
      CELERY_RESULT_BACKEND: redis://redis:6379/0
    depends_on:
      - postgres
      - redis
    volumes:
      - /share/Container/openpolicy/regions_report.json:/app/regions_report.json:ro
      - /share/Container/openpolicy/scrapers:/app/scrapers:ro
    restart: unless-stopped
    command: ["celery", "-A", "src.scheduler.tasks", "worker", "--loglevel=info"]
    networks:
      - openpolicy_network

  # Celery Beat (Scheduler)
  celery_beat:
    image: ashishtandon9/openpolicyashback:latest
    container_name: openpolicy_beat
    environment:
      DB_HOST: postgres
      DB_PORT: 5432
      DB_NAME: opencivicdata
      DB_USER: openpolicy
      DB_PASSWORD: openpolicy123
      CELERY_BROKER_URL: redis://redis:6379/0
      CELERY_RESULT_BACKEND: redis://redis:6379/0
    depends_on:
      - postgres
      - redis
    volumes:
      - /share/Container/openpolicy/regions_report.json:/app/regions_report.json:ro
      - /share/Container/openpolicy/scrapers:/app/scrapers:ro
    restart: unless-stopped
    command: ["celery", "-A", "src.scheduler.tasks", "beat", "--loglevel=info"]
    networks:
      - openpolicy_network

  # Celery Flower (Monitoring)
  flower:
    image: mher/flower:2.0
    container_name: openpolicy_flower
    ports:
      - "5555:5555"
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
      - FLOWER_PORT=5555
    depends_on:
      - redis
    restart: unless-stopped
    networks:
      - openpolicy_network

  # OpenPolicy Dashboard (Frontend)
  dashboard:
    image: nginx:alpine
    container_name: openpolicy_dashboard
    ports:
      - "3000:80"
    volumes:
      - /share/Container/openpolicy/dashboard:/usr/share/nginx/html:ro
      - /share/Container/openpolicy/nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - api
    restart: unless-stopped
    networks:
      - openpolicy_network

networks:
  openpolicy_network:
    driver: bridge
EOF

# Create Nginx configuration for the dashboard
cat > qnap-nginx.conf << 'EOF'
events {
    worker_connections 1024;
}

http {
    include       /etc/nginx/mime.types;
    default_type  application/octet-stream;

    server {
        listen 80;
        server_name localhost;
        root /usr/share/nginx/html;
        index index.html;

        # API proxy
        location /api/ {
            proxy_pass http://api:8000/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Health check
        location /health {
            proxy_pass http://api:8000/health;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Dashboard
        location / {
            try_files $uri $uri/ /index.html;
        }

        # CORS headers
        add_header Access-Control-Allow-Origin *;
        add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS";
        add_header Access-Control-Allow-Headers "Content-Type, Authorization";
    }
}
EOF

# Create a build script for the dashboard
cat > build-dashboard.sh << 'EOF'
#!/bin/bash

echo "🏗️ Building OpenPolicy Dashboard..."

# Create dashboard directory
mkdir -p /share/Container/openpolicy/dashboard

# Create a simple dashboard HTML
cat > /share/Container/openpolicy/dashboard/index.html << 'HTML_EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OpenPolicy Dashboard</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/axios/dist/axios.min.js"></script>
</head>
<body class="bg-gray-50">
    <div class="min-h-screen">
        <!-- Header -->
        <header class="bg-white shadow">
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div class="flex justify-between h-16">
                    <div class="flex items-center">
                        <h1 class="text-xl font-semibold text-gray-900">OpenPolicy Dashboard</h1>
                    </div>
                    <div class="flex items-center space-x-4">
                        <div id="health-status" class="flex items-center">
                            <div class="w-2 h-2 bg-gray-400 rounded-full mr-2"></div>
                            <span class="text-sm text-gray-600">Checking...</span>
                        </div>
                    </div>
                </div>
            </div>
        </header>

        <!-- Main Content -->
        <main class="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
            <!-- Stats Cards -->
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                <div class="bg-white overflow-hidden shadow rounded-lg">
                    <div class="p-5">
                        <div class="flex items-center">
                            <div class="flex-shrink-0">
                                <div class="w-8 h-8 bg-blue-500 rounded-md flex items-center justify-center">
                                    <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"></path>
                                    </svg>
                                </div>
                            </div>
                            <div class="ml-5 w-0 flex-1">
                                <dl>
                                    <dt class="text-sm font-medium text-gray-500 truncate">Jurisdictions</dt>
                                    <dd id="jurisdictions-count" class="text-lg font-medium text-gray-900">-</dd>
                                </dl>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="bg-white overflow-hidden shadow rounded-lg">
                    <div class="p-5">
                        <div class="flex items-center">
                            <div class="flex-shrink-0">
                                <div class="w-8 h-8 bg-green-500 rounded-md flex items-center justify-center">
                                    <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"></path>
                                    </svg>
                                </div>
                            </div>
                            <div class="ml-5 w-0 flex-1">
                                <dl>
                                    <dt class="text-sm font-medium text-gray-500 truncate">Representatives</dt>
                                    <dd id="representatives-count" class="text-lg font-medium text-gray-900">-</dd>
                                </dl>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="bg-white overflow-hidden shadow rounded-lg">
                    <div class="p-5">
                        <div class="flex items-center">
                            <div class="flex-shrink-0">
                                <div class="w-8 h-8 bg-purple-500 rounded-md flex items-center justify-center">
                                    <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                                    </svg>
                                </div>
                            </div>
                            <div class="ml-5 w-0 flex-1">
                                <dl>
                                    <dt class="text-sm font-medium text-gray-500 truncate">Bills</dt>
                                    <dd id="bills-count" class="text-lg font-medium text-gray-900">-</dd>
                                </dl>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="bg-white overflow-hidden shadow rounded-lg">
                    <div class="p-5">
                        <div class="flex items-center">
                            <div class="flex-shrink-0">
                                <div class="w-8 h-8 bg-yellow-500 rounded-md flex items-center justify-center">
                                    <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path>
                                    </svg>
                                </div>
                            </div>
                            <div class="ml-5 w-0 flex-1">
                                <dl>
                                    <dt class="text-sm font-medium text-gray-500 truncate">Events</dt>
                                    <dd id="events-count" class="text-lg font-medium text-gray-900">-</dd>
                                </dl>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Data Tables -->
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <!-- Jurisdictions -->
                <div class="bg-white shadow rounded-lg">
                    <div class="px-4 py-5 sm:p-6">
                        <h3 class="text-lg leading-6 font-medium text-gray-900 mb-4">Jurisdictions</h3>
                        <div id="jurisdictions-list" class="space-y-2">
                            <div class="text-gray-500 text-sm">Loading...</div>
                        </div>
                    </div>
                </div>

                <!-- Representatives -->
                <div class="bg-white shadow rounded-lg">
                    <div class="px-4 py-5 sm:p-6">
                        <h3 class="text-lg leading-6 font-medium text-gray-900 mb-4">Recent Representatives</h3>
                        <div id="representatives-list" class="space-y-2">
                            <div class="text-gray-500 text-sm">Loading...</div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Actions -->
            <div class="mt-8 bg-white shadow rounded-lg">
                <div class="px-4 py-5 sm:p-6">
                    <h3 class="text-lg leading-6 font-medium text-gray-900 mb-4">System Actions</h3>
                    <div class="flex space-x-4">
                        <button onclick="startScraping('federal')" class="bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-md">
                            Start Federal Scraping
                        </button>
                        <button onclick="startScraping('provincial')" class="bg-green-600 hover:bg-green-700 text-white font-medium py-2 px-4 rounded-md">
                            Start Provincial Scraping
                        </button>
                        <button onclick="startScraping('municipal')" class="bg-purple-600 hover:bg-purple-700 text-white font-medium py-2 px-4 rounded-md">
                            Start Municipal Scraping
                        </button>
                    </div>
                    <div id="scraping-status" class="mt-4 text-sm text-gray-600"></div>
                </div>
            </div>
        </main>
    </div>

    <script>
        const API_BASE = 'http://192.168.2.152:8000';
        
        // Check health status
        async function checkHealth() {
            try {
                const response = await axios.get(`${API_BASE}/health`);
                document.getElementById('health-status').innerHTML = `
                    <div class="w-2 h-2 bg-green-500 rounded-full mr-2"></div>
                    <span class="text-sm text-green-600">Healthy</span>
                `;
                return true;
            } catch (error) {
                document.getElementById('health-status').innerHTML = `
                    <div class="w-2 h-2 bg-red-500 rounded-full mr-2"></div>
                    <span class="text-sm text-red-600">Unhealthy</span>
                `;
                return false;
            }
        }

        // Load stats
        async function loadStats() {
            try {
                const response = await axios.get(`${API_BASE}/stats`);
                const stats = response.data;
                
                document.getElementById('jurisdictions-count').textContent = stats.total_jurisdictions || 0;
                document.getElementById('representatives-count').textContent = stats.total_representatives || 0;
                document.getElementById('bills-count').textContent = stats.total_bills || 0;
                document.getElementById('events-count').textContent = stats.total_events || 0;
            } catch (error) {
                console.error('Error loading stats:', error);
            }
        }

        // Load jurisdictions
        async function loadJurisdictions() {
            try {
                const response = await axios.get(`${API_BASE}/jurisdictions?limit=5`);
                const jurisdictions = response.data;
                
                const html = jurisdictions.map(j => `
                    <div class="flex justify-between items-center py-2 border-b border-gray-100">
                        <div>
                            <div class="font-medium text-gray-900">${j.name}</div>
                            <div class="text-sm text-gray-500">${j.jurisdiction_type}</div>
                        </div>
                        <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                            ${j.jurisdiction_type}
                        </span>
                    </div>
                `).join('');
                
                document.getElementById('jurisdictions-list').innerHTML = html || '<div class="text-gray-500 text-sm">No jurisdictions found</div>';
            } catch (error) {
                document.getElementById('jurisdictions-list').innerHTML = '<div class="text-red-500 text-sm">Error loading jurisdictions</div>';
            }
        }

        // Load representatives
        async function loadRepresentatives() {
            try {
                const response = await axios.get(`${API_BASE}/representatives?limit=5`);
                const representatives = response.data;
                
                const html = representatives.map(r => `
                    <div class="flex justify-between items-center py-2 border-b border-gray-100">
                        <div>
                            <div class="font-medium text-gray-900">${r.name}</div>
                            <div class="text-sm text-gray-500">${r.role} • ${r.party || 'No party'}</div>
                        </div>
                        <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                            ${r.role}
                        </span>
                    </div>
                `).join('');
                
                document.getElementById('representatives-list').innerHTML = html || '<div class="text-gray-500 text-sm">No representatives found</div>';
            } catch (error) {
                document.getElementById('representatives-list').innerHTML = '<div class="text-red-500 text-sm">Error loading representatives</div>';
            }
        }

        // Start scraping
        async function startScraping(type) {
            const statusDiv = document.getElementById('scraping-status');
            statusDiv.innerHTML = `<div class="text-blue-600">Starting ${type} scraping...</div>`;
            
            try {
                const response = await axios.post(`${API_BASE}/scheduling/schedule`, {
                    task_type: type
                });
                
                statusDiv.innerHTML = `<div class="text-green-600">${type} scraping started successfully! Task ID: ${response.data.task_id}</div>`;
                
                // Refresh data after a delay
                setTimeout(() => {
                    loadStats();
                    loadJurisdictions();
                    loadRepresentatives();
                }, 5000);
            } catch (error) {
                statusDiv.innerHTML = `<div class="text-red-600">Error starting ${type} scraping: ${error.message}</div>`;
            }
        }

        // Initialize dashboard
        async function initDashboard() {
            await checkHealth();
            await loadStats();
            await loadJurisdictions();
            await loadRepresentatives();
        }

        // Load dashboard on page load
        document.addEventListener('DOMContentLoaded', initDashboard);

        // Refresh data every 30 seconds
        setInterval(() => {
            loadStats();
        }, 30000);
    </script>
</body>
</html>
HTML_EOF

echo "✅ Dashboard built successfully!"
echo "📁 Dashboard location: /share/Container/openpolicy/dashboard/"
EOF

chmod +x build-dashboard.sh

# Create a comprehensive startup script
cat > qnap-full-start.sh << 'EOF'
#!/bin/bash

echo "🚀 Starting Complete OpenPolicy System on QNAP..."

# Navigate to deployment directory
cd /share/Container/openpolicy

# Build the dashboard
echo "🏗️ Building dashboard..."
./build-dashboard.sh

# Create data directories
echo "📁 Creating data directories..."
mkdir -p postgres_data redis_data

# Start the system using Container Station
echo "📋 Next Steps:"
echo ""
echo "1. Open QNAP Container Station in your web browser:"
echo "   http://192.168.2.152:8080"
echo ""
echo "2. Import the docker-compose file:"
echo "   - Click 'Create' → 'Application'"
echo "   - Click 'Import from docker-compose.yml'"
echo "   - Upload: /share/Container/openpolicy/qnap-full-docker-compose.yml"
echo "   - Click 'Create'"
echo ""
echo "3. Start all containers in this order:"
echo "   - postgres (first)"
echo "   - redis"
echo "   - api"
echo "   - celery_worker"
echo "   - celery_beat"
echo "   - flower"
echo "   - dashboard (last)"
echo ""
echo "4. Test the system:"
echo "   - API: http://192.168.2.152:8000/health"
echo "   - Dashboard: http://192.168.2.152:3000"
echo "   - Flower Monitor: http://192.168.2.152:5555"
echo ""
echo "✅ Setup complete! Follow the steps above to start the system."
EOF

chmod +x qnap-full-start.sh

# Transfer all files to QNAP
echo "📤 Transferring deployment files to QNAP..."

# Create directories
ssh $QNAP_USER@$QNAP_HOST "mkdir -p $QNAP_PATH"

# Transfer files
scp qnap-full-docker-compose.yml $QNAP_USER@$QNAP_HOST:$QNAP_PATH/docker-compose.yml
scp qnap-nginx.conf $QNAP_USER@$QNAP_HOST:$QNAP_PATH/nginx.conf
scp build-dashboard.sh $QNAP_USER@$QNAP_HOST:$QNAP_PATH/
scp qnap-full-start.sh $QNAP_USER@$QNAP_HOST:$QNAP_PATH/

# Make scripts executable
ssh $QNAP_USER@$QNAP_HOST "chmod +x $QNAP_PATH/build-dashboard.sh $QNAP_PATH/qnap-full-start.sh"

echo "✅ QNAP Container Station deployment package ready!"
echo ""
echo "🚀 To deploy:"
echo "1. Run: ssh ashish101@192.168.2.152 'cd /share/Container/openpolicy && ./qnap-full-start.sh'"
echo "2. Follow the Container Station instructions"
echo ""
echo "🌐 After deployment:"
echo "   - Dashboard: http://192.168.2.152:3000"
echo "   - API: http://192.168.2.152:8000"
echo "   - Flower Monitor: http://192.168.2.152:5555" 