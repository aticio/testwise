"""Testwise"""
import statistics
import csv
import copy
import matplotlib.pyplot as plt

class Testwise:
    """Testwise initialization class
    """
    def __init__(
            self, initial_capital=100000, commission=0, slippage=0, risk_factor=1.5,
            limit_factor=1, position_risk=0.02, use_margin=True, margin_factor=3,
            use_trailing_stop=False, trailing_stop_activation_ratio=2):
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

        self.equity = initial_capital
        self.cash = initial_capital

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
        self.sortino_record = []

        self.pos = 0
        self.current_open_pos = None
        self.positions = []

    def calculate_share(self, current_atr):
        """Calculates how many shares to buy in nnfx way

        Arguments:
            current_atr {float} -- atr
            current_atr_pips {float} -- atr in pips

        Returns:
            float -- shares to buy
        """
        risk = self.equity * self.position_risk
        share = risk / (self.risk_factor * current_atr)
        return share

    def entry_long(self, date, price, share, current_atr):
        """Opening a long position

        Arguments:
            date {string} -- date of entry
            price {float} -- opening price of position
            share {float} -- number of shares to buy
            current_atr {float} -- atr to define take profit and stop loss
            """
        if self.current_open_pos is None:
            adjusted_price = price + self.slippage

            if self.use_margin:
                if adjusted_price * share > self.equity * self.margin_factor:
                    share = ((self.equity * self.margin_factor) - (self.equity * self.position_risk))  / adjusted_price
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
                self.cash = self.cash - (adjusted_price * share) - (adjusted_price * share * self.commission)
                self.equity = self.equity - (adjusted_price * share * self.commission)
            else:
                self.cash = self.cash - (adjusted_price * share) - (adjusted_price * share)

            self.total_trades = self.total_trades + 1
            self.current_open_pos = copy.copy(position)
            self.pos = 1
        else:
            print("Position already open")

    def exit_long(self, date, price, share, tptaken=False):
        """Closing a long position

        Arguments:
            date {string} -- date of closing
            price {float} -- closing price of position
            share {float} -- number of shares to sell

        Keyword Arguments:
            tptaken {bool} -- True if take profit is taken with this particular transaction (default: {False})
        """
        if self.current_open_pos is not None:
            adjusted_price = price - self.slippage
            position = {"type": "exit long", "date":date, "price": price, "adj_price": adjusted_price, "qty": share}
            self.positions.append(position)

            self.equity = self.equity + ((adjusted_price - self.current_open_pos["price"]) * share) - (adjusted_price * share * self.commission)
            self.cash = self.cash + ((adjusted_price - self.current_open_pos["price"]) * share) - (adjusted_price * share * self.commission)

            if adjusted_price - self.current_open_pos["price"] > 0:
                self.gross_profit = self.gross_profit + ((adjusted_price - self.current_open_pos["price"]) * share)
                if not self.current_open_pos["tptaken"]:
                    self.number_of_winning_traders = self.number_of_winning_traders + 1
            else:
                self.gross_loss = self.gross_loss + abs(((adjusted_price - self.current_open_pos["price"]) * share))
                if not self.current_open_pos["tptaken"]:
                    self.number_of_losing_trades = self.number_of_losing_trades + 1

            self.net_profit_record.append((date, self.equity - self.initial_capital))
            self.net_profit = self.equity - self.initial_capital
            self.__update_drawdown_record()
            self.sortino_record.append((adjusted_price - self.current_open_pos["price"]) * share)
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

        Arguments:
            date {string} -- date of entry
            price {float} -- opening price of position
            share {float} -- number of shares to short
            current_atr {float} -- atr to define take profit and stop loss
            """
        if self.current_open_pos is None:
            adjusted_price = price - self.slippage

            if self.use_margin:
                if adjusted_price * share > self.equity * self.margin_factor:
                    share = ((self.equity * self.margin_factor) - (self.equity * self.position_risk))  / adjusted_price
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
                self.cash = self.cash - (adjusted_price * share) - (adjusted_price * share * self.commission)
                self.equity = self.equity - (adjusted_price * share * self.commission)
            else:
                self.cash = self.cash - (adjusted_price * share) - (adjusted_price * share)

            self.total_trades = self.total_trades + 1
            self.current_open_pos = copy.copy(position)
            self.pos = -1
        else:
            print("Position already open")

    def exit_short(self, date, price, share, tptaken=False):
        """Closing a short position

        Arguments:
            date {string} -- date of closing
            price {float} -- closing price of position
            share {float} -- number of shares to short-sell

        Keyword Arguments:
            tptaken {bool} -- True if take profit is taken with this particular transaction (default: {False})
        """
        if self.current_open_pos is not None:
            adjusted_price = price + self.slippage
            position = {"type": "exit short", "date":date, "price": price, "adj_price": adjusted_price, "qty": share}
            self.positions.append(position)

            self.equity = self.equity - ((adjusted_price - self.current_open_pos["price"]) * share) - (adjusted_price * share * self.commission)
            self.cash = self.cash - ((adjusted_price - self.current_open_pos["price"]) * share) - (adjusted_price * share * self.commission)

            if adjusted_price - self.current_open_pos["price"] < 0:
                self.gross_profit = self.gross_profit + abs(((adjusted_price - self.current_open_pos["price"]) * share))
                if not self.current_open_pos["tptaken"]:
                    self.number_of_winning_traders = self.number_of_winning_traders + 1
            else:
                self.gross_loss = self.gross_loss + ((adjusted_price - self.current_open_pos["price"]) * share)
                if not self.current_open_pos["tptaken"]:
                    self.number_of_losing_trades = self.number_of_losing_trades + 1

            self.net_profit_record.append((date, self.equity - self.initial_capital))
            self.net_profit = self.equity - self.initial_capital
            self.__update_drawdown_record()
            self.sortino_record.append((price - self.current_open_pos["price"]) * share)
            self.max_drawdown = self.get_max_drawdown()

            if self.current_open_pos["qty"] == share:
                self.current_open_pos = None
                self.pos = 0

            if tptaken:
                self.current_open_pos["tptaken"] = True
                self.current_open_pos["qty"] = self.current_open_pos["qty"] - share

        else:
            print("No position to exit")

    def break_even(self):
        """Change stop loss level to break even. This function could be used after take profit.
        """
        self.current_open_pos["sl"] = self.current_open_pos["price"]

    def set_trailing_stop(self, price, ts_atr):
        """Setting trailing stop

        Args:
            price (float): close price when trailing stop level reached
            ts_atr (float): atr value of position opening
        """
        if self.pos == 1:
            self.current_open_pos["sl"] = price - ts_atr
        elif self.pos == -1:
            self.current_open_pos["sl"] = price + ts_atr

    def get_result(self):
        """Generates backtest results

        Returns:
            dictionary -- a dictionary of backtest results including various ratios.
        """
        result = {
            "net_profit": self.net_profit, "net_profit_percent": self.get_net_profit_percent(),
            "gross_profit": self.gross_profit, "gross_loss": self.gross_loss, "max_drawdown": self.max_drawdown,
            "max_drawdown_rate": self.get_max_drawdown_rate(), "win_rate": self.get_win_rate(),
            "risk_reward_ratio": self.get_risk_reward_ratio(), "profit_factor": self.get_profit_factor(),
            "return_on_capital": self.get_return_on_capital(), "max_capital_required": self.get_max_capital_required(),
            "total_trades": self.total_trades, "number_of_winning_trades": self.number_of_winning_traders,
            "sortino_ratio": self.get_sortino_ratio(), "number_of_losing_trades": self.number_of_losing_trades,
            "largest_winning_trade": self.get_largest_winning_trade(), "largest_losing_trade": self.get_largest_losing_trade()}
        return result

    def get_net_profit(self):
        """Net profit

        Returns:
            float -- net profit
        """
        npr = self.net_profit_record[-1]
        return npr[1]

    def get_net_profit_percent(self):
        """Net profit percent value

        Returns:
            float -- net profit percent value
        """
        npr = self.net_profit_record[-1]
        npp = self.__calculate_percent(npr[1], self.initial_capital)
        return npp

    def get_max_drawdown(self):
        """Calculates maximum drawdown

        Returns:
            float -- maximum drawdown
        """
        maxddr = self.max_drawdown_record[0]
        for mdr in self.max_drawdown_record:
            if mdr[2] < maxddr[2]:
                maxddr = mdr
        return maxddr[2]

    def get_max_drawdown_rate(self):
        """Calculates rate of maximum drawdown

        Returns:
            float -- rate of maximum drawdown
        """
        if self.get_max_drawdown() == 0:
            return 0
        else:
            mddr = self.net_profit / abs(self.get_max_drawdown())
            return mddr

    def get_risk_reward_ratio(self):
        """Calculates risk reward ratio

        Returns:
            float -- risk reward ratio
        """
        risk = self.gross_profit / self.number_of_winning_traders
        reward = self.gross_loss / self.number_of_losing_trades
        return risk / reward

    def get_win_rate(self):
        """Calculates win rate

        Returns:
            float -- win rate
        """
        win_rate = (self.number_of_winning_traders * 100) / self.total_trades
        return win_rate

    def get_max_capital_required(self):
        """Calculates maximum capital required for the strategy

        Returns:
            float -- maximum capital required
        """
        mcr = self.initial_capital + abs(self.get_max_drawdown())
        return mcr

    def get_return_on_capital(self):
        """Calculates return on capital

        Returns:
            float -- return on capital
        """
        roc = self.net_profit / self.get_max_capital_required()
        return roc

    def get_profit_factor(self):
        """Calculates profit factor

        Returns:
            float -- profit factor
        """
        profit_factor = self.gross_profit / self.gross_loss
        return profit_factor

    def get_sortino_ratio(self):
        """Calculates sortino ratio

        Returns:
            float -- sortino ratio
        """
        mean_return = sum(self.sortino_record) / len(self.sortino_record)

        downside = []
        for dws in self.sortino_record:
            if dws < 0:
                downside.append(dws)

        downside_std = statistics.stdev(downside)

        sortino = mean_return / downside_std
        return sortino

    def get_largest_winning_trade(self):
        """Largest winning trade

        Returns:
            tuple -- date and value of largest winning trade
        """
        maxnpr = self.net_profit_record[0]
        for i in range(0, len(self.net_profit_record)):
            if i > 0:
                nprf = self.net_profit_record[i][1] - self.net_profit_record[i-1][1]
                if nprf > maxnpr[1]:
                    maxnpr = self.net_profit_record[i]
        return maxnpr

    def get_largest_losing_trade(self):
        """Largest losing trade

        Returns:
            tuple -- date and value of largest losing trade
        """
        minnpr = self.net_profit_record[0]
        for i in range(0, len(self.net_profit_record)):
            if i > 0:
                nprf = self.net_profit_record[i][1] - self.net_profit_record[i-1][1]
                if nprf < minnpr[1]:
                    minnpr = self.net_profit_record[i]
        return minnpr

    def write_trades_to_csv(self, name="trades"):
        """Write all transactions to a csv file

        Keyword Arguments:
            name {str} -- name of the csv file (default: {"trades"})
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

        Arguments:
            date {string} -- date of drawdown
        """
        maxnp = self.net_profit_record[0]
        for npr in self.net_profit_record:
            if npr[1] > maxnp[1]:
                maxnp = npr
        self.max_drawdown_record.append((maxnp[0], self.net_profit_record[-1][0], self.net_profit_record[-1][-1] - maxnp[1]))

    def __calculate_percent(self, nominator, denominator):
        """Calculates percent value with given nominator and denominator

        Arguments:
            nominator {float} -- nominator
            denominator {float} -- denominator

        Returns:
            float -- percent value
        """
        return (100 * nominator) / denominator
