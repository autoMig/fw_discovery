import aiohttp
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class UnicornClient:
    """Client for interacting with the Unicorn inventory API"""
    
    def __init__(self, api_url: str, api_key: str):
        self.api_url = api_url.rstrip('/')
        self.api_key = api_key
        self.timeout = aiohttp.ClientTimeout(total=30)
        
    async def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """Make an authenticated request to the Unicorn API"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        url = f"{self.api_url}/{endpoint}"
        
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(url, headers=headers, params=params) as response:
                    response.raise_for_status()
                    return await response.json()
        except aiohttp.ClientError as e:
            logger.error(f"Error calling Unicorn API: {str(e)}")
            raise
    
    async def get_application_hosts(self, application_name: str) -> List[Dict]:
        """
        Get all hosts associated with a business application
        
        Args:
            application_name: Name of the business application
            
        Returns:
            List of host records with their properties
        """
        try:
            # TODO: Update endpoint and response structure based on actual Unicorn API
            response = await self._make_request(
                "applications/search",
                params={"name": application_name}
            )
            
            # Mock response structure - update when you have real API responses
            # Expected structure:
            # {
            #     "application": {
            #         "name": "MyApp",
            #         "hosts": [...]
            #     }
            # }
            
            return response.get("hosts", [])
            
        except Exception as e:
            logger.error(f"Error getting hosts for application {application_name}: {str(e)}")
            # Return mock data for development
            return self._get_mock_application_hosts(application_name)
    
    async def get_host_info(self, hostname: str) -> Optional[Dict]:
        """
        Get information about a specific host
        
        Args:
            hostname: The hostname to query
            
        Returns:
            Host record with properties
        """
        try:
            # TODO: Update endpoint and response structure based on actual Unicorn API
            response = await self._make_request(
                "hosts/search",
                params={"hostname": hostname}
            )
            
            return response.get("host", None)
            
        except Exception as e:
            logger.error(f"Error getting info for host {hostname}: {str(e)}")
            # Return mock data for development
            return self._get_mock_host_info(hostname)
    
    def _get_mock_application_hosts(self, application_name: str) -> List[Dict]:
        """Mock data for development - replace with real API calls"""
        return [
            {
                "hostname": "webserver01.dmz.example.com",
                "location": "DMZ",
                "network_zone": "Standard",
                "platform": "ESX",
                "os_type": "Linux",
                "ip_address": "10.1.1.10"
            },
            {
                "hostname": "appserver01.internal.example.com",
                "location": "Internal",
                "network_zone": "High Risk",
                "platform": "Physical",
                "os_type": "Linux",
                "ip_address": "10.2.1.20"
            },
            {
                "hostname": "dbserver01.internal.example.com",
                "location": "Internal",
                "network_zone": "Standard",
                "platform": "ESX",
                "os_type": "Windows",
                "ip_address": "10.2.2.30"
            }
        ]
    
    def _get_mock_host_info(self, hostname: str) -> Dict:
        """Mock data for development - replace with real API calls"""
        return {
            "hostname": hostname,
            "location": "Internal",
            "network_zone": "Standard",
            "platform": "ESX",
            "os_type": "Linux",
            "ip_address": "10.2.1.50"
        }
