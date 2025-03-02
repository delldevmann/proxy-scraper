# Delldevman's Proxy Scrubber

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

### Summary (Last updated: 2025-03-02 01:32:14)

| Proxy Type | Total Found | Working | Success Rate | Export Path |
|------------|-------------|---------|--------------|-------------|
| HTTP | 32,485 | 681 | 2.1% | [results/http](results/http/) |
| SOCKS4 | 2,730 | 176 | 6.4% | [results/socks4](results/socks4/) |
| SOCKS5 | 2,047 | 287 | 14.0% | [results/socks5](results/socks5/) |
| **TOTAL** | **37,262** | **1,144** | **3.1%** | [results/](results/) |

### Country Distribution

```
United States  : 307 (26.8%)
China          : 173 (15.1%)
United Kingdom : 63 (5.5%)
France         : 53 (4.6%)
Germany        : 48 (4.2%)
India          : 36 (3.1%)
Japan          : 32 (2.8%)
South Korea    : 30 (2.6%)
Russia         : 25 (2.2%)
Other          : 56 (4.9%)
```

### Anonymity Levels

```
Elite       : 91 (8.0%)
Anonymous   : 3 (0.3%)
Transparent : 138 (12.1%)
Unknown     : 912 (79.7%)
```

### Sample HTTP Proxies

| Proxy | Country | City | Anonymity | Latency |
|-------|---------|------|-----------|---------|
| 72.10.160.170:28907 | United States | Newark | Elite | 220ms |
| 42.112.22.6:80 | Vietnam | Ho Chi Minh City | Unknown | 1611ms |
| 8.209.96.245:9080 | Germany | Frankfurt am Main | Unknown | 2182ms |
| 8.212.151.166:8006 | Philippines | Manila | Unknown | 2515ms |
| 47.119.22.92:8081 | China | Shenzhen | Unknown | 2488ms |

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
