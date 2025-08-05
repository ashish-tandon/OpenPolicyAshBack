#!/bin/bash

# Install Docker on QNAP NAS
# This script installs Docker and Docker Compose on QNAP

set -e

# Configuration
QNAP_HOST="192.168.2.152"
QNAP_PORT="22"
QNAP_USER="ashish101"
QNAP_PASS="Pergola@41"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
}

# Function to create Docker installation script
create_docker_install_script() {
    log "Creating Docker installation script..."
    
    cat > qnap-install-docker.sh << 'EOF'
#!/bin/bash
set -e

echo "🐳 Installing Docker on QNAP..."

# Check if we're on QNAP
if [ ! -f /etc/config/qpkg.conf ]; then
    echo "❌ This script is designed for QNAP NAS only"
    exit 1
fi

# Check if Docker is already installed
if command -v docker &> /dev/null; then
    echo "✅ Docker is already installed"
    docker --version
else
    echo "📦 Installing Docker..."
    
    # Install Docker using QNAP's package manager
    if command -v qpkg &> /dev/null; then
        echo "Installing Docker via QPKG..."
        # Try to install Docker from QNAP App Center
        echo "Please install Docker from the QNAP App Center manually:"
        echo "1. Open QNAP App Center"
        echo "2. Search for 'Docker'"
        echo "3. Install 'Container Station' or 'Docker'"
        echo "4. Wait for installation to complete"
    else
        echo "❌ QPKG not available. Please install Docker manually from QNAP App Center"
        exit 1
    fi
fi

# Check if docker-compose is available
if command -v docker-compose &> /dev/null; then
    echo "✅ Docker Compose is already installed"
    docker-compose --version
else
    echo "📦 Installing Docker Compose..."
    
    # Install docker-compose
    if command -v curl &> /dev/null; then
        echo "Downloading Docker Compose..."
        curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        chmod +x /usr/local/bin/docker-compose
        
        # Create symlink if needed
        if [ ! -f /usr/bin/docker-compose ]; then
            ln -sf /usr/local/bin/docker-compose /usr/bin/docker-compose
        fi
        
        echo "✅ Docker Compose installed"
        docker-compose --version
    else
        echo "❌ curl not available. Please install Docker Compose manually"
        exit 1
    fi
fi

# Test Docker installation
echo "🧪 Testing Docker installation..."
if docker --version && docker-compose --version; then
    echo "✅ Docker and Docker Compose are working correctly"
    
    # Test Docker daemon
    if docker info >/dev/null 2>&1; then
        echo "✅ Docker daemon is running"
    else
        echo "⚠️ Docker daemon is not running. Please start it from QNAP App Center"
    fi
else
    echo "❌ Docker installation test failed"
    exit 1
fi

echo "🎉 Docker installation completed successfully!"
EOF

    chmod +x qnap-install-docker.sh
    success "Docker installation script created"
}

# Function to install Docker on QNAP
install_docker_on_qnap() {
    log "Installing Docker on QNAP..."
    
    # Create installation script
    create_docker_install_script
    
    # Copy script to QNAP
    log "Copying Docker installation script to QNAP..."
    if sshpass -p "${QNAP_PASS}" scp -o ConnectTimeout=10 -P ${QNAP_PORT} qnap-install-docker.sh ${QNAP_USER}@${QNAP_HOST}:/tmp/; then
        success "Docker installation script copied to QNAP"
    else
        error "Failed to copy Docker installation script to QNAP"
        exit 1
    fi
    
    # Execute installation on QNAP
    log "Executing Docker installation on QNAP..."
    if sshpass -p "${QNAP_PASS}" ssh -o ConnectTimeout=10 -p ${QNAP_PORT} ${QNAP_USER}@${QNAP_HOST} "bash /tmp/qnap-install-docker.sh"; then
        success "Docker installation completed on QNAP"
    else
        error "Failed to install Docker on QNAP"
        exit 1
    fi
    
    # Clean up local script
    rm qnap-install-docker.sh
}

# Function to check Docker installation
check_docker_installation() {
    log "Checking Docker installation on QNAP..."
    
    if sshpass -p "${QNAP_PASS}" ssh -o ConnectTimeout=10 -p ${QNAP_PORT} ${QNAP_USER}@${QNAP_HOST} "docker --version && docker-compose --version"; then
        success "Docker and Docker Compose are installed and working"
        return 0
    else
        error "Docker installation check failed"
        return 1
    fi
}

# Function to show installation instructions
show_manual_instructions() {
    log "Manual Docker Installation Instructions:"
    echo ""
    echo "🔧 If automatic installation fails, please install Docker manually:"
    echo ""
    echo "1. 📱 Open QNAP App Center in your web browser:"
    echo "   http://${QNAP_HOST}:8080"
    echo ""
    echo "2. 🔍 Search for 'Container Station' or 'Docker'"
    echo ""
    echo "3. 📦 Install 'Container Station' (includes Docker)"
    echo ""
    echo "4. ⏳ Wait for installation to complete"
    echo ""
    echo "5. 🚀 Start Container Station"
    echo ""
    echo "6. ✅ Verify Docker is working by running:"
    echo "   docker --version"
    echo ""
    echo "7. 🔄 Run this script again after manual installation"
}

# Main installation function
main() {
    log "🐳 Starting Docker Installation on QNAP (IP: ${QNAP_HOST})"
    log "Username: ${QNAP_USER}"
    
    # Try automatic installation
    if install_docker_on_qnap; then
        # Check if installation was successful
        if check_docker_installation; then
            success "Docker installation completed successfully!"
            log "You can now run the deployment script: ./deploy-qnap-final.sh"
        else
            warning "Docker installation may not be complete"
            show_manual_instructions
        fi
    else
        error "Automatic Docker installation failed"
        show_manual_instructions
    fi
}

# Run main function
main "$@" 