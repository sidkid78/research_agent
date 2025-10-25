#!/bin/bash

# Research Agent - Docker Quick Start Script

set -e

echo "🔬 Research Agent - Docker Deployment"
echo "======================================"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  No .env file found!"
    echo "📝 Creating .env from template..."
    cp env.example .env
    echo ""
    echo "⚠️  IMPORTANT: Please edit .env and add your API keys:"
    echo "   - GEMINI_API_KEY"
    echo "   - PUBMED_EMAIL"
    echo ""
    read -p "Press Enter after you've updated .env file..."
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if Docker Compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install it and try again."
    exit 1
fi

echo "🏗️  Building Docker images..."
docker-compose build

echo ""
echo "🚀 Starting services..."
docker-compose up -d

echo ""
echo "⏳ Waiting for services to be healthy..."
sleep 5

# Check health
BACKEND_HEALTH=$(docker inspect --format='{{.State.Health.Status}}' research-agent-backend 2>/dev/null || echo "starting")
FRONTEND_HEALTH=$(docker inspect --format='{{.State.Health.Status}}' research-agent-frontend 2>/dev/null || echo "starting")

echo ""
echo "📊 Service Status:"
echo "   Backend:  $BACKEND_HEALTH"
echo "   Frontend: $FRONTEND_HEALTH"

echo ""
echo "✅ Deployment complete!"
echo ""
echo "🌐 Access the application:"
echo "   Frontend:  http://localhost:3000"
echo "   Backend:   http://localhost:8000"
echo "   API Docs:  http://localhost:8000/docs"
echo ""
echo "📝 Useful commands:"
echo "   View logs:     docker-compose logs -f"
echo "   Stop services: docker-compose down"
echo "   Restart:       docker-compose restart"
echo ""
echo "📖 For more information, see DOCKER_DEPLOYMENT.md"

