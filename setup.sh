#!/bin/bash

# AgentSudo Local Development Setup Script
# This script sets up the local development environment for AgentSudo

set -e

echo "🛡️  AgentSudo Local Development Setup"
echo "======================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check prerequisites
check_prerequisites() {
    echo "📋 Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}❌ Docker is not installed. Please install Docker first.${NC}"
        echo "   Visit: https://docs.docker.com/get-docker/"
        exit 1
    fi
    echo -e "${GREEN}✓${NC} Docker installed"
    
    # Check Docker Compose
    if ! docker compose version &> /dev/null; then
        echo -e "${RED}❌ Docker Compose is not installed. Please install Docker Compose first.${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓${NC} Docker Compose installed"
    
    # Check Node.js
    if ! command -v node &> /dev/null; then
        echo -e "${RED}❌ Node.js is not installed. Please install Node.js 18+ first.${NC}"
        echo "   Visit: https://nodejs.org/"
        exit 1
    fi
    NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
    if [ "$NODE_VERSION" -lt 18 ]; then
        echo -e "${RED}❌ Node.js version must be 18 or higher. Current: $(node -v)${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓${NC} Node.js $(node -v) installed"
    
    echo ""
}

# Setup environment files
setup_env() {
    echo "📝 Setting up environment files..."
    
    # Root .env
    if [ ! -f .env ]; then
        cp .env.example .env
        echo -e "${GREEN}✓${NC} Created .env from .env.example"
    else
        echo -e "${YELLOW}⚠${NC} .env already exists, skipping"
    fi
    
    # Dashboard .env.local
    if [ ! -f dashboard/.env.local ]; then
        cat > dashboard/.env.local << 'EOF'
# Local development environment
NEXT_PUBLIC_SUPABASE_URL=http://localhost:54321
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJleHAiOjE5ODM4MTI5OTZ9.CRXP1A7WOeoJeXxjNni43kdQwgnWNReilDMblYTn_I0
EOF
        echo -e "${GREEN}✓${NC} Created dashboard/.env.local"
    else
        echo -e "${YELLOW}⚠${NC} dashboard/.env.local already exists, skipping"
    fi
    
    echo ""
}

# Install dependencies
install_deps() {
    echo "📦 Installing dependencies..."
    
    cd dashboard
    npm install
    cd ..
    
    echo -e "${GREEN}✓${NC} Dashboard dependencies installed"
    echo ""
}

# Start services
start_services() {
    echo "🚀 Starting services..."
    echo ""
    echo "Option 1: Use Supabase CLI (recommended for development)"
    echo "   cd dashboard && npx supabase start"
    echo ""
    echo "Option 2: Use Docker Compose"
    echo "   docker compose up -d"
    echo ""
    echo "Then start the dashboard:"
    echo "   cd dashboard && npm run dev"
    echo ""
}

# Main
main() {
    check_prerequisites
    setup_env
    install_deps
    
    echo "======================================"
    echo -e "${GREEN}✅ Setup complete!${NC}"
    echo "======================================"
    echo ""
    start_services
    echo ""
    echo "📚 Documentation: http://localhost:3000/docs"
    echo "🎮 Dashboard: http://localhost:3000/dashboard"
    echo ""
    echo "For more information, see SELF_HOSTING.md"
}

main "$@"
