import hmac
import hashlib
import requests
import time
from urllib.parse import urlencode


class YoBitAPI:
    __exchange_instance: object = None
    url = 'https://yobit.net'

    def __new__(cls, *args, **kwargs):
        if cls.__exchange_instance is None:
            cls.__exchange_instance = super().__new__(cls)
        return cls.__exchange_instance

    def __init__(self):
        self.api_public_url = '/api/3/'

    def _api_query_public(self, url: str):
        request_url = self.url + url
        try:
            return requests.get(request_url).json()
        except ValueError as ex:
            raise Exception(f'Exchange has not responded with JSON: {ex}')

    def _make_request_url(self, method: str, pair: str = '', ignore_invalid: bool = False, limit: int = 0):
        request_url = self.api_public_url + method
        if pair:
            request_url += f'/{pair}'

        options = dict()
        if ignore_invalid:
            options['ignore_invalid'] = '1'
        if limit > 0:
            options['limit'] = str(limit)

        options_url = urlencode(options)
        if options_url > '':
            request_url += f'?{options_url}'

        return request_url

    def info(self):
        request_url = self._make_request_url(method='info')
        return self._api_query_public(request_url)

    def ticker(self, pair: str, ignore_invalid: bool = True):
        request_url = self._make_request_url(method='ticker', pair=pair, ignore_invalid=ignore_invalid)
        return self._api_query_public(request_url)

    def depth(self, pair: str, ignore_invalid: bool = True, limit: int = 150):
        request_url = self._make_request_url(method='depth', pair=pair, ignore_invalid=ignore_invalid, limit=limit)
        return self._api_query_public(request_url)

    def trades(self, pair: str, ignore_invalid: bool = True, limit: int = 150):
        request_url = self._make_request_url(method='trades', pair=pair, ignore_invalid=ignore_invalid, limit=limit)
        return self._api_query_public(request_url)


class YoBitAccount(YoBitAPI):
    __account_instance: object = None

    def __new__(cls, *args, **kwargs):
        if cls.__account_instance is None:
            cls.__account_instance = super().__new__(cls)
        return cls.__account_instance

    def __init__(self, api_key: str, api_secret: str):
        super(YoBitAccount, self).__init__()
        self.api_key = api_key
        self.api_secret = api_secret
        self.api_private_url = '/tapi/'
        self.nonce = int(time.time())

    def _get_account_instance(self):
        return self.__account_instance

    def _api_query(self, options: dict):
        sign = hmac.new(self.api_secret.encode(), urlencode(options).encode(), hashlib.sha512)
        headers = dict({'Key': self.api_key,
                        'Sign': sign.hexdigest()})
        try:
            return requests.post(YoBitAPI.url + self.api_private_url, data=options, headers=headers).json()
        except ValueError as ex:
            raise Exception(f'Exchange has not responded with JSON: {ex}')

    def _get_nonce(self):
        if self.nonce == int(time.time()):
            time.sleep(1)
        self.nonce = int(time.time())
        return str(self.nonce)

    def getinfo(self):
        options = dict({'method': 'getInfo',
                        'nonce': self._get_nonce()})
        return self._api_query(options=options)

    def order_info(self, order_id: str):
        options = dict({'method': 'OrderInfo',
                        'nonce': self._get_nonce(),
                        'order_id': order_id})
        return self._api_query(options=options)

    def active_orders(self, pair: str):
        options = dict({'method': 'ActiveOrders',
                        'nonce': self._get_nonce(),
                        'pair': pair})
        return self._api_query(options=options)

    def cancel_order(self, order_id: str):
        options = dict({'method': 'CancelOrder',
                        'nonce': self._get_nonce(),
                        'order_id': order_id})
        return self._api_query(options=options)

    def trade_history(self, from_: str = '0', count: str = '1000', from_id: str = '0', end_id: str = '',
                      order: str = 'DESC', since: str = '0', end: str = '', pair: str = ''):
        options = dict({'method': 'TradeHistory',
                        'nonce': self._get_nonce(),
                        'from': from_,
                        'count': count,
                        'from_id': from_id,
                        'end_id': end_id,
                        'order': order,
                        'since': since,
                        'end': end,
                        'pair': pair})
        return self._api_query(options=options)


class YoBitTrade:
    def __init__(self, account: YoBitAccount, pair: str):
        self.account: YoBitAccount = account
        self.pair: str = pair

    def _trade(self):
        pass

    def get_active_orders(self):
        return self.account.active_orders(pair=self.pair)

    def sell(self):
        pass

    def buy(self):
        pass
