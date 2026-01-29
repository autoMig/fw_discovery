# Firewall Discovery Tool - Windows Management Script
# 
# This script provides easy commands to manage your Firewall Discovery Tool
# on Windows 11 with Docker Desktop
#
# Usage:
#   .\manage.ps1 start      - Start the application
#   .\manage.ps1 stop       - Stop the application
#   .\manage.ps1 restart    - Restart the application
#   .\manage.ps1 logs       - View logs
#   .\manage.ps1 build      - Rebuild containers
#   .\manage.ps1 status     - Check status
#   .\manage.ps1 clean      - Clean up everything
#   .\manage.ps1 help       - Show this help
#
# =============================================================================

param(
    [Parameter(Mandatory=$true, Position=0)]
    [ValidateSet('start','stop','restart','logs','build','status','clean','help','test')]
    [string]$Command
)

# Configuration
$ComposeFile = "docker-compose-windows.yml"
$ProjectName = "firewall-discovery-tool"

# Colors for output
function Write-Success { Write-Host $args -ForegroundColor Green }
function Write-Info { Write-Host $args -ForegroundColor Cyan }
function Write-Warning { Write-Host $args -ForegroundColor Yellow }
function Write-Error-Message { Write-Host $args -ForegroundColor Red }

# Check if Docker is running
function Test-DockerRunning {
    try {
        docker ps | Out-Null
        return $true
    } catch {
        Write-Error-Message "❌ Docker is not running!"
        Write-Info "Please start Docker Desktop and try again."
        return $false
    }
}

# Check if project files exist
function Test-ProjectFiles {
    if (-not (Test-Path $ComposeFile)) {
        Write-Error-Message "❌ $ComposeFile not found!"
        Write-Info "Make sure you're in the project directory."
        return $false
    }
    
    if (-not (Test-Path "backend\.env")) {
        Write-Warning "⚠️  backend\.env not found!"
        Write-Info "You may need to copy .env.example to .env and configure it."
    }
    
    return $true
}

# Main command switch
switch ($Command) {
    'start' {
        Write-Info "🚀 Starting Firewall Discovery Tool..."
        
        if (-not (Test-DockerRunning)) { exit 1 }
        if (-not (Test-ProjectFiles)) { exit 1 }
        
        docker-compose -f $ComposeFile up -d
        
        if ($LASTEXITCODE -eq 0) {
            Write-Success "`n✅ Application started successfully!"
            Write-Info "`nAccess your application at:"
            Write-Info "  Frontend:  http://localhost:3000"
            Write-Info "  Backend:   http://localhost:8000"
            Write-Info "  API Docs:  http://localhost:8000/docs"
            Write-Info "`nView logs with: .\manage.ps1 logs"
        } else {
            Write-Error-Message "`n❌ Failed to start application"
            Write-Info "Check logs with: .\manage.ps1 logs"
        }
    }
    
    'stop' {
        Write-Info "🛑 Stopping Firewall Discovery Tool..."
        
        if (-not (Test-DockerRunning)) { exit 1 }
        
        docker-compose -f $ComposeFile down
        
        if ($LASTEXITCODE -eq 0) {
            Write-Success "`n✅ Application stopped successfully!"
        }
    }
    
    'restart' {
        Write-Info "🔄 Restarting Firewall Discovery Tool..."
        
        if (-not (Test-DockerRunning)) { exit 1 }
        if (-not (Test-ProjectFiles)) { exit 1 }
        
        docker-compose -f $ComposeFile restart
        
        if ($LASTEXITCODE -eq 0) {
            Write-Success "`n✅ Application restarted successfully!"
        }
    }
    
    'logs' {
        Write-Info "📋 Showing logs (Ctrl+C to exit)..."
        Write-Info ""
        
        if (-not (Test-DockerRunning)) { exit 1 }
        
        docker-compose -f $ComposeFile logs -f
    }
    
    'build' {
        Write-Info "🔨 Building containers..."
        Write-Warning "This may take several minutes on first build..."
        Write-Info ""
        
        if (-not (Test-DockerRunning)) { exit 1 }
        if (-not (Test-ProjectFiles)) { exit 1 }
        
        docker-compose -f $ComposeFile build
        
        if ($LASTEXITCODE -eq 0) {
            Write-Success "`n✅ Build completed successfully!"
            Write-Info "`nStart the application with: .\manage.ps1 start"
        } else {
            Write-Error-Message "`n❌ Build failed"
            Write-Info "Check the error messages above for details"
        }
    }
    
    'status' {
        Write-Info "📊 Checking status..."
        Write-Info ""
        
        if (-not (Test-DockerRunning)) { exit 1 }
        
        # Check container status
        $containers = docker ps --filter "name=firewall-tool" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
        
        if ($containers) {
            Write-Success "Running containers:"
            Write-Host $containers
            
            Write-Info "`nTesting backend health..."
            try {
                $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 5
                if ($response.StatusCode -eq 200) {
                    Write-Success "✅ Backend is healthy"
                }
            } catch {
                Write-Warning "⚠️  Backend health check failed (may still be starting)"
            }
            
            Write-Info "`nTesting frontend..."
            try {
                $response = Invoke-WebRequest -Uri "http://localhost:3000" -UseBasicParsing -TimeoutSec 5
                if ($response.StatusCode -eq 200) {
                    Write-Success "✅ Frontend is accessible"
                }
            } catch {
                Write-Warning "⚠️  Frontend not accessible (may still be starting)"
            }
            
        } else {
            Write-Warning "No containers are running"
            Write-Info "Start the application with: .\manage.ps1 start"
        }
    }
    
    'clean' {
        Write-Warning "🧹 This will stop and remove all containers, networks, and volumes!"
        $confirm = Read-Host "Are you sure? (yes/no)"
        
        if ($confirm -eq "yes") {
            Write-Info "Cleaning up..."
            
            if (Test-DockerRunning) {
                docker-compose -f $ComposeFile down -v --remove-orphans
                
                Write-Success "`n✅ Cleanup completed!"
                Write-Info "You can rebuild with: .\manage.ps1 build"
            }
        } else {
            Write-Info "Cancelled."
        }
    }
    
    'test' {
        Write-Info "🧪 Testing application..."
        Write-Info ""
        
        if (-not (Test-DockerRunning)) { exit 1 }
        
        # Test backend
        Write-Info "Testing backend health endpoint..."
        try {
            $response = Invoke-RestMethod -Uri "http://localhost:8000/health" -TimeoutSec 5
            if ($response.status -eq "healthy") {
                Write-Success "✅ Backend health check passed"
                Write-Info "   Version: $($response.version)"
            }
        } catch {
            Write-Error-Message "❌ Backend health check failed"
            Write-Info "   Error: $($_.Exception.Message)"
        }
        
        Write-Info ""
        
        # Test frontend
        Write-Info "Testing frontend..."
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:3000" -UseBasicParsing -TimeoutSec 5
            if ($response.StatusCode -eq 200) {
                Write-Success "✅ Frontend is accessible"
            }
        } catch {
            Write-Error-Message "❌ Frontend not accessible"
            Write-Info "   Error: $($_.Exception.Message)"
        }
        
        Write-Info ""
        Write-Info "Full test with: curl http://localhost:8000/docs"
    }
    
    'help' {
        Write-Host @"

Firewall Discovery Tool - Management Script
============================================

Available Commands:

  start      Start the application
             Builds and starts all containers
             Access at: http://localhost:3000

  stop       Stop the application
             Stops all containers but keeps configuration

  restart    Restart the application
             Quick restart without rebuilding

  logs       View application logs
             Shows real-time logs from all containers
             Press Ctrl+C to exit

  build      Build/rebuild containers
             Use after changing Dockerfile or dependencies
             Takes several minutes on first build

  status     Check application status
             Shows running containers and health checks

  clean      Remove everything
             Stops containers and removes volumes
             WARNING: This deletes all data!

  test       Test application endpoints
             Checks if backend and frontend are working

  help       Show this help message

Examples:

  .\manage.ps1 start
  .\manage.ps1 logs
  .\manage.ps1 status
  .\manage.ps1 stop

Quick Start:

  1. Configure backend\.env with your API credentials
  2. .\manage.ps1 build
  3. .\manage.ps1 start
  4. Open http://localhost:3000

Troubleshooting:

  - If containers won't start: .\manage.ps1 logs
  - If ports are in use: Change ports in $ComposeFile
  - After code changes: .\manage.ps1 restart
  - For clean slate: .\manage.ps1 clean then .\manage.ps1 build

"@
    }
}
