import hmac
import hashlib
import requests
import time
from urllib.parse import urlencode


class _YoBitPublic:
    """
        Basic methods to use YoBit Public API (https://yobit.net/en/api/)
        Available methods: depth, ticker, trades, info.
    """

    url = 'https://yobit.net'

    def __init__(self):
        self._api_public_url = '/api/3/'

    """
        Public methods query
    """
    def _api_query_public(self, url: str):
        request_url = self.url + url
        try:
            return requests.get(request_url).json()
        except ValueError as ex:
            raise Exception(f'Exchange has not responded with JSON: {ex}')

    """
        Compose public query URL
        The link looks like: https://yobit.net/api/3/{method name}/{pair list}
        Several pairs can be stipulated without repetitions or only one pair can be stipulated.
    """

    def _make_request_url(self, method: str, pair: str = '', ignore_invalid: bool = False, limit: int = 0):
        request_url = self._api_public_url + method
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

    """
        Use to get a server time and coin pares of the YoBit market.
        Hidden pairs are not shown in the list at Stock Exchange home page, but exchange transactions continue.
        In case if any pair is disabled it disappears from the list.
    
        :return JSON
        'servertime': timestamp
        'pairs': dict
            {pair}:dict
    
        {pair}
        - decimal_places: Quantity of permitted numbers after decimal point
        - min_price: minimal permitted price
        - max_price: maximal permitted price
        - min_amount: minimal permitted buy or sell amount
        - hidden: pair is hidden (0 or 1)
        - fee: pair commission
    """

    def info(self):
        request_url = self._make_request_url(method='info')
        return self._api_query_public(request_url)

    """
        Method provides statistic data for the last 24 hours.
        Note! If we disable any pair from the list API will throw an error message. 
        To ignore of such errors GET-parameter is available ignore_invalid.
    
        :return JSON
        {pair}:dict
    
        - high: maximal price
        - low: minimal price
        - avg: average price
        - vol: traded volume
        - vol_cur: traded volume in currency
        - last: last transaction price
        - buy: buying price
        - sell: selling price
        - updated: last cache upgrade
    """

    def ticker(self, pair: str, ignore_invalid: bool = True):
        request_url = self._make_request_url(method='ticker', pair=pair, ignore_invalid=ignore_invalid)
        return self._api_query_public(request_url)

    """
        Method returns information about lists of active orders for selected pairs.
        GET-parameter limit stipulates size of withdrawal (on default 150 to 2000 maximum).
        Note! If we disable any pair from the list API will throw an error message. 
        To ignore of such errors GET-parameter is available ignore_invalid.
    
        :return JSON
        {pair}:['asks': list, 'bids': list]
    
        - asks: selling orders
        - bids: buying orders
    """

    def depth(self, pair: str, ignore_invalid: bool = True, limit: int = 150):
        request_url = self._make_request_url(method='depth', pair=pair, ignore_invalid=ignore_invalid, limit=limit)
        return self._api_query_public(request_url)

    """
        Method returns information about the last transactions of selected pairs.
        GET-parameter limit stipulates size of withdrawal (on default 150 to 2000 maximum).
        Note! If we disable any pair from the list API will throw an error message. 
        To ignore of such errors GET-parameter is available ignore_invalid.
    
        :return JSON
        {pair}:[{},{}]
    
        - type: ask - sell, bid - buy
        - price: buying / selling price
        - amount: amount
        - tid: transaction id
        - timestamp: transaction timestamp
    """

    def trades(self, pair: str, ignore_invalid: bool = True, limit: int = 150):
        request_url = self._make_request_url(method='trades', pair=pair, ignore_invalid=ignore_invalid, limit=limit)
        return self._api_query_public(request_url)


class _YoBitPrivate(_YoBitPublic):
    def __init__(self, api_key: str, api_secret: str):
        super(_YoBitPrivate, self).__init__()
        self._api_key = api_key
        self._api_secret = api_secret
        self._api_private_url = '/tapi/'
        self._nonce = int(time.time())

    def _api_query(self, options: dict):
        sign = hmac.new(self._api_secret.encode(), urlencode(options).encode(), hashlib.sha512)
        headers = dict({'Key': self._api_key,
                        'Sign': sign.hexdigest()})
        try:
            return requests.post(self.url + self._api_private_url, data=options, headers=headers).json()
        except ValueError as ex:
            raise Exception(f'Exchange has not responded with JSON: {ex}')

    def _get_nonce(self):
        if self._nonce == int(time.time()):
            time.sleep(1)
        self._nonce = int(time.time())
        return str(self._nonce)

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

    def trade(self, pair: str, order_type: str = None, rate: str = None, amount: str = None):
        options = dict({'method': 'Trade',
                        'pair': pair,
                        'type': order_type,
                        'rate': rate,
                        'amount': amount})
        return self._api_query(options=options)
