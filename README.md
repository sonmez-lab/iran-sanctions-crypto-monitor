# Iran Sanctions Crypto Monitor

[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Real-time monitoring dashboard for OFAC-designated Iran-linked cryptocurrency addresses and transaction patterns.**

## 🎯 Purpose

Iran represents one of the most significant cryptocurrency-based sanctions evasion threats, with the IRGC controlling an estimated 50% of Iran's $7.8-10B annual crypto activity. This tool monitors:

- OFAC-designated Iran-linked wallet addresses
- Transaction activity on designated addresses
- Patterns indicating sanctions evasion
- Turkey-Iran corridor transactions

## 🚨 Recent Designations

### Zedcex Exchange (January 2026)
First-ever OFAC designation of digital asset exchanges for Iran operations:
- 7 Tron wallet addresses designated
- Operating in Iran's financial sector
- Facilitating IRGC transactions

### Central Bank of Iran
- Acquired $507M USDT in 2025
- Using stablecoins to circumvent banking sanctions

## 📋 Features

- ✅ Real-time blockchain monitoring (BTC, ETH, TRX, USDT)
- ✅ OFAC SDN integration for Iran-designated addresses
- ✅ Transaction volume and pattern analysis
- ✅ Alert system for high-risk activity
- ✅ RESTful API with FastAPI
- ✅ CLI for quick operations

## 🛠️ Tech Stack

- **Python 3.10+**
- **FastAPI** - API framework
- **SQLAlchemy** - Database ORM
- **PostgreSQL** - Transaction storage
- **Redis** - Caching
- **httpx** - Async HTTP client
- **Etherscan/TronGrid/Blockchair APIs** - Blockchain data

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
cd iran-sanctions-crypto-monitor

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env
# Edit .env with your API keys
```

### CLI Usage

```bash
# Fetch latest OFAC Iran designations
python main.py fetch

# Show statistics
python main.py stats

# Monitor a specific address
python main.py monitor 0x742d35Cc6634C0532925a3b844Bc9e7595f2bD4e --blockchain ethereum

# Start API server
python main.py serve
```

### API Usage

```bash
# Start the server
python main.py serve

# API available at http://localhost:8000
# Docs at http://localhost:8000/docs
```

#### Key Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /api/v1/sanctions/addresses` | List OFAC-designated addresses |
| `GET /api/v1/monitor/address/{addr}` | Get transactions for address |
| `GET /api/v1/stats` | Monitoring statistics |
| `GET /api/v1/dashboard` | Dashboard aggregated data |

## 📁 Project Structure

```
iran-sanctions-crypto-monitor/
├── main.py                 # CLI entry point
├── requirements.txt
├── .env.example
├── src/
│   ├── __init__.py
│   ├── config.py          # Settings management
│   ├── models.py          # Database models
│   ├── api.py             # FastAPI application
│   ├── sanctions/
│   │   ├── __init__.py
│   │   └── ofac.py        # OFAC SDN parser
│   └── monitors/
│       ├── __init__.py
│       └── blockchain.py  # Blockchain monitoring
└── tests/
    └── test_sanctions.py
```

## 🔑 API Keys

For best results, configure API keys in `.env`:

- **ETHERSCAN_API_KEY** - Get from [etherscan.io](https://etherscan.io/apis)
- **TRONGRID_API_KEY** - Get from [trongrid.io](https://www.trongrid.io/)
- **BLOCKCHAIR_API_KEY** - Get from [blockchair.com](https://blockchair.com/api)

Without API keys, rate limits may apply.

## 📊 Example Output

```
$ python main.py stats

============================================================
Iran Sanctions Crypto Monitor - Statistics
Generated: 2026-02-22T07:10:00.000000
============================================================

Designated Addresses:
  Total: 47
  • bitcoin: 12
  • ethereum: 18
  • tron: 17

Classification:
  IRGC-linked: 23
  Exchange-linked: 7

Programs:
  • IRAN: 35
  • IRGC: 23
  • IRAN-EO13846: 15
```

## 🔮 Roadmap

- [ ] Real-time WebSocket updates
- [ ] D3.js visualization dashboard
- [ ] Email/Slack alerts
- [ ] Turkey-Iran corridor analysis
- [ ] Machine learning pattern detection

## 👤 Author

**Osman Sönmez**

Blockchain Security Researcher & Legal Tech Specialist | Smart Contract Auditor | Solidity Developer

Bridging the gap between legal compliance and blockchain technology. Specializing in cryptocurrency AML/CFT frameworks, smart contract security audits, and regulatory technology solutions.

- 🌐 Website: [osmansonmez.com](https://osmansonmez.com)
- 💼 LinkedIn: [linkedin.com/in/sonmezosman](https://www.linkedin.com/in/sonmezosman)
- 🔐 Focus: Blockchain Security | AML Compliance | Smart Contract Auditing

---

## 📄 License

MIT License - See [LICENSE](LICENSE) for details.

## ⚠️ Disclaimer

This tool is for research and compliance purposes only. The accuracy of OFAC data depends on the official SDN list. Always verify with official sources for compliance decisions.
