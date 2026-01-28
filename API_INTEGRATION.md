# API Integration Guide

This guide helps you integrate the Firewall Discovery Tool with your actual API endpoints. The application currently uses mock data for development and testing.

## Overview

The tool integrates with multiple APIs:
1. **Unicorn API** - Server and Application Inventory
2. **Illumio API** - Host-based Firewall Policy
3. **Checkpoint APIs** (Future) - External and Internal Firewalls
4. **NSX API** (Future) - Virtual Firewall

## Unicorn API Integration

### Expected API Structure

The Unicorn API should provide:
- **Application Search**: Query by application name, return list of hosts
- **Host Search**: Query by hostname, return host details

### Required Host Properties

Each host record should include:
```json
{
  "hostname": "server01.example.com",
  "ip_address": "10.1.1.10",
  "location": "DMZ",           // Used to determine External Checkpoint
  "network_zone": "High Risk",  // Used to determine Internal Checkpoint
  "platform": "ESX",            // Used to determine NSX
  "os_type": "Linux"            // Used to determine Illumio
}
```

### Configuration Steps

1. **Get API Credentials**
   ```bash
   # Request API key from Unicorn team
   # Note the API endpoint URL
   ```

2. **Update Environment Variables**
   
   Edit `backend/.env`:
   ```env
   UNICORN_API_URL=https://unicorn.yourcompany.com/api/v1
   UNICORN_API_KEY=your_actual_api_key_here
   ```

3. **Update API Client Code**

   Edit `backend/api_clients/unicorn_client.py`:

   ```python
   async def get_application_hosts(self, application_name: str) -> List[Dict]:
       """Get all hosts for an application"""
       try:
           # Update endpoint based on your Unicorn API documentation
           response = await self._make_request(
               "applications",  # Change to your endpoint
               params={"name": application_name, "include": "hosts"}
           )
           
           # Parse response based on actual structure
           # Example: if response is {"data": {"hosts": [...]}}
           hosts = response.get("data", {}).get("hosts", [])
           
           # Map fields if needed
           normalized_hosts = []
           for host in hosts:
               normalized_hosts.append({
                   "hostname": host.get("hostname"),
                   "ip_address": host.get("ip"),  # May need field mapping
                   "location": host.get("datacenter_location"),  # Field name may differ
                   "network_zone": host.get("zone"),
                   "platform": host.get("virtualization_platform"),
                   "os_type": host.get("operating_system")
               })
           
           return normalized_hosts
           
       except Exception as e:
           logger.error(f"Error getting hosts for {application_name}: {str(e)}")
           raise
   ```

4. **Test the Integration**

   ```bash
   # Start backend
   cd backend
   uvicorn main:app --reload
   
   # In another terminal, test the endpoint
   curl -X POST http://localhost:8000/api/v1/discover-firewalls \
     -H "Content-Type: application/json" \
     -d '{"application_name": "YourActualApp"}'
   ```

### Example API Responses

**Example 1: Nested Response**
```json
{
  "status": "success",
  "data": {
    "application": {
      "name": "MyApp",
      "id": 12345
    },
    "hosts": [
      {
        "hostname": "web01.dmz.example.com",
        "ip": "10.1.1.10",
        "datacenter_location": "DMZ",
        "zone": "Standard",
        "virtualization_platform": "ESX",
        "operating_system": "Linux"
      }
    ]
  }
}
```

**Parsing Code:**
```python
hosts = response.get("data", {}).get("hosts", [])
```

**Example 2: Flat Response**
```json
{
  "hosts": [
    {
      "hostname": "web01.dmz.example.com",
      "ip_address": "10.1.1.10",
      "location": "DMZ",
      "network_zone": "Standard",
      "platform": "ESX",
      "os_type": "Linux"
    }
  ]
}
```

**Parsing Code:**
```python
hosts = response.get("hosts", [])
```

## Illumio API Integration

### Expected API Structure

The Illumio API should provide:
- **Workload Information**: Get operating mode for a host
- **Policy Check**: Test if traffic would be allowed
- **Rule Search**: Find rules matching criteria

### Configuration Steps

1. **Get API Credentials**
   ```bash
   # Request API credentials from Illumio admin
   # You'll need: API URL, API key (or org_id/api_key)
   ```

2. **Update Environment Variables**
   
   Edit `backend/.env`:
   ```env
   ILLUMIO_API_URL=https://illumio.yourcompany.com:8443/api/v2
   ILLUMIO_API_KEY=your_illumio_api_key
   ```

