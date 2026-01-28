from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # API Configuration
    UNICORN_API_URL: str = "http://unicorn-api.example.com/api"
    UNICORN_API_KEY: str = "your-unicorn-api-key"
    
    ILLUMIO_API_URL: str = "https://illumio.example.com/api/v2"
    ILLUMIO_API_KEY: str = "your-illumio-api-key"
    
    # Future firewall integrations
    CHECKPOINT_EXTERNAL_API_URL: Optional[str] = None
    CHECKPOINT_EXTERNAL_API_KEY: Optional[str] = None
    
    CHECKPOINT_INTERNAL_API_URL: Optional[str] = None
    CHECKPOINT_INTERNAL_API_KEY: Optional[str] = None
    
    NSX_API_URL: Optional[str] = None
    NSX_API_KEY: Optional[str] = None
    
    # Application settings
    LOG_LEVEL: str = "INFO"
    API_TIMEOUT: int = 30
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
