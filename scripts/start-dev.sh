#!/bin/bash

# MANDI EAR™ Development Startup Script

echo "Starting MANDI EAR™ Development Environment..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "Error: Docker is not running. Please start Docker first."
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
fi

# Start the services
echo "Starting database services..."
docker-compose up -d postgres mongodb redis influxdb

# Wait for databases to be ready
echo "Waiting for databases to initialize..."
sleep 10

# Start the application services
echo "Starting application services..."
docker-compose up -d api-gateway ambient-ai-service voice-processing-service price-discovery-service user-management-service

echo "MANDI EAR™ services are starting up..."
echo "API Gateway will be available at: http://localhost:8000"
echo "API Documentation: http://localhost:8000/docs"
echo ""
echo "To view logs: docker-compose logs -f"
echo "To stop services: docker-compose down"