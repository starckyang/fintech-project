import pandas as pd
import numpy as np
from backtesting import Backtest, Strategy
import pickle
from functions import identify_trend, identify_order_blocks  # Import your custom functions

# Define the strategy class
class OrderBlockStrategy(Strategy):
    def init(self):
        self.order_block_top = None
        self.order_block_bottom = None
        self.order_trend = None
        self.order_block_found = False
        self.position_size = 1000

    def next(self):
        # Check if there's a new order block
        if not np.isnan(self.data.Order_Block_Top[-1]):
            self.order_block_top = self.data.Order_Block_Top[-1]
            self.order_block_bottom = self.data.Order_Block_Bot[-1]
            self.order_trend = self.data.Trend[-1]
            self.order_block_found = True

        if self.order_block_found:
            # Buy condition: if the price reaches the order block's top and within the block range
            if (self.data.Close[-1] <= self.order_block_top) and (self.data.Close[-1] >= self.order_block_bottom) \
                and (self.order_trend == "Uptrend"):
                self.buy()
                print(f"Longing at {self.data.Close[-1]}")
            elif (self.data.Close[-1] >= self.order_block_bottom) and (self.data.Close[-1] <= self.order_block_top) \
                    and (self.order_trend == "Downtrend"):
                self.sell()
                print(f"Shorting at {self.data.Close[-1]}")
            # Sell conditions
            order_block_range = self.order_block_top - self.order_block_bottom

            # Exit conditions
            if ((self.data.Low[-1] <= self.order_block_bottom) and self.position.is_long) or \
               ((self.data.Close[-1] >= self.order_block_top + 4 * order_block_range) and self.position.is_long) or \
               ((self.data.Close[-1] >= self.order_block_top) and self.position.is_short) or \
               ((self.data.Close[-1] <= self.order_block_bottom - 4 * order_block_range) and self.position.is_short):
                self.position.close()  # Close the position
                print(f"Closed position at {self.data.Close[-1]}")
                self.order_block_found = False  # Reset order block


if __name__ == "__main__":
    # Load your data
    with open("ETHUSDT.pkl", "rb") as f:
        data = pickle.load(f)

    # Identify BoS, CHoCH, and Order Blocks
    data = identify_trend(data)
    data = identify_order_blocks(data)

    # Ensure the data has the necessary columns
    data['Order_Block_Top'] = data['Order Block Top']
    data['Order_Block_Bot'] = data['Order Block Bot']

    # Run the backtest
    bt = Backtest(data, OrderBlockStrategy, cash=10000)
    stats = bt.run()
    print(stats)
    bt.plot()
