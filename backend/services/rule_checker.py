import logging
from typing import Dict, List
from api_clients.illumio_client import IllumioClient

logger = logging.getLogger(__name__)


class RuleCheckerService:
    """
    Service to check connectivity rules across firewall platforms
    Currently supports Illumio, will be extended to other platforms
    """
    
    def __init__(self, illumio_client: IllumioClient):
        self.illumio_client = illumio_client
    
    async def check_connectivity(
        self,
        source_info: Dict,
        dest_info: Dict,
        port: int,
        protocol: str
    ) -> Dict:
        """
        Check connectivity rules between source and destination
        
        Args:
            source_info: Firewall discovery info for source
            dest_info: Firewall discovery info for destination
            port: Port number
            protocol: Protocol (TCP/UDP)
            
        Returns:
            Dictionary with rule check results for each applicable firewall
        """
        
        results = {
            "illumio": None,
            "external_checkpoint": None,
            "internal_checkpoint": None,
            "nsx": None
        }
        
        # Check if Illumio applies to both source and destination
        source_has_illumio = self._check_firewall_applies(source_info, "illumio")
        dest_has_illumio = self._check_firewall_applies(dest_info, "illumio")
        
        if source_has_illumio or dest_has_illumio:
            results["illumio"] = await self._check_illumio_rules(
                source_info, dest_info, port, protocol
            )
        
        # Future: Add checks for other firewall platforms
        # if self._check_firewall_applies(source_info, "external_checkpoint") or ...
        #     results["external_checkpoint"] = await self._check_checkpoint_external(...)
        
        return results
    
    def _check_firewall_applies(self, info: Dict, firewall_type: str) -> bool:
        """Check if a specific firewall type applies to the given host/app info"""
        
        summary = info.get("summary", {})
        return summary.get(firewall_type, False)
    
    async def _check_illumio_rules(
        self,
        source_info: Dict,
        dest_info: Dict,
        port: int,
        protocol: str
    ) -> Dict:
        """
        Check Illumio rules for connectivity
        
        Performs both policy check and rule search
        """
        
        # Extract IP addresses from source and dest
        source_ips = self._extract_ips(source_info)
        dest_ips = self._extract_ips(dest_info)
        
        if not source_ips or not dest_ips:
            return {
                "status": "error",
                "message": "Could not determine IP addresses for source or destination"
            }
        
        # Use first IP for simplicity (can be enhanced to check all combinations)
        source_ip = source_ips[0]
        dest_ip = dest_ips[0]
        
        # Perform policy check
        policy_check_result = await self.illumio_client.policy_check(
            source_ip, dest_ip, port, protocol
        )
        
        # Perform rule search
        matching_rules = await self.illumio_client.rule_search(
            source_ip, dest_ip, port, protocol
        )
        
        return {
            "status": "success",
            "source_ip": source_ip,
            "dest_ip": dest_ip,
            "port": port,
            "protocol": protocol,
            "policy_check": policy_check_result,
            "matching_rules": matching_rules,
            "rule_count": len(matching_rules)
        }
    
    def _extract_ips(self, info: Dict) -> List[str]:
        """Extract IP addresses from discovery info"""
        
        ips = []
        hosts = info.get("hosts", [])
        
        for host in hosts:
            ip = host.get("ip_address")
            if ip and ip != "unknown":
                ips.append(ip)
        
        return ips
    
    # Placeholder methods for future firewall integrations
    
    async def _check_checkpoint_external(
        self, source_info: Dict, dest_info: Dict, port: int, protocol: str
    ) -> Dict:
        """Check External Checkpoint rules - to be implemented"""
        return {
            "status": "not_implemented",
            "message": "External Checkpoint integration coming soon"
        }
    
    async def _check_checkpoint_internal(
        self, source_info: Dict, dest_info: Dict, port: int, protocol: str
    ) -> Dict:
        """Check Internal Checkpoint rules - to be implemented"""
        return {
            "status": "not_implemented",
            "message": "Internal Checkpoint integration coming soon"
        }
    
    async def _check_nsx(
        self, source_info: Dict, dest_info: Dict, port: int, protocol: str
    ) -> Dict:
        """Check NSX rules - to be implemented"""
        return {
            "status": "not_implemented",
            "message": "NSX integration coming soon"
        }
