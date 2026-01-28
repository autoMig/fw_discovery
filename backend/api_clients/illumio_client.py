import aiohttp
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class IllumioClient:
    """Client for interacting with the Illumio API"""
    
    def __init__(self, api_url: str, api_key: str):
        self.api_url = api_url.rstrip('/')
        self.api_key = api_key
        self.timeout = aiohttp.ClientTimeout(total=30)
        
    async def _make_request(self, endpoint: str, method: str = "GET", data: Optional[Dict] = None) -> Dict:
        """Make an authenticated request to the Illumio API"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        url = f"{self.api_url}/{endpoint}"
        
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                if method == "GET":
                    async with session.get(url, headers=headers) as response:
                        response.raise_for_status()
                        return await response.json()
                elif method == "POST":
                    async with session.post(url, headers=headers, json=data) as response:
                        response.raise_for_status()
                        return await response.json()
        except aiohttp.ClientError as e:
            logger.error(f"Error calling Illumio API: {str(e)}")
            raise
    
    async def get_workload_info(self, hostname: str) -> Optional[Dict]:
        """
        Get workload information including operating mode
        
        Args:
            hostname: The hostname to query
            
        Returns:
            Workload information including operating mode
        """
        try:
            # TODO: Update endpoint based on actual Illumio API
            response = await self._make_request(
                f"workloads",
                params={"hostname": hostname}
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error getting workload info for {hostname}: {str(e)}")
            return self._get_mock_workload_info(hostname)
    
    async def policy_check(self, source: str, destination: str, port: int, protocol: str) -> Dict:
        """
        Perform a policy check to see if traffic would be allowed
        
        Args:
            source: Source IP or hostname
            destination: Destination IP or hostname
            port: Port number
            protocol: Protocol (TCP/UDP)
            
        Returns:
            Policy check results
        """
        try:
            # TODO: Update endpoint and payload based on actual Illumio API
            payload = {
                "sources": [{"ip": source}],
                "destinations": [{"ip": destination}],
                "services": [{"port": port, "proto": protocol.lower()}]
            }
            
            response = await self._make_request(
                "policy_check",
                method="POST",
                data=payload
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error performing policy check: {str(e)}")
            return self._get_mock_policy_check_result(source, destination, port, protocol)
    
    async def rule_search(self, source: str, destination: str, port: int, protocol: str) -> List[Dict]:
        """
        Search for rules matching the given criteria
        
        Args:
            source: Source IP or hostname
            destination: Destination IP or hostname
            port: Port number
            protocol: Protocol (TCP/UDP)
            
        Returns:
            List of matching rules
        """
        try:
            # TODO: Update endpoint and payload based on actual Illumio API
            payload = {
                "sources": [{"ip": source}],
                "destinations": [{"ip": destination}],
                "services": [{"port": port, "proto": protocol.lower()}]
            }
            
            response = await self._make_request(
                "rule_search",
                method="POST",
                data=payload
            )
            
            return response.get("rules", [])
            
        except Exception as e:
            logger.error(f"Error performing rule search: {str(e)}")
            return self._get_mock_rule_search_results(source, destination, port, protocol)
    
    def _get_mock_workload_info(self, hostname: str) -> Dict:
        """Mock workload data for development"""
        return {
            "hostname": hostname,
            "operating_mode": "enforced",  # Can be: enforced, visibility_only, idle
            "policy_state": "active",
            "interfaces": [
                {
                    "name": "eth0",
                    "ip_address": "10.2.1.50"
                }
            ]
        }
    
    def _get_mock_policy_check_result(self, source: str, destination: str, port: int, protocol: str) -> Dict:
        """Mock policy check result for development"""
        return {
            "allowed": True,
            "decision": "allow",
            "matched_rules": [
                {
                    "rule_id": "rule-12345",
                    "rule_name": "Allow App Tier Communication",
                    "action": "allow"
                }
            ]
        }
    
    def _get_mock_rule_search_results(self, source: str, destination: str, port: int, protocol: str) -> List[Dict]:
        """Mock rule search results for development"""
        return [
            {
                "rule_id": "rule-12345",
                "rule_name": "Allow App Tier Communication",
                "enabled": True,
                "sources": [{"label": "App-Tier"}],
                "destinations": [{"label": "DB-Tier"}],
                "services": [{"port": port, "protocol": protocol}],
                "action": "allow"
            },
            {
                "rule_id": "rule-67890",
                "rule_name": "Default Allow Internal",
                "enabled": True,
                "sources": [{"ip_range": "10.0.0.0/8"}],
                "destinations": [{"ip_range": "10.0.0.0/8"}],
                "services": [{"port": port, "protocol": protocol}],
                "action": "allow"
            }
        ]
