@echo off
REM MANDI EAR™ Development Startup Script for Windows

echo Starting MANDI EAR™ Development Environment...

REM Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo Error: Docker is not running. Please start Docker first.
    exit /b 1
)

REM Create .env file if it doesn't exist
if not exist .env (
    echo Creating .env file from template...
    copy .env.example .env
)

REM Start the services
echo Starting database services...
docker-compose up -d postgres mongodb redis influxdb

REM Wait for databases to be ready
echo Waiting for databases to initialize...
timeout /t 10 /nobreak >nul

REM Start the application services
echo Starting application services...
docker-compose up -d api-gateway ambient-ai-service voice-processing-service price-discovery-service user-management-service

echo MANDI EAR™ services are starting up...
echo API Gateway will be available at: http://localhost:8000
echo API Documentation: http://localhost:8000/docs
echo.
echo To view logs: docker-compose logs -f
echo To stop services: docker-compose down

pause