@echo off
rem AiDiy2026 Docker - Step 1: Build Images
rem SSL certificate generation and Docker image building

echo AiDiy2026 Docker - Step 1: Build Images
echo ========================================

cd /d "%~dp0"

rem Docker check
docker version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker not available
    echo Please install Docker Desktop and ensure it is running
    pause
    exit /b 1
)

rem SSL Certificate Generation
echo Generating SSL certificates...
if not exist ssl mkdir ssl

rem Check for OpenSSL (try multiple common locations)
set OPENSSL_FOUND=0
openssl version >nul 2>&1
if %errorlevel% == 0 (
    set OPENSSL_FOUND=1
) else (
    rem Try Git's OpenSSL
    if exist "C:\Program Files\Git\usr\bin\openssl.exe" (
        set "PATH=C:\Program Files\Git\usr\bin;%PATH%"
        set OPENSSL_FOUND=1
    ) else if exist "C:\Program Files (x86)\Git\usr\bin\openssl.exe" (
        set "PATH=C:\Program Files (x86)\Git\usr\bin;%PATH%"
        set OPENSSL_FOUND=1
    )
)

if %OPENSSL_FOUND% == 1 (
    rem Generate new SSL certificates
    echo Generating new SSL certificate for localhost...
    openssl genrsa -out ssl/key.pem 2048 >nul 2>&1
    openssl req -new -key ssl/key.pem -out ssl/cert.csr -subj "/C=JP/ST=Tokyo/L=Tokyo/O=AiDiy2026/OU=Development/CN=localhost/emailAddress=admin@localhost" >nul 2>&1
    openssl x509 -req -days 365 -in ssl/cert.csr -signkey ssl/key.pem -out ssl/cert.pem >nul 2>&1
    del ssl\cert.csr >nul 2>&1
    echo [OK] SSL certificates generated
) else (
    echo [WARN] OpenSSL not found. Using Docker to generate SSL certificates...
    docker run --rm -v "%cd%\ssl:/ssl" alpine/openssl genrsa -out /ssl/key.pem 2048
    docker run --rm -v "%cd%\ssl:/ssl" alpine/openssl req -new -key /ssl/key.pem -out /ssl/cert.csr -subj "/C=JP/ST=Tokyo/L=Tokyo/O=AiDiy2026/OU=Development/CN=localhost/emailAddress=admin@localhost"
    docker run --rm -v "%cd%\ssl:/ssl" alpine/openssl x509 -req -days 365 -in /ssl/cert.csr -signkey /ssl/key.pem -out /ssl/cert.pem
    docker run --rm -v "%cd%\ssl:/ssl" alpine sh -c "rm -f /ssl/cert.csr"
    echo [OK] SSL certificates generated via Docker
)

rem Build Docker images
echo.
echo Building Docker images (this may take a few minutes)...
docker-compose build --no-cache

if %errorlevel% == 0 (
    echo.
    echo ========================================
    echo   BUILD COMPLETE
    echo ========================================
    echo.
    echo Docker images and SSL certificates are ready.
    echo Next step: Run docker_2start.bat
    echo.
) else (
    echo.
    echo ERROR: Failed to build images
    docker-compose logs --tail=20
)

echo.
pause