import asyncio
import aiohttp
import re
import json
import time
import random
import os
import sys
import argparse
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TimeElapsedColumn, BarColumn
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.box import ROUNDED
from rich.layout import Layout
from rich.live import Live
from datetime import datetime
from urllib.parse import urlparse
from asyncio import Semaphore

console = Console()

class ProxyScraper:
    def __init__(self, max_concurrent=100, timeout=3, output_dir="results", save_format="json", 
                 verbose=False, check_anonymity=True, max_proxies=None):
        self.apis = {
            'http': [
                "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt",
                "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/all.txt",
                "https://raw.githubusercontent.com/ErcinDedeoglu/proxies/main/proxies/http.txt",
                "https://raw.githubusercontent.com/ErcinDedeoglu/proxies/main/proxies/https.txt",
                "https://cdn.jsdelivr.net/gh/proxifly/free-proxy-list@main/proxies/all/data.json",
                "https://api.proxyscrape.com/?request=getproxies&proxytype=http"
            ],
            'socks4': [
                "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/socks4.txt",
                "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks4.txt",
                "https://api.proxyscrape.com/?request=getproxies&proxytype=socks4"
            ],
            'socks5': [
                "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/socks5.txt",
                "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks5.txt",
                "https://api.proxyscrape.com/?request=getproxies&proxytype=socks5"
            ]
        }
        self.test_url = "http://httpbin.org/ip"
        self.socks5_test_urls = [
            "http://httpbin.org/ip",
            "http://ip-api.com/json/",
            "http://ifconfig.me/ip"
        ]
        self.anonymity_test_url = "http://ip-api.com/json/"
        self.timeout = timeout
        # Custom timeouts for different proxy types
        self.timeouts = {
            'http': timeout,
            'socks4': timeout,
            'socks5': 10  # Longer timeout for SOCKS5
        }
        self.semaphore = Semaphore(max_concurrent)
        self.proxy_pattern = re.compile(r"\d{1,3}(?:\.\d{1,3}){3}(?::\d{1,5})?")
        self.headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124"}
        self.ip_info_cache = {}  # Cache IP geolocation results
        self.output_dir = output_dir
        self.save_format = save_format
        self.verbose = verbose
        self.check_anonymity = check_anonymity
        self.max_proxies = max_proxies
        self.real_ip = None  # Will be set during initialization
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)

    async def get_real_ip(self):
        """Get our real IP address"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("http://ip-api.com/json/") as response:
                    data = await response.json()
                    if data.get("status") == "success":
                        self.real_ip = data.get("query")
                        return data
        except Exception as e:
            if self.verbose:
                console.print(f"[red]Error getting real IP: {e}")
        return {"query": "Unknown"}

    async def check_proxy(self, proxy: str, proxy_type: str, working_proxies, connector):
        proxy_url = f"{proxy_type}://{proxy}"
        timeout = self.timeouts.get(proxy_type, self.timeout)
        
        try:
            async with aiohttp.ClientSession(connector=connector, connector_owner=False) as session:
                # Choose test URL based on proxy type
                test_urls = self.socks5_test_urls if proxy_type == 'socks5' else [self.test_url]
                
                for test_url in test_urls:
                    try:
                        # Test if proxy works
                        async with session.get(
                            test_url, 
                            proxy=proxy_url, 
                            headers=self.headers, 
                            ssl=False,
                            timeout=timeout
                        ) as response:
                            if response.status == 200:
                                # Get IP from proxy response
                                try:
                                    response_data = await response.json()
                                    detected_ip = response_data.get("origin", "").split(", ")[0]
                                    if not detected_ip:
                                        detected_ip = response_data.get("query", "")
                                except:
                                    detected_ip = proxy.split(':')[0]
                                
                                # Get geolocation data
                                location = await self.get_ip_info(detected_ip, session)
                                
                                # Check proxy anonymity if enabled
                                anonymity_level = "Unknown"
                                if self.check_anonymity and self.real_ip:
                                    anonymity_level = await self.check_anonymity_level(proxy, proxy_type, detected_ip, session)
                                
                                # Calculate latency
                                latency = await self.measure_latency(proxy, proxy_type, session)
                                
                                # Store working proxy with all data
                                working_proxies[proxy] = {
                                    "ip": detected_ip,
                                    "type": proxy_type,
                                    "anonymity": anonymity_level,
                                    "latency_ms": latency,
                                    "last_checked": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                    "location": location
                                }
                                return True
                    except:
                        continue  # Try next test URL if this one fails
        except:
            pass
        return False

    async def check_anonymity_level(self, proxy, proxy_type, detected_ip, session):
        """Check the anonymity level of a proxy"""
        try:
            if detected_ip != self.real_ip:
                # Try to see if our real IP is exposed in the headers
                proxy_url = f"{proxy_type}://{proxy}"
                timeout = self.timeouts.get(proxy_type, self.timeout)
                
                async with session.get(
                    "https://httpbin.org/headers", 
                    proxy=proxy_url,
                    headers=self.headers,
                    ssl=False, 
                    timeout=timeout
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        headers = data.get("headers", {})
                        
                        # Check for common headers that might reveal original IP
                        suspicious_headers = ["X-Forwarded-For", "Via", "Forwarded", "X-Real-IP", "Client-IP"]
                        
                        for header in suspicious_headers:
                            if header in headers:
                                if self.real_ip in headers[header]:
                                    return "Transparent"
                        
                        # If we got here, the proxy is likely anonymous but let's check if it's elite
                        if not any(header in headers for header in suspicious_headers):
                            return "Elite"
                        else:
                            return "Anonymous"
                            
                return "Anonymous"  # Default if we couldn't determine exactly
            else:
                return "Transparent"
        except:
            return "Unknown"

    async def measure_latency(self, proxy, proxy_type, session):
        """Measure the response time of a proxy in milliseconds"""
        try:
            proxy_url = f"{proxy_type}://{proxy}"
            timeout = self.timeouts.get(proxy_type, self.timeout)
            
            start_time = time.time()
            async with session.get(
                "http://httpbin.org/get", 
                proxy=proxy_url,
                headers=self.headers, 
                ssl=False,
                timeout=timeout
            ) as response:
                if response.status == 200:
                    end_time = time.time()
                    return int((end_time - start_time) * 1000)  # Convert to milliseconds
        except:
            pass
        return 9999  # Return high latency for failures

    async def get_ip_info(self, ip, session):
        """Get geolocation data for an IP address"""
        if ip in self.ip_info_cache:
            return self.ip_info_cache[ip]
            
        try:
            # Use ip-api for geolocation (free and no API key required)
            async with session.get(f"http://ip-api.com/json/{ip}", timeout=5) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("status") == "success":
                        location = {
                            "country": data.get("country", "Unknown"),
                            "countryCode": data.get("countryCode", ""),
                            "region": data.get("regionName", ""),
                            "city": data.get("city", "Unknown"),
                            "isp": data.get("isp", ""),
                            "org": data.get("org", ""),
                            "as": data.get("as", ""),
                            "timezone": data.get("timezone", ""),
                            "lat": data.get("lat", 0),
                            "lon": data.get("lon", 0)
                        }
                        self.ip_info_cache[ip] = location
                        return location
        except:
            pass
            
        # Return default data if we can't get location info
        default = {"country": "Unknown", "city": "Unknown", "countryCode": "", "region": "", "isp": "", "lat": 0, "lon": 0}
        self.ip_info_cache[ip] = default
        return default

    async def verify_batch(self, proxies, proxy_type, progress, verify_task, working_proxies):
        connector = aiohttp.TCPConnector(limit_per_host=100, force_close=True, enable_cleanup_closed=True)
        
        async def verify_single(proxy):
            async with self.semaphore:
                try:
                    await self.check_proxy(proxy, proxy_type, working_proxies, connector)
                except Exception as e:
                    if self.verbose:
                        console.print(f"[red]Error checking {proxy}: {str(e)}")
                finally:
                    progress.update(verify_task, advance=1)
                    # Check if we've reached max proxies
                    if self.max_proxies and len(working_proxies) >= self.max_proxies:
                        return True
            return False

        # Process in smaller chunks to avoid connection issues
        chunk_size = 250
        for i in range(0, len(proxies), chunk_size):
            chunk = proxies[i:i+chunk_size]
            tasks = [verify_single(proxy) for proxy in chunk]
            results = await asyncio.gather(*tasks)
            
            # Stop if we've reached max proxies
            if self.max_proxies and len(working_proxies) >= self.max_proxies:
                break
                
        await connector.close()

    async def fetch_proxies(self, session, url):
        try:
            async with session.get(url, timeout=10) as response:
                content = await response.text()
                
                if 'json' in url:
                    try:
                        data = json.loads(content)
                        if isinstance(data, list):
                            proxies = [f"{p['ip']}:{p['port']}" for p in data if 'ip' in p and 'port' in p]
                        elif isinstance(data, dict) and 'proxies' in data:
                            proxies = [f"{p['ip']}:{p['port']}" for p in data['proxies'] if 'ip' in p and 'port' in p]
                        else:
                            proxies = []
                    except:
                        proxies = self.proxy_pattern.findall(content)
                else:
                    proxies = self.proxy_pattern.findall(content)
                
                return proxies
        except Exception as e:
            if self.verbose:
                console.print(f"[red]Error fetching {url}: {str(e)}")
            return []

    async def export_proxies(self, proxy_type, working_proxies, country_stats, total_found, elapsed_time):
        """Export proxies to various formats"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create a results JSON with all data
        results = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "type": proxy_type,
            "total_found": total_found,
            "working": len(working_proxies),
            "country_distribution": country_stats,
            "proxies": working_proxies,
            "elapsed_time": f"{elapsed_time:.2f}s"
        }
        
        # Always save JSON for complete data
        with open(f"{self.output_dir}/{proxy_type}_proxies_{timestamp}.json", "w") as f:
            json.dump(results, f, indent=2)
        
        # Export text file with just the proxies if requested
        if self.save_format == "txt" or self.save_format == "all":
            with open(f"{self.output_dir}/{proxy_type}_proxies_{timestamp}.txt", "w") as f:
                for proxy in working_proxies.keys():
                    f.write(f"{proxy}\n")
        
        # Export CSV with selected data if requested
        if self.save_format == "csv" or self.save_format == "all":
            with open(f"{self.output_dir}/{proxy_type}_proxies_{timestamp}.csv", "w") as f:
                # Write header
                f.write("proxy,type,country,city,isp,anonymity,latency_ms\n")
                
                # Write data rows
                for proxy, data in working_proxies.items():
                    country = data["location"].get("country", "Unknown")
                    city = data["location"].get("city", "Unknown")
                    isp = data["location"].get("isp", "Unknown").replace(",", " ")
                    anonymity = data.get("anonymity", "Unknown")
                    latency = data.get("latency_ms", 9999)
                    
                    f.write(f"{proxy},{proxy_type},{country},{city},{isp},{anonymity},{latency}\n")
        
        return results

    async def scrape(self, proxy_type='http'):
        start_time = time.time()
        proxies = []
        working_proxies = {}  # Changed to dict to store location info
        
        # Configure TCP connector to handle many connections
        connector = aiohttp.TCPConnector(limit=100, force_close=True)
        
        async with aiohttp.ClientSession(headers=self.headers, connector=connector) as session:
            with Progress(
                SpinnerColumn(),
                BarColumn(bar_width=40),
                *Progress.get_default_columns(),
                TimeElapsedColumn(),
                console=console
            ) as progress:
                # Fetch phase
                fetch_task = progress.add_task(f"Fetching {proxy_type} proxies...", total=len(self.apis[proxy_type]))
                
                tasks = []
                for url in self.apis[proxy_type]:
                    task = asyncio.create_task(self.fetch_proxies(session, url))
                    task.add_done_callback(lambda _: progress.update(fetch_task, advance=1))
                    tasks.append(task)
                
                results = await asyncio.gather(*tasks)
                
                for result in results:
                    proxies.extend(result)
                
                proxies = list(set(proxies))
                random.shuffle(proxies)
                total_found = len(proxies)
                
                # If max_proxies is set, only check that many
                if self.max_proxies and total_found > self.max_proxies:
                    proxies = proxies[:self.max_proxies * 10]  # Check 10x max_proxies to find enough working ones
                
                # Verify phase - process in batches to avoid overwhelming connections
                verify_task = progress.add_task(f"Verifying {proxy_type} proxies...", total=len(proxies))
                
                # Split into batches
                batch_size = 1000
                batches = [proxies[i:i+batch_size] for i in range(0, len(proxies), batch_size)]
                
                for batch in batches:
                    if self.max_proxies and len(working_proxies) >= self.max_proxies:
                        break
                    await self.verify_batch(batch, proxy_type, progress, verify_task, working_proxies)
                
                # Ensure the progress bar completes
                progress.update(verify_task, completed=len(proxies))
                
                # Analyze country distribution
                country_stats = self.get_country_stats(working_proxies)
                
                # Get anonymity distribution
                anonymity_stats = self.get_anonymity_stats(working_proxies)
                
                # Export results in the requested format
                results = await self.export_proxies(
                    proxy_type, working_proxies, country_stats, total_found, time.time() - start_time
                )

                self.display_results(
                    proxy_type, total_found, working_proxies, 
                    country_stats, anonymity_stats, time.time() - start_time
                )
                
                return working_proxies

    def get_country_stats(self, proxies):
        """Calculate country distribution statistics"""
        country_count = {}
        for _, data in proxies.items():
            country = data["location"].get("country", "Unknown")
            if country not in country_count:
                country_count[country] = 0
            country_count[country] += 1
        
        # Sort by count, descending
        return dict(sorted(country_count.items(), key=lambda x: x[1], reverse=True))

    def get_anonymity_stats(self, proxies):
        """Calculate anonymity level distribution"""
        anonymity_count = {}
        for _, data in proxies.items():
            level = data.get("anonymity", "Unknown")
            if level not in anonymity_count:
                anonymity_count[level] = 0
            anonymity_count[level] += 1
        
        # Sort by count, descending
        return dict(sorted(anonymity_count.items(), key=lambda x: x[1], reverse=True))

    def display_results(self, proxy_type, total_found, working_proxies, country_stats, anonymity_stats, elapsed_time):
        # Main results table
        table = Table(show_header=True, header_style="bold magenta", box=ROUNDED)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", justify="right")
        
        table.add_row("Proxy Type", proxy_type.upper())
        table.add_row("Total Found", str(total_found))
        table.add_row("Working", str(len(working_proxies)))
        success_rate = (len(working_proxies) / total_found * 100) if total_found > 0 else 0
        table.add_row("Success Rate", f"{success_rate:.1f}%")
        table.add_row("Time Elapsed", f"{elapsed_time:.2f}s")
        table.add_row("Export Directory", self.output_dir)
        
        console.print("\n")
        console.print(Panel(table, title="[bold cyan]Results", border_style="cyan", box=ROUNDED))
        
        # Create layout for side-by-side tables
        layout = Layout()
        layout.split_row(
            Layout(name="countries", ratio=1),
            Layout(name="anonymity", ratio=1)
        )
        
        # Country distribution table
        country_table = Table(show_header=True, header_style="bold magenta", box=ROUNDED)
        country_table.add_column("Country", style="cyan")
        country_table.add_column("Count", justify="right")
        country_table.add_column("Percentage", justify="right")
        
        # Display top 10 countries or all if less than 10
        top_countries = list(country_stats.items())[:min(10, len(country_stats))]
        for country, count in top_countries:
            percentage = (count / len(working_proxies) * 100) if working_proxies else 0
            country_table.add_row(country, str(count), f"{percentage:.1f}%")
        
        # Anonymity distribution table
        anonymity_table = Table(show_header=True, header_style="bold magenta", box=ROUNDED)
        anonymity_table.add_column("Anonymity Level", style="cyan")
        anonymity_table.add_column("Count", justify="right")
        anonymity_table.add_column("Percentage", justify="right")
        
        for level, count in anonymity_stats.items():
            percentage = (count / len(working_proxies) * 100) if working_proxies else 0
            anonymity_table.add_row(level, str(count), f"{percentage:.1f}%")
        
        # Add tables to layout
        layout["countries"].update(Panel(country_table, title="[bold cyan]Top 10 Countries", border_style="cyan", box=ROUNDED))
        layout["anonymity"].update(Panel(anonymity_table, title="[bold cyan]Anonymity Levels", border_style="cyan", box=ROUNDED))
        
        console.print(layout)
        
        # Display sample proxies
        if working_proxies:
            sample_count = min(5, len(working_proxies))
            sample_proxies = list(working_proxies.items())[:sample_count]
            
            sample_table = Table(show_header=True, header_style="bold magenta", box=ROUNDED)
            sample_table.add_column("Proxy", style="cyan")
            sample_table.add_column("Country", style="cyan")
            sample_table.add_column("City", style="cyan")
            sample_table.add_column("Anonymity", style="cyan")
            sample_table.add_column("Latency", style="cyan", justify="right")
            
            for proxy, data in sample_proxies:
                country = data["location"].get("country", "Unknown")
                city = data["location"].get("city", "Unknown")
                anonymity = data.get("anonymity", "Unknown")
                latency = data.get("latency_ms", 9999)
                
                sample_table.add_row(
                    proxy, 
                    country,
                    city,
                    anonymity,
                    f"{latency}ms"
                )
            
            console.print(Panel(sample_table, title="[bold cyan]Sample Proxies", border_style="cyan", box=ROUNDED))

