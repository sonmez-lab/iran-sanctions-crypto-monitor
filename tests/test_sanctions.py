"""Tests for Iran Sanctions Crypto Monitor."""

import pytest
import asyncio
from datetime import datetime
from decimal import Decimal

# Test imports
from src.config import get_settings, Settings
from src.models import BlockchainType, AlertSeverity
from src.sanctions.ofac import OFACIranFetcher, IranDesignation


class TestConfig:
    """Test configuration module."""
    
    def test_settings_defaults(self):
        """Test default settings values."""
        settings = get_settings()
        
        assert settings.app_name == "Iran Sanctions Crypto Monitor"
        assert settings.port == 8000
        assert settings.monitor_interval_minutes == 15
        assert settings.alert_threshold_usd == 10000.0
    
    def test_settings_cached(self):
        """Test that settings are cached."""
        settings1 = get_settings()
        settings2 = get_settings()
        
        assert settings1 is settings2


class TestModels:
    """Test database models."""
    
    def test_blockchain_type_enum(self):
        """Test BlockchainType enum values."""
        assert BlockchainType.BITCOIN.value == "bitcoin"
        assert BlockchainType.ETHEREUM.value == "ethereum"
        assert BlockchainType.TRON.value == "tron"
        assert BlockchainType.USDT_ERC20.value == "usdt_erc20"
        assert BlockchainType.USDT_TRC20.value == "usdt_trc20"
    
    def test_alert_severity_enum(self):
        """Test AlertSeverity enum values."""
        assert AlertSeverity.LOW.value == "low"
        assert AlertSeverity.MEDIUM.value == "medium"
        assert AlertSeverity.HIGH.value == "high"
        assert AlertSeverity.CRITICAL.value == "critical"


class TestIranDesignation:
    """Test IranDesignation dataclass."""
    
    def test_basic_designation(self):
        """Test creating a basic designation."""
        designation = IranDesignation(
            sdn_id="12345",
            name="Test Entity",
            sdn_type="Entity",
            program="IRAN"
        )
        
        assert designation.sdn_id == "12345"
        assert designation.name == "Test Entity"
        assert designation.is_irgc is False
        assert designation.is_exchange is False
        assert designation.crypto_addresses == []
    
    def test_irgc_designation(self):
        """Test IRGC-linked designation."""
        designation = IranDesignation(
            sdn_id="12345",
            name="IRGC Test",
            sdn_type="Entity",
            program="IRGC",
            is_irgc=True
        )
        
        assert designation.is_irgc is True
    
    def test_exchange_designation(self):
        """Test exchange designation."""
        designation = IranDesignation(
            sdn_id="12345",
            name="Zedcex Exchange",
            sdn_type="Entity",
            program="IRAN",
            is_exchange=True,
            crypto_addresses=[
                {"address": "TXY...", "blockchain": "tron"}
            ]
        )
        
        assert designation.is_exchange is True
        assert len(designation.crypto_addresses) == 1


class TestOFACFetcher:
    """Test OFAC fetcher (mocked tests)."""
    
    def test_blockchain_type_parsing(self):
        """Test blockchain type parsing from OFAC ID types."""
        fetcher = OFACIranFetcher()
        
        assert fetcher._parse_blockchain_type("Digital Currency Address - XBT") == "bitcoin"
        assert fetcher._parse_blockchain_type("Digital Currency Address - ETH") == "ethereum"
        assert fetcher._parse_blockchain_type("Digital Currency Address - TRX") == "tron"
        assert fetcher._parse_blockchain_type("Unknown Type") == "unknown"
    
    def test_iran_programs_defined(self):
        """Test that Iran programs are defined."""
        assert "IRAN" in OFACIranFetcher.IRAN_PROGRAMS
        assert "IRGC" in OFACIranFetcher.IRAN_PROGRAMS


# Async tests
@pytest.fixture
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


class TestAsyncOperations:
    """Test async operations."""
    
    @pytest.mark.asyncio
    async def test_fetcher_initialization(self):
        """Test OFAC fetcher can be initialized."""
        fetcher = OFACIranFetcher()
        assert fetcher.client is not None
        await fetcher.close()


# Integration tests (require network)
class TestIntegration:
    """Integration tests - require network access."""
    
    @pytest.mark.skip(reason="Requires network access")
    @pytest.mark.asyncio
    async def test_fetch_ofac_list(self):
        """Test fetching actual OFAC list."""
        fetcher = OFACIranFetcher()
        try:
            addresses = await fetcher.get_iran_crypto_addresses()
            assert isinstance(addresses, list)
        finally:
            await fetcher.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
