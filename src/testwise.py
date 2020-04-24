import statistics
import csv
import matplotlib.pyplot as plt

class Testwise:
    def __init__(self, initialCapital = 100000, commission = 0, slippage = 0, riskFactor = 1.2, limitFactor = 2.3, positionRisk = 0.02, takeProfitRatio = 0.5):
        self.initialCapital = initialCapital
        self.commission = commission
        self.slippage = slippage
        self.riskFactor = riskFactor
        self.limitFactor = limitFactor
        self.positionRisk = positionRisk
        self.takeProfitRatio = takeProfitRatio

        self.equity = initialCapital
        self.cash = initialCapital

        self.netProfit = 0
        self.grossProfit = 0
        self.grossLoss = 0
        self.maxDrawdown = 0
        self.largestWinningTrade = 0
        self.largestLosingTrade = 0
        self.totalTrades = 0
        self.numberOfWinningTraders = 0
        self.numberOfLosingTrades = 0

        self.netProfitRecord = []
        self.maxDrawdownRecord = []
        self.sortinoRecord = []

        self.pos = 0
        self.currentOpenPos = None
        self.positions = []


    def calculateShare(self, currentAtrPips):
        """Calculates how many shares to buy

        Arguments:
            currentAtrPips {int} -- atr in pips

        Returns:
            float -- shares to buy
        """        

        risk = self.equity * self.positionRisk
        pv = risk / (self.riskFactor * currentAtrPips)
        return pv

    def entryLong(self, date, price, share, currentAtr):
        """Opening a long position

        Arguments:
            date {string} -- date of entry
            price {float} -- opening price of position
            share {float} -- number of shares to buy
            currentAtr {float} -- atr to define take profit and stop loss 
        """        
        if self.currentOpenPos == None:
            adjustedPrice = price + self.slippage

            position = {"type": "entry long", "date": date, "price": price, "adjPrice": adjustedPrice, "qty": share, "tp": price + (self.limitFactor * currentAtr), "sl": price - (self.riskFactor * currentAtr), "tptaken": False}
            self.positions.append(position)

            if self.commission != 0:
                self.cash = self.cash - (adjustedPrice * share) - (adjustedPrice * share * self.commission)
                self.equity = self.equity - (adjustedPrice * share * self.commission)
            else:
                self.cash = self.cash - (adjustedPrice * share) - (adjustedPrice * share)
            
            self.totalTrades = self.totalTrades + 1
            self.currentOpenPos = position
            self.pos = 1
        else:
            print("Position already open")

    def exitLong(self, date, price, share, tptaken=False):
        """Closing a long position

        Arguments:
            date {string} -- date of closing
            price {float} -- closing price of position
            share {float} -- number of shares to sell

        Keyword Arguments:
            tptaken {bool} -- True if take profit is taken with this particular transaction (default: {False})
        """        
        if self.currentOpenPos != None:
            adjustedPrice = price - self.slippage
            position = {"type": "exit long", "date":date, "price": price, "adjPrice": adjustedPrice, "qty": share}
            self.positions.append(position)
            
            self.equity = self.equity + ((adjustedPrice - self.currentOpenPos["price"]) * share) - (abs(adjustedPrice - self.currentOpenPos["price"]) * share * self.commission)
            self.cash = self.cash + ((adjustedPrice - self.currentOpenPos["price"]) * share) - (abs(adjustedPrice - self.currentOpenPos["price"]) * share * self.commission)

            if adjustedPrice - self.currentOpenPos["price"] > 0:
                self.grossProfit = self.grossProfit + ((adjustedPrice - self.currentOpenPos["price"]) * share)
                if tptaken == False:
                    self.numberOfWinningTraders = self.numberOfWinningTraders + 1
            else:
                self.grossLoss = self.grossLoss + abs(((adjustedPrice - self.currentOpenPos["price"]) * share))
                if tptaken == False:
                    self.numberOfLosingTrades = self.numberOfLosingTrades + 1

            self.netProfitRecord.append((date,self.equity - self.initialCapital))
            self.netProfit = self.equity - self.initialCapital
            self.__updateDrawdownRecord(date)
            self.sortinoRecord.append((adjustedPrice - self.currentOpenPos["price"]) * share)
            self.maxDrawdown = self.getMaxDrawdown()

            if self.currentOpenPos["qty"] == share:
                self.currentOpenPos = None
                self.pos = 0
            
            if tptaken:
                self.currentOpenPos["tptaken"] = True
                self.currentOpenPos["qty"] = self.currentOpenPos["qty"] - share

        else:
            print("No position to exit")

    def entryShort(self, date, price, share, currentAtr):
        """Opening a short position

        Arguments:
            date {string} -- date of entry
            price {float} -- opening price of position
            share {float} -- number of shares to short
            currentAtr {float} -- atr to define take profit and stop loss 
        """           
        if self.currentOpenPos == None:
            adjustedPrice = price - self.slippage
            position = {"type": "entry short", "date": date,"price": price, "adjPrice": adjustedPrice, "qty": share, "tp": price - (self.limitFactor * currentAtr), "sl": price + (self.riskFactor * currentAtr), "tptaken": False}
            self.positions.append(position)
            
            if self.commission != 0:
                self.cash = self.cash - (adjustedPrice * share) - (adjustedPrice * share * self.commission)
                self.equity = self.equity - (adjustedPrice * share * self.commission)
            else:
                self.cash = self.cash - (adjustedPrice * share) - (adjustedPrice * share)

            self.totalTrades = self.totalTrades + 1
            self.currentOpenPos = position
            self.pos = -1
        else:
            print("Position already open")

    def exitShort(self, date, price, share, tptaken=False):
        """Closing a short position

        Arguments:
            date {string} -- date of closing
            price {float} -- closing price of position
            share {float} -- number of shares to short-sell

        Keyword Arguments:
            tptaken {bool} -- True if take profit is taken with this particular transaction (default: {False})
        """        
        if self.currentOpenPos != None:
            adjustedPrice = price + self.slippage
            position = {"type": "exit short", "date":date, "price": price, "adjPrice": adjustedPrice, "qty": share}
            self.positions.append(position)
            
            self.equity = self.equity - ((adjustedPrice - self.currentOpenPos["price"]) * share) - (abs(price - self.currentOpenPos["price"]) * share * self.commission)
            self.cash = self.cash - ((adjustedPrice - self.currentOpenPos["price"]) * share) - (abs(price - self.currentOpenPos["price"]) * share * self.commission)

            if adjustedPrice - self.currentOpenPos["price"] < 0:
                self.grossProfit = self.grossProfit + abs(((adjustedPrice - self.currentOpenPos["price"]) * share))
                if tptaken == False:
                    self.numberOfWinningTraders = self.numberOfWinningTraders + 1
            else:
                self.grossLoss = self.grossLoss + ((adjustedPrice - self.currentOpenPos["price"]) * share)
                if tptaken == False:
                    self.numberOfLosingTrades = self.numberOfLosingTrades + 1
            
            self.netProfitRecord.append((date,self.equity - self.initialCapital))
            self.netProfit = self.equity - self.initialCapital
            self.__updateDrawdownRecord(date)
            self.sortinoRecord.append((price - self.currentOpenPos["price"]) * share)
            self.maxDrawdown = self.getMaxDrawdown()

            if self.currentOpenPos["qty"] == share:
                self.currentOpenPos = None
                self.pos = 0
            
            if tptaken:
                self.currentOpenPos["tptaken"] = True
                self.currentOpenPos["qty"] = self.currentOpenPos["qty"] - share

        else:
            print("No position to exit")
    
    def breakEven(self):
        """Change stop loss level to break even. This function could be used after take profit.
        """        
        self.currentOpenPos["sl"] = self.currentOpenPos["price"]

    def getResult(self):
        """Generates backtest results

        Returns:
            dictionary -- a dictionary of backtest results including various ratios.
        """        
        result = {"netProfit": self.netProfit, "netProfitPercent": self.getNetProfitPercent(), "grossProfit": self.grossProfit, "grossLoss": self.grossLoss, "maxDrawdown": self.maxDrawdown, "maxDrawdownRate": self.getMaxDrawdownRate(), "riskRewardRatio": self.getRiskRewardRatio(), "profitFactor": self.getProfitFactor(), "returnOnCapital": self.getReturnOnCapital(), "maxCapitalRequired": self.getMaxCapitalRequired(), "totalTrades": self.totalTrades, "numberOfWinningTrades": self.numberOfWinningTraders, "numberOfLosingTrades": self.numberOfLosingTrades, "largestWinningTrade": self.getLargestWinningTrade(), "largestLosingTrade": self.getLargestLosingTrade()}
        return result

    def getNetProfit(self):
        """Net profit

        Returns:
            float -- net profit
        """        
        npr = self.netProfitRecord[-1]
        return npr[1]

    def getNetProfitPercent(self):
        """Net profit percent value

        Returns:
            float -- net profit percent value
        """        
        npr = self.netProfitRecord[-1]
        npp = self.__calculatePercent(npr[1], self.initialCapital)
        return npp

    def getMaxDrawdown(self):
        """Calculates maximum drawdown

        Returns:
            float -- maximum drawdown
        """        
        m = self.maxDrawdownRecord[0]
        for maxddr in self.maxDrawdownRecord:
            if maxddr[2] < m[2]:
                m = maxddr
        
        return m[2]

    def getMaxDrawdownRate(self):
        """Calculates rate of maximum drawdown

        Returns:
            float -- rate of maximum drawdown
        """        
        if self.getMaxDrawdown() == 0:
            return 0
        else:
            mddr = self.netProfit / self.getMaxDrawdown()
            return mddr

    def getRiskRewardRatio(self):
        """Calculates risk reward ratio

        Returns:
            float -- risk reward ratio
        """        
        risk = self.grossProfit / self.numberOfWinningTraders
        reward = self.grossLoss / self.numberOfLosingTrades
        return reward / risk

    def getWinRate(self):
        """Calculates win rate

        Returns:
            float -- win rate
        """        
        wr = (self.numberOfWinningTraders * 100) / self.totalTrades
        return wr

    def getMaxCapitalRequired(self):
        """Calculates maximum capital required for the strategy

        Returns:
            float -- maximum capital required
        """        
        mcr = self.initialCapital + self.getMaxDrawdown()
        return mcr

    def getReturnOnCapital(self):
        """Calculates return on capital

        Returns:
            float -- return on capital
        """        
        roc = self.netProfit / self.getMaxCapitalRequired()
        return roc

    def getProfitFactor(self):
        """Calculates profit factor

        Returns:
            float -- profit factor
        """        
        pf = self.grossProfit / self.grossLoss
        return pf

    def getSortinoRatio(self):
        """Calculates sortino ratio

        Returns:
            float -- sortino ratio
        """        
        meanReturn = sum(self.sortinoRecord) / len(self.sortinoRecord)
        
        downside = []
        for d in self.sortinoRecord:
            if d < 0:
                downside.append(d)

        downsideStd = statistics.stdev(downside)

        sortino = mean / downsideStd
        return sortino

    def getLargestWinningTrade(self):
        """Largest winning trade

        Returns:
            tuple -- date and value of largest winning trade
        """        
        maxnpr = self.netProfitRecord[0]
        for i in range(0,len(self.netProfitRecord)):
            if i > 0:
                np = self.netProfitRecord[i][1] - self.netProfitRecord[i-1][1]
                if np > maxnpr[1]:
                    maxnpr = self.netProfitRecord[i]
        return maxnpr
    
    def getLargestLosingTrade(self):
        """Largest losing trade

        Returns:
            tuple -- date and value of largest losing trade
        """        
        minnpr = self.netProfitRecord[0]
        for i in range(0,len(self.netProfitRecord)):
            if i > 0:
                np = self.netProfitRecord[i][1] - self.netProfitRecord[i-1][1]
                if np < minnpr[1]:
                    minnpr = self.netProfitRecord[i]
        return minnpr

    def writeTradesToCSV(self, name="trades"):
        """Write all transactions to a csv file

        Keyword Arguments:
            name {str} -- name of the csv file (default: {"trades"})
        """        
        f = open(name + ".csv", "w", newline="")
        with f:
            fnames = ["type", "date", "price", "adjPrice", "qty", "tp", "sl", "tptaken"]

            writer = csv.DictWriter(f, fieldnames=fnames)
            writer.writeheader()
            for trade in self.positions:
                writer.writerow(trade)

    def drawNetProfitGraph(self):
        """Draws net profit graph
        """        
        plt.plot(*zip(*self.netProfitRecord))
        plt.show()

    def printOutAllPositions(self):
        """Prints out all trades line by line
        """        
        for p in self.positions:
            print(p)

    def __updateDrawdownRecord(self, date):
        """Records drawdon to calculate maximum drawdown

        Arguments:
            date {string} -- date of drawdown
        """        
        maxnp = self.netProfitRecord[0]
        for np in self.netProfitRecord:
            if np[1] > maxnp[1]:
                maxnp = np
        self.maxDrawdownRecord.append((maxnp[0], self.netProfitRecord[-1][0], self.netProfitRecord[-1][-1] - maxnp[1]))
    
    def __calculatePercent(self, nominator, denominator):
        """Calculates percent value with given nominator and denominator

        Arguments:
            nominator {float} -- nominator
            denominator {float} -- denominator

        Returns:
            float -- percent value
        """        
        return (100 * nominator) / denominator