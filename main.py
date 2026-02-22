#!/usr/bin/env python3
"""
Iran Sanctions Crypto Monitor - CLI Entry Point

Real-time monitoring dashboard for OFAC-designated Iran-linked 
cryptocurrency addresses and transaction patterns.

Usage:
    python main.py serve          # Start API server
    python main.py fetch          # Fetch latest OFAC data
    python main.py monitor <addr> # Monitor specific address
    python main.py stats          # Show current stats
"""

import asyncio
import argparse
import sys
import json
from datetime import datetime

import structlog
import uvicorn

from src.config import get_settings
from src.sanctions import OFACIranFetcher
from src.monitors import IranMonitor
from src.models import BlockchainType

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer()
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
)

logger = structlog.get_logger()


async def cmd_serve(args):
    """Start the API server."""
    settings = get_settings()
    
    logger.info(
        "Starting Iran Sanctions Crypto Monitor",
        host=settings.host,
        port=settings.port,
        debug=settings.debug
    )
    
    config = uvicorn.Config(
        "src.api:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info" if not settings.debug else "debug"
    )
    server = uvicorn.Server(config)
    await server.serve()


async def cmd_fetch(args):
    """Fetch and display latest OFAC Iran designations."""
    logger.info("Fetching OFAC SDN list for Iran designations...")
    
    fetcher = OFACIranFetcher()
    try:
        addresses = await fetcher.get_iran_crypto_addresses()
        
        print(f"\n{'='*60}")
        print(f"OFAC Iran-Linked Crypto Addresses")
        print(f"{'='*60}")
        print(f"Total addresses found: {len(addresses)}")
        print(f"IRGC-linked: {len([a for a in addresses if a['is_irgc']])}")
        print(f"Exchange-linked: {len([a for a in addresses if a['is_exchange']])}")
        print(f"{'='*60}\n")
        
        # Group by blockchain
        by_blockchain = {}
        for addr in addresses:
            bc = addr["blockchain"]
            if bc not in by_blockchain:
                by_blockchain[bc] = []
            by_blockchain[bc].append(addr)
        
        for blockchain, addrs in by_blockchain.items():
            print(f"\n{blockchain.upper()} ({len(addrs)} addresses):")
            for addr in addrs[:5]:  # Show first 5
                flags = []
                if addr["is_irgc"]:
                    flags.append("IRGC")
                if addr["is_exchange"]:
                    flags.append("Exchange")
                flag_str = f" [{', '.join(flags)}]" if flags else ""
                print(f"  • {addr['address'][:42]}...{flag_str}")
                print(f"    Entity: {addr['sdn_name'][:50]}...")
            
            if len(addrs) > 5:
                print(f"    ... and {len(addrs) - 5} more")
        
        if args.json:
            print(f"\n{json.dumps(addresses, indent=2)}")
            
    finally:
        await fetcher.close()


async def cmd_monitor(args):
    """Monitor a specific address."""
    logger.info(f"Monitoring address: {args.address}")
    
    try:
        bc_type = BlockchainType(args.blockchain)
    except ValueError:
        print(f"Error: Invalid blockchain '{args.blockchain}'")
        print(f"Valid options: {', '.join(e.value for e in BlockchainType)}")
        sys.exit(1)
    
    monitor = IranMonitor()
    try:
        transactions = await monitor.monitor_address(args.address, bc_type)
        
        print(f"\n{'='*60}")
        print(f"Transaction History for {args.address[:20]}...")
        print(f"Blockchain: {bc_type.value}")
        print(f"{'='*60}")
        print(f"Total transactions: {len(transactions)}\n")
        
        for tx in transactions[:args.limit]:
            direction = "↑ OUT" if tx.from_address.lower() == args.address.lower() else "↓ IN"
            timestamp = tx.block_timestamp.strftime("%Y-%m-%d %H:%M") if tx.block_timestamp else "N/A"
            
            print(f"{direction} | {timestamp} | {tx.value:.6f} | {tx.tx_hash[:16]}...")
        
        if len(transactions) > args.limit:
            print(f"\n... and {len(transactions) - args.limit} more transactions")
            
    finally:
        await monitor.close()


async def cmd_stats(args):
    """Show current monitoring statistics."""
    fetcher = OFACIranFetcher()
    
    try:
        addresses = await fetcher.get_iran_crypto_addresses()
        
        # Calculate stats
        by_blockchain = {}
        for addr in addresses:
            bc = addr["blockchain"]
            by_blockchain[bc] = by_blockchain.get(bc, 0) + 1
        
        print(f"\n{'='*60}")
        print(f"Iran Sanctions Crypto Monitor - Statistics")
        print(f"Generated: {datetime.utcnow().isoformat()}")
        print(f"{'='*60}\n")
        
        print("Designated Addresses:")
        print(f"  Total: {len(addresses)}")
        for bc, count in sorted(by_blockchain.items()):
            print(f"  • {bc}: {count}")
        
        print(f"\nClassification:")
        print(f"  IRGC-linked: {len([a for a in addresses if a['is_irgc']])}")
        print(f"  Exchange-linked: {len([a for a in addresses if a['is_exchange']])}")
        
        print(f"\nPrograms:")
        programs = {}
        for addr in addresses:
            prog = addr.get("program", "Unknown")
            programs[prog] = programs.get(prog, 0) + 1
        for prog, count in sorted(programs.items(), key=lambda x: -x[1])[:5]:
            print(f"  • {prog}: {count}")
            
    finally:
        await fetcher.close()


def main():
    parser = argparse.ArgumentParser(
        description="Iran Sanctions Crypto Monitor CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # serve command
    serve_parser = subparsers.add_parser("serve", help="Start API server")
    
    # fetch command
    fetch_parser = subparsers.add_parser("fetch", help="Fetch latest OFAC data")
    fetch_parser.add_argument("--json", action="store_true", help="Output as JSON")
    
    # monitor command
    monitor_parser = subparsers.add_parser("monitor", help="Monitor specific address")
    monitor_parser.add_argument("address", help="Crypto address to monitor")
    monitor_parser.add_argument(
        "--blockchain", "-b",
        default="ethereum",
        help="Blockchain type (ethereum, tron, bitcoin, usdt_erc20, usdt_trc20)"
    )
    monitor_parser.add_argument(
        "--limit", "-l",
        type=int,
        default=20,
        help="Number of transactions to show"
    )
    
    # stats command
    stats_parser = subparsers.add_parser("stats", help="Show current statistics")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Run the appropriate command
    commands = {
        "serve": cmd_serve,
        "fetch": cmd_fetch,
        "monitor": cmd_monitor,
        "stats": cmd_stats
    }
    
    asyncio.run(commands[args.command](args))


if __name__ == "__main__":
    main()
