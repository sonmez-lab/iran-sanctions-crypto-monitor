# Iran Sanctions Crypto Monitor

[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
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

- Real-time blockchain monitoring (BTC, ETH, TRX, USDT)
- OFAC SDN integration for Iran-designated addresses
- Transaction volume and pattern analysis
- Alert system for high-risk activity
- Dashboard with D3.js visualizations

## 🛠️ Tech Stack

- Python 3.10+
- Flask/FastAPI for API
- PostgreSQL for transaction storage
- Redis for caching
- Chart.js/D3.js for visualization
- Blockchain APIs (Etherscan, Blockchain.com, Blockchair)

## 📄 License

MIT License
