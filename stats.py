from collections import defaultdict
from orderside import OrderSide

#  Requirements:
# - Total trading volume, in USD
# - PNL generated from this trading
# - VWAP of the fills for each instruments


'''
Methodology of PnL calculation:
We start with a balance of 0. 
Every BUY trade increases inventory and decreases the balance, while every SELL/SHORT trade decreases inventory and increases the balance.
At the point of PnL calculation, we use the VWAP of the fills to estimate the value of our existing inventory, and add it to the balance.
Formula: PnL = balance + sum((inventory * VWAP) for each instrument)

Note that both balance or inventory could be negative (which means we owe cash or inventory).
'''
class DTLTradeStats:
    def __init__(self, instruments):
        self.total_volume = 0
        self.balance = 0
        self.instrument_value = defaultdict(int)
        self.instrument_volume = defaultdict(int)
        self.inventories = defaultdict(int)
        self.instruments = instruments

    def process(self, transaction):
        self.total_volume += transaction.qty
        self.instrument_value[transaction.symbol] += (
            transaction.price * transaction.qty
        )
        self.instrument_volume[transaction.symbol] += transaction.qty

        if transaction.side == OrderSide.BUY:
            self.inventories[transaction.symbol] += transaction.qty
            self.balance -= transaction.qty * transaction.price
        else:
            self.inventories[transaction.symbol] -= transaction.qty
            self.balance += transaction.qty * transaction.price

    def calculate_vwap_fills(self):
        vwap_fills = {}
        for instrument in self.instruments:
            # If there is no volume, define the VWAP of the instrument as 0
            if self.instrument_volume[instrument] == 0:
                vwap_fills[instrument] = 0
                continue
                
            vwap_fills[instrument] = (
                self.instrument_value[instrument] / self.instrument_volume[instrument]
            )
        return vwap_fills

    def calculate_PnL(self, vwap_fills):
        value_of_inventories = 0
        for instrument in self.instruments:
            value_of_inventories += (
                self.inventories[instrument] * vwap_fills[instrument]
            )
        print("Balance: $",  f"{self.balance:.2f}")
        print("Value of inventories: $", f"{value_of_inventories:.2f}")
        return self.balance + value_of_inventories
    

    def summarize(self):
        print("Total trading volume:", self.total_volume)
        vwap_fills = self.calculate_vwap_fills()
        PnL = self.calculate_PnL(vwap_fills)
        print("PnL: $",  f"{PnL:.2f}" )
        print("VWAP of fills:", vwap_fills)
        print("Inventories:", dict(self.inventories))
