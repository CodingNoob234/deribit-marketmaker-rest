import time, requests
import config
from requests.structures import CaseInsensitiveDict

import logging
LOGGER = logging.getLogger(__name__)

class DeriBit(object):
    def __init__(self, test = False, url=None):
        if test:
            key = config.API_KEY_TEST
            secret = config.API_SECRET_TEST
        else:
            key = config.API_KEY
            secret = config.API_SECRET

        self.key = key
        self.secret = secret
        self.session = requests.Session()

        if url:
            self.url = url
        else:
            if test:
                self.url = "https://test.deribit.com"
            else:
                self.url = "https://www.deribit.com"

        self.refresh_token = None

    def request(self, action, data):
        response = None

        if action.startswith("/api/v2/private/"):
            if self.key is None or self.secret is None:
                raise Exception("Key or secret empty")

            response = self.session.get(self.url + action, params=data, headers = self.headers, verify = True)
        else:
            response = self.session.get(self.url + action, params=data, verify = True)
        
        if response.status_code != 200:
            raise Exception("Wrong response code: {0}".format(response.status_code))
        LOGGER.debug("response:\n" + str(response.json()))
        json = response.json()

        if "result" in json:
            return json["result"]
        elif "message" in json:
            return json["message"]
        else:
            return "Ok"

    def getauth(self):
        if not self.refresh_token:
            options = {
                "grant_type": "client_credentials",
                "client_id": self.key,
                "client_secret": self.secret,
            }
        if self.refresh_token:
            options = {
                "grant_type": "refresh_token",
                "refresh_token": self.refresh_token,
            }
        res = self.request("/api/v2/public/auth", options)
        self.refresh_token = res["refresh_token"]
        access_token = res["access_token"]
        self.headers = CaseInsensitiveDict()
        self.headers["Authorization"] = f"Bearer {access_token}"
        self.last_refresh = time.time()
        return res

    def account_sum(self, currency):
        options = {
            "currency": currency
            }
        return self.request("/api/v2/private/get_account_summary", options)


    def getorderbook(self, instrument_name, session = None):
        if session:
            self.session = session
        return self.request("/api/v2/public/get_order_book", {'instrument_name': instrument_name})

    def getinstruments(self, currency):
        options = {
            "currency": currency,
        }
        return self.request("/api/v2/public/get_instruments", options)

    def getinstrument(self, instrument_name):
        options = {
            "instrument_name": instrument_name,
        }
        return self.request("/api/v2/public/get_instrument", options)

    def getcurrencies(self):
        return self.request("/api/v2/public/get_currencies", {})

    def buy(self, instrument_name, order_type, amount: int, price: float = None, post_only=None, reduce_only=None, label=None):
        options = {
            "instrument_name": instrument_name,
            "type": order_type,
            "amount": amount,
            "time_in_force": "good_til_cancelled",
        }
        if label:
            options["label"] = label
        if post_only:
            options["post_only"] = post_only
        if reduce_only:
            options["reduce_only"] = reduce_only
        if order_type == "limit":
            if price:
                options["price"] = price
            else:
                raise Exception("Price required for limit order")
        return self.request("/api/v2/private/buy", options)

    def sell(self, instrument_name, order_type, amount:int, price:float = None, post_only=None, reduce_only=None, label=None):
        options = {
            "instrument_name":instrument_name,
            "type":order_type,
            "amount":amount,
            "time_in_force": "good_til_cancelled",
        }
        if label:
            options["label"] = label
        if post_only:
            options["post_only"] = post_only
        if reduce_only:
            options["reduce_only"] = reduce_only
        if order_type == "limit":
            if price:
                options["price"] = price
            else:
                raise Exception("Price required for limit order")
        return self.request("/api/v2/private/sell", options)
    
    def order(self, instrument_name, order_type, order_side:str, amount, price=None, post_only=None, reduce_only=None, label=None):
        if order_side.upper() == "BUY":
            self.buy(instrument_name, order_type, amount, price=None, post_only=None, reduce_only=None, label=None)
        elif order_side.upper() == "SELL":
            self.sell(instrument_name, order_type, amount, price=None, post_only=None, reduce_only=None, label=None)
        else:
            raise Exception("No valid order_side provided")

    def cancel(self, orderId):
        options = {
            "order_id": orderId
        }  
        return self.request("/api/v2/private/cancel", options)

    def cancelall(self):
        return self.request("/api/v2/private/cancel_all", {})

    def cancelallbyinstrument(self, instrument_name):
        options = {
            "instrument_name": instrument_name,
        }
        return self.request("/api/v2/private/cancel_all_by_instrument", options)

    def edit(self, orderId, quantity, price, post_only = None):
        options = {
            "order_id": orderId,
            "amount": quantity,
            "price": price
        }
        if post_only:
            options["post_only"] = post_only
        return self.request("/api/v2/private/edit", options)

    def getopenorders(self, instrument_name):
        options = {
            "instrument_name": instrument_name,
        }
        return self.request("/api/v2/private/get_open_orders_by_instrument", options)

    def position(self, instrument_name:str):
        options = {
            "instrument_name": instrument_name}
        return self.request("/api/v2/private/get_position", options)

    def getorderstate(self, order_id):
        options = {
            "order_id": order_id,
        }
        return self.request("/api/v2/private/get_order_state", options)

    def tradehistory(self, instrument_name, countNum = None, start_seq = None, end_seq = None):
        options = {
            "instrument_name": instrument_name,
        }
        if start_seq:
            options["start_seq"] = start_seq
        if end_seq:
            options["end_seq"] = end_seq
        if countNum:
            options["count"] = countNum
        
        return self.request("/api/v2/private/get_user_trades_by_instrument", options)

    def tradehistory_bytime(self, instrument_name, countNum = None, start_timestamp = None, end_timestamp = None):
        options = {
            "instrument_name": instrument_name,
        }
        if start_timestamp:
            options["start_timestamp"] = start_timestamp
        if end_timestamp:
            options["end_timestamp"] = end_timestamp
        if countNum:
            options["count"] = countNum
        
        return self.request("/api/v2/private/get_user_trades_by_instrument_and_time", options)

    def gettransactionlog(self, currency, start_timestamp, end_timestamp, count=None):
        options = {
            "currency": currency,
            "start_timestamp": start_timestamp,
            "end_timestamp": end_timestamp,
        }
        if count:
            options["count"] = count
        return self.request("/api/v2/private/get_transaction_log", options)

    def getpricehistory(self, instrument_name, start_timestamp, end_timestamp, delta):
        options = { 
            "currency": instrument_name,
            "start_timestamp": start_timestamp,
            "end_timestamp": end_timestamp,
            "resolution": delta,
        }
        return self.request("/api/v2/public/get_tradingview_chart_data", options)

    def getlasttrades(self, instrument_name, count = None):
        options = {
            "instrument_name": instrument_name,
        }
        if count:
            options["count"] = count
        return self.request("/api/v2/public/get_last_trades_by_instrument", options)

    def getlasttrades_bytime(self, instrument_name, start_timestamp, end_timestamp):
        options = {
            "instrument_name": instrument_name,
            "start_timestamp": start_timestamp,
            "end_timestamp": end_timestamp,
        }
        return self.request("/api/v2/public/get_last_trades_by_instrument_and_time", options)
    
    def get_index_price(self, index_name):
        options = {
            "index_name": index_name,
        }
        return self.request("/api/v2/public/get_index_price", options)