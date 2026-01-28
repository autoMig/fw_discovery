import logging
from typing import Dict, List, Optional
from api_clients.unicorn_client import UnicornClient
from api_clients.illumio_client import IllumioClient

logger = logging.getLogger(__name__)


class FirewallDiscoveryService:
    """
    Service to discover which firewall platforms apply to applications and hosts
    """
    
    def __init__(self, unicorn_client: UnicornClient, illumio_client: IllumioClient):
        self.unicorn_client = unicorn_client
        self.illumio_client = illumio_client
    
    async def discover_firewalls(
        self, 
        application_name: Optional[str] = None,
        hostname: Optional[str] = None
    ) -> Dict:
        """
        Discover which firewall platforms apply
        
        Args:
            application_name: Name of business application
            hostname: Specific hostname
            
        Returns:
            Dictionary with hosts and their applicable firewall platforms
        """
        
        if application_name:
            return await self._discover_for_application(application_name)
        elif hostname:
            return await self._discover_for_host(hostname)
        else:
            raise ValueError("Either application_name or hostname must be provided")
    
    async def _discover_for_application(self, application_name: str) -> Dict:
        """Discover firewalls for an entire application"""
        
        # Get all hosts for the application
        hosts = await self.unicorn_client.get_application_hosts(application_name)
        
        if not hosts:
            return {
                "application_name": application_name,
                "hosts": [],
                "summary": {
                    "external_checkpoint": False,
                    "internal_checkpoint": False,
                    "illumio": False,
                    "nsx": False
                }
            }
        
        # Process each host
        processed_hosts = []
        summary = {
            "external_checkpoint": False,
            "internal_checkpoint": False,
            "illumio": False,
            "nsx": False
        }
        
        for host in hosts:
            host_info = await self._analyze_host(host)
            processed_hosts.append(host_info)
            
            # Update summary
            for fw in host_info["applicable_firewalls"]:
                summary[fw] = True
        
        return {
            "application_name": application_name,
            "hosts": processed_hosts,
            "summary": summary
        }
    
    async def _discover_for_host(self, hostname: str) -> Dict:
        """Discover firewalls for a specific host"""
        
        # Get host information
        host = await self.unicorn_client.get_host_info(hostname)
        
        if not host:
            return {
                "hostname": hostname,
                "found": False,
                "applicable_firewalls": []
            }
        
        host_info = await self._analyze_host(host)
        
        return {
            "hostname": hostname,
            "found": True,
            "hosts": [host_info],
            "summary": {
                "external_checkpoint": "external_checkpoint" in host_info["applicable_firewalls"],
                "internal_checkpoint": "internal_checkpoint" in host_info["applicable_firewalls"],
                "illumio": "illumio" in host_info["applicable_firewalls"],
                "nsx": "nsx" in host_info["applicable_firewalls"]
            }
        }
    
    async def _analyze_host(self, host: Dict) -> Dict:
        """
        Analyze a host record to determine which firewalls apply
        
        Business Logic:
        - Location = DMZ → External Checkpoint
        - Network Zone = High Risk → Internal Checkpoint
        - OS Type = Windows/Linux → Illumio
        - Platform = ESX → NSX
        """
        
        hostname = host.get("hostname", "unknown")
        location = host.get("location", "").upper()
        network_zone = host.get("network_zone", "").upper()
        platform = host.get("platform", "").upper()
        os_type = host.get("os_type", "").upper()
        
        applicable_firewalls = []
        firewall_details = {}
        
        # Check for External Checkpoint
        if location == "DMZ":
            applicable_firewalls.append("external_checkpoint")
            firewall_details["external_checkpoint"] = {
                "reason": f"Host location is {location}",
                "platform": "Checkpoint - External/Perimeter"
            }
        
        # Check for Internal Checkpoint
        if network_zone == "HIGH RISK":
            applicable_firewalls.append("internal_checkpoint")
            firewall_details["internal_checkpoint"] = {
                "reason": f"Network zone is {network_zone}",
                "platform": "Checkpoint - Internal"
            }
        
        # Check for Illumio
        if os_type in ["WINDOWS", "LINUX"]:
            applicable_firewalls.append("illumio")
            
            # Get Illumio workload information including operating mode
            workload_info = await self.illumio_client.get_workload_info(hostname)
            operating_mode = workload_info.get("operating_mode", "unknown") if workload_info else "unknown"
            
            firewall_details["illumio"] = {
                "reason": f"Host OS type is {os_type}",
                "platform": "Illumio - Host-Based Firewall",
                "operating_mode": operating_mode
            }
        
        # Check for NSX
        if platform == "ESX":
            applicable_firewalls.append("nsx")
            firewall_details["nsx"] = {
                "reason": f"Host platform is {platform}",
                "platform": "NSX - Virtual Firewall"
            }
        
        return {
            "hostname": hostname,
            "location": location,
            "network_zone": network_zone,
            "platform": platform,
            "os_type": os_type,
            "ip_address": host.get("ip_address", "unknown"),
            "applicable_firewalls": applicable_firewalls,
            "firewall_details": firewall_details
        }
