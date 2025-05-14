import requests
import json
import hashlib
import os


MANIFEST_URL = "https://discord.com/api/updates/distributions/app/manifests/latest?channel=canary&platform=win&arch=x86"
CACHE_FILE = "manifest_cache.json"
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # Set this as GitHub secret

def get_remote_manifest():
    response = requests.get(MANIFEST_URL)
    response.raise_for_status()
    return response.json()

def load_cached_manifest():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    return None

def save_manifest(manifest):
    with open(CACHE_FILE, "w") as f:
        json.dump(manifest, f, indent=2)

def hash_manifest(manifest):
    return hashlib.sha256(json.dumps(manifest, sort_keys=True).encode()).hexdigest()

def send_webhook():
    embed = {
        "title": "🚀 Discord Distribution Manifest Updated",
        "description": "A new build has been published or updated in the Discord distribution manifest.",
        "color": 0x5865F2,  # Discord blurple
        "timestamp": __import__("datetime").datetime.utcnow().isoformat(),
        "footer": {
            "text": "Discord Manifest Watcher",
            "icon_url": "https://cdn.discordapp.com/embed/avatars/0.png"
        }
    }
    data = {
        "embeds": [embed],
        "username": "Manifest Watcher",
    }
    requests.post(WEBHOOK_URL, json=data)


def main():
    new_manifest = get_remote_manifest()
    cached_manifest = load_cached_manifest()

    if cached_manifest is None or hash_manifest(cached_manifest) != hash_manifest(new_manifest):
        save_manifest(new_manifest)
        send_webhook()
    else:
        print("No changes to manifest.")

if __name__ == "__main__":
    main()
