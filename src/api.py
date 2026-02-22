"""FastAPI application for Iran Sanctions Crypto Monitor."""

from datetime import datetime
from typing import Optional
from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import structlog

from .config import get_settings, Settings
from .sanctions import OFACIranFetcher
from .monitors import IranMonitor

logger = structlog.get_logger()

# Initialize FastAPI app
app = FastAPI(
    title="Iran Sanctions Crypto Monitor",
    description="Real-time monitoring for OFAC-designated Iran-linked cryptocurrency addresses",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models for API
class AddressInfo(BaseModel):
    address: str
    blockchain: str
    sdn_name: Optional[str] = None
    sdn_id: Optional[str] = None
    program: Optional[str] = None
    is_irgc: bool = False
    is_exchange: bool = False


class TransactionInfo(BaseModel):
    tx_hash: str
    blockchain: str
    from_address: str
    to_address: str
    value: str
    value_usd: Optional[str] = None
    block_timestamp: Optional[datetime] = None
    direction: Optional[str] = None
    risk_score: Optional[float] = None


class MonitoringStats(BaseModel):
    total_addresses: int
    active_addresses: int
    total_transactions: int
    total_volume_usd: str
    irgc_related_count: int
    zedcex_count: int
    last_updated: datetime


class AlertInfo(BaseModel):
    id: int
    alert_type: str
    severity: str
    title: str
    description: Optional[str] = None
    created_at: datetime


# Global instances (in production, use dependency injection)
ofac_fetcher: Optional[OFACIranFetcher] = None
iran_monitor: Optional[IranMonitor] = None


@app.on_event("startup")
async def startup():
    """Initialize services on startup."""
    global ofac_fetcher, iran_monitor
    ofac_fetcher = OFACIranFetcher()
    iran_monitor = IranMonitor()
    logger.info("Iran Sanctions Crypto Monitor started")


@app.on_event("shutdown")
async def shutdown():
    """Cleanup on shutdown."""
    if ofac_fetcher:
        await ofac_fetcher.close()
    if iran_monitor:
        await iran_monitor.close()
    logger.info("Iran Sanctions Crypto Monitor stopped")


# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.utcnow()}


# OFAC/Sanctions endpoints
@app.get("/api/v1/sanctions/addresses", response_model=list[AddressInfo])
async def get_designated_addresses(
    blockchain: Optional[str] = Query(None, description="Filter by blockchain type"),
    irgc_only: bool = Query(False, description="Only IRGC-linked addresses"),
    exchange_only: bool = Query(False, description="Only exchange addresses"),
    limit: int = Query(100, le=1000)
):
    """Get list of OFAC-designated Iran-linked crypto addresses."""
    
    addresses = await ofac_fetcher.get_iran_crypto_addresses()
    
    # Apply filters
    if blockchain:
        addresses = [a for a in addresses if a["blockchain"] == blockchain]
    if irgc_only:
        addresses = [a for a in addresses if a["is_irgc"]]
    if exchange_only:
        addresses = [a for a in addresses if a["is_exchange"]]
    
    return [AddressInfo(**addr) for addr in addresses[:limit]]


@app.get("/api/v1/sanctions/refresh")
async def refresh_sanctions_list():
    """Force refresh of OFAC sanctions list."""
    try:
        addresses = await ofac_fetcher.get_iran_crypto_addresses()
        return {
            "status": "success",
            "addresses_count": len(addresses),
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Monitoring endpoints
@app.get("/api/v1/monitor/address/{address}", response_model=list[TransactionInfo])
async def monitor_address(
    address: str,
    blockchain: str = Query("ethereum", description="Blockchain type"),
    limit: int = Query(50, le=200)
):
    """Get recent transactions for a specific address."""
    
    from .models import BlockchainType
    
    try:
        bc_type = BlockchainType(blockchain)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid blockchain: {blockchain}")
    
    transactions = await iran_monitor.monitor_address(address, bc_type)
    
    return [
        TransactionInfo(
            tx_hash=tx.tx_hash,
            blockchain=tx.blockchain.value,
            from_address=tx.from_address,
            to_address=tx.to_address,
            value=str(tx.value),
            value_usd=str(tx.value_usd) if tx.value_usd else None,
            block_timestamp=tx.block_timestamp,
            direction="outgoing" if tx.from_address.lower() == address.lower() else "incoming",
            risk_score=tx.risk_score if hasattr(tx, 'risk_score') else None
        )
        for tx in transactions[:limit]
    ]


@app.post("/api/v1/monitor/batch")
async def monitor_batch(addresses: list[dict]):
    """Monitor multiple addresses in batch."""
    
    results = await iran_monitor.monitor_all(addresses)
    
    return {
        "addresses_monitored": len(addresses),
        "transactions_found": sum(len(txs) for txs in results.values()),
        "results": {
            addr: len(txs) for addr, txs in results.items()
        }
    }


# Statistics endpoints
@app.get("/api/v1/stats", response_model=MonitoringStats)
async def get_stats():
    """Get current monitoring statistics."""
    
    # In production, this would query the database
    addresses = await ofac_fetcher.get_iran_crypto_addresses()
    
    return MonitoringStats(
        total_addresses=len(addresses),
        active_addresses=0,  # Would come from DB
        total_transactions=0,
        total_volume_usd="0",
        irgc_related_count=len([a for a in addresses if a.get("is_irgc")]),
        zedcex_count=len([a for a in addresses if a.get("is_exchange")]),
        last_updated=datetime.utcnow()
    )


# Alerts endpoints
@app.get("/api/v1/alerts", response_model=list[AlertInfo])
async def get_alerts(
    severity: Optional[str] = Query(None),
    unacknowledged_only: bool = Query(True),
    limit: int = Query(50, le=200)
):
    """Get monitoring alerts."""
    # In production, this would query the database
    return []


@app.post("/api/v1/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: int, acknowledged_by: str = Query(...)):
    """Acknowledge an alert."""
    # In production, this would update the database
    return {"status": "acknowledged", "alert_id": alert_id}


# Dashboard data endpoint
@app.get("/api/v1/dashboard")
async def get_dashboard_data():
    """Get aggregated data for dashboard visualization."""
    
    addresses = await ofac_fetcher.get_iran_crypto_addresses()
    
    # Group by blockchain
    by_blockchain = {}
    for addr in addresses:
        bc = addr["blockchain"]
        if bc not in by_blockchain:
            by_blockchain[bc] = 0
        by_blockchain[bc] += 1
    
    return {
        "total_addresses": len(addresses),
        "by_blockchain": by_blockchain,
        "irgc_count": len([a for a in addresses if a.get("is_irgc")]),
        "exchange_count": len([a for a in addresses if a.get("is_exchange")]),
        "recent_designations": [],  # Would come from DB
        "high_activity_addresses": [],  # Would come from monitoring
        "last_updated": datetime.utcnow()
    }


def create_app() -> FastAPI:
    """Factory function for creating the app."""
    return app
