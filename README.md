# Firewall Discovery Tool

A comprehensive web application to help application teams identify firewall platforms used by their infrastructure and check connectivity rules across multiple firewall solutions.

## Features

### 🔍 Firewall Discovery
- Search by **Application Name** or **Hostname**
- Automatically identifies applicable firewall platforms:
  - External Checkpoint (Perimeter)
  - Internal Checkpoint
  - Illumio (Host-Based)
  - NSX (Virtual)
- View detailed host information and firewall assignments

### 🔗 Connectivity Checking
- Check connectivity rules between source and destination
- Support for application names or hostnames
- Port and protocol specification
- View matching firewall rules (currently Illumio, more platforms coming)
- Policy decision results (Allow/Block)

## Architecture

```
┌─────────────────┐
│  React Frontend │  (Port 80)
│    (nginx)      │
└────────┬────────┘
         │
         │ HTTP/REST
         │
┌────────▼────────┐
│  FastAPI        │  (Port 8000)
│  Backend        │
└────────┬────────┘
         │
         ├─────────► Unicorn API (Inventory)
         ├─────────► Illumio API (Policy/Rules)
         ├─────────► Checkpoint API (Future)
         └─────────► NSX API (Future)
```

## Prerequisites

- Docker and Docker Compose
- API access to:
  - Unicorn (Server & Application Inventory)
  - Illumio (Policy Engine)
  - (Future) Checkpoint External & Internal
  - (Future) NSX

## Quick Start

### 1. Clone and Configure

```bash
# Navigate to project directory
cd firewall-discovery-tool

# Copy environment template
cp backend/.env.example backend/.env

# Edit backend/.env with your API credentials
nano backend/.env
```

### 2. Configure Environment Variables

Edit `backend/.env`:

```env
# Unicorn API Configuration
UNICORN_API_URL=https://your-unicorn-api.company.com/api
UNICORN_API_KEY=your-unicorn-api-key

# Illumio API Configuration
ILLUMIO_API_URL=https://your-illumio-instance.company.com/api/v2
ILLUMIO_API_KEY=your-illumio-api-key

# Application Settings
LOG_LEVEL=INFO
API_TIMEOUT=30
```

### 3. Build and Run

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Check status
docker-compose ps
```

### 4. Access the Application

- **Frontend**: http://localhost
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## Development Setup

### Backend Development

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Development

```bash
cd frontend

# Install dependencies
npm install

# Copy environment file
cp .env.example .env

# Run development server
npm start
```

The development frontend will run on http://localhost:3000

## API Endpoints

### Health Check
```
GET /health
```

### Discover Firewalls
```
POST /api/v1/discover-firewalls
{
  "application_name": "MyApp"  // OR "hostname": "server01.example.com"
}
```

### Check Connectivity
```
POST /api/v1/check-connectivity
{
  "source": "MySourceApp",
  "destination": "MyDestApp",
  "port": 443,
  "protocol": "TCP"
}
```

## Business Logic

### Firewall Platform Detection

The tool determines applicable firewalls based on host properties from Unicorn:

| Condition | Firewall Platform |
|-----------|-------------------|
| `location = "DMZ"` | External Checkpoint |
| `network_zone = "High Risk"` | Internal Checkpoint |
| `os_type = "Windows" or "Linux"` | Illumio (Host-Based) |
| `platform = "ESX"` | NSX (Virtual) |

### Operating Modes (Illumio)

For hosts using Illumio, the tool queries the workload API to determine operating mode:
- **Enforced**: Firewall rules are actively blocking traffic
- **Visibility Only**: Rules are logged but not enforced
- **Idle**: Workload is not actively managed

## Project Structure

```
firewall-discovery-tool/
├── backend/
│   ├── api_clients/
│   │   ├── unicorn_client.py      # Unicorn API integration
│   │   └── illumio_client.py      # Illumio API integration
│   ├── services/
│   │   ├── firewall_discovery.py  # Business logic for firewall detection
│   │   └── rule_checker.py        # Connectivity rule checking
│   ├── main.py                    # FastAPI application
│   ├── config.py                  # Configuration management
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── FirewallDiscovery.js
│   │   │   └── ConnectivityCheck.js
│   │   ├── App.js
│   │   └── index.js
│   ├── public/
│   ├── package.json
│   ├── Dockerfile
│   └── nginx.conf
├── docker-compose.yml
└── README.md
```

## Updating API Responses

The application currently uses mock data for development. To integrate with real APIs:

### 1. Update Unicorn Client

Edit `backend/api_clients/unicorn_client.py`:

```python
async def get_application_hosts(self, application_name: str) -> List[Dict]:
    # Update the endpoint and response parsing
    response = await self._make_request(
        "your-actual-endpoint",
        params={"name": application_name}
    )
    
    # Parse response based on actual structure
    return response.get("data", {}).get("hosts", [])
```

### 2. Update Illumio Client

Edit `backend/api_clients/illumio_client.py`:

```python
async def policy_check(self, source: str, destination: str, port: int, protocol: str) -> Dict:
    # Update the endpoint and payload structure
    payload = {
        # Your actual Illumio API payload structure
    }
    
    response = await self._make_request(
        "your-actual-endpoint",
        method="POST",
        data=payload
    )
    
    return response
```

## Extending to Other Firewall Platforms

The architecture supports easy extension to additional firewall platforms:

### 1. Create API Client

```python
# backend/api_clients/checkpoint_client.py
class CheckpointClient:
    def __init__(self, api_url: str, api_key: str):
        # Initialize client
        pass
    
    async def check_rule(self, source, dest, port, protocol):
        # Implement API call
        pass
```

### 2. Update Rule Checker Service

```python
# backend/services/rule_checker.py
async def _check_checkpoint_external(self, ...):
    # Implement Checkpoint checking logic
    pass
```

### 3. Update Configuration

Add API credentials to `backend/config.py` and `backend/.env`

## Troubleshooting

### Backend Issues

```bash
# View backend logs
docker-compose logs backend

# Restart backend
docker-compose restart backend

# Access backend container
docker-compose exec backend /bin/bash
```

### Frontend Issues

```bash
# View frontend logs
docker-compose logs frontend

# Rebuild frontend
docker-compose up -d --build frontend
```

### API Connection Issues

1. Verify API credentials in `backend/.env`
2. Check network connectivity to API endpoints
3. Review API request/response in backend logs
4. Test API endpoints directly using curl or Postman

## Security Considerations

- **API Keys**: Store securely in environment variables, never commit to version control
- **HTTPS**: Configure SSL/TLS certificates for production deployment
- **Authentication**: Add user authentication (ADFS integration planned)
- **CORS**: Update CORS settings in production (currently allows all origins)
- **Network**: Deploy in secure network segment with appropriate firewall rules

## Future Enhancements

- [ ] Checkpoint External API integration
- [ ] Checkpoint Internal API integration
- [ ] NSX API integration
- [ ] User authentication (ADFS/AD integration)
- [ ] Role-based access control
- [ ] Audit logging
- [ ] Export results to PDF/CSV
- [ ] Historical connectivity analysis
- [ ] Firewall rule recommendations
- [ ] Integration with ticketing systems

## Support

For issues or questions:
1. Check the API documentation at http://localhost:8000/docs
2. Review application logs
3. Contact the infrastructure team

## License

Internal use only - [Your Organization]

## Version History

- **v1.0.0** (Current)
  - Initial release
  - Firewall discovery for applications and hosts
  - Illumio connectivity checking
  - Mock data support for development
