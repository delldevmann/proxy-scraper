# Bob's Proxy Bopper

![GitHub last commit](https://img.shields.io/github/last-commit/delldevmann/proxy-scraper)
![GitHub issues](https://img.shields.io/github/issues/delldevmann/proxy-scraper)
![Python version](https://img.shields.io/badge/python-3.7%2B-blue)
![License](https://img.shields.io/github/license/delldevmann/proxy-scraper)

Agent Bob scrapes and validates tagging geolocation via the AS registration. Automatically fetches, validates, and exports proxies with detailed information about their location, anonymity level, and performance metrics.

## Features

- 🔍 **Multi-source collection**: Fetches proxies from multiple reliable sources
- ✅ **Thorough validation**: Tests each proxy for connectivity, anonymity, and latency
- 🌎 **Geolocation data**: Provides country, city, and ISP information
- 🔒 **Anonymity detection**: Classifies proxies as Elite, Anonymous, or Transparent
- 📊 **Detailed statistics**: Generates comprehensive reports on proxy distribution
- 📂 **Multiple export formats**: Supports JSON, CSV, and TXT output formats
- ⚡ **Highly concurrent**: Efficiently processes thousands of proxies in minutes
- 🔄 **Automated updates**: Can be scheduled to keep proxy lists fresh

## Latest Results

### Summary (Last updated: 2025-03-01 12:40:03)

| Proxy Type | Total Found | Working | Success Rate | Export Path |
|------------|-------------|---------|--------------|-------------|
| HTTP | 30,939 | 381 | 1.2% | [results/http](results/http/) |
| SOCKS4 | 2,698 | 183 | 6.8% | [results/socks4](results/socks4/) |
| SOCKS5 | 1,901 | 203 | 10.7% | [results/socks5](results/socks5/) |
| **TOTAL** | **35,538** | **767** | **2.2%** | [results/](results/) |

### Country Distribution

```
United States  : 207 (27.0%)
China          : 59 (7.7%)
Germany        : 53 (6.9%)
United Kingdom : 44 (5.7%)
India          : 40 (5.2%)
France         : 37 (4.8%)
Japan          : 29 (3.8%)
South Korea    : 25 (3.3%)
Brazil         : 17 (2.2%)
Other          : 39 (5.1%)
```

### Anonymity Levels

```
Elite       : 18 (2.3%)
Anonymous   : 3 (0.4%)
Transparent : 63 (8.2%)
Unknown     : 683 (89.0%)
```

### Sample HTTP Proxies

| Proxy | Country | City | Anonymity | Latency |
|-------|---------|------|-----------|---------|
| 80.249.112.163:80 | China | Guangzhou | Unknown | 466ms |
| 8.211.195.173:80 | United Kingdom | London | Unknown | 2257ms |
| 72.10.160.91:14595 | India | Chennai | Unknown | 9999ms |
| 8.209.96.245:5060 | Germany | Frankfurt am Main | Unknown | 9999ms |
| 13.38.153.36:80 | France | Paris | Unknown | 270ms |

[View all HTTP proxies](results/http/latest.txt) • [View all SOCKS4 proxies](results/socks4/latest.txt) • [View all SOCKS5 proxies](results/socks5/latest.txt)

## Installation

```bash
# Clone the repository
git clone https://github.com/delldevmann/proxy-scraper.git
cd proxy-scraper

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Basic Usage

```bash
python scraper.py
```

This will scrape all proxy types and save them to the `results` directory in JSON format.

### Advanced Options

```bash
# Scrape only HTTP proxies with a 5-second timeout
python scraper.py -t http --timeout 5

# Scrape SOCKS5 proxies with higher concurrency and export as CSV
python scraper.py -t socks5 -c 200 -f csv

# Scrape all proxy types but limit to finding 500 working proxies
python scraper.py -m 500

# Full options
python scraper.py [-t TYPE] [-c CONCURRENT] [--timeout SECONDS] 
                [-o OUTPUT_DIR] [-f FORMAT] [-v] [-m MAX]
                [--no-anonymity]
```

### Command Line Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `-t, --type` | Proxy type to scrape (http, socks4, socks5, all) | all |
| `-c, --concurrent` | Maximum concurrent connections | 100 |
| `--timeout` | Connection timeout in seconds | 3 |
| `-o, --output` | Output directory for results | results |
| `-f, --format` | Output format (json, txt, csv, all) | json |
| `-v, --verbose` | Enable verbose output | False |
| `-m, --max` | Maximum number of proxies to find | None |
| `--no-anonymity` | Disable anonymity checking | False |

## Automated Updates

This repository automatically updates proxy lists every 6 hours using GitHub Actions.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
