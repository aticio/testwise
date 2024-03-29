# Testwise

![Publish Python 🐍 distributions 📦 to PyPI and TestPyPI](https://github.com/aticio/legitindicators/workflows/Publish%20Python%20%F0%9F%90%8D%20distributions%20%F0%9F%93%A6%20to%20PyPI%20and%20TestPyPI/badge.svg)

A backtester (backtest helper) for testing my trading strategies.

It requires a lot of manual processing and coding. Difficult to comprehend. I tried to explain the use of the library with examples as best I could. But writing such automation is quite complex.
There may still be errors. It is pretty difficult to check but I'm trying to improve the usage.

## Example Usage
```python
# Testwise is a backtester library that requires some coding knowledge
# There is no cli or interface. 
# You should directly execute necessary functions like enter_long() or exit_short()
# This is a backtesting example of Exponential Moving Average cross strategy.
# There is a 1.5 ATR stop loss level and a 1 ATR take profit level for every position. 
# Commission rate is 0.1000%. 
# Margin usage is allowed up to 5 times the main capital.
from datetime import datetime, timedelta
from testwise import Testwise
import requests
from legitindicators import ema, atr

# In this example, daily BTCUSDT kline data is used from binance
# Let's say you want to backtest your strategy for about 450 days.
# It would be useful to add some extra days to the specified time interval
# for the indicators to work properly.
# (For example 10 days of EMA won't be calculated for the first 9 days of time range)
# In this example I add 40 extra days. This value can be determined by assigning the TRIM variable
TRIM = 40
BINANCE_URL = "https://api.binance.com/api/v3/klines"
SYMBOL = "BTCUSDT"
INTERVAL = "1d"

# These are the initial paramters for backtester.
# You can find a more detailed explanation where the Testwise definition is given below.
COMMISSION = 0.001
DYNAMIC_POSITIONING = True
MARGIN_FACTOR = 5
LIMIT_FACTOR = 1
RISK_FACTOR = 1.5


def main():
    # Here we define the start time and end time of backtesting.
    # Notice usage of TRIM variable to start to backtest a few days earlier for proper indicator use.
    start_time = datetime(2020, 6, 1, 0, 0, 0)
    start_time = start_time - timedelta(days=TRIM)

    end_time = datetime(2021, 9, 1, 0, 0, 0)

    # In this example, timestamps are used. (Because binance accept timestamp)
    start_time_ts = int(datetime.timestamp(start_time) * 1000)
    end_time_ts = int(datetime.timestamp(end_time) * 1000)

    backtest(start_time_ts, end_time_ts)


def backtest(start_time, end_time):
    # Getting OHLC data
    # Example binance kline response
    # [
    #     [
    #         1499040000000,      // Open time
    #         "0.01634790",       // Open
    #         "0.80000000",       // High
    #         "0.01575800",       // Low
    #         "0.01577100",       // Close
    #         "148976.11427815",  // Volume
    #         1499644799999,      // Close time
    #         "2434.19055334",    // Quote asset volume
    #         308,                // Number of trades
    #         "1756.87402397",    // Taker buy base asset volume
    #         "28.46694368",      // Taker buy quote asset volume
    #         "17928899.62484339" // Ignore.
    #     ]
    # ]
    params = {"symbol": SYMBOL, "interval": INTERVAL, "startTime": start_time, "endTime": end_time}
    data = get_data(params)
    opn, high, low, close = get_ohlc(data)

    # Again for proper indicator usage number of bars to work on is defined as lookback
    lookback = len(data) - TRIM

    # These are simply trimmed OHLC data
    data = data[-lookback:]
    # Here, a list of close prices kept under different naming conventions than other OHL data
    # That is because I will use this close data as a parameter 
    # for Exponential Moving Average indicator and then trim the list of EMA values afterward.
    close_tmp = close[-lookback:]
    opn = opn[-lookback:]
    high = high[-lookback:]
    low = low[-lookback:]

    # Here is the calculation of ATR values historically. I use legitindicators library.
    atr_input = []
    for i, _ in enumerate(data):
        ohlc = [opn[i], high[i], low[i], close_tmp[i]]
        atr_input.append(ohlc)
    atrng = atr(atr_input, 14)

    # Backtesting operation starts here.
    # Following two for loops will check two EMA crosses in the range of 10 to 30
    for ema_length1 in range(10, 11):
        for ema_length2 in range(ema_length1 + 1, 30):
            # When the dynamic_positioning is set to True, 
            # the backtester will work as if the margin usage is available for use.
            # margin_factor indicates the margin ratio. (In this example, it is 5 times the main capital)
            # limit_factor is an ATR based take profit level. (it is 1 ATR from the position price)
            # risk_factor is an ATR based stop loss level. (it is 1.5 ATR from the position price)
            twise = Testwise(
                commission=COMMISSION,
                dynamic_positioning=DYNAMIC_POSITIONING,
                margin_factor=MARGIN_FACTOR,
                limit_factor=LIMIT_FACTOR,
                risk_factor=RISK_FACTOR
            )

            # Here, two EMA indicators are defined. I use legitindicators library.
            ema_first = ema(close, ema_length1)
            ema_second = ema(close, ema_length2)
            # List of indicator values trimmed accordingly
            ema_first = ema_first[-lookback:]
            ema_second = ema_second[-lookback:]

            # Notice that at this point:
            # open, high, low, close, ema_first and ema_second lists are all trimmed
            #  and all have the same length
            # Ready for testing

            # Start walking on the data taken from the binance.
            for i, _ in enumerate(data):
                # Exclude first price data
                if i > 1 and i < len(data) - 1:
                    # Here, data[n][0] is the open time of price data
                    # date_open is kept for use if there will be a pose to be opened the next day
                    # date_close is kept for use if the current open position is closed in this iteration
                    date_open = datetime.fromtimestamp(int(data[i+1][0] / 1000)).strftime("%Y-%m-%d %H")
                    date_close = datetime.fromtimestamp(int(data[i][0] / 1000)).strftime("%Y-%m-%d %H")

                    # Position exits
                    # On every iteration, position exits checked firstly 
                    # Below, if the current position is long (1 means long) and
                    # the ema_first crosses below the ema_second, position exit function triggered
                    if twise.pos == 1 and (ema_first[i] < ema_second[i]):
                        # exit_long function takes closing date, 
                        # closing price as open price of next day opn[i + 1],
                        # and amount to close the position. 
                        # This amount already kept in twise.current_open_pos["qty"].
                        # This value is set when opening the positions
                        twise.exit_long(date_close, opn[i + 1], twise.current_open_pos["qty"])

                    # Closing short position(-1 means short)
                    if twise.pos == -1 and (ema_first[i] > ema_second[i]):
                        twise.exit_short(date_close, opn[i + 1], twise.current_open_pos["qty"])

                    # The following if condition simulates price movements inside the bar. 
                    # This is crucial if you want to add take profit and stop loss logic to the backtester.
                    # This pine script broker emulator documentation will explain this condition more clearly:
                    # https://www.tradingview.com/pine-script-docs/en/v5/concepts/Strategies.html?highlight=strategy#broker-emulator
                    if abs(high[i] - opn[i]) < abs(low[i] - opn[i]):
                        # Simply, If the bar’s high is closer to bar’s open than the bar’s low, 
                        # bar movement will be like: 
                        # open - high - low - close

                        # In this movement, take profit operation will be checked before stop loss. 
                        # This is because, it is assumed that the price will go up first. 
                        # For example, if both take profit and stop loss prices are exceeded, 
                        # it is assumed that first, take profit is taken, than stop loss price is reached.

                        # if current position is long, here is take profit logic:
                        # if current position is long and high is 
                        # higher than take proift price (twise.current_open_pos["tp"]) 
                        # and take profit is not taken (twise.current_open_pos["tptaken"] is False)
                        if twise.pos == 1 and high[i] > twise.current_open_pos["tp"] and twise.current_open_pos["tptaken"] is False:
                            # Stop loss price will be set to break even with break_even() function
                            twise.break_even()
                            # Take profit operation is simply a partially position closing operation. 
                            # Here, half of the position is closed. (twise.current_open_pos["qty"] / 2)  
                            twise.exit_long(date_close, twise.current_open_pos["tp"], twise.current_open_pos["qty"] / 2, True)

                        # if current position is long, here is stop loss logic:
                        # if current position is long and low is 
                        # lower than stop loss price (twise.current_open_pos["sl"])
                        if twise.pos == 1 and low[i] < twise.current_open_pos["sl"]:
                            twise.exit_long(date_close, twise.current_open_pos["sl"], twise.current_open_pos["qty"])

                        # if current position is short, here is take profit logic:
                        if twise.pos == -1 and high[i] > twise.current_open_pos["sl"]:
                            twise.exit_short(date_close, twise.current_open_pos["sl"], twise.current_open_pos["qty"])

                        # if current position is short, here is stop loss logic:
                        if twise.pos == -1 and low[i] < twise.current_open_pos["tp"] and twise.current_open_pos["tptaken"] is False:
                            twise.break_even()
                            twise.exit_short(date_close, twise.current_open_pos["tp"], twise.current_open_pos["qty"] / 2, True)
                    else:
                        # If the bar’s low is closer to bar’s open than the bar’s high, 
                        # bar movement will be like: 
                        # open - low - high - close

                        # In this movement, stop loss operation will be checked before take profit. 
                        # This is because, it is assumed that the price will go down firstly. 
                        # For example, if both take profit and stop loss prices are exceeded,
                        # it is assumed that first, stop loss is executed, 
                        # then take profit will never be reached because 
                        # if the position is fully closed with exit_long, 
                        # twise.pos value will be 0 (which means there is no open position).

                        # if the current position is long, here is stop loss logic:
                        if twise.pos == 1 and low[i] < twise.current_open_pos["sl"]:
                            twise.exit_long(date_close, twise.current_open_pos["sl"], twise.current_open_pos["qty"])

                        # if current position is long, here is take profit logic:
                        if twise.pos == 1 and high[i] > twise.current_open_pos["tp"] and twise.current_open_pos["tptaken"] is False:
                            twise.break_even()
                            twise.exit_long(date_close, twise.current_open_pos["tp"], twise.current_open_pos["qty"] / 2, True)

                        # if current position is short, here is take profit logic:
                        if twise.pos == -1 and low[i] < twise.current_open_pos["tp"] and twise.current_open_pos["tptaken"] is False:
                            twise.break_even()
                            twise.exit_short(date_close, twise.current_open_pos["tp"], twise.current_open_pos["qty"] / 2, True)

                        # if current position is short, here is stop loss logic:
                        if twise.pos == -1 and high[i] > twise.current_open_pos["sl"]:
                            twise.exit_short(date_close, twise.current_open_pos["sl"], twise.current_open_pos["qty"])

                    # Opening long position
                    # If there is no long positions open
                    if twise.pos != 1:
                        # If ema_first crosses over ema_second
                        if ema_first[i] > ema_second[i]:
                            # You can manually set the amount to open position. 
                            # But there will be a calculation overhead.
                            # Testwise has a built-in share calculation funciton
                            # In tihs function, share is calculated as: 
                            # share = (equity * position risk) / (atr * risk factor)
                            share = twise.calculate_share(atrng[i], custom_position_risk=0.02)
                            # Opening long position with opening date (date_open), 
                            # opening price of next day (opn[i + 1]),
                            # amount to buy, and current atr value to define take profit and stop loss prices
                            twise.entry_long(date_open, opn[i + 1], share, atrng[i])

                    if twise.pos != -1:
                        if ema_first[i] < ema_second[i]:
                            share = twise.calculate_share(atrng[i], custom_position_risk=0.02)
                            # Opening short position with opening date (date_open), 
                            # opening price of next day (opn[i + 1]),
                            # amount to buy, and current atr value to define take profit and stop loss prices
                            twise.entry_short(date_open, opn[i + 1], share, atrng[i])
            # get_result() function will give you the backtest results
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

```python
Example backtest result:
{
    'net_profit': 30557.012567638478, 
    'net_profit_percent': 30.557012567638477, 
    'gross_profit': 69163.31181062985, 
    'gross_loss': 36783.34343506002, 
    'max_drawdown': -13265.365111723615, 
    'max_drawdown_rate': 2.3035183962356918, 
    'win_rate': 53.48837209302326, 
    'risk_reward_ratio': 1.6350338129618904, 
    'profit_factor': 1.880288884906174, 
    'ehlers_ratio': 0.1311829454585705, 
    'return_on_capital': 0.26978249297565415, 
    'max_capital_required': 113265.36511172361, 
    'total_trades': 43, 
    'pearsonsr': 0.8022110890986095, 
    'number_of_winning_trades': 23, 
    'number_of_losing_trades': 20, 
    'largest_winning_trade': ('2021-01-23 03', 34417.71907928039), 
    'largest_losing_trade': ('2020-09-21 03', -4627.351985682239)}
```

## Important note: 
Do not rely on a single test result. 
At least do walkforward test with a few iterations.

## Installation

Run the following to install:

```python
pip install testwise
```
