"""Blockchain monitoring for Iran-linked addresses."""

import asyncio
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional, AsyncIterator
import httpx
import structlog
from dataclasses import dataclass

from ..config import get_settings
from ..models import BlockchainType

logger = structlog.get_logger()


@dataclass
class Transaction:
    """Parsed blockchain transaction."""
    tx_hash: str
    blockchain: BlockchainType
    from_address: str
    to_address: str
    value: Decimal
    value_usd: Optional[Decimal] = None
    block_number: int = 0
    block_timestamp: Optional[datetime] = None
    raw_data: dict = None


class EtherscanMonitor:
    """Monitor Ethereum addresses via Etherscan API."""
    
    def __init__(self):
        self.settings = get_settings()
        self.client = httpx.AsyncClient(timeout=30.0)
        self.base_url = self.settings.etherscan_base_url
        self.api_key = self.settings.etherscan_api_key
        
    async def get_transactions(
        self, 
        address: str, 
        start_block: int = 0,
        end_block: int = 99999999
    ) -> list[Transaction]:
        """Fetch transactions for an address."""
        
        params = {
            "module": "account",
            "action": "txlist",
            "address": address,
            "startblock": start_block,
            "endblock": end_block,
            "sort": "desc",
            "apikey": self.api_key or ""
        }
        
        response = await self.client.get(self.base_url, params=params)
        data = response.json()
        
        if data.get("status") != "1":
            logger.warning(f"Etherscan API error: {data.get('message')}")
            return []
        
        transactions = []
        for tx in data.get("result", []):
            transactions.append(Transaction(
                tx_hash=tx["hash"],
                blockchain=BlockchainType.ETHEREUM,
                from_address=tx["from"],
                to_address=tx["to"],
                value=Decimal(tx["value"]) / Decimal(10**18),  # Wei to ETH
                block_number=int(tx["blockNumber"]),
                block_timestamp=datetime.fromtimestamp(int(tx["timeStamp"])),
                raw_data=tx
            ))
        
        logger.info(f"Fetched {len(transactions)} ETH transactions for {address[:10]}...")
        return transactions
    
    async def get_token_transfers(
        self,
        address: str,
        contract_address: Optional[str] = None
    ) -> list[Transaction]:
        """Fetch ERC-20 token transfers (USDT, etc.)."""
        
        params = {
            "module": "account",
            "action": "tokentx",
            "address": address,
            "sort": "desc",
            "apikey": self.api_key or ""
        }
        
        if contract_address:
            params["contractaddress"] = contract_address
        
        response = await self.client.get(self.base_url, params=params)
        data = response.json()
        
        if data.get("status") != "1":
            return []
        
        transactions = []
        for tx in data.get("result", []):
            decimals = int(tx.get("tokenDecimal", 18))
            transactions.append(Transaction(
                tx_hash=tx["hash"],
                blockchain=BlockchainType.USDT_ERC20 if "usdt" in tx.get("tokenSymbol", "").lower() else BlockchainType.ETHEREUM,
                from_address=tx["from"],
                to_address=tx["to"],
                value=Decimal(tx["value"]) / Decimal(10**decimals),
                block_number=int(tx["blockNumber"]),
                block_timestamp=datetime.fromtimestamp(int(tx["timeStamp"])),
                raw_data=tx
            ))
        
        return transactions
    
    async def close(self):
        await self.client.aclose()


class TrongridMonitor:
    """Monitor Tron addresses via TronGrid API."""
    
    # USDT TRC-20 contract address
    USDT_CONTRACT = "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t"
    
    def __init__(self):
        self.settings = get_settings()
        self.client = httpx.AsyncClient(timeout=30.0)
        self.base_url = self.settings.trongrid_base_url
        self.api_key = self.settings.trongrid_api_key
        
    async def get_transactions(self, address: str, limit: int = 50) -> list[Transaction]:
        """Fetch TRX transactions for an address."""
        
        headers = {}
        if self.api_key:
            headers["TRON-PRO-API-KEY"] = self.api_key
        
        url = f"{self.base_url}/v1/accounts/{address}/transactions"
        params = {"limit": limit, "only_confirmed": "true"}
        
        response = await self.client.get(url, params=params, headers=headers)
        data = response.json()
        
        transactions = []
        for tx in data.get("data", []):
            raw_data = tx.get("raw_data", {})
            contract = raw_data.get("contract", [{}])[0]
            
            if contract.get("type") == "TransferContract":
                value_data = contract.get("parameter", {}).get("value", {})
                transactions.append(Transaction(
                    tx_hash=tx["txID"],
                    blockchain=BlockchainType.TRON,
                    from_address=value_data.get("owner_address", ""),
                    to_address=value_data.get("to_address", ""),
                    value=Decimal(value_data.get("amount", 0)) / Decimal(10**6),
                    block_timestamp=datetime.fromtimestamp(tx.get("block_timestamp", 0) / 1000),
                    raw_data=tx
                ))
        
        logger.info(f"Fetched {len(transactions)} TRX transactions for {address[:10]}...")
        return transactions
    
    async def get_trc20_transfers(self, address: str, limit: int = 50) -> list[Transaction]:
        """Fetch TRC-20 (USDT) transfers."""
        
        headers = {}
        if self.api_key:
            headers["TRON-PRO-API-KEY"] = self.api_key
        
        url = f"{self.base_url}/v1/accounts/{address}/transactions/trc20"
        params = {"limit": limit, "only_confirmed": "true"}
        
        response = await self.client.get(url, params=params, headers=headers)
        data = response.json()
        
        transactions = []
        for tx in data.get("data", []):
            token_info = tx.get("token_info", {})
            decimals = int(token_info.get("decimals", 6))
            
            transactions.append(Transaction(
                tx_hash=tx["transaction_id"],
                blockchain=BlockchainType.USDT_TRC20,
                from_address=tx.get("from", ""),
                to_address=tx.get("to", ""),
                value=Decimal(tx.get("value", 0)) / Decimal(10**decimals),
                block_timestamp=datetime.fromtimestamp(tx.get("block_timestamp", 0) / 1000),
                raw_data=tx
            ))
        
        return transactions
    
    async def close(self):
        await self.client.aclose()


