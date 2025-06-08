import datetime
import json
import os

from matplotlib import colors
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

def plot_trends_with_timezones_s(df):
    df['date'] = pd.to_datetime(df['date'], utc=True)
    pivot = df.pivot(index="date", columns="sName", values="iCount")
    
    plt.style.use('default')  # Reset to clean style
    fig, ax = plt.subplots(figsize=(14, 10))
    fig.patch.set_facecolor('white')
    ax.set_facecolor('#f8f9fa')
    
    colors_list = [
        '#e41a1c', '#377eb8', '#4daf4a', '#984ea3', '#ff7f00',
        '#ffff33', '#a65628', '#f781bf', '#999999', '#1f77b4',
        '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b'
    ]
    
    line_styles = ['-', '--', '-.', ':', '-', '--', '-.', ':', '-', '--']
    markers = ['o', 's', '^', 'D', 'v', '<', '>', 'p', '*', 'h']
    
    # Plot each series with distinct styling
    for i, col in enumerate(pivot.columns):
        color = colors_list[i % len(colors_list)]
        linestyle = line_styles[i % len(line_styles)]
        marker = markers[i % len(markers)]
        
        ax.plot(pivot.index, pivot[col], 
               color=color,
               linestyle=linestyle,
               marker=marker, 
               markersize=6,
               linewidth=2.5,
               label=col,
               alpha=0.8,
               markerfacecolor='white',
               markeredgecolor=color,
               markeredgewidth=2)
    
    ax.grid(True, alpha=0.3, linestyle='-', linewidth=0.5)
    ax.set_axisbelow(True)
    
    locator = mdates.AutoDateLocator()
    formatter = ConciseDateFormatter(locator)
    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(formatter)
    ax.set_xlabel("UTC", fontsize=12, fontweight='bold')
    ax.set_ylabel("Count", fontsize=12, fontweight='bold')
    
    ax.tick_params(axis='both', which='major', labelsize=10)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#cccccc')
    ax.spines['bottom'].set_color('#cccccc')
    
    def format_timezone(tzname):
        tz = pytz.timezone(tzname)
        formatter = ConciseDateFormatter(locator, tz=tz)
        return formatter
    
    ax2 = ax.secondary_xaxis('top', functions=(lambda x: x, lambda x: x))
    ax2.xaxis.set_major_locator(locator)
    ax2.xaxis.set_major_formatter(format_timezone("Asia/Manila"))
    ax2.set_xlabel("Philippines (GMT+8)", fontsize=11, fontweight='bold', color='#2E8B57')
    ax2.tick_params(axis='x', labelsize=9, colors='#2E8B57')
    
    ax3 = ax.secondary_xaxis(-0.12, functions=(lambda x: x, lambda x: x))
    ax3.xaxis.set_major_locator(locator)
    ax3.xaxis.set_major_formatter(format_timezone("America/New_York"))
    ax3.set_xlabel("US Eastern (EST/EDT)", fontsize=11, fontweight='bold', color='#4169E1')
    ax3.tick_params(axis='x', labelsize=9, colors='#4169E1')
    
    ax4 = ax.secondary_xaxis(-0.24, functions=(lambda x: x, lambda x: x))
    ax4.xaxis.set_major_locator(locator)
    ax4.xaxis.set_major_formatter(format_timezone("America/Sao_Paulo"))
    ax4.set_xlabel("Brazil (GMT-3)", fontsize=11, fontweight='bold', color='#FF6347')
    ax4.tick_params(axis='x', labelsize=9, colors='#FF6347')
    
    ax5 = ax.secondary_xaxis(-0.36, functions=(lambda x: x, lambda x: x))
    ax5.xaxis.set_major_locator(locator)
    ax5.xaxis.set_major_formatter(format_timezone("Asia/Jayapura"))
    ax5.set_xlabel("Indonesia (GMT+9)", fontsize=11, fontweight='bold', color='#8A2BE2')
    ax5.tick_params(axis='x', labelsize=9, colors='#8A2BE2')
    
    fig.autofmt_xdate(rotation=45)
    
    legend = ax.legend(
        fontsize=10, 
        ncol=min(3, len(pivot.columns)), 
        loc='upper left',
        frameon=True,
        fancybox=True,
        shadow=True,
        framealpha=0.9,
        facecolor='white',
        edgecolor='#cccccc'
    )
    legend.get_frame().set_linewidth(0.5)
    
    ax.set_title("Population Analysis Across Multiple Timezones", 
                fontsize=16, fontweight='bold', pad=20, color='#333333')
    
    plt.tight_layout()
    plt.subplots_adjust(bottom=0.2)  # Make room for timezone labels
    
    fig.savefig("chart.png", dpi=300, bbox_inches='tight', 
                facecolor='white', edgecolor='none')
    plt.close()

def send_discord(df):
    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
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
    plot_trends_with_timezones_s(history)
    send_discord(history)


if __name__ == "__main__":
    main()
