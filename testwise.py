# flake8: noqa
import csv
import copy
import matplotlib.pyplot as plt
from scipy import stats


class Testwise:
    """Testwise initialization class
    """
    def __init__(
            self, initial_capital=100000, commission=0, slippage=0, risk_factor=1.5,
            limit_factor=1, position_risk=0.02, use_margin=True, margin_factor=3,
            use_trailing_stop=False, trailing_stop_activation_ratio=2, dynamic_positioning=False):
        self.initial_capital = initial_capital
        self.commission = commission
        self.slippage = slippage
        self.risk_factor = risk_factor
        self.limit_factor = limit_factor
        self.position_risk = position_risk
        self.use_margin = use_margin
        self.margin_factor = margin_factor
        self.use_trailing_stop = use_trailing_stop
        self.trailing_stop_activation_ratio = trailing_stop_activation_ratio
        self.dynamic_positioning = dynamic_positioning

        self.equity = initial_capital

        self.net_profit = 0
        self.gross_profit = 0
        self.gross_loss = 0
        self.max_drawdown = 0
        self.largest_winning_trade = 0
        self.largest_losing_lrade = 0
        self.total_trades = 0
        self.number_of_winning_traders = 0
        self.number_of_losing_trades = 0

        self.net_profit_record = []
        self.max_drawdown_record = []

        self.pos = 0
        self.current_open_pos = None
        self.positions = []


    def calculate_share(self, current_atr, custom_position_risk=0.02):
        """Calculates how many shares to buy (share = risk / (risk_factor * atr))

        :param current_atr: atr
        :type current_atr: float
        :param custom_position_risk: custom position risk ratio, defaults to 0.02
        :type custom_position_risk: float, optional
        :return: share
        :rtype: float
        """
        if not self.dynamic_positioning:
            risk = self.equity * self.position_risk
            share = risk / (self.risk_factor * current_atr)
            return share
        else:
            risk = self.equity * custom_position_risk
            share = risk / (self.risk_factor * current_atr)
            return share


    def calculate_share_static(self, difference, custom_position_risk=0.02):
        """Calculates how many shares to buy with given price difference from entry to stop loss

        :param difference: price difference from entry to stop loss
        :type difference: float
        :param custom_position_risk: custom position risk ratio, defaults to 0.02
        :type custom_position_risk: float, optional
        :return: share
        :rtype: float
        """
        risk = self.equity * custom_position_risk
        share = risk / (difference)
        return share


    def entry_long(self, date, price, share, current_atr):
        """Opening a long position

        :param date: date of entry
        :type date: string
        :param price: opening price of position
        :type price: float
        :param share: number of shares to buy
        :type share: float
        :param current_atr: atr to define take profit and stop loss
        :type current_atr: float
        """
        if self.current_open_pos is None:
            adjusted_price = price + self.slippage

            if self.use_margin:
                if adjusted_price * share > self.equity * self.margin_factor:
                    share = (self.equity * self.margin_factor) / adjusted_price
            else:
                if adjusted_price * share > self.equity:
                    share = self.equity / adjusted_price

            if self.use_trailing_stop:
                position = {"type": "entry long", "date": date, "price": price,
                            "adj_price": adjusted_price, "qty": share,
                            "tp": price + (self.limit_factor * current_atr),
                            "sl": price - (self.risk_factor * current_atr), "tptaken": False,
                            "ts_active": price + (self.trailing_stop_activation_ratio * current_atr),
                            "ts_atr": current_atr}
            else:
                position = {"type": "entry long", "date": date, "price": price,
                            "adj_price": adjusted_price, "qty": share,
                            "tp": price + (self.limit_factor * current_atr),
                            "sl": price - (self.risk_factor * current_atr), "tptaken": False}
            self.positions.append(position)

            if self.commission != 0:
                self.equity = self.equity - (adjusted_price * share * self.commission)

            self.total_trades = self.total_trades + 1
            self.current_open_pos = copy.copy(position)
            self.pos = 1
        else:
            print("Position already open")


    def exit_long(self, date, price, share, tptaken=False):
        """Closing a long position

        :param date: date of closing
        :type date: string
        :param price: closing price of position
        :type price: float
        :param share: number of shares to sell
        :type share: float
        :param tptaken: True if take profit is taken with this particular transaction, defaults to False
        :type tptaken: bool, optional
        """
        if self.current_open_pos is not None:
            adjusted_price = price - self.slippage
            position = {"type": "exit long", "date": date, "price": price, "adj_price": adjusted_price, "qty": share}
            self.positions.append(position)

            self.equity = self.equity + ((adjusted_price - self.current_open_pos["price"]) * share) - (adjusted_price * share * self.commission)

            if adjusted_price - self.current_open_pos["price"] > 0:
                self.gross_profit = self.gross_profit + ((adjusted_price - self.current_open_pos["price"]) * share) - (adjusted_price * share * self.commission)
                if not self.current_open_pos["tptaken"]:
                    self.number_of_winning_traders = self.number_of_winning_traders + 1
            else:
                self.gross_loss = self.gross_loss + abs(((adjusted_price - self.current_open_pos["price"]) * share)) + (adjusted_price * share * self.commission)
                if not self.current_open_pos["tptaken"]:
                    self.number_of_losing_trades = self.number_of_losing_trades + 1

            self.net_profit_record.append((date, self.equity - self.initial_capital))
            self.net_profit = self.equity - self.initial_capital
            self.__update_drawdown_record()
            self.max_drawdown = self.get_max_drawdown()

            if self.current_open_pos["qty"] == share:
                self.current_open_pos = None
                self.pos = 0

            if tptaken:
                self.current_open_pos["tptaken"] = True
                self.current_open_pos["qty"] = self.current_open_pos["qty"] - share

        else:
            print("No position to exit")


    def entry_short(self, date, price, share, current_atr):
        """Opening a short position

        :param date: date of entry
        :type date: string
        :param price: opening price of position
        :type price: float
        :param share: number of shares to short
        :type share: float
        :param current_atr: atr to define take profit and stop loss
        :type current_atr: float
        """
        if self.current_open_pos is None:
            adjusted_price = price - self.slippage

            if self.use_margin:
                if adjusted_price * share > self.equity * (self.margin_factor - 1):
                    share = (self.equity * (self.margin_factor - 1)) / adjusted_price
            else:
                if adjusted_price * share > self.equity:
                    share = self.equity / adjusted_price

            if self.use_trailing_stop:
                position = {
                    "type": "entry short", "date": date, "price": price, "adj_price": adjusted_price,
                    "qty": share, "tp": price - (self.limit_factor * current_atr),
                    "sl": price + (self.risk_factor * current_atr), "tptaken": False,
                    "ts_active": price - (self.trailing_stop_activation_ratio * current_atr),
                    "ts_atr": current_atr}
            else:
                position = {
                    "type": "entry short", "date": date, "price": price, "adj_price": adjusted_price,
                    "qty": share, "tp": price - (self.limit_factor * current_atr),
                    "sl": price + (self.risk_factor * current_atr), "tptaken": False}
            self.positions.append(position)

            if self.commission != 0:
                self.equity = self.equity - (adjusted_price * share * self.commission)

            self.total_trades = self.total_trades + 1
            self.current_open_pos = copy.copy(position)
            self.pos = -1
        else:
            print("Position already open")


    def exit_short(self, date, price, share, tptaken=False):
        """Closing a short position

        :param date: date of closing
        :type date: string
        :param price: closing price of position
        :type price: float
        :param share: number of shares to short-sell
        :type share: float
        :param tptaken: True if take profit is taken with this particular transaction, defaults to False
        :type tptaken: bool, optional
        """
        if self.current_open_pos is not None:
            adjusted_price = price + self.slippage
            position = {"type": "exit short", "date": date, "price": price, "adj_price": adjusted_price, "qty": share}
            self.positions.append(position)

            self.equity = self.equity - ((adjusted_price - self.current_open_pos["price"]) * share) - (adjusted_price * share * self.commission)

            if adjusted_price - self.current_open_pos["price"] < 0:
                self.gross_profit = self.gross_profit + abs(((adjusted_price - self.current_open_pos["price"]) * share)) - (adjusted_price * share * self.commission)
                if not self.current_open_pos["tptaken"]:
                    self.number_of_winning_traders = self.number_of_winning_traders + 1
            else:
                self.gross_loss = self.gross_loss + ((adjusted_price - self.current_open_pos["price"]) * share) + (adjusted_price * share * self.commission)
                if not self.current_open_pos["tptaken"]:
                    self.number_of_losing_trades = self.number_of_losing_trades + 1

            self.net_profit_record.append((date, self.equity - self.initial_capital))
            self.net_profit = self.equity - self.initial_capital
            self.__update_drawdown_record()
            self.max_drawdown = self.get_max_drawdown()

            if self.current_open_pos["qty"] == share:
                self.current_open_pos = None
                self.pos = 0

            if tptaken:
                self.current_open_pos["tptaken"] = True
                self.current_open_pos["qty"] = self.current_open_pos["qty"] - share

        else:
            print("No position to exit")


    def break_even(self, adjust_level=False, tpratio=0.5, slippage=0):
        """Change stop loss level to break even. This function could be used after take profit.
        """
        if not adjust_level:
            self.current_open_pos["sl"] = self.current_open_pos["price"]
        else:
            if self.pos == 1:
                self.current_open_pos["sl"] = self.current_open_pos["price"] \
                    + (self.current_open_pos["price"] * self.current_open_pos["qty"] * self.commission) \
                    + (self.current_open_pos["tp"] * (self.current_open_pos["qty"] * tpratio) * self.commission) \
                    + (2 * slippage)
            elif self.pos == -1:
                self.current_open_pos["sl"] = self.current_open_pos["price"] \
                    - (self.current_open_pos["price"] * self.current_open_pos["qty"] * self.commission) \
                    - (self.current_open_pos["tp"] * (self.current_open_pos["qty"] * tpratio) * self.commission) \
                    - (2 * slippage)


    def set_trailing_stop(self, price, ts_atr):
        """Setting trailing stop

        :param price: close price when trailing stop level reached
        :type price: float
        :param ts_atr: atr value of position opening
        :type ts_atr: float
        """
        if self.pos == 1:
            self.current_open_pos["sl"] = price - ts_atr
        elif self.pos == -1:
            self.current_open_pos["sl"] = price + ts_atr


    def get_result(self):
        """Generates backtest results

        :return: a dictionary of backtest results including various ratios.
        :rtype: dictionary
        """
        result = {
            "net_profit": self.net_profit, "net_profit_percent": self.get_net_profit_percent(),
            "gross_profit": self.gross_profit, "gross_loss": self.gross_loss, "max_drawdown": self.max_drawdown,
            "max_drawdown_rate": self.get_max_drawdown_rate(), "win_rate": self.get_win_rate(),
            "risk_reward_ratio": self.get_risk_reward_ratio(), "profit_factor": self.get_profit_factor(),
            "ehlers_ratio": self.get_ehlers_ratio(), "return_on_capital": self.get_return_on_capital(),
            "max_capital_required": self.get_max_capital_required(), "total_trades": self.total_trades, "pearsonsr": self.get_pearsons_r(),
            "number_of_winning_trades": self.number_of_winning_traders, "number_of_losing_trades": self.number_of_losing_trades,
            "largest_winning_trade": self.get_largest_winning_trade(), "largest_losing_trade": self.get_largest_losing_trade()}
        return result


    def get_net_profit(self):
        """Net profit

        :return: net profit
        :rtype: float
        """
        npr = self.net_profit_record[-1]
        net_profit = npr[1]
        return net_profit


    def get_net_profit_percent(self):
        """Net profit percent value

        :return: net profit percent value
        :rtype: float
        """
        if len(self.net_profit_record) > 0:
            npr = self.net_profit_record[-1]
            npp = self.__calculate_percent(npr[1], self.initial_capital)
            return npp
        else:
            return 0.0


    def get_max_drawdown(self):
        """Calculates maximum drawdown

        :return: maximum drawdown
        :rtype: float
        """
        if len(self.max_drawdown_record) > 0:
            maxddr = self.max_drawdown_record[0]
            for mdr in self.max_drawdown_record:
                if mdr[2] < maxddr[2]:
                    maxddr = mdr
            return maxddr[2]
        else:
            return 0.0


    def get_max_drawdown_rate(self):
        """Calculates rate of maximum drawdown

        :return: rate of maximum drawdown
        :rtype: float
        """
        if self.get_max_drawdown() == 0:
            return 0
        else:
            mddr = self.net_profit / abs(self.get_max_drawdown())
            return mddr


    def get_risk_reward_ratio(self):
        """Calculates risk reward ratio

        :return: risk reward ratio
        :rtype: float
        """
        if self.number_of_losing_trades == 0:
            self.number_of_losing_trades = 0.0001

        if self.number_of_winning_traders == 0:
            self.number_of_winning_traders = 0.0001

        risk = self.gross_profit / self.number_of_winning_traders
        reward = self.gross_loss / self.number_of_losing_trades

        if reward == 0:
            reward = 0.0001
        return risk / reward


    def get_win_rate(self):
        """Calculates win rate

        :return: win rate
        :rtype: float
        """
        if self.total_trades > 0:
            win_rate = (self.number_of_winning_traders * 100) / self.total_trades
            return win_rate
        else:
            return 0.0


    def get_max_capital_required(self):
        """Calculates maximum capital required for the strategy

        :return: maximum capital required
        :rtype: float
        """
        mcr = self.initial_capital + abs(self.get_max_drawdown())
        return mcr


    def get_return_on_capital(self):
        """Calculates return on capital

        :return:  return on capital
        :rtype: float
        """
        roc = self.net_profit / self.get_max_capital_required()
        return roc


    def get_profit_factor(self):
        """Calculates profit factor

        :return: profit factor
        :rtype: float
        """
        if self.gross_loss == 0:
            self.gross_loss = 0.0001
        profit_factor = self.gross_profit / self.gross_loss
        return profit_factor


    def get_largest_winning_trade(self):
        """Largest winning trade

        :return: date and value of largest winning trade
        :rtype: tuple
        """
        if len(self.net_profit_record) > 0:
            maxnpr = self.net_profit_record[0]
            for i in range(0, len(self.net_profit_record)):
                if i > 0:
                    nprf = self.net_profit_record[i][1] - self.net_profit_record[i-1][1]
                    if nprf > maxnpr[1]:
                        maxnpr = self.net_profit_record[i]
            return maxnpr
        else:
            return None


    def get_largest_losing_trade(self):
        """Largest losing trade

        :return: date and value of largest losing trade
        :rtype: tuple
        """
        if len(self.net_profit_record) > 0:
            minnpr = self.net_profit_record[0]
            for i in range(0, len(self.net_profit_record)):
                if i > 0:
                    nprf = self.net_profit_record[i][1] - self.net_profit_record[i-1][1]
                    if nprf < minnpr[1]:
                        minnpr = self.net_profit_record[i]
            return minnpr
        else:
            return None


    def get_ehlers_ratio(self):
        """Calculates ratio given by Ehlers, for choosing best optimization results

        :return: [description]ehlers ration
        :rtype: float
        """
        ehlers_ratio = (2 * (self.get_win_rate() / 100) - 1) * self.get_profit_factor()
        return ehlers_ratio


    def get_pearsons_r(self):
        """Calculate pearsons r for net profit record.
        """
        if len(self.net_profit_record) > 2:
            npr = []
            for _, k in enumerate(self.net_profit_record):
                npr.append(k[1])

            x = range(0, len(npr))

            psrs = stats.pearsonr(x, npr)
            return psrs[0]
        else:
            return -1


    def write_trades_to_csv(self, name="trades"):
        """Write all transactions to a csv file

        :param name: name of the csv file, defaults to "trades"
        :type name: str, optional
        """
        file = open(name + ".csv", "w", newline="")
        with file:
            fnames = ["type", "date", "price", "adj_price", "qty", "tp", "sl", "tptaken"]

            writer = csv.DictWriter(file, fieldnames=fnames)
            writer.writeheader()
            for trade in self.positions:
                writer.writerow(trade)


    def draw_net_profit_graph(self):
        """Draws net profit graph
        """
        plt.plot(*zip(*self.net_profit_record))
        plt.show()


    def print_out_all_positions(self):
        """Prints out all trades line by line
        """
        for pos in self.positions:
            print(pos)


    def __update_drawdown_record(self):
        """Records drawdon to calculate maximum drawdown
        """
        maxnp = self.net_profit_record[0]
        for npr in self.net_profit_record:
            if npr[1] > maxnp[1]:
                maxnp = npr
        self.max_drawdown_record.append((maxnp[0], self.net_profit_record[-1][0], self.net_profit_record[-1][-1] - maxnp[1]))


    def __calculate_percent(self, nominator, denominator):
        """Calculates percent value with given nominator and denominator

        :param nominator: nominator
        :type nominator: float
        :param denominator: denominator
        :type denominator: float
        :return: percent value
        :rtype: float
        """
        return (100 * nominator) / denominator