3. **Update API Client Code**

   Edit `backend/api_clients/illumio_client.py`:

   #### Workload Information

   ```python
   async def get_workload_info(self, hostname: str) -> Optional[Dict]:
       """Get workload operating mode"""
       try:
           # Illumio API: GET /workloads?hostname={hostname}
           response = await self._make_request(
               f"workloads?hostname={hostname}"
           )
           
           # Parse response
           workloads = response if isinstance(response, list) else [response]
           
           if not workloads:
               return None
           
           workload = workloads[0]
           
           return {
               "hostname": workload.get("hostname"),
               "operating_mode": workload.get("agent", {}).get("mode", "unknown"),
               "policy_state": workload.get("agent", {}).get("status", {}).get("security_policy_sync_state"),
               "interfaces": [
                   {
                       "name": iface.get("name"),
                       "ip_address": iface.get("address")
                   }
                   for iface in workload.get("interfaces", [])
               ]
           }
       except Exception as e:
           logger.error(f"Error getting workload info: {str(e)}")
           return None
   ```

   #### Policy Check

   ```python
   async def policy_check(self, source: str, destination: str, port: int, protocol: str) -> Dict:
       """Perform policy check"""
       try:
           # Illumio API: POST /network_enforcement_boundaries/policy_decisions
           payload = {
               "sources": [{"ip_address": source}],
               "destinations": [{"ip_address": destination}],
               "services": [{
                   "port": port,
                   "proto": protocol.upper()
               }]
           }
           
           response = await self._make_request(
               "network_enforcement_boundaries/policy_decisions",
               method="POST",
               data=payload
           )
           
           # Parse decision
           decision = response.get("decision", "unknown")
           
           return {
               "allowed": decision == "allowed",
               "decision": decision,
               "matched_rules": response.get("matched_rules", [])
           }
       except Exception as e:
           logger.error(f"Policy check error: {str(e)}")
           raise
   ```

   #### Rule Search

   ```python
   async def rule_search(self, source: str, destination: str, port: int, protocol: str) -> List[Dict]:
       """Search for matching rules"""
       try:
           # Illumio API: GET /sec_policy/active/rule_sets
           # Then filter rules matching criteria
           
           response = await self._make_request("sec_policy/active/rule_sets")
           
           matching_rules = []
           
           for ruleset in response:
               for rule in ruleset.get("rules", []):
                   # Check if rule matches our criteria
                   if self._rule_matches(rule, source, destination, port, protocol):
                       matching_rules.append({
                           "rule_id": rule.get("href").split("/")[-1],
                           "rule_name": rule.get("description", "Unnamed"),
                           "enabled": rule.get("enabled", True),
                           "sources": rule.get("resolve_labels_as", {}).get("providers", []),
                           "destinations": rule.get("resolve_labels_as", {}).get("consumers", []),
                           "services": rule.get("ingress_services", []),
                           "action": "allow"  # Illumio rules are allow by default
                       })
           
           return matching_rules
       except Exception as e:
           logger.error(f"Rule search error: {str(e)}")
           raise
   
   def _rule_matches(self, rule: Dict, source: str, dest: str, port: int, protocol: str) -> bool:
       """Check if a rule matches the search criteria"""
       # Implement matching logic based on your Illumio configuration
       # This is a simplified example
       
       services = rule.get("ingress_services", [])
       for service in services:
           if (service.get("port") == port and 
               service.get("proto", "").upper() == protocol.upper()):
               return True
       
       return False
   ```

4. **Authentication Variations**

   If your Illumio API uses different authentication:

   ```python
   # Option 1: API Key in header
   headers = {
       "Authorization": f"Bearer {self.api_key}",
       "Content-Type": "application/json"
   }
   
   # Option 2: Basic Auth with org_id and api_key
   import base64
   
   auth_string = f"{org_id}:{api_key}"
   encoded = base64.b64encode(auth_string.encode()).decode()
   headers = {
       "Authorization": f"Basic {encoded}",
       "Content-Type": "application/json"
   }
   
   # Option 3: Session-based authentication
   async def _get_session(self):
       """Get authenticated session"""
       async with aiohttp.ClientSession() as session:
           async with session.post(
               f"{self.api_url}/login",
               json={"username": self.username, "password": self.password}
           ) as response:
               return await response.json()
   ```

5. **Test Integration**

   ```bash
   # Test workload info
   curl -X POST http://localhost:8000/api/v1/discover-firewalls \
     -H "Content-Type: application/json" \
     -d '{"hostname": "actual-server.example.com"}'
   
   # Test policy check
   curl -X POST http://localhost:8000/api/v1/check-connectivity \
     -H "Content-Type: application/json" \
     -d '{
       "source": "10.1.1.10",
       "destination": "10.2.2.20",
       "port": 443,
       "protocol": "TCP"
     }'
   ```

## Field Mapping

If your API uses different field names, create a mapping function:

```python
class UnicornClient:
    
    FIELD_MAPPING = {
        "hostname": "fqdn",  # If Unicorn uses 'fqdn' instead of 'hostname'
        "ip_address": "primary_ip",
        "location": "datacenter",
        "network_zone": "security_zone",
        "platform": "virtualization",
        "os_type": "os"
    }
    
    def _normalize_host(self, raw_host: Dict) -> Dict:
        """Map API fields to expected fields"""
        return {
            standard_field: raw_host.get(api_field)
            for standard_field, api_field in self.FIELD_MAPPING.items()
        }
    
    async def get_application_hosts(self, application_name: str) -> List[Dict]:
        response = await self._make_request(...)
        raw_hosts = response.get("data", {}).get("hosts", [])
        
        # Normalize field names
        return [self._normalize_host(host) for host in raw_hosts]
```

## Error Handling

Add proper error handling for production:

```python
from typing import Optional
import logging

logger = logging.getLogger(__name__)

async def get_application_hosts(self, application_name: str) -> List[Dict]:
    """Get hosts for application with error handling"""
    try:
        response = await self._make_request(
            "applications",
            params={"name": application_name}
        )
        
        # Validate response
        if "error" in response:
            logger.error(f"API returned error: {response.get('error')}")
            raise ValueError(f"Unicorn API error: {response.get('error')}")
        
        hosts = response.get("data", {}).get("hosts", [])
        
        if not hosts:
            logger.warning(f"No hosts found for application: {application_name}")
        
        return hosts
        
    except aiohttp.ClientError as e:
        logger.error(f"Network error calling Unicorn API: {str(e)}")
        raise ConnectionError(f"Failed to connect to Unicorn API: {str(e)}")
    
    except ValueError as e:
        logger.error(f"Invalid response from Unicorn API: {str(e)}")
        raise
    
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise RuntimeError(f"Failed to get application hosts: {str(e)}")
```

## Testing Your Integration

Create a test script:

```python
# test_integration.py
import asyncio
from api_clients.unicorn_client import UnicornClient
from api_clients.illumio_client import IllumioClient
from config import settings

async def test_unicorn():
    """Test Unicorn integration"""
    client = UnicornClient(settings.UNICORN_API_URL, settings.UNICORN_API_KEY)
    
    # Test application search
    print("Testing application search...")
    hosts = await client.get_application_hosts("TestApp")
    print(f"Found {len(hosts)} hosts")
    for host in hosts:
        print(f"  - {host.get('hostname')}: {host.get('ip_address')}")
    
    # Test host search
    print("\nTesting host search...")
    host = await client.get_host_info("server01.example.com")
    print(f"Host: {host}")

async def test_illumio():
    """Test Illumio integration"""
    client = IllumioClient(settings.ILLUMIO_API_URL, settings.ILLUMIO_API_KEY)
    
    # Test workload info
    print("Testing workload info...")
    workload = await client.get_workload_info("server01.example.com")
    print(f"Workload: {workload}")
    
    # Test policy check
    print("\nTesting policy check...")
    result = await client.policy_check("10.1.1.10", "10.2.2.20", 443, "TCP")
    print(f"Policy check result: {result}")

if __name__ == "__main__":
    asyncio.run(test_unicorn())
    asyncio.run(test_illumio())
```

Run tests:
```bash
cd backend
python test_integration.py
```

## Common Integration Issues

### Issue 1: SSL Certificate Verification

If your APIs use self-signed certificates:

```python
import ssl

async def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
    # Create SSL context that doesn't verify certificates
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    connector = aiohttp.TCPConnector(ssl=ssl_context)
    
    async with aiohttp.ClientSession(connector=connector) as session:
        # ... rest of request code
```

### Issue 2: Timeout Issues

Increase timeout for slow APIs:

```python
self.timeout = aiohttp.ClientTimeout(
    total=60,      # Total timeout
    connect=10,    # Connection timeout
    sock_read=30   # Socket read timeout
)
```

### Issue 3: Rate Limiting

Add retry logic with backoff:

```python
import asyncio
from functools import wraps

def retry_with_backoff(max_retries=3, backoff_factor=2):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except aiohttp.ClientError as e:
                    if attempt == max_retries - 1:
                        raise
                    wait_time = backoff_factor ** attempt
                    logger.warning(f"Request failed, retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
        return wrapper
    return decorator

@retry_with_backoff(max_retries=3)
async def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
    # ... request code
```

## Next Steps

After integrating your APIs:

1. Remove mock data functions
2. Add comprehensive error handling
3. Add logging for debugging
4. Create monitoring/alerts for API failures
5. Document your specific API endpoints and responses
6. Add integration tests
7. Update deployment documentation with API dependencies

## Getting Help

For API integration issues:

1. Check API documentation from your providers
2. Review application logs: `docker-compose logs backend`
3. Test APIs directly with curl or Postman
4. Contact API provider support teams
5. Review this project's GitHub issues (if applicable)
