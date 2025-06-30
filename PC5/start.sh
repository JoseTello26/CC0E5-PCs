#!/bin/bash

echo "🚀 Starting Anomaly Detection System..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Check if Docker Compose is available
if ! command -v docker compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

echo "📦 Building and starting services..."

# Build and start all services
docker compose up -d --build

echo "⏳ Waiting for services to start..."
sleep 30

echo "🔍 Checking service status..."

# Check if services are running
if docker compose ps | grep -q "Up"; then
    echo "✅ Services are running!"
    echo ""
    echo "📊 Service URLs:"
    echo "   - Flink Web UI: http://localhost:8081"
    echo "   - Kafka: localhost:9092"
    echo ""
    echo "📋 To view logs:"
    echo "   - All services: docker compose logs -f"
    echo "   - Producer only: docker compose logs -f producer"
    echo "   - Flink job only: docker compose logs -f flink-job"
    echo ""
    echo "🛑 To stop services: docker compose down"
else
    echo "❌ Some services failed to start. Check logs with: docker compose logs"
    exit 1
fi 