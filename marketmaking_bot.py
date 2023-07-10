import numpy as np
import time
import joblib
import warnings
from numba import jit
warnings.simplefilter('ignore')

# own function to connect to exchange and engineer features
from deribitv2 import DeriBit
from marketstate import MarketState
from feature_engineering import feature_functions
from strategy import strategies
from config import config_dict, strategy_params
import config
from simple_functions import *

from configure_logger import configure_logger
configure_logger()
import logging
LOGGER = logging.getLogger(__name__)

# request instrument to trade on, automatically takes the perpetual contract
ASSET = config_dict["asset"]
INSTRUMENT = config_dict["contract"]
CURRENCY = config_dict["currency"]
TRADE_QTY = config_dict["trade_qty"]
MIN_QTY = config_dict["min_qty"]
MAX_POSITION = strategy_params["max_pos"]

# paramters for refreshing orders and time series
MIN_LOOP_TIME = .001
WAVELEN_TIME_SERIES = 1 # wavelength to refresh time series from which volatility etc. are predicted
WAVELEN_UPDATE_ORDERS = .5 # time to refresh orders, for this we need to replace two orders + request orderbook. I.e. costing 3 API requests, from which 2 matching engine. Allowed to refresh every .5 seconds
WAVELEN_STATUS = 60
RESTART_INTERVAL = 5
BURN_IN = -100

class MarketMakingBot(DeriBit):
    
    model = joblib.load(f"models/{INSTRUMENT}_model_1s_regr.joblib")
    vol_model = joblib.load(f"models/{INSTRUMENT}_model_1s_vol.joblib")
    
    def __init__(self):
        super(MarketMakingBot, self).__init__(test = config.TEST_EXCHANGE)
        
        # get authorization for the first time
        self.getauth()

        # request and store ticker information
        instrument_info = self.getinstrument(INSTRUMENT)
        self.min_qty = max(MIN_QTY, instrument_info["min_trade_amount"])
        self.tick = instrument_info["tick_size"]
        
        # cancel all orders before start market making
        self.cancelallbyinstrument(INSTRUMENT)
        self.pos_p = self.position(INSTRUMENT)["size"]
        self.initial_pos = self.account_sum(CURRENCY)["equity"]

        # current open orders
        self.p_bid = None
        self.p_bid_size = None
        self.p_ask = None
        self.p_ask_size = None
        
        self.previous_bid_order = None
        self.previous_ask_order = None

        # feature_functions is a dictionary with different feature_engineering functions for different time frames
        self.feature_engineer = feature_functions["15_dir"] 
        self.feature_engineer_vol = feature_functions["15_dir"]
        self.compute_quotes = strategies[strategy_params["ML_model"]]
        
        self.ended_at = time.time()

        # load model and initialize df
        self.market_state = MarketState()

    # @jit
    def update_quotes(self, bid_order, ask_order):
        """ 
        Update orders on both sides, if order exists try to replace, else post new order
        """
        # if existing bid quote
        if self.p_bid:
            # if the order is 'passive' and was 'passive', leave it (placed at such a wide spread making it impossible to get filled)
            if bid_order["price"] != strategy_params["min_quote"] or self.previous_bid_order["price"] != strategy_params["min_quote"]:
                try:
                    self.edit(self.p_bid, quantity = bid_order["size"], price = bid_order["price"], post_only = bid_order["post_only"])
                    self.p_bid_size = bid_order["size"]
                except:
                    LOGGER.info(f"bid order filled:\n {self.p_bid}")
                    self.p_bid = None
                    self.pos_p += self.p_bid_size
        # create new order if new existing order to replace
        else:
            self.p_bid = self.buy(INSTRUMENT, "limit", bid_order["size"], bid_order["price"], post_only = bid_order["post_only"])['order']['order_id']
            self.p_bid_size = bid_order["size"]
        self.previous_bid_order = bid_order

        if self.p_ask:
            if ask_order["price"] != strategy_params["max_quote"] or self.previous_ask_order["price"] != strategy_params["max_quote"]:
                try:
                    self.edit(self.p_ask, quantity = ask_order["size"], price = ask_order["price"], post_only = ask_order["post_only"])
                    self.p_ask_size = ask_order["size"]
                except:
                    LOGGER.info(f"ask order filled:\n {self.p_ask}")
                    self.p_ask = None
                    self.pos_p += - self.p_ask_size
        else:
            self.p_ask = self.sell(INSTRUMENT, "limit", ask_order["size"], ask_order["price"], post_only = ask_order["post_only"])['order']['order_id']
            self.p_ask_size = ask_order["size"]
        self.previous_ask_order = ask_order
    
    def forecast(self):
        # feature engineer and predict
        features = self.feature_engineer(self.market_state().copy())
        direction = self.model.predict(np.array(features.iloc[-1]).reshape(1,-1))[0]

        features_vol = features
        volatility = self.vol_model.predict(np.array(features_vol.iloc[-1]).reshape(1,-1))[0]
        return direction, volatility

    # def validate_size(self, bid_order, ask_order, position):
    #     if abs(position)<=MAX_POSITION - TRADE_QTY:
    #         bid_order["size"] = TRADE_QTY
    #         ask_order["size"] = TRADE_QTY
    #     elif position > MAX_POSITION - TRADE_QTY:
    #         bid_order["size"] = MAX_POSITION - position
    #         if position >= MAX_POSITION:
    #             bid_order["size"] = MIN_QTY
    #         ask_order["size"] = TRADE_QTY
    #     elif position < -MAX_POSITION + TRADE_QTY:
    #         bid_order["size"] = TRADE_QTY
    #         ask_order["size"] = abs(-MAX_POSITION - position)
    #         if position <= - MAX_POSITION:
    #             ask_order["size"] = MIN_QTY
    #     return bid_order, ask_order
    
    def validate_price(self, bid_order, ask_order):
        bid_order["price"] = round(round(bid_order["price"]/self.tick)*self.tick, config_dict["sign"])
        ask_order["price"] = round(round(ask_order["price"]/self.tick)*self.tick, config_dict["sign"])    
        return bid_order, ask_order

    def request_data(self, substract_own_orders = False):
        started_at = time.time()

        # request book and own open orders
        book = self.getorderbook(INSTRUMENT)
        bids_asks = [[book["bids"][i][0], book["bids"][i][1], book["asks"][i][0], book["asks"][i][1]] for i in range(20)]
        
        # substract own orders from order book
        if substract_own_orders:
            own_orders = self.getopenorders(INSTRUMENT)
            own_bids_asks_prices = [ord["price"] for ord in own_orders]
            own_bids_asks_amounts = [ord["amount"] for ord in own_orders]
            book_data = []
            for bid_ask in bids_asks:
                if bid_ask[0] in own_bids_asks_prices:
                    bid_ask[1] = max(0, bid_ask[1] - own_bids_asks_amounts[own_bids_asks_prices.index(bid_ask[0])])
                if bid_ask[2] in own_bids_asks_prices:
                    bid_ask[3] = max(0, bid_ask[3] - own_bids_asks_amounts[own_bids_asks_prices.index(bid_ask[2])])
                book_data += bid_ask
        else:
            book_data = bids_asks

        # request recent trades
        trades = self.getlasttrades_bytime(INSTRUMENT, start_timestamp=int(self.ended_at*1000), end_timestamp=int(started_at*1000))['trades']
        trade_data = []
        trade_data += [len(trades), sum([t["amount"] for t in trades])]

        # seperate for buy and sell
        trades_buy = [t for t in trades if t["direction"] == "buy"]
        trades_sell = [t for t in trades if t["direction"] == "sell"]
        trade_data += [len(trades_buy), sum([t["amount"] for t in trades_buy])]
        trade_data += [len(trades_sell), sum([t["amount"] for t in trades_sell])]

        # add to df
        self.market_state.add_line([started_at] + book_data + trade_data)
        self.ended_at = time.time()

        # shorten
        if self.market_state().shape[0] > 200:
            self.market_state.df = self.market_state.df.iloc[-100:]
        return book

    def repeat(self,):
        # to refresh the authentication token in time
        last_pos_refresh = last_time_refresh = last_quote_refresh = time.time() - max(WAVELEN_STATUS, WAVELEN_TIME_SERIES, WAVELEN_UPDATE_ORDERS)

        i = 0
        while True:
            
            # start timing
            started_at = time.time()
            
            if started_at - last_time_refresh > WAVELEN_TIME_SERIES:
                # get market data and own orders
                last_time_refresh = started_at
                book = self.request_data(substract_own_orders=True)
                direction, volatility = self.forecast()
                
                print(self.get_index_price(config_dict["assert"].lower() + "_usd"))

            # refresh quotes and replace them
            # the structure is, get: position, orders, book, replace orders
            if started_at - last_quote_refresh > WAVELEN_UPDATE_ORDERS:
                last_quote_refresh = started_at
                
                # at initialisation, wait for enough data to forecast
                if i < BURN_IN:
                    i += 1
                    continue

                # with all information above, compute bid/ask quotes
                bid_order, ask_order = self.compute_quotes(data = {"book": book, "dir": direction, "vol": volatility, "pos": self.pos_p}, params = strategy_params)
                # bid_order, ask_order = self.validate_size(bid_order, ask_order, position)
                bid_order, ask_order = self.validate_price(bid_order, ask_order)
                LOGGER.debug(f"volatility prediction: {str(round(volatility,12))}")
                LOGGER.debug(f"directional prediction: {str(round(direction,12))}")
                LOGGER.debug(f"bid_order: {str(bid_order)}")
                LOGGER.debug(f"ask_order: {str(ask_order)}")
                
                # update orders as desired
                self.update_quotes(bid_order, ask_order)

            # refresh pnl
            if started_at - last_pos_refresh > WAVELEN_STATUS:
                last_pos_refresh = started_at
                curr_equity = self.account_sum(CURRENCY)["equity"]
                self.pos_p = self.position(INSTRUMENT)["size"]
                LOGGER.info(f"initial: {self.initial_pos} | current: {curr_equity} | P&L: {curr_equity - self.initial_pos} {CURRENCY}")
                LOGGER.info(f"current position: {self.pos_p} {CURRENCY}")

            # refresh_auth
            if started_at - self.last_refresh > 800:
                self.getauth()

            # refresh loop
            run_time = time.time() - started_at
            if run_time < MIN_LOOP_TIME: 
                time.sleep(MIN_LOOP_TIME - run_time)
            else: pass

if __name__ == "__main__":
    while True:
        try:
            bot = MarketMakingBot()
            bot.repeat()
        except (KeyboardInterrupt, SystemExit) as e:
            LOGGER.error("keyboard interrupt, cancelling outstanding orders ...")
            bot.__init__()
            bot.cancelallbyinstrument(INSTRUMENT)
            break
        except Exception as e:
            LOGGER.error(str(e))
            bot.__init__()
            bot.cancelallbyinstrument(INSTRUMENT)
        time.sleep(RESTART_INTERVAL)