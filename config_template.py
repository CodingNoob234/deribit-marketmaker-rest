config_dict = {
    "asset": "BTC",
    "contract": "BTC-PERPETUAL",
    "currency": "BTC",
    "min_qty": 10,
    "trade_qty": 10,
    "sign": 1,
    "logging_level": "INFO"
}

strategy_params = {
    "trade_qty": 10,
    "max_position": 1,
    "risk_aversion": 1e0,
    "min_spread": .01,
    "base_spread": .001,
    "vol_mult": 1e0,
    "dir_mult": 1e0,
    
    "threshold": 1.75e-5,
    "min_quote": 25000,
    "max_quote": 35000,
    
    "ML_model": "strategy:1.0",
}

API_KEY = ''
API_SECRET = ''

API_KEY_TEST = ''
API_SECRET_TEST = ''

TEST_EXCHANGE = False