#!/usr/bin/env python
"""
Post-processing script for Proxy Scraper results
- Organizes existing results into a structured directory format
- Generates a comprehensive README.md with statistics
"""

import os
import sys
import json
import shutil
import glob
from datetime import datetime
import argparse
import re

def organize_results(base_dir="results", no_cleanup=False):
    """Organize existing proxy results into a better structure"""
    print(f"Organizing proxy results in {base_dir}...")
    
    # Create base directories for each proxy type if they don't exist
    proxy_types = ["http", "socks4", "socks5"]
    for proxy_type in proxy_types:
        os.makedirs(f"{base_dir}/{proxy_type}", exist_ok=True)
    
    # Find all JSON files
    json_files = glob.glob(f"{base_dir}/*_proxies_*.json")
    
    # Track the summary data for README generation
    summary = {}
    
    # Process each JSON file
    for json_file in json_files:
        filename = os.path.basename(json_file)
        
        # Extract proxy type and timestamp from filename
        match = re.search(r"(.*?)_proxies_(\d{8}_\d{6})\.json", filename)
        if not match:
            continue
            
        proxy_type = match.group(1)
        timestamp = match.group(2)
        
        if proxy_type not in proxy_types:
            continue
            
        # Parse the date from the timestamp
        try:
            date_obj = datetime.strptime(timestamp, "%Y%m%d_%H%M%S")
            date_str = date_obj.strftime("%Y-%m-%d %H:%M:%S")
            date_dir = date_obj.strftime("%Y%m%d")
        except:
            continue
        
        # Create directories
        type_dir = f"{base_dir}/{proxy_type}"
        date_dir_path = f"{type_dir}/{date_dir}"
        time_dir = f"{date_dir_path}/{timestamp}"
        countries_dir = f"{time_dir}/countries"
        
        os.makedirs(type_dir, exist_ok=True)
        os.makedirs(date_dir_path, exist_ok=True)
        os.makedirs(time_dir, exist_ok=True)
        
        # Read the JSON data
        try:
            with open(json_file, "r") as f:
                data = json.load(f)
        except:
            print(f"Error reading {json_file}")
            continue
        
        # Extract key information
        proxies = data.get("proxies", {})
        total_found = data.get("total_found", 0)
        working = len(proxies)
        success_rate = (working / total_found * 100) if total_found > 0 else 0
        country_stats = data.get("country_distribution", {})
        
        # If using old format, recalculate country distribution
        if not country_stats and proxies:
            country_stats = {}
            for _, proxy_data in proxies.items():
                country = proxy_data.get("location", {}).get("country", "Unknown")
                if country not in country_stats:
                    country_stats[country] = 0
                country_stats[country] += 1
            
            # Sort by count
            country_stats = dict(sorted(country_stats.items(), key=lambda x: x[1], reverse=True))
        
        # Get anonymity distribution
        anonymity_stats = {}
        for _, proxy_data in proxies.items():
            anonymity = proxy_data.get("anonymity", "Unknown")
            if anonymity not in anonymity_stats:
                anonymity_stats[anonymity] = 0
            anonymity_stats[anonymity] += 1
        
        # Save to new location with better structure
        new_json_path = f"{time_dir}/{proxy_type}_proxies_{timestamp}.json"
        
        # Create new JSON with better structure
        results = {
            "metadata": {
                "timestamp": date_str,
                "type": proxy_type,
                "total_found": total_found,
                "working": working,
                "success_rate": f"{success_rate:.1f}%",
                "version": "1.2.0"
            },
            "country_distribution": country_stats,
            "anonymity_distribution": anonymity_stats,
            "proxies": proxies
        }
        
        # Write the new JSON
        with open(new_json_path, "w") as f:
            json.dump(results, f, indent=2)
        
        # Create latest.json symlink
        latest_json = f"{type_dir}/latest.json"
        if os.path.exists(latest_json):
            if os.path.islink(latest_json):
                os.remove(latest_json)
            else:
                os.rename(latest_json, f"{type_dir}/previous.json")
                
        # Use relative path for compatibility
        try:
            rel_path = os.path.relpath(new_json_path, os.path.dirname(latest_json))
            os.symlink(rel_path, latest_json)
        except:
            # Copy the file instead if symlink fails
            shutil.copy2(new_json_path, latest_json)
        
        # Generate TXT files
        txt_path = f"{time_dir}/{proxy_type}_proxies_{timestamp}.txt"
        
        # Group proxies by anonymity level
        elite_proxies = []
        anonymous_proxies = []
        transparent_proxies = []
        unknown_proxies = []
        
        for proxy, data in proxies.items():
            anonymity = data.get("anonymity", "Unknown")
            country = data.get("location", {}).get("country", "Unknown")
            latency = data.get("latency_ms", 9999)
            
            proxy_line = f"{proxy} | {country} | {anonymity} | {latency}ms"
            
            if anonymity == "Elite":
                elite_proxies.append(proxy_line)
            elif anonymity == "Anonymous":
                anonymous_proxies.append(proxy_line)
            elif anonymity == "Transparent":
                transparent_proxies.append(proxy_line)
            else:
                unknown_proxies.append(proxy_line)
        
        with open(txt_path, "w") as f:
            f.write(f"# PROXY LIST: {proxy_type.upper()} - Generated: {date_str}\n")
            f.write(f"# Total found: {total_found} | Working: {working} | ")
            f.write(f"Success rate: {success_rate:.1f}%\n")
            f.write("# Format: IP:PORT | COUNTRY | ANONYMITY | LATENCY\n")
            f.write("# ---------------------------------------------------------\n\n")
            
            f.write(f"# ELITE PROXIES ({len(elite_proxies)})\n")
            for proxy in elite_proxies:
                f.write(f"{proxy}\n")
            f.write("\n")
            
            f.write(f"# ANONYMOUS PROXIES ({len(anonymous_proxies)})\n")
            for proxy in anonymous_proxies:
                f.write(f"{proxy}\n")
            f.write("\n")
            
            f.write(f"# TRANSPARENT PROXIES ({len(transparent_proxies)})\n")
            for proxy in transparent_proxies:
                f.write(f"{proxy}\n")
            f.write("\n")
            
            if unknown_proxies:
                f.write(f"# UNKNOWN ANONYMITY PROXIES ({len(unknown_proxies)})\n")
                for proxy in unknown_proxies:
                    f.write(f"{proxy}\n")
                f.write("\n")
            
            f.write("# ---------------------------------------------------------\n")
            f.write(f"# Export path: {time_dir}/\n")
            f.write("# ProxyScraper | https://github.com/delldevmann/proxy-scraper")
        
        # Create latest.txt symlink
        latest_txt = f"{type_dir}/latest.txt"
        if os.path.exists(latest_txt):
            if os.path.islink(latest_txt):
                os.remove(latest_txt)
            else:
                os.rename(latest_txt, f"{type_dir}/previous.txt")
                
        # Use relative path for compatibility
        try:
            rel_path = os.path.relpath(txt_path, os.path.dirname(latest_txt))
            os.symlink(rel_path, latest_txt)
        except:
            # Copy the file instead if symlink fails
            shutil.copy2(txt_path, latest_txt)
        
        # Update summary for README
        summary[proxy_type] = {
            "timestamp": date_str,
            "total_found": total_found,
            "working": working,
            "success_rate": f"{success_rate:.1f}%",
            "country_distribution": dict(list(country_stats.items())[:10]),  # Top 10 countries
            "anonymity_distribution": anonymity_stats,
            "sample_proxies": dict(list(proxies.items())[:5])  # 5 sample proxies
        }
    
    # Save summary for README generation
    with open(f"{base_dir}/summary.json", "w") as f:
        json.dump(summary, f, indent=2)
    
    # Clean up old files if requested
    if not no_cleanup:
        for json_file in json_files:
            filename = os.path.basename(json_file)
            # Skip all_proxies files which contain combined results
            if filename.startswith("all_proxies_"):
                continue
            # Remove old format files
            try:
                os.remove(json_file)
                print(f"Removed old file: {json_file}")
            except:
                print(f"Failed to remove: {json_file}")
    
    return summary

def generate_readme(summary, output_file="README.md"):
    """Generate README.md with the latest proxy statistics"""
    
    if not summary:
        print("No summary data available to generate README")
        return False
    
    # Calculate totals
    total_found = sum(int(data.get("total_found", 0)) for data in summary.values())
    total_working = sum(int(data.get("working", 0)) for data in summary.values())
    success_rate = (total_working / total_found * 100) if total_found > 0 else 0
    total_success_rate = f"{success_rate:.1f}%"
    
    # Get the latest timestamp
    latest_timestamp = max([data.get("timestamp", "2000-01-01 00:00:00") for data in summary.values()])
    
    # Prepare country distribution
    all_countries = {}
    for proxy_type, data in summary.items():
        for country, count in data.get("country_distribution", {}).items():
            if country not in all_countries:
                all_countries[country] = 0
            all_countries[country] += count
    
    # Sort countries by count
    sorted_countries = sorted(all_countries.items(), key=lambda x: x[1], reverse=True)
    
    # Prepare anonymity distribution
    all_anonymity = {"Elite": 0, "Anonymous": 0, "Transparent": 0, "Unknown": 0}
    for proxy_type, data in summary.items():
        for level, count in data.get("anonymity_distribution", {}).items():
            all_anonymity[level] = all_anonymity.get(level, 0) + count
    
    # Get sample proxies (HTTP preferred, then SOCKS4, then SOCKS5)
    sample_proxies = []
    proxy_preference = ["http", "socks4", "socks5"]
    
    for proxy_type in proxy_preference:
        if proxy_type in summary and "sample_proxies" in summary[proxy_type]:
            samples = summary[proxy_type]["sample_proxies"]
            for proxy, data in samples.items():
                if len(sample_proxies) < 5:
                    sample_proxies.append({
                        "proxy": proxy,
                        "country": data.get("location", {}).get("country", "Unknown"),
                        "city": data.get("location", {}).get("city", "Unknown"),
                        "anonymity": data.get("anonymity", "Unknown"),
                        "latency": data.get("latency_ms", 9999)
                    })
    
    # Fill with placeholders if we don't have enough
    while len(sample_proxies) < 5:
        sample_proxies.append({
            "proxy": "N/A",
            "country": "N/A",
            "city": "N/A",
            "anonymity": "N/A",
            "latency": "N/A"
        })
    
    # Generate README content
    readme = f"""# Advanced Proxy Scraper

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

### Summary (Last updated: {latest_timestamp})

| Proxy Type | Total Found | Working | Success Rate | Export Path |
|------------|-------------|---------|--------------|-------------|
"""
    
    # Add rows for each proxy type
    for proxy_type in ["http", "socks4", "socks5"]:
        if proxy_type in summary:
            data = summary[proxy_type]
            readme += f"| {proxy_type.upper()} | {int(data.get('total_found', 0)):,} | {int(data.get('working', 0)):,} | {data.get('success_rate', '0%')} | [results/{proxy_type}](results/{proxy_type}/) |\n"
        else:
            readme += f"| {proxy_type.upper()} | 0 | 0 | 0% | [results/{proxy_type}](results/{proxy_type}/) |\n"
    
    # Add total row
    readme += f"| **TOTAL** | **{total_found:,}** | **{total_working:,}** | **{total_success_rate}** | [results/](results/) |\n\n"
    
    # Add country distribution
    readme += """### Country Distribution

```
"""
    
    # Add top countries (up to 10)
    for country, count in sorted_countries[:min(9, len(sorted_countries))]:
        percentage = (count / total_working * 100) if total_working > 0 else 0
        readme += f"{country.ljust(15)}: {count} ({percentage:.1f}%)\n"
    
    # Add "Other" for the rest
    if len(sorted_countries) > 9:
        other_count = sum(count for _, count in sorted_countries[9:])
        other_percentage = (other_count / total_working * 100) if total_working > 0 else 0
        readme += f"{'Other'.ljust(15)}: {other_count} ({other_percentage:.1f}%)\n"
    
    readme += """```

### Anonymity Levels

```
"""
    
    # Add anonymity levels
    for level, count in all_anonymity.items():
        if level != "Unknown" or all_anonymity["Unknown"] > 0:  # Skip Unknown if it's 0
            percentage = (count / total_working * 100) if total_working > 0 else 0
            readme += f"{level.ljust(12)}: {count} ({percentage:.1f}%)\n"
    
    readme += """```

### Sample HTTP Proxies

| Proxy | Country | City | Anonymity | Latency |
|-------|---------|------|-----------|---------|
"""
    
    # Add sample proxies
    for proxy in sample_proxies:
        latency = f"{proxy['latency']}ms" if isinstance(proxy['latency'], (int, float)) else proxy['latency']
        readme += f"| {proxy['proxy']} | {proxy['country']} | {proxy['city']} | {proxy['anonymity']} | {latency} |\n"
    
    readme += """
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
"""

    # Write README
    with open(output_file, "w") as f:
        f.write(readme)
    
    print(f"README generated: {output_file}")
    return True

def main():
    parser = argparse.ArgumentParser(description="Post-process proxy scraper results")
    parser.add_argument("-d", "--dir", type=str, default="results",
                      help="Directory containing result files (default: results)")
    parser.add_argument("-o", "--output", type=str, default="README.md",
                      help="Output path for README.md (default: README.md)")
    parser.add_argument("--no-cleanup", action="store_true",
                      help="Don't delete original files after organizing")
    
    args = parser.parse_args()
    
    # Organize the results
    summary = organize_results(args.dir, args.no_cleanup)
    
    # Generate README
    generate_readme(summary, args.output)

if __name__ == "__main__":
    main()
