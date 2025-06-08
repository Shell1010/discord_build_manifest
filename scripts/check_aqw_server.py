import datetime
import json
import os

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd
import requests
from matplotlib.dates import ConciseDateFormatter
import pytz

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
    return resp.json()["servers"]


def append_today(history_df, servers):
    now = datetime.datetime.utcnow()
    rows = []
    for s in servers:
        rows.append({"date": now, "sName": s["sName"], "iCount": s["iCount"]})
    today_df = pd.DataFrame(rows)
    return pd.concat([history_df, today_df], ignore_index=True)


def get_overall_average(csv_path: str = "data.csv") -> float:
    """
    Reads the CSV, computes and returns the mean of the iCount column.
    Returns float('nan') if the file is empty or has no iCount.
    """
    try:
        df = pd.read_csv(csv_path)
    except FileNotFoundError:
        raise FileNotFoundError(f"{csv_path} not found")

    if "iCount" not in df.columns or df["iCount"].dropna().empty:
        return float("nan")

    return df["iCount"].mean()


def get_average_per_server(csv_path: str = "data.csv") -> dict:
    """
    Returns a dict mapping each server name to its average iCount.
    """
    df = pd.read_csv(csv_path)
    if not {"sName", "iCount"}.issubset(df.columns):
        return {}
    return df.groupby("sName")["iCount"].mean().to_dict()


def plot_trends(df):
    pivot = df.pivot(index="date", columns="sName", values="iCount")

    fig, ax = plt.subplots(figsize=(10, 6))
    for col in pivot.columns:
        ax.plot(pivot.index, pivot[col], marker="o", label=col)

    locator = mdates.AutoDateLocator()
    formatter = ConciseDateFormatter(locator)  # concise, context‐aware labels
    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(formatter)
    fig.autofmt_xdate()

    ax.legend(fontsize="small", ncol=2)
    plt.tight_layout()
    fig.savefig("chart.png")
    plt.close()

def plot_trends_with_timezones(df):
    df['date'] = pd.to_datetime(df['date'], utc=True)
    pivot = df.pivot(index="date", columns="sName", values="iCount")

    fig, ax = plt.subplots(figsize=(12, 8))
    for col in pivot.columns:
        ax.plot(pivot.index, pivot[col], marker="o", label=col)

    # UTC as the primary X-axis
    locator = mdates.AutoDateLocator()
    formatter = ConciseDateFormatter(locator)
    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(formatter)
    ax.set_xlabel("UTC")

    # Add secondary X-axes for each timezone
    def format_timezone(tzname):
        tz = pytz.timezone(tzname)
        def convert(x):
            dt = pd.to_datetime(x, utc=True)
            return dt.tz_convert(tz).to_pydatetime()
        return mdates.ConciseDateFormatter(locator, tz=tz)

    ax2 = ax.secondary_xaxis('top', functions=(lambda x: x, lambda x: x))
    ax2.xaxis.set_major_locator(locator)
    ax2.xaxis.set_major_formatter(format_timezone("Asia/Manila"))
    ax2.set_xlabel("Philippines (GMT+8)")

    ax3 = ax.secondary_xaxis(-0.1, functions=(lambda x: x, lambda x: x))
    ax3.xaxis.set_major_locator(locator)
    ax3.xaxis.set_major_formatter(format_timezone("America/New_York"))
    ax3.set_xlabel("US Eastern (EST/EDT)")

    ax4 = ax.secondary_xaxis(-0.2, functions=(lambda x: x, lambda x: x))
    ax4.xaxis.set_major_locator(locator)
    ax4.xaxis.set_major_formatter(format_timezone("America/Sao_Paulo"))
    ax4.set_xlabel("Brazil (GMT-3)")

    ax5 = ax.secondary_xaxis(-0.3, functions=(lambda x: x, lambda x: x))
    ax5.xaxis.set_major_locator(locator)
    ax5.xaxis.set_major_formatter(format_timezone("Asia/Jayapura"))
    ax5.set_xlabel("Indonesia (GMT+9)")

    fig.autofmt_xdate()
    ax.legend(fontsize="small", ncol=2)
    plt.tight_layout()
    fig.savefig("chart.png")
    plt.close()


def send_discord(df):
    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
    webhook_url = "https://canary.discord.com/api/webhooks/1372012402534518874/xN9Gl0NkjPpG_eykWWaEkM7zNvIEFOZ4_Hl2sWD-UCf2Ycsm5qdDG08qq5OzjD0rvViT"
    if not webhook_url:
        print("ERROR: DISCORD_WEBHOOK_URL not set")
        return

    latest_time = df["date"].max()
    latest = df[df["date"] == latest_time]

    avgs_per_server = get_average_per_server()

    embed = {
        "title": "AQW Server Populations",
        "description": f"As of {latest_time.strftime('%Y-%m-%d %H:%M UTC')}",
        "fields": [
            {"name": row["sName"], "value": f"Count: `{str(row["iCount"])}`\nAVG: `{avg:.2f}`", "inline": True}
            for (_, row), (svr, avg) in zip(latest.iterrows(), avgs_per_server.items())
            
        ],
        "image": {"url": "attachment://chart.png"},
    }

    payload = {"embeds": [embed]}
    print(payload)
    with open("./chart.png", "rb") as fp:
        files = {
            "payload_json": (None, json.dumps(payload), "application/json"),
            "file": (os.path.basename("./chart.png"), fp, "image/png"),
        }

        r = requests.post(webhook_url, json=payload, files=files)
        print("Discord response:", r.status_code, r.text)


def main():
    history = load_history()
    servers = fetch_servers()
    history = append_today(history, servers)
    save_history(history)
    plot_trends_with_timezones(history)
    send_discord(history)


if __name__ == "__main__":
    main()
