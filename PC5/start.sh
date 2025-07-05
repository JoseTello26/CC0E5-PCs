#!/bin/bash

echo "Starting Cluster..."


echo "Building and starting services..."

# Build and start all services
docker compose up -d --build

echo "Waiting for services to start..."
sleep 15

echo "Checking service status..."

# Check if services are running
if docker compose ps | grep -q "Up"; then
    echo "Services are running!"
    echo ""
    echo "Service URLs:"
    echo "   - Flink Web UI: http://localhost:8081"
    echo "   - Kafka: localhost:9092"
    echo ""

else
    echo "Some services failed to start. Check logs with: docker compose logs"
    exit 1
fi 

echo "Starting dashboard..."
streamlit run dashboard/app.py

echo "Dashboard URL:"
echo "   - http://localhost:8501"
echo ""
exit 0
