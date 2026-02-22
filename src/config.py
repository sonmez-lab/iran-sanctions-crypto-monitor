"""Configuration settings for Iran Sanctions Crypto Monitor."""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # App
    app_name: str = "Iran Sanctions Crypto Monitor"
    app_version: str = "0.1.0"
    debug: bool = False
    
    # API Server
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://localhost/iran_sanctions_monitor",
        description="PostgreSQL connection URL"
    )
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    
    # OFAC SDN API
    ofac_sdn_url: str = "https://www.treasury.gov/ofac/downloads/sdn.xml"
    ofac_update_interval_hours: int = 24
    
    # Blockchain APIs
    etherscan_api_key: Optional[str] = None
    etherscan_base_url: str = "https://api.etherscan.io/api"
    
    trongrid_api_key: Optional[str] = None
    trongrid_base_url: str = "https://api.trongrid.io"
    
    blockchair_api_key: Optional[str] = None
    blockchair_base_url: str = "https://api.blockchair.com"
    
    # Monitoring
    monitor_interval_minutes: int = 15
    alert_threshold_usd: float = 10000.0
    
    # Iran-specific targets
    iran_designated_exchanges: list[str] = Field(
        default=["zedcex"],
        description="Known Iran-linked exchanges"
    )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
