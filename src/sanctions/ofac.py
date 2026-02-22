"""OFAC SDN List integration for Iran-linked addresses."""

import asyncio
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Optional
import httpx
import structlog
from dataclasses import dataclass, field

from ..config import get_settings

logger = structlog.get_logger()


@dataclass
class IranDesignation:
    """Parsed Iran-linked OFAC designation."""
    sdn_id: str
    name: str
    sdn_type: str  # "Individual", "Entity"
    program: str   # "IRAN", "IRGC", etc.
    addresses: list[dict] = field(default_factory=list)
    aliases: list[str] = field(default_factory=list)
    remarks: str = ""
    
    # Crypto-specific
    crypto_addresses: list[dict] = field(default_factory=list)
    
    # Flags
    is_irgc: bool = False
    is_exchange: bool = False


class OFACIranFetcher:
    """Fetch and parse OFAC SDN list for Iran designations."""
    
    IRAN_PROGRAMS = ["IRAN", "IRGC", "IRAN-HR", "IRAN-TRA", "IRAN-EO13846"]
    CRYPTO_ID_TYPES = ["Digital Currency Address - XBT", "Digital Currency Address - ETH", 
                       "Digital Currency Address - USDT", "Digital Currency Address - TRX"]
    
    def __init__(self):
        self.settings = get_settings()
        self.client = httpx.AsyncClient(timeout=60.0)
        
    async def fetch_sdn_xml(self) -> str:
        """Download the latest SDN XML file."""
        logger.info("Fetching OFAC SDN list", url=self.settings.ofac_sdn_url)
        
        response = await self.client.get(self.settings.ofac_sdn_url)
        response.raise_for_status()
        
        logger.info("SDN list downloaded", size_kb=len(response.content) / 1024)
        return response.text
    
    def parse_iran_designations(self, xml_content: str) -> list[IranDesignation]:
        """Parse SDN XML and extract Iran-related designations with crypto addresses."""
        
        root = ET.fromstring(xml_content)
        ns = {"sdn": "http://www.un.org/sanctions/1.0"}
        
        iran_designations = []
        
        # Find all SDN entries
        for entry in root.findall(".//sdnEntry", ns):
            # Check if Iran-related program
            programs = entry.findall(".//program", ns)
            program_names = [p.text for p in programs if p.text]
            
            iran_programs = [p for p in program_names if any(ip in p for ip in self.IRAN_PROGRAMS)]
            
            if not iran_programs:
                continue
            
            # Extract basic info
            uid = entry.find("uid", ns)
            sdn_id = uid.text if uid is not None else ""
            
            first_name = entry.find("firstName", ns)
            last_name = entry.find("lastName", ns)
            name = " ".join(filter(None, [
                first_name.text if first_name is not None else "",
                last_name.text if last_name is not None else ""
            ]))
            
            sdn_type_elem = entry.find("sdnType", ns)
            sdn_type = sdn_type_elem.text if sdn_type_elem is not None else ""
            
            remarks_elem = entry.find("remarks", ns)
            remarks = remarks_elem.text if remarks_elem is not None else ""
            
            # Extract crypto addresses from ID list
            crypto_addresses = []
            id_list = entry.find("idList", ns)
            if id_list is not None:
                for id_entry in id_list.findall("id", ns):
                    id_type = id_entry.find("idType", ns)
                    id_number = id_entry.find("idNumber", ns)
                    
                    if id_type is not None and id_type.text in self.CRYPTO_ID_TYPES:
                        blockchain = self._parse_blockchain_type(id_type.text)
                        crypto_addresses.append({
                            "address": id_number.text if id_number is not None else "",
                            "blockchain": blockchain,
                            "id_type": id_type.text
                        })
            
            # Extract aliases
            aliases = []
            aka_list = entry.find("akaList", ns)
            if aka_list is not None:
                for aka in aka_list.findall("aka", ns):
                    aka_name = aka.find("lastName", ns)
                    if aka_name is not None and aka_name.text:
                        aliases.append(aka_name.text)
            
            # Check for IRGC
            is_irgc = any("IRGC" in p for p in iran_programs) or "IRGC" in remarks.upper()
            
            # Check for exchange (like Zedcex)
            is_exchange = "exchange" in name.lower() or "exchange" in remarks.lower()
            
            designation = IranDesignation(
                sdn_id=sdn_id,
                name=name,
                sdn_type=sdn_type,
                program=", ".join(iran_programs),
                crypto_addresses=crypto_addresses,
                aliases=aliases,
                remarks=remarks,
                is_irgc=is_irgc,
                is_exchange=is_exchange
            )
            
            iran_designations.append(designation)
        
        logger.info(
            "Parsed Iran designations",
            total=len(iran_designations),
            with_crypto=len([d for d in iran_designations if d.crypto_addresses]),
            irgc_linked=len([d for d in iran_designations if d.is_irgc])
        )
        
        return iran_designations
    
    def _parse_blockchain_type(self, id_type: str) -> str:
        """Convert OFAC ID type to blockchain enum."""
        mapping = {
            "Digital Currency Address - XBT": "bitcoin",
            "Digital Currency Address - ETH": "ethereum",
            "Digital Currency Address - USDT": "usdt_trc20",
            "Digital Currency Address - TRX": "tron"
        }
        return mapping.get(id_type, "unknown")
    
    async def get_iran_crypto_addresses(self) -> list[dict]:
        """Fetch and return all Iran-linked crypto addresses."""
        xml_content = await self.fetch_sdn_xml()
        designations = self.parse_iran_designations(xml_content)
        
        addresses = []
        for d in designations:
            for addr in d.crypto_addresses:
                addresses.append({
                    "address": addr["address"],
                    "blockchain": addr["blockchain"],
                    "sdn_id": d.sdn_id,
                    "sdn_name": d.name,
                    "program": d.program,
                    "is_irgc": d.is_irgc,
                    "is_exchange": d.is_exchange
                })
        
        return addresses
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


# Zedcex-specific addresses (January 2026 designation)
ZEDCEX_ADDRESSES = [
    {
        "address": "TXYZzedcex1...",  # Placeholder - replace with actual
        "blockchain": "tron",
        "entity": "Zedcex Exchange",
        "designation_date": "2026-01-15"
    },
    # Add more Zedcex addresses as they become public
]


async def main():
    """Test the OFAC fetcher."""
    fetcher = OFACIranFetcher()
    try:
        addresses = await fetcher.get_iran_crypto_addresses()
        print(f"Found {len(addresses)} Iran-linked crypto addresses")
        for addr in addresses[:5]:
            print(f"  - {addr['address'][:20]}... ({addr['blockchain']}) - {addr['sdn_name']}")
    finally:
        await fetcher.close()


if __name__ == "__main__":
    asyncio.run(main())
