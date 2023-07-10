import math
import numpy as np
from numba import jit
import logging
LOGGER = logging.getLogger(__name__)

@jit
def get_quotes2(data, params):
    # market data + forecast
    book = data["book"]
    dir = data["dir"]
    vol = data["vol"]
    pos = data["pos"]
    best_bid, best_ask = book["bids"][0][0], book["asks"][0][0]
        
    # strategy params
    trade_qty = params["trade_qty"]
    
    order_buy = {}
    order_sell = {}
    
    mid = .5 * (best_bid + best_ask)    
    pos /= trade_qty

    s_b = (-1 - 2*pos) / ((1+params["max_position"])**2 - pos**2)
    s_a = (1 - 2*pos) / ((1+params["max_position"])**2 - pos**2)
    
    rel_bid = (1 + 1/params["risk_aversion"] * np.log(1+s_b))
    rel_ask = (1 + 1/params["risk_aversion"] * np.log(1+s_a))

    vol_spread = params["vol_mult"] * math.log(1 + math.sqrt(vol))
    spread = params["base_spread"] + vol_spread*2

    bid_quote = (rel_bid - spread/2 + np.log(1+dir) * params["dir_mult"]) * mid
    ask_quote = (rel_ask + spread/2 + np.log(1+dir) * params["dir_mult"]) * mid

    bid_quote = max(mid*.95,    bid_quote)
    ask_quote = min(mid*1.05,   ask_quote)
    if params["min_spread"]:
        bid_quote = min((1 - params["min_spread"]/2)*mid, bid_quote)
        ask_quote = max((1 + params["min_spread"]/2)*mid, ask_quote)
        
    order_buy["side"] = "buy"
    order_buy["price"] = bid_quote
    order_buy["size"] = trade_qty
    order_buy["post_only"] = "true"

    order_sell["side"] = "sell"
    order_sell["price"] = ask_quote
    order_sell["size"] = trade_qty
    order_sell["post_only"] = "true"

    return order_buy, order_sell

@jit
def test_strategy(data, params):
    # market data + forecast
    book = data["book"]
    dir = data["dir"]
    vol = data["vol"]
    pos = data["pos"]
    # best_bid, best_ask = book["bids"][0][0], book["asks"][0][0]
    
    # strategy params
    max_pos = params["max_pos"]
    trade_qty = params["trade_qty"]
    threshold = params["threshold"]
    
    if (dir > threshold and pos < max_pos) or (pos < -max_pos):
        bid_quote = ask_quote = params["max_quote"]
    elif (dir < -threshold and pos > -max_pos) or (pos > max_pos):
        bid_quote = ask_quote = params["min_quote"]
    else:
        bid_quote = params["min_quote"]
        ask_quote = params["max_quote"]
    
    order_buy = {}
    order_sell = {}

    order_buy["side"] = "buy"
    order_buy["price"] = bid_quote
    order_buy["size"] = trade_qty
    order_buy["post_only"] = "true"

    order_sell["side"] = "sell"
    order_sell["price"] = ask_quote
    order_sell["size"] = trade_qty
    order_sell["post_only"] = "true"

    return order_buy, order_sell

strategies = {
    "strategy:1.0": get_quotes2, 
    "strategy:beta:1.0": test_strategy,
}