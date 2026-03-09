#!/bin/bash
# Quick start script for APCAN Voice AI development

set -e  # Exit on error

echo "🚀 Starting APCAN Voice AI Development Environment..."
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  No .env file found. Creating from .env.example..."
    cp .env.example .env
    echo "✅ Created .env file. Please edit it with your credentials!"
    echo ""
    echo "Required:"
    echo "  1. DATABASE_URL (get from https://neon.tech)"
    echo "  2. GOOGLE_API_KEY (get from https://aistudio.google.com/app/apikey)"
    echo "  3. SECRET_KEY (run: openssl rand -hex 32)"
    echo ""
    echo "After updating .env, run this script again."
    exit 1
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop and try again."
    exit 1
fi

echo "🐳 Starting Docker services (PostgreSQL, Redis, Backend)..."
docker-compose up -d

echo ""
echo "⏳ Waiting for services to be healthy..."
sleep 5

# Check if services are healthy
if docker-compose ps | grep -q "unhealthy"; then
    echo "❌ Some services are unhealthy. Check logs with: docker-compose logs"
    exit 1
fi

echo ""
echo "✅ All services started successfully!"
echo ""
echo "📍 Service URLs:"
echo "  • Backend API:    http://localhost:8000"
echo "  • API Docs:       http://localhost:8000/api/docs"
echo "  • Health Check:   http://localhost:8000/api/v1/health"
echo "  • PostgreSQL:     localhost:5432"
echo "  • Redis:          localhost:6379"
echo ""
echo "🔧 Useful commands:"
echo "  • View logs:      docker-compose logs -f"
echo "  • Stop services:  docker-compose down"
echo "  • Restart:        docker-compose restart"
echo "  • Run tests:      docker-compose exec backend pytest"
echo ""
echo "📖 Next steps:"
echo "  1. Visit http://localhost:8000/api/docs"
echo "  2. Test signup: POST /api/v1/auth/signup"
echo "  3. Check docs/phase-1-implementation.md for API examples"
echo ""
