import pandas
import numpy as np
import pickle
import mplfinance as mpf
from datetime import datetime, timedelta


# the function to identify the trend of the price
def identify_trend(df):
    df["Trend"] = None
    df["BoS"] = 0  # Break of Structure
    df["CHoCH"] = 0  # Change of Character
    df["Conti"] = 0  # If BoS continuously happens
    local_highs_range = 30  # Number of candles to consider for local highs and lows

    for i in range(local_highs_range, len(df)):
        recent_Highs = df["High"][i - local_highs_range : i].max()
        recent_Lows = df["Low"][i - local_highs_range : i].min()
        if (
            (df["Close"][i] > recent_Highs)
            and (df["BoS"][i - 1] == 0)
            and (df["Conti"][i - 1] == 0)
        ):
            df.loc[df.index[i] :, "Trend"] = "Uptrend"
            if (df["Trend"][i - 1] == "Uptrend") or (df["Trend"][i - 1] is None):
                df.loc[df.index[i], "BoS"] = 1
            else:
                df.loc[df.index[i], "CHoCH"] = 1
        elif df["Close"][i] > recent_Highs:
            df.loc[df.index[i], "Conti"] = 1
        if (
            df["Close"][i] < recent_Lows
            and (df["BoS"][i - 1] == 0)
            and (df["Conti"][i - 1] == 0)
        ):
            df.loc[df.index[i] :, "Trend"] = "Downtrend"
            if (df["Trend"][i - 1] == "Downtrend") or (df["Trend"][i - 1] is None):
                df.loc[df.index[i], "BoS"] = 1
            else:
                df.loc[df.index[i], "CHoCH"] = 1
        elif (df["Close"][i] < recent_Lows) & (df["Close"][i] < recent_Highs):
            df.loc[df.index[i], "Conti"] = 1
    return df


# Identify Order Blocks
def identify_order_blocks(df):
    df["Order Block Top"] = np.nan
    df["Order Block Bot"] = np.nan
    last_order_block_index = None

    for i in range(5, len(df)):
        if df.loc[df.index[i], "BoS"]:
            # Find the last opposite-direction candlestick
            for j in range(i - 1, max(i - 5, 0), -1):
                if (
                    df.loc[df.index[j], "Open"] > df.loc[df.index[j], "Close"]
                    and df.loc[df.index[i], "Trend"] == "Uptrend"
                ) or (
                    df.loc[df.index[j], "Open"] < df.loc[df.index[j], "Close"]
                    and df.loc[df.index[i], "Trend"] == "Downtrend"
                ):
                    df.loc[df.index[j], "Order Block Top"] = df.loc[df.index[j], "High"]
                    df.loc[df.index[j], "Order Block Bot"] = df.loc[df.index[j], "Low"]
                    last_order_block_index = j
                    break
            # Check for Fair Value Gap
            if last_order_block_index is not None:
                for k in range(
                    last_order_block_index + 1, min(last_order_block_index + 3, len(df)-3)
                ):
                    if (
                        df.loc[df.index[k], "High"]
                        < df.loc[df.index[k + 2], "Low"] * 1.01
                    ) or (
                        df.loc[df.index[k], "Low"] > df.loc[df.index[k + 2], "High"]
                    ):
                        break
                else:
                    df.loc[df.index[last_order_block_index], "Order Block Top"] = np.nan
                    df.loc[df.index[last_order_block_index], "Order Block Bot"] = np.nan
                    last_order_block_index = None
    return df


##TODO: Implement the breaker block identification


def generate_month_intervals(start_date, end_date):
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")

    current = start
    intervals = []

    while current <= end:
        month_start = current.replace(day=1)
        next_month = (month_start + timedelta(days=32)).replace(day=1)
        month_end = next_month - timedelta(days=1)
        if month_end > end:
            month_end = end
        if month_start < start:
            month_start = start
        intervals.append(
            (month_start.strftime("%Y-%m-%d"), month_end.strftime("%Y-%m-%d"))
        )
        current = next_month

    return intervals


if __name__ == "__main__":

    path = "./ETHUSDT.pkl"
    with open(path, "rb") as file:
        df = pickle.load(file)

    df = identify_trend(df[:30])
    df = identify_order_blocks(df)
    ob = [0, 0]
    for i in range(len(df)):
        if not np.isnan(df.iloc[i]["Order Block Top"]):
            ob = [df.iloc[i]["Order Block Top"], df.iloc[i]["Order Block Bot"]]
    temp_df = df["Close"] * df["BoS"]
    temp_df = temp_df.replace(0, np.nan)
    apd = mpf.make_addplot(
        temp_df, type="scatter", markersize=100, marker="^", color="r", label="BoS"
    )
    mpf.plot(
        df.iloc[:, :5],
        type="candle",
        volume=True,
        style="charles",
        title="BTC/USDT Candlestick Chart with BoS and CHoCH",
        addplot=apd,
        fill_between=dict(y1=ob[0], y2=ob[1]),
    )
