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

def organize_and_sort_results(base_dir="results", no_cleanup=False):
    """Organize and sort proxy results into a structured directory format."""
    print(f"[INFO] Organizing proxy results in {base_dir}. Sorting by date, removing old files, and generating summaries...")

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
            date_folder = date_obj.strftime("%Y-%m-%d")
            time_folder = date_obj.strftime("%H-%M-%S")
        except:
            continue

        # Create structured directories
        type_dir = f"{base_dir}/{proxy_type}"
        date_dir_path = f"{type_dir}/{date_folder}"
        time_dir = f"{date_dir_path}/{time_folder}"

        os.makedirs(date_dir_path, exist_ok=True)
        os.makedirs(time_dir, exist_ok=True)

        # Read the JSON data
        try:
            with open(json_file, "r") as f:
                data = json.load(f)
        except:
            print(f"[ERROR] Failed to read {json_file}. Skipping...")
            continue

        # Extract key statistics
        proxies = data.get("proxies", {})
        total_scraped = data.get("total_found", 0)
        verified_proxies = len(proxies)
        verification_success_rate = (verified_proxies / total_scraped * 100) if total_scraped > 0 else 0
        country_stats = data.get("country_distribution", {})

        # Recalculate country distribution if missing
        if not country_stats and proxies:
            country_stats = {}
            for _, proxy_data in proxies.items():
                country = proxy_data.get("location", {}).get("country", "Unknown")
                country_stats[country] = country_stats.get(country, 0) + 1
            country_stats = dict(sorted(country_stats.items(), key=lambda x: x[1], reverse=True))

        # Get anonymity distribution
        anonymity_stats = {}
        for _, proxy_data in proxies.items():
            anonymity = proxy_data.get("anonymity", "Unknown")
            anonymity_stats[anonymity] = anonymity_stats.get(anonymity, 0) + 1

        # Save to structured JSON file
        new_json_path = f"{time_dir}/{proxy_type}_proxies.json"

        results = {
            "metadata": {
                "timestamp": date_str,
                "type": proxy_type,
                "total_scraped": total_scraped,
                "verified_proxies": verified_proxies,
                "verification_success_rate": f"{verification_success_rate:.1f}%",
                "version": "1.2.0"
            },
            "country_distribution": country_stats,
            "anonymity_distribution": anonymity_stats,
            "proxies": proxies
        }

        with open(new_json_path, "w") as f:
            json.dump(results, f, indent=2)

        # Create latest.json symlink
        latest_json = f"{type_dir}/latest.json"
        if os.path.exists(latest_json):
            if os.path.islink(latest_json):
                os.remove(latest_json)
            else:
                os.rename(latest_json, f"{type_dir}/previous.json")

        try:
            rel_path = os.path.relpath(new_json_path, os.path.dirname(latest_json))
            os.symlink(rel_path, latest_json)
        except:
            shutil.copy2(new_json_path, latest_json)

        # Update summary for README
        summary[proxy_type] = {
            "timestamp": date_str,
            "total_scraped": total_scraped,
            "verified_proxies": verified_proxies,
            "verification_success_rate": f"{verification_success_rate:.1f}%",
            "country_distribution": dict(list(country_stats.items())[:10]),  # Top 10 countries
            "anonymity_distribution": anonymity_stats,
            "sample_proxies": dict(list(proxies.items())[:5])  # 5 sample proxies
        }

    # Save updated summary
    summary_path = f"{base_dir}/summary_latest.json"
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)

    # Remove old files if not disabled
    if not no_cleanup:
        for json_file in json_files:
            if "all_proxies_" in json_file:
                continue  # Skip combined results
            try:
                os.remove(json_file)
                print(f"[INFO] Removed old file: {json_file}")
            except:
                print(f"[WARNING] Failed to remove: {json_file}")

    return summary


def update_readme_with_stats(summary, output_file="README.md"):
    """Generate README.md with the latest proxy statistics"""

    if not summary:
        print("[ERROR] No summary data available to generate README.")
        return False

    latest_timestamp = max([data.get("timestamp", "2000-01-01 00:00:00") for data in summary.values()])
    
    readme = f"""# Proxy Scraper Summary

_Last Updated: {latest_timestamp}_

| Proxy Type | Total Scraped | Verified Proxies | Verification Success Rate |
|------------|--------------|------------------|--------------------------|
"""

    for proxy_type in ["http", "socks4", "socks5"]:
        if proxy_type in summary:
            data = summary[proxy_type]
            readme += f"| {proxy_type.upper()} | {data.get('total_scraped', 0):,} | {data.get('verified_proxies', 0):,} | {data.get('verification_success_rate', '0%')} |\n"
        else:
            readme += f"| {proxy_type.upper()} | 0 | 0 | 0% |\n"

    with open(output_file, "w") as f:
        f.write(readme)

    print(f"[INFO] README updated: {output_file}")
    return True


def main():
    parser = argparse.ArgumentParser(description="Post-process proxy scraper results")
    parser.add_argument("-d", "--dir", type=str, default="results", help="Directory containing result files (default: results)")
    parser.add_argument("-o", "--output", type=str, default="README.md", help="Output path for README.md (default: README.md)")
    parser.add_argument("--no-cleanup", action="store_true", help="Don't delete original files after organizing")

    args = parser.parse_args()

    # Organize results
    summary = organize_and_sort_results(args.dir, args.no_cleanup)

    # Generate README
    update_readme_with_stats(summary, args.output)


if __name__ == "__main__":
    main()