async def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Advanced Proxy Scraper with Geolocation")
    parser.add_argument("-t", "--type", choices=["http", "socks4", "socks5", "all"], default="all",
                      help="Type of proxies to scrape (default: all)")
    parser.add_argument("-c", "--concurrent", type=int, default=100,
                      help="Maximum concurrent connections (default: 100)")
    parser.add_argument("--timeout", type=int, default=3,
                      help="Connection timeout in seconds (default: 3)")
    parser.add_argument("-o", "--output", type=str, default="results",
                      help="Output directory for results (default: results)")
    parser.add_argument("-f", "--format", choices=["json", "txt", "csv", "all"], default="json",
                      help="Output format (default: json)")
    parser.add_argument("-v", "--verbose", action="store_true",
                      help="Enable verbose output")
    parser.add_argument("-m", "--max", type=int, default=None,
                      help="Maximum number of proxies to find (default: unlimited)")
    parser.add_argument("--no-anonymity", action="store_true",
                      help="Disable anonymity checking")
    
    args = parser.parse_args()
    
    # Create scraper instance
    scraper = ProxyScraper(
        max_concurrent=args.concurrent,
        timeout=args.timeout,
        output_dir=args.output,
        save_format=args.format,
        verbose=args.verbose,
        check_anonymity=not args.no_anonymity,
        max_proxies=args.max
    )
    
    console.print(Panel(
        "[bold cyan]Advanced Proxy Scraper with Geolocation[/bold cyan]\n"
        f"[yellow]Concurrent connections: {args.concurrent} | Timeout: {args.timeout}s | Format: {args.format}[/yellow]",
        box=ROUNDED,
        expand=False
    ))
    
    # Get our real IP for anonymity checking
    if not args.no_anonymity:
        console.print("[cyan]Getting your real IP address for anonymity testing...[/cyan]")
        real_ip_data = await scraper.get_real_ip()
        console.print(f"[cyan]Your IP: {real_ip_data.get('query', 'Unknown')} ({real_ip_data.get('country', 'Unknown')})[/cyan]")
    
    # Determine which proxy types to scrape
    proxy_types = ["http", "socks4", "socks5"] if args.type == "all" else [args.type]
    
    all_proxies = {}
    country_distribution = {}
    
    for proxy_type in proxy_types:
        proxies = await scraper.scrape(proxy_type)
        all_proxies[proxy_type] = proxies
        
        # Update global country distribution
        for _, data in proxies.items():
            country = data["location"].get("country", "Unknown")
            if country not in country_distribution:
                country_distribution[country] = 0
            country_distribution[country] += 1
    
    # Sort country distribution by count
    country_distribution = dict(sorted(country_distribution.items(), key=lambda x: x[1], reverse=True))
    
    # Save combined results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    with open(f"{scraper.output_dir}/all_proxies_{timestamp}.json", "w") as f:
        json.dump({
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_proxies": sum(len(p) for p in all_proxies.values()),
            "http_proxies": len(all_proxies.get('http', {})),
            "socks4_proxies": len(all_proxies.get('socks4', {})),
            "socks5_proxies": len(all_proxies.get('socks5', {})),
            "country_distribution": country_distribution,
            "proxies": all_proxies
        }, f, indent=2)
    
    # Display global stats
    total_working = sum(len(p) for p in all_proxies.values())
    if total_working > 0:
        console.print("\n")
        console.print(Panel(
            f"[bold green]Total working proxies: {total_working}[/bold green]\n"
            f"[cyan]Results saved to: {scraper.output_dir}/all_proxies_{timestamp}.json[/cyan]", 
            title="[bold cyan]Summary", 
            border_style="cyan",
            box=ROUNDED
        ))

if __name__ == "__main__":
    # Handle Windows ProactorEventLoop errors
    if sys.platform == 'win32':
        # Suppress the noisy connection reset errors on Windows
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    # Handle Windows ProactorEventLoop errors
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("[bold red]Scraping interrupted by user.")
    except Exception as e:
        console.print(f"[bold red]Error: {str(e)}")