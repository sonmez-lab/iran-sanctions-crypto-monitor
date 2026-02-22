"""Database models for Iran Sanctions Crypto Monitor."""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional
from sqlalchemy import (
    Column, String, DateTime, Numeric, Boolean, 
    Integer, ForeignKey, Text, Index, Enum as SQLEnum
)
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy.dialects.postgresql import JSONB


class Base(DeclarativeBase):
    """Base class for all models."""
    pass


class BlockchainType(str, Enum):
    """Supported blockchain types."""
    BITCOIN = "bitcoin"
    ETHEREUM = "ethereum"
    TRON = "tron"
    USDT_ERC20 = "usdt_erc20"
    USDT_TRC20 = "usdt_trc20"


class AlertSeverity(str, Enum):
    """Alert severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class DesignatedAddress(Base):
    """OFAC-designated Iran-linked cryptocurrency addresses."""
    
    __tablename__ = "designated_addresses"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    address = Column(String(128), unique=True, nullable=False, index=True)
    blockchain = Column(SQLEnum(BlockchainType), nullable=False)
    
    # OFAC designation info
    sdn_name = Column(String(512))
    sdn_id = Column(String(64))
    designation_date = Column(DateTime)
    designation_program = Column(String(128))  # e.g., "IRAN", "IRGC"
    
    # Entity info
    entity_name = Column(String(256))  # e.g., "Zedcex Exchange"
    entity_type = Column(String(64))   # e.g., "exchange", "wallet", "individual"
    
    # Iran-specific
    irgc_linked = Column(Boolean, default=False)
    zedcex_linked = Column(Boolean, default=False)
    
    # Metadata
    notes = Column(Text)
    metadata = Column(JSONB, default={})
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    transactions = relationship("TrackedTransaction", back_populates="address_record")
    
    __table_args__ = (
        Index("ix_designated_blockchain", "blockchain"),
        Index("ix_designated_irgc", "irgc_linked"),
    )


class TrackedTransaction(Base):
    """Transactions involving designated addresses."""
    
    __tablename__ = "tracked_transactions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    tx_hash = Column(String(128), unique=True, nullable=False, index=True)
    blockchain = Column(SQLEnum(BlockchainType), nullable=False)
    
    # Transaction details
    from_address = Column(String(128), index=True)
    to_address = Column(String(128), index=True)
    value = Column(Numeric(36, 18))
    value_usd = Column(Numeric(18, 2))
    
    # Block info
    block_number = Column(Integer)
    block_timestamp = Column(DateTime)
    
    # Designation link
    designated_address_id = Column(Integer, ForeignKey("designated_addresses.id"))
    address_record = relationship("DesignatedAddress", back_populates="transactions")
    
    # Analysis
    direction = Column(String(16))  # "incoming", "outgoing"
    risk_score = Column(Numeric(5, 2))  # 0-100
    
    # Metadata
    raw_data = Column(JSONB, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index("ix_tx_timestamp", "block_timestamp"),
        Index("ix_tx_value_usd", "value_usd"),
    )


class Alert(Base):
    """Alerts generated from monitoring."""
    
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    alert_type = Column(String(64), nullable=False)  # "high_value", "new_activity", "pattern"
    severity = Column(SQLEnum(AlertSeverity), default=AlertSeverity.MEDIUM)
    
    # Alert details
    title = Column(String(256), nullable=False)
    description = Column(Text)
    
    # Related records
    designated_address_id = Column(Integer, ForeignKey("designated_addresses.id"))
    transaction_id = Column(Integer, ForeignKey("tracked_transactions.id"))
    
    # Status
    is_acknowledged = Column(Boolean, default=False)
    acknowledged_at = Column(DateTime)
    acknowledged_by = Column(String(64))
    
    # Metadata
    metadata = Column(JSONB, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index("ix_alert_severity", "severity"),
        Index("ix_alert_unack", "is_acknowledged"),
    )


class MonitoringStats(Base):
    """Daily monitoring statistics."""
    
    __tablename__ = "monitoring_stats"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(DateTime, nullable=False, index=True)
    
    # Counts
    total_addresses_monitored = Column(Integer, default=0)
    active_addresses = Column(Integer, default=0)
    new_transactions = Column(Integer, default=0)
    
    # Values
    total_volume_usd = Column(Numeric(18, 2), default=0)
    largest_tx_usd = Column(Numeric(18, 2), default=0)
    
    # Iran-specific
    irgc_related_volume = Column(Numeric(18, 2), default=0)
    zedcex_volume = Column(Numeric(18, 2), default=0)
    
    # Alerts
    alerts_generated = Column(Integer, default=0)
    critical_alerts = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
