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
        self.previous_trade_top = None
        self.previous_trade_bottom = None
        self.position_size = 10000
        self.index = 0

    def next(self):
        # Check if there's a new order block
        if not np.isnan(self.data.Order_Block_Top[-1]):
            self.order_block_top = self.data.Order_Block_Top[-1]
            self.order_block_bottom = self.data.Order_Block_Bot[-1]
            self.order_trend = self.data.Trend[-1]
            self.order_block_found = True
            self.index = 5

        elif (self.order_block_found) & (self.index == 0):
            # Buy condition: if the price reaches the order block's top and within the block range
            if (self.data.Close[-1] <= self.order_block_top) and (self.data.Close[-1] >= self.order_block_bottom) and \
                    (self.order_trend == "Uptrend") and (not self.previous_trade_top) & (self.position.size == 0):
                entry_price = self.data.Close[-1]
                stop_loss_price = entry_price * 0.95  # Set stop loss 5% below entry price
                print(stop_loss_price)
                print(self.position_size)
                print(entry_price)
                self.buy(sl=stop_loss_price, size=self.position_size//entry_price)

                # self.buy()
                print(f"Longing at {self.data.Close[-1]}")
                self.previous_trade_top = self.order_block_top
                self.previous_trade_bottom = self.order_block_bottom
            elif (self.data.Close[-1] <= self.order_block_top) and (self.data.Close[-1] >= self.order_block_bottom) and \
                    (self.order_trend == "Uptrend") and (self.previous_trade_top):
                self.previous_trade_top = None
                self.previous_trade_bottom = None
                self.position.close()
            elif (self.data.Close[-1] >= self.order_block_bottom) and (self.data.Close[-1] <= self.order_block_top) \
                    and (self.order_trend == "Downtrend") and (not self.previous_trade_top) & (self.position.size == 0):
                entry_price = self.data.Close[-1]
                stop_loss_price = entry_price * 1.05
                self.sell(sl=stop_loss_price, size=self.position_size//entry_price)
                # self.sell()
                print(f"Shorting at {self.data.Close[-1]}")
                self.previous_trade_top = self.order_block_top
                self.previous_trade_bottom = self.order_block_bottom
            elif (self.data.Close[-1] >= self.order_block_bottom) and (self.data.Close[-1] <= self.order_block_top) \
                    and (self.order_trend == "Downtrend") and (not self.previous_trade_top):
                self.previous_trade_top = None
                self.previous_trade_bottom = None
                self.position.close()
        # Sell conditions
            # Exit conditions

            # add in percentage stop loss
        elif self.index != 0:
            self.index -= 1

        if (self.order_block_found) & (self.position.size != 0) & (self.previous_trade_top is not None):
            # # stop profit exist
            # if ((self.data.Low[-1] <= self.order_block_bottom) and self.position.is_long) or \
            #    ((self.data.Close[-1] >= self.order_block_top + 4 * order_block_range) and self.position.is_long) or \
            #    ((self.data.Close[-1] >= self.order_block_top) and self.position.is_short) or \
            #    ((self.data.Close[-1] <= self.order_block_bottom - 4 * order_block_range) and self.position.is_short):
            # stop profit don't exist
            if ((self.data.Low[-1] <= self.previous_trade_bottom) and (self.position.is_long))  or \
                    ((self.data.High[-1] >= self.previous_trade_top) and self.position.is_short):
                self.position.close()  # Close the position
                print(f"Closed position at {self.data.Close[-1]}")
                self.order_block_found = False  # Reset order block



if __name__ == "__main__":
    # Load your data
    with open("ETHUSDT_training.pkl", "rb") as f:
        data = pickle.load(f)

    # Identify BoS, CHoCH, and Order Blocks
    data = identify_trend(data)
    data = identify_order_blocks(data)

    # Ensure the data has the necessary columns
    data['Order_Block_Top'] = data['Order Block Top']
    data['Order_Block_Bot'] = data['Order Block Bot']

    # Run the backtest
    bt = Backtest(data, OrderBlockStrategy, cash=100000)
    stats = bt.run()
    print(stats)
    bt.plot()


