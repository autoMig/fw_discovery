from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import logging

from api_clients.unicorn_client import UnicornClient
from api_clients.illumio_client import IllumioClient
from services.firewall_discovery import FirewallDiscoveryService
from services.rule_checker import RuleCheckerService
from config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Firewall Discovery Tool",
    description="Tool to help application teams identify firewall platforms and check connectivity rules",
    version="1.0.0"
)

# CORS middleware - adjust origins for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update with specific frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize clients and services
unicorn_client = UnicornClient(settings.UNICORN_API_URL, settings.UNICORN_API_KEY)
illumio_client = IllumioClient(settings.ILLUMIO_API_URL, settings.ILLUMIO_API_KEY)

discovery_service = FirewallDiscoveryService(unicorn_client, illumio_client)
rule_checker_service = RuleCheckerService(illumio_client)


# Request/Response Models
class FirewallDiscoveryRequest(BaseModel):
    application_name: Optional[str] = None
    hostname: Optional[str] = None


class ConnectivityCheckRequest(BaseModel):
    source: str  # Can be application name or hostname
    destination: str  # Can be application name or hostname
    port: int
    protocol: str = "TCP"


class HealthResponse(BaseModel):
    status: str
    version: str


@app.get("/", response_model=HealthResponse)
async def root():
    """Health check endpoint"""
    return HealthResponse(status="healthy", version="1.0.0")


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(status="healthy", version="1.0.0")


@app.post("/api/v1/discover-firewalls")
async def discover_firewalls(request: FirewallDiscoveryRequest):
    """
    Discover which firewall platforms apply to an application or host
    
    Args:
        request: Contains either application_name or hostname
        
    Returns:
        Dictionary containing hosts and their applicable firewall platforms
    """
    try:
        if not request.application_name and not request.hostname:
            raise HTTPException(
                status_code=400,
                detail="Either application_name or hostname must be provided"
            )
        
        logger.info(f"Discovering firewalls for: {request.application_name or request.hostname}")
        
        result = await discovery_service.discover_firewalls(
            application_name=request.application_name,
            hostname=request.hostname
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error in firewall discovery: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/check-connectivity")
async def check_connectivity(request: ConnectivityCheckRequest):
    """
    Check connectivity rules between source and destination
    
    Args:
        request: Contains source, destination, port, and protocol
        
    Returns:
        Dictionary containing applicable firewalls and matching rules
    """
    try:
        logger.info(f"Checking connectivity: {request.source} -> {request.destination}:{request.port}/{request.protocol}")
        
        # First discover which firewalls apply
        source_firewalls = await discovery_service.discover_firewalls(
            application_name=request.source if not _is_hostname(request.source) else None,
            hostname=request.source if _is_hostname(request.source) else None
        )
        
        dest_firewalls = await discovery_service.discover_firewalls(
            application_name=request.destination if not _is_hostname(request.destination) else None,
            hostname=request.destination if _is_hostname(request.destination) else None
        )
        
        # Then check rules for applicable firewalls
        rule_results = await rule_checker_service.check_connectivity(
            source_info=source_firewalls,
            dest_info=dest_firewalls,
            port=request.port,
            protocol=request.protocol
        )
        
        return {
            "source": request.source,
            "destination": request.destination,
            "port": request.port,
            "protocol": request.protocol,
            "source_firewalls": source_firewalls,
            "destination_firewalls": dest_firewalls,
            "rule_results": rule_results
        }
        
    except Exception as e:
        logger.error(f"Error in connectivity check: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


def _is_hostname(value: str) -> bool:
    """
    Simple heuristic to determine if a value is a hostname vs application name
    Hostnames typically contain dots or are FQDN-like
    """
    return "." in value or value.count("-") > 2


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
