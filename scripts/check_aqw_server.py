import requests

import os, json, datetime
import pandas as pd
import matplotlib.pyplot as plt
import requests

DATA_FILE = "data.csv"
JSON_FILE = "servers.json"

def load_history():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE, parse_dates=["date"])
    else:
        return pd.DataFrame(columns=["date","sName","iCount"])

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
    # pivot so each server is a column
    pivot = df.pivot(index="date", columns="sName", values="iCount")
    plt.figure(figsize=(10,6))
    for col in pivot.columns:
        plt.plot(pivot.index, pivot[col], label=col)
    plt.legend(fontsize="small", ncol=2)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig("chart.png")
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