class BlockchairMonitor:
    """Monitor Bitcoin addresses via Blockchair API."""
    
    def __init__(self):
        self.settings = get_settings()
        self.client = httpx.AsyncClient(timeout=30.0)
        self.base_url = self.settings.blockchair_base_url
        self.api_key = self.settings.blockchair_api_key
        
    async def get_address_info(self, address: str) -> dict:
        """Get address balance and transaction count."""
        
        url = f"{self.base_url}/bitcoin/dashboards/address/{address}"
        params = {}
        if self.api_key:
            params["key"] = self.api_key
        
        response = await self.client.get(url, params=params)
        data = response.json()
        
        addr_data = data.get("data", {}).get(address, {}).get("address", {})
        return {
            "balance": Decimal(addr_data.get("balance", 0)) / Decimal(10**8),
            "tx_count": addr_data.get("transaction_count", 0),
            "received": Decimal(addr_data.get("received", 0)) / Decimal(10**8),
            "spent": Decimal(addr_data.get("spent", 0)) / Decimal(10**8)
        }
    
    async def close(self):
        await self.client.aclose()


class IranMonitor:
    """Combined monitor for Iran-linked addresses."""
    
    def __init__(self):
        self.etherscan = EtherscanMonitor()
        self.trongrid = TrongridMonitor()
        self.blockchair = BlockchairMonitor()
        self.settings = get_settings()
        
    async def monitor_address(
        self, 
        address: str, 
        blockchain: BlockchainType
    ) -> list[Transaction]:
        """Monitor a single address based on blockchain type."""
        
        if blockchain == BlockchainType.ETHEREUM:
            return await self.etherscan.get_transactions(address)
        elif blockchain == BlockchainType.USDT_ERC20:
            return await self.etherscan.get_token_transfers(address)
        elif blockchain == BlockchainType.TRON:
            return await self.trongrid.get_transactions(address)
        elif blockchain == BlockchainType.USDT_TRC20:
            return await self.trongrid.get_trc20_transfers(address)
        elif blockchain == BlockchainType.BITCOIN:
            # Bitcoin doesn't return transactions list easily, return empty
            info = await self.blockchair.get_address_info(address)
            logger.info(f"BTC address {address[:10]}... balance: {info['balance']} BTC")
            return []
        
        return []
    
    async def monitor_all(
        self, 
        addresses: list[dict]
    ) -> dict[str, list[Transaction]]:
        """Monitor multiple addresses concurrently."""
        
        results = {}
        tasks = []
        
        for addr_info in addresses:
            address = addr_info["address"]
            blockchain = BlockchainType(addr_info["blockchain"])
            tasks.append((address, self.monitor_address(address, blockchain)))
        
        for address, task in tasks:
            try:
                results[address] = await task
            except Exception as e:
                logger.error(f"Failed to monitor {address}: {e}")
                results[address] = []
        
        total_txs = sum(len(txs) for txs in results.values())
        logger.info(f"Monitored {len(addresses)} addresses, found {total_txs} transactions")
        
        return results
    
    async def close(self):
        await asyncio.gather(
            self.etherscan.close(),
            self.trongrid.close(),
            self.blockchair.close()
        )


async def main():
    """Test the blockchain monitor."""
    monitor = IranMonitor()
    
    # Test with a sample ETH address
    test_addresses = [
        {"address": "0x742d35Cc6634C0532925a3b844Bc9e7595f2bD4e", "blockchain": "ethereum"}
    ]
    
    try:
        results = await monitor.monitor_all(test_addresses)
        for addr, txs in results.items():
            print(f"\n{addr[:20]}...: {len(txs)} transactions")
    finally:
        await monitor.close()


if __name__ == "__main__":
    asyncio.run(main())
