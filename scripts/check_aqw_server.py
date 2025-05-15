import socket
import os
import requests
from collections import defaultdict
from datetime import datetime, timezone
from time import perf_counter
# Server definitions
servers = {
    "Artix": "172.65.160.131",
    "Swordhaven (EU)": "172.65.207.70",
    "Yokai (SEA)": "172.65.236.72",
    "Yorumi": "172.65.249.41",
    "Twilly": "172.65.210.123",
    "Safiria": "172.65.249.3",
    "Galanoth": "172.65.249.3",
    "Alteon": "172.65.235.85",
    "Gravelyn": "172.65.235.85",
    "Twig": "172.65.235.85",
    "Sir Ver": "172.65.220.106",
    "Espada": "172.65.220.106",
    "Sepulchure": "172.65.220.106",
}

# Group servers by IP
ip_to_servers = defaultdict(list)
for name, ip in servers.items():
    ip_to_servers[ip].append(name)


def tcp_ping(ip, port=443, timeout=2, attempts=30):
    latencies = []

    for _ in range(attempts):
        try:
            start = perf_counter()
            with socket.create_connection((ip, port), timeout=timeout):
                end = perf_counter()
            latency_ms = (end - start) * 1000
            latencies.append(latency_ms)
        except (socket.timeout, socket.error):
            continue

    if not latencies:
        return "unreachable"

    avg_latency = sum(latencies) / len(latencies)
    return f"{avg_latency:.2f} ms"

results = {}
for ip, names in ip_to_servers.items():
    print(f"Pinging {ip} - {names}")
    latency = tcp_ping(ip)
    for name in names:
        results[name] = {
            "ip": ip,
            "latency": latency,
            "source": names[0]  # Identify primary
        }

# Build embed fields
fields = []
for name in sorted(results):
    entry = results[name]
    same_as = entry['source']
    shared = f" (shared with **{same_as}**)" if same_as != name else ""
    value = f"IP: `{entry['ip']}`\nLatency: `{entry['latency']}`{shared}"
    fields.append({
        "name": name,
        "value": value,
        "inline": True
    })

# Create the embed payload
embed = {
    "title": "🛰️ AQWorlds Server Latency Report (TCP)",
    "description": f"TCP pinged **{len(ip_to_servers)}** unique IPs for **{len(servers)}** servers.\n10 sample per IP using port 443.",
    "color": 0x00bfff,
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "fields": fields,
    "footer": {
        "text": "Generated via GitHub Actions • All times UTC"
    }
}

# Send to webhook
WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
print(WEBHOOK_URL)
if not WEBHOOK_URL:
    raise ValueError("DISCORD_WEBHOOK_URL environment variable not set.")

requests.post(WEBHOOK_URL, json={"embeds": [embed]})
print("Latency report sent as embed.")
