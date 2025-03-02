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
from datetime import datetime
from asyncio import Semaphore

console = Console()

class ProxyScraper:
    def __init__(self, max_concurrent=500, timeout=3, output_dir="results", save_format="json", 
                 verbose=False, check_anonymity=True, max_proxies=None):
        self.apis = {
            'http': [
                "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt",
                "https://raw.githubusercontent.com/r00tee/Proxy-List/refs/heads/main/Https.txt",
                "https://raw.githubusercontent.com/proxifly/free-proxy-list/main/proxies/protocols/http/data.txt",
                "https://raw.githubusercontent.com/mmpx12/proxy-list/refs/heads/master/http.txt",
                "https://raw.githubusercontent.com/vmheaven/VMHeaven-Free-Proxy-Updated/refs/heads/main/http.txt",
                "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/all.txt",
                "https://raw.githubusercontent.com/ErcinDedeoglu/proxies/main/proxies/http.txt",
                "https://raw.githubusercontent.com/Zaeem20/FREE_PROXIES_LIST/refs/heads/master/https.txt",
                "https://raw.githubusercontent.com/ErcinDedeoglu/proxies/main/proxies/https.txt",
                "https://raw.githubusercontent.com/dpangestuw/Free-Proxy/refs/heads/main/http_proxies.txt",
                "https://raw.githubusercontent.com/theriturajps/proxy-list/refs/heads/main/proxies.txt",
                "https://raw.githubusercontent.com/andigwandi/free-proxy/refs/heads/main/proxy_list.txt",
                "https://api.proxyscrape.com/?request=getproxies&proxytype=http",
                "https://raw.githubusercontent.com/fyvri/fresh-proxy-list/archive/storage/classic/all.txt",
                "https://raw.githubusercontent.com/roosterkid/openproxylist/refs/heads/main/HTTPS_RAW.txt"
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
        self.timeout = timeout
        self.timeouts = {'http': timeout, 'socks4': timeout, 'socks5': 10}
        self.semaphore = Semaphore(max_concurrent)
        self.proxy_pattern = re.compile(r"\d{1,3}(?:\.\d{1,3}){3}(?::\d{1,5})?")
        self.headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124"}
        self.output_dir = output_dir
        self.save_format = save_format
        self.verbose = verbose
        self.check_anonymity = check_anonymity
        self.max_proxies = max_proxies
        os.makedirs(self.output_dir, exist_ok=True)

    async def fetch_proxies(self, session, url):
        """Fetch proxies from a given URL with retries"""
        for attempt in range(3):
            try:
                async with session.get(url, timeout=5) as response:
                    if response.status == 200:
                        content = await response.text()
                        return self.proxy_pattern.findall(content)
            except:
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
        return []

    async def fetch_all_proxies(self, proxy_type):
        """Fetch proxies from all sources in parallel"""
        async with aiohttp.ClientSession(headers=self.headers) as session:
            tasks = [self.fetch_proxies(session, url) for url in self.apis[proxy_type]]
            results = await asyncio.gather(*tasks)

        return list(set(proxy for sublist in results for proxy in sublist))  # Remove duplicates

    async def check_proxy(self, proxy: str, proxy_type: str, working_proxies, connector):
        """Check if a proxy is working"""
        proxy_url = f"{proxy_type}://{proxy}"
        timeout = min(self.timeout * 2, 10)  # 🔥 Adaptive timeout (max 10s)

        try:
            async with aiohttp.ClientSession(connector=connector, connector_owner=False) as session:
                async with session.get(self.test_url, proxy=proxy_url, headers=self.headers, timeout=timeout) as response:
                    if response.status == 200:
                        detected_ip = (await response.json()).get("origin", proxy.split(":")[0])
                        working_proxies[proxy] = {"ip": detected_ip, "type": proxy_type}
                        return True
        except:
            pass
        return False

    async def verify_proxies(self, proxies, proxy_type, progress, verify_task, working_proxies):
        """Verify proxies concurrently"""
        connector = aiohttp.TCPConnector(limit_per_host=500, force_close=True)

        async def verify_single(proxy):
            async with self.semaphore:
                if await self.check_proxy(proxy, proxy_type, working_proxies, connector):
                    progress.update(verify_task, advance=1)

        await asyncio.gather(*(verify_single(proxy) for proxy in proxies))  # 🔥 Verify all proxies in parallel

    async def export_proxies(self, proxy_type, working_proxies):
        """Save working proxies to a file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"{self.output_dir}/{proxy_type}_proxies_{timestamp}.json"

        with open(results_file, "w") as f:
            json.dump({"timestamp": timestamp, "type": proxy_type, "proxies": working_proxies}, f, indent=2)

        return results_file

    async def scrape(self, proxy_type='http'):
        """Main function to scrape proxies"""
        start_time = time.time()
        proxies = await self.fetch_all_proxies(proxy_type)
        working_proxies = {}

        with Progress(SpinnerColumn(), BarColumn(bar_width=40), TimeElapsedColumn(), console=console) as progress:
            verify_task = progress.add_task(f"Verifying {proxy_type} proxies...", total=len(proxies))
            await self.verify_proxies(proxies, proxy_type, progress, verify_task, working_proxies)

        results_file = await self.export_proxies(proxy_type, working_proxies)

        console.print(Panel(f"[bold green]Proxies saved to: {results_file}[/bold green]", border_style="cyan"))
        console.print(f"✅ [bold cyan]Total Proxies Checked:[/bold cyan] {len(proxies)}")
        console.print(f"✅ [bold green]Total Working Proxies:[/bold green] {len(working_proxies)}")
        console.print(f"⏳ [bold yellow]Time Taken:[/bold yellow] {time.time() - start_time:.2f}s")

        return working_proxies

async def main():
    scraper = ProxyScraper()
    await scraper.scrape('http')

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("[bold red]Scraping interrupted by user.")
    except Exception as e:
        console.print(f"[bold red]Error: {str(e)}")
