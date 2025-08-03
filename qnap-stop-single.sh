#!/bin/bash
echo "⏹️ Stopping OpenPolicy All-in-One..."
cd /share/Container/openpolicy
docker-compose down
echo "✅ Container stopped!"
