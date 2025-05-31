import datetime
import json
import os

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd
import requests
from matplotlib.dates import ConciseDateFormatter

DATA_FILE = "data.csv"
JSON_FILE = "servers.json"

def load_history():
    if os.path.exists(DATA_FILE):
        # protect against a zero-byte or malformed CSV
        if os.path.getsize(DATA_FILE) > 0:
            try:
                return pd.read_csv(DATA_FILE, parse_dates=["date"])
            except pd.errors.EmptyDataError:
                print(f"{DATA_FILE} exists but is empty – starting fresh")
            except Exception as e:
                print(f"Could not parse {DATA_FILE}: {e} – starting fresh")
    # fallback
    return pd.DataFrame(columns=["date", "sName", "iCount"])

def save_history(df):
    df.to_csv(DATA_FILE, index=False)

def fetch_servers():
    url = "https://game.aq.com/game/api/login/now?ran=0.5168141750618815"
    form_data = {"user": "JoeIsTesting", "option": 1, "pass": "abcd12345"}
    resp = requests.post(url, data=form_data)
    return resp.json()['servers']

def append_today(history_df, servers):
    now = datetime.datetime.utcnow()
    rows = []
    for s in servers:
        rows.append({
            "date": now,
            "sName": s["sName"],
            "iCount": s["iCount"]
        })
    today_df = pd.DataFrame(rows)
    return pd.concat([history_df, today_df], ignore_index=True)

def plot_trends(df):
    pivot = df.pivot(index="date", columns="sName", values="iCount")

    fig, ax = plt.subplots(figsize=(10,6))
    for col in pivot.columns:
        ax.plot(pivot.index, pivot[col], marker="o", label=col)

    locator = mdates.AutoDateLocator()
    formatter = ConciseDateFormatter(locator)   # concise, context‐aware labels
    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(formatter)
    fig.autofmt_xdate()

    ax.legend(fontsize="small", ncol=2)
    plt.tight_layout()
    fig.savefig("chart.png")
    plt.close()

def send_discord(df):
    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        print("ERROR: DISCORD_WEBHOOK_URL not set")
        return

    latest_time = df["date"].max()
    latest = df[df["date"] == latest_time]

    embed = {
        "title": "AQW Server Populations",
        "description": f"As of {latest_time.strftime('%Y-%m-%d %H:%M UTC')}",
        "fields": [
            {"name": row["sName"], "value": str(row["iCount"]), "inline": True}
            for _, row in latest.iterrows()
        ],
        # tell Discord to use our attached image
        "image": {"url": "attachment://chart.png"}
    }

    payload = {"embeds": [embed]}
    print(payload)
    files = {"file": ("chart.png", open("chart.png","rb"), "image/png")}

    r = requests.post(webhook_url, json=payload, files=files)
    print("Discord response:", r.status_code, r.text)

def main():
    history = load_history()
    servers = fetch_servers()
    history = append_today(history, servers)
    save_history(history)
    plot_trends(history)
    send_discord(history)

if __name__=="__main__":
    main()
