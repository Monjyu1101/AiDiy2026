@echo off
rem AiDiy2026 Docker - Step 2: Start Containers
rem Start Docker containers from built images

echo AiDiy2026 Docker - Step 2: Start Containers
echo =============================================

cd /d "%~dp0"

rem Docker check
docker version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker not available
    echo Please ensure Docker Desktop is running
    pause
    exit /b 1
)

rem Check if images exist
echo Checking Docker images...
docker images aidiy2026* -q >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker images not found.
    echo Please run docker_1build.bat first.
    pause
    exit /b 1
)

rem Start containers
echo Starting containers...
docker-compose up -d

if %errorlevel% == 0 (
    echo.
    echo =============================================
    echo   STARTUP COMPLETE
    echo =============================================
    echo.
    echo *** IMPORTANT: For audio/video features, use HTTPS ***
    echo.
    echo Primary Access (HTTPS - Required for audio):
    echo   - Frontend (HTTPS):  https://localhost/
    echo.
    echo Alternative Access (HTTP - No audio support):
    echo   - Frontend (HTTP):   http://localhost:8090
    echo   - Frontend (Nginx):  http://localhost/
    echo.
    echo Backend API Documentation:
    echo   - Core API (Direct): http://localhost:8091/docs
    echo   - Apps API (Direct): http://localhost:8092/docs
    echo   - Core API (Nginx):  http://localhost/api/core/docs
    echo   - Apps API (Nginx):  http://localhost/api/apps/docs
    echo.
    echo Default Login:
    echo   - Username: admin
    echo   - Password: (check README.md)
    echo.
    echo Note: You will need to accept the self-signed certificate warning
    echo       in your browser when accessing HTTPS for the first time.
    echo.
    docker-compose ps
) else (
    echo.
    echo ERROR: Failed to start containers
    docker-compose logs --tail=20
)

echo.
pause