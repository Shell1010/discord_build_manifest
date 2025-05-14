
import requests
import os
from datetime import datetime

WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

def fetch_json(url):
    return requests.get(url, timeout=10).json()

def main():
    summary = fetch_json("https://discordstatus.com/api/v2/summary.json")
    unresolved = fetch_json("https://discordstatus.com/api/v2/unresolved.json")
    print(summary)
    status_desc = summary["status"]["description"]
    incidents = unresolved.get("incidents", [])
    components = summary.get("components", [])

    incident_text = "\n".join(
        f"• {i['name']} ({i['impact']}) — {i['status']}" for i in incidents
    ) or "No unresolved incidents."

    component_text = "\n".join(
        f"• {c['name']}: {c['status']}" for c in components if c["status"] != "operational"
    ) or "All components operational."

    payload = {
        "embeds": [
            {
                "title": "📡 Discord Status Update",
                "color": 0x5865F2,
                "fields": [
                    {"name": "🔔 Summary", "value": status_desc, "inline": False},
                    {"name": "🚨 Unresolved Incidents", "value": incident_text, "inline": False},
                    {"name": "🧩 Component Status", "value": component_text, "inline": False}
                ],
                "timestamp": datetime.utcnow().isoformat()
            }
        ]
    }

    resp = requests.post(WEBHOOK_URL, json=payload)
    resp.raise_for_status()

if __name__ == "__main__":
    main()
