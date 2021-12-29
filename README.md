# Testwise

![Publish Python 🐍 distributions 📦 to PyPI and TestPyPI](https://github.com/aticio/legitindicators/workflows/Publish%20Python%20%F0%9F%90%8D%20distributions%20%F0%9F%93%A6%20to%20PyPI%20and%20TestPyPI/badge.svg)

A backtester (backtest helper) for testing my trading strategies.

## Example Usage
Note: Explanatory comments will be updated soon.
```python
# Testwise is a backtester library that requires some coding knowledge
# There is no cli or interface. 
# You should directly execute necessary functions like enter_long() or exit_short()
# This is a backtesting example of Exponantial Moving Average cross strategy.
# There is 1.5 ATR stop loss level and 1 ATR take profit level for every position. 
# Commission rate is 0.1000%. 
# Margin usage is allowed up to 5 times the main capital.
from datetime import datetime, timedelta
from testwise import Testwise
import requests
from legitindicators import ema, atr

# In this example, daily BTCUSDT kline data is used from binance
# Let's say you want to backtest your strategy for 180 days.
# It would be useful to add some extra days to the specified time interval
# for the indicators to work properly.
# (For example a 10 days of EMA won't be calculated for the first 9 days of time range)
# In this examle I add 40 extra days. This value can be determined by assigning the TRIM variable
TRIM = 40
BINANCE_URL = "https://api.binance.com/api/v3/klines"
SYMBOL = "BTCUSDT"
INTERVAL = "1d"

# These are the initial paramteres for backtester.
# You can find a more detailed explanation where the Testwise definition is given below.
COMMISSION = 0.001
DYNAMIC_POSITIONING = True
MARGIN_FACTOR = 5
LIMIT_FACTOR = 1
RISK_FACTOR = 1.5


def main():
    # Here we define start time and end time of backtest.
    # Notice usage of TRIM variable to start backtest a few days earlier for proper indicator use.
    start_time = datetime(2020, 6, 1, 0, 0, 0)
    start_time = start_time - timedelta(days=TRIM)

    end_time = datetime(2021, 9, 1, 0, 0, 0)

    # In this example, timestamps are used. (Because binance api requests accept timestamp)
    start_time_ts = int(datetime.timestamp(start_time) * 1000)
    end_time_ts = int(datetime.timestamp(end_time) * 1000)

    backtest(start_time_ts, end_time_ts)


def backtest(start_time, end_time):
    # Getting OHLC data
    params = {"symbol": SYMBOL, "interval": INTERVAL, "startTime": start_time, "endTime": end_time}
    data = get_data(params)
    opn, high, low, close = get_ohlc(data)

    # Backtest section
    lookback = len(data) - TRIM

    data = data[-lookback:]
    close_tmp = close[-lookback:]
    opn = opn[-lookback:]
    high = high[-lookback:]
    low = low[-lookback:]

    # ATR
    atr_input = []
    for i, _ in enumerate(data):
        ohlc = [opn[i], high[i], low[i], close_tmp[i]]
        atr_input.append(ohlc)
    atrng = atr(atr_input, 14)

    for ema_length1 in range(10, 11):
        for ema_length2 in range(ema_length1 + 1, 12):
            # When the dynamic_positioning is set to True, 
            # the backtester will work as if the margin usage is available for use.
            # margin_factor indicates the margin ratio. (In this example, it is 5 times the main capital)
            # limit_factor is an ATR based take profit level. (In this example, it is 1 ATR from the position price)
            # risk_factor is an ATR based stop loss level. (In this example, it is 1.5 ATR from the position price)
            twise = Testwise(
                commission=COMMISSION,
                dynamic_positioning=DYNAMIC_POSITIONING,
                margin_factor=MARGIN_FACTOR,
                limit_factor=LIMIT_FACTOR,
                risk_factor=RISK_FACTOR
            )

            ema_first = ema(close, ema_length1)
            ema_second = ema(close, ema_length2)
            ema_first = ema_first[-lookback:]
            print(ema_first)
            ema_second = ema_second[-lookback:]

            for i, _ in enumerate(data):
                if i > 1 and i < len(data) - 1:
                    date_open = datetime.fromtimestamp(int(data[i+1][0] / 1000)).strftime("%Y-%m-%d %H")
                    date_close = datetime.fromtimestamp(int(data[i][0] / 1000)).strftime("%Y-%m-%d %H")

                    # Position exits
                    if twise.pos == 1 and (ema_first[i] < ema_second[i]):
                        twise.exit_long(date_close, opn[i + 1], twise.current_open_pos["qty"])

                    if twise.pos == -1 and (ema_first[i] > ema_second[i]):
                        twise.exit_short(date_close, opn[i + 1], twise.current_open_pos["qty"])

                    if abs(high[i] - opn[i]) < abs(low[i] - opn[i]):
                        # open - high - low - close

                        # if long
                        #   TP check
                        if twise.pos == 1 and high[i] > twise.current_open_pos["tp"] and twise.current_open_pos["tptaken"] is False:
                            twise.break_even()
                            twise.exit_long(date_close, twise.current_open_pos["tp"], twise.current_open_pos["qty"] / 2, True)

                        #   SL check
                        if twise.pos == 1 and low[i] < twise.current_open_pos["sl"]:
                            twise.exit_long(date_close, twise.current_open_pos["sl"], twise.current_open_pos["qty"])

                        # if short
                        #   SL check
                        if twise.pos == -1 and high[i] > twise.current_open_pos["sl"]:
                            twise.exit_short(date_close, twise.current_open_pos["sl"], twise.current_open_pos["qty"])

                        #   TP check
                        if twise.pos == -1 and low[i] < twise.current_open_pos["tp"] and twise.current_open_pos["tptaken"] is False:
                            twise.break_even()
                            twise.exit_short(date_close, twise.current_open_pos["tp"], twise.current_open_pos["qty"] / 2, True)
                    else:
                        # open - low - high - close

                        # if long
                        #   SL check
                        if twise.pos == 1 and low[i] < twise.current_open_pos["sl"]:
                            twise.exit_long(date_close, twise.current_open_pos["sl"], twise.current_open_pos["qty"])

                        #   TP check
                        if twise.pos == 1 and high[i] > twise.current_open_pos["tp"] and twise.current_open_pos["tptaken"] is False:
                            twise.break_even()
                            twise.exit_long(date_close, twise.current_open_pos["tp"], twise.current_open_pos["qty"] / 2, True)

                        # if short
                        #   TP check
                        if twise.pos == -1 and low[i] < twise.current_open_pos["tp"] and twise.current_open_pos["tptaken"] is False:
                            twise.break_even()
                            twise.exit_short(date_close, twise.current_open_pos["tp"], twise.current_open_pos["qty"] / 2, True)

                        #   SL check
                        if twise.pos == -1 and high[i] > twise.current_open_pos["sl"]:
                            twise.exit_short(date_close, twise.current_open_pos["sl"], twise.current_open_pos["qty"])

                    # Open position
                    if twise.pos != 1:
                        if ema_first[i] > ema_second[i]:
                            share = twise.calculate_share(atrng[i], custom_position_risk=0.02)
                            twise.entry_long(date_open, opn[i + 1], share, atrng[i])

                    if twise.pos != -1:
                        if ema_first[i] < ema_second[i]:
                            share = twise.calculate_share(atrng[i], custom_position_risk=0.02)
                            twise.entry_short(date_open, opn[i + 1], share, atrng[i])
            print(twise.get_result())


def get_data(params):
    r = requests.get(url=BINANCE_URL, params=params)
    data = r.json()
    return data


def get_ohlc(data):
    opn = [float(o[1]) for o in data]
    close = [float(d[4]) for d in data]
    high = [float(h[2]) for h in data]
    low = [float(lo[3]) for lo in data]

    return opn, high, low, close


if __name__ == "__main__":
    main()
```

## Installation

Run the following to install:

```python
pip install testwise
```
