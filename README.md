# Advanced Proxy Scraper

![GitHub last commit](https://img.shields.io/github/last-commit/delldevmann/proxy-scraper)
![GitHub issues](https://img.shields.io/github/issues/delldevmann/proxy-scraper)
![Python version](https://img.shields.io/badge/python-3.7%2B-blue)
![License](https://img.shields.io/github/license/delldevmann/proxy-scraper)

An advanced proxy scraper and validator with geolocation capabilities. Automatically fetches, validates, and exports proxies with detailed information about their location, anonymity level, and performance metrics.

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

### Summary (Last updated: 2025-03-01 18:47:45)

| Proxy Type | Total Found | Working | Success Rate | Export Path |
|------------|-------------|---------|--------------|-------------|
| HTTP | 33,744 | 608 | 1.8% | [results/http](results/http/) |
| SOCKS4 | 2,644 | 161 | 6.1% | [results/socks4](results/socks4/) |
| SOCKS5 | 2,018 | 263 | 13.0% | [results/socks5](results/socks5/) |
| **TOTAL** | **38,406** | **1,032** | **2.7%** | [results/](results/) |

### Country Distribution

```
United States  : 266 (25.8%)
China          : 162 (15.7%)
United Kingdom : 54 (5.2%)
Germany        : 51 (4.9%)
France         : 47 (4.6%)
India          : 45 (4.4%)
South Korea    : 27 (2.6%)
Japan          : 20 (1.9%)
Singapore      : 17 (1.6%)
Other          : 69 (6.7%)
```

### Anonymity Levels

```
Elite       : 46 (4.5%)
Anonymous   : 2 (0.2%)
Transparent : 108 (10.5%)
Unknown     : 876 (84.9%)
```

### Sample HTTP Proxies

| Proxy | Country | City | Anonymity | Latency |
|-------|---------|------|-----------|---------|
| 3.71.239.218:3128 | Germany | Frankfurt am Main | Unknown | 187ms |
| 185.154.194.174:3128 | United States | Boydton | Transparent | 1223ms |
| 203.89.8.107:80 | South Korea | Seoul | Unknown | 1792ms |
| 72.10.164.178:6397 | Argentina | Quilmes | Elite | 807ms |
| 47.237.92.86:86 | Singapore | Singapore | Unknown | 2473ms |

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
