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
