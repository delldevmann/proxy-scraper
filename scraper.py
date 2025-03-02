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
                "https://raw.githubusercontent.com/r00tee/Proxy-List/refs/heads/main/Https.txt",
                "https://cdn.jsdelivr.net/gh/proxifly/free-proxy-list@main/proxies/protocols/http/data.txt",
                "https://raw.githubusercontent.com/mmpx12/proxy-list/refs/heads/master/http.txt",
                "https://raw.githubusercontent.com/vmheaven/VMHeaven-Free-Proxy-Updated/refs/heads/main/http.txt",
                "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/all.txt",
                "https://raw.githubusercontent.com/ErcinDedeoglu/proxies/main/proxies/http.txt",
                "https://raw.githubusercontent.com/Zaeem20/FREE_PROXIES_LIST/refs/heads/master/https.txt",
                "https://raw.githubusercontent.com/ErcinDedeoglu/proxies/main/proxies/https.txt",
                "https://cdn.jsdelivr.net/gh/proxifly/free-proxy-list@main/proxies/all/data.json",
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
