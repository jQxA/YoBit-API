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
        self._api_public_url: str = '/api'

    """
        Public methods query
    """
    def _api_query_public(self, url: str):
        request_url: str = self.url + url
        try:
            return requests.get(request_url).json()
        except ValueError as ex:
            raise Exception(f'Exchange has not responded with JSON: {ex}')

    """
        Compose public query URL
        The link looks like: https://yobit.net/api/{market_type}/{method name}/{pair list}
        Several pairs can be stipulated without repetitions or only one pair can be stipulated.
    """
    def _make_request_url(self, market_type: str, method: str, pair: str = None,
                          ignore_invalid: bool = False, limit: int = 0):
        request_url: str = f'{self._api_public_url}/{market_type}/{method}'
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
        request_url = self._make_request_url(market_type='3', method='info')
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
        request_url = self._make_request_url(market_type='3', method='ticker', pair=pair, ignore_invalid=ignore_invalid)
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
        request_url = self._make_request_url(market_type='3', method='depth', pair=pair,
                                             ignore_invalid=ignore_invalid, limit=limit)
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
        request_url = self._make_request_url(market_type='3', method='trades', pair=pair,
                                             ignore_invalid=ignore_invalid, limit=limit)
        return self._api_query_public(request_url)

    """
        Use to get a server time and pools of the YoBit DeFi market.
        
        Hidden pools are not shown in the list at Exchange home page.
        In case if any pair is disabled it disappears from the list.
    
        - liq1: liquidity providers invested currency 1 in the pool
        - liq2: liquidity providers invested currency 2 in the pool
        - price1: actual price 1
        - price2: actual price 2
        - fee: in % (0.003 means 0.3%)
        - price24high1: the highest price 1 at last 24 hours
        - price24low1: the lowest price 1 at last 24 hours
        - price24high2: the highest price 2 at last 24 hours
        - price24low2: the lowest price 2 at last 24 hours
        - vol1: volume of swaps in currency 1 at last 24 hours
        - vol2: volume of swaps in currency 2 at last 24 hours
        - algo1: erc20, trc20, bep20 or SHA256/Scrypt/X11
        - tokenid1: currency 1 token address for erc20, trc20, bep20 algos or empty for others
        - algo2: erc20, trc20, bep20 or SHA256/Scrypt/X11
        - tokenid2: currency 2 token address for erc20, trc20, bep20 algos or empty for others
    """
    def defi_info(self):
        request_url = self._make_request_url(market_type='defi', method='info')
        return self._api_query_public(request_url)


class _YoBitPrivate(_YoBitPublic):
    """
        Basic methods to use YoBit Private API (https://yobit.net/en/api/)
        Available methods: getinfo, order_info, active_orders, cancel_order, trade_history, trade.

        Trade API is necessary for creation and cancellation of orders, request of active balances as well
        as for obtaining the information that requires access to account personal data.
    """
    def __init__(self, api_key: str, api_secret: str):
        super(_YoBitPrivate, self).__init__()
        self._api_key: str = api_key
        self._api_secret: str = api_secret
        self._api_private_url: str = '/tapi/'
        self._nonce: int = 0

    """
        Private methods query
        
        :param
        - options: dict - query options
        
        :return
        All the responses are created by the server in JSON format

        Example of server's successful response:
        {"success":1,"return":{%answer%}}

        Example of error informing response:
        {"success":0,"error":"%error%"}
    """
    def _api_query(self, options: dict):
        sign = hmac.new(self._api_secret.encode(), urlencode(options).encode(), hashlib.sha512)
        headers = dict({'Key': self._api_key,
                        'Sign': sign.hexdigest()})

        try:
            return self.result(requests.post(self.url + self._api_private_url, data=options, headers=headers).json())
        except ValueError as ex:
            raise Exception(f'Exchange has not responded with JSON: {ex}')

    """
        Returns only the api query result
        Returns None if an error occurs.
    """
    @staticmethod
    def result(request: dict):
        if request.get('success'):
            return request.get('return')
        else:
            print(request)
            return None

    """
        Generate nonce
        Parameter nonce (1 minimum to 2147483646 maximum) in succeeding request should exceed that in the previous one.
        To null nonce it is necessary to generate new key.
    """
    def _get_nonce(self):
        if self._nonce <= int(time.time()):
            time.sleep(1)
        self._nonce = int(time.time())
        return str(self._nonce)

    """
        Method returns information about user's balances and privileges of API-key as well as server time.
        Requirements: privilege of key info
        
        :param
        absent
        
        :return
        - funds: available account balance (does not include money on open orders)
        - funds_incl_orders: available account balance (include money on open orders)
        - rights: privileges of key. withdraw is not used (reserved)
        - transaction_count: always 0 (outdated)
        - open_orders: always 0 (outdated)
        - server_time: server time
    """
    def getinfo(self):
        options = dict({'method': 'getInfo',
                        'nonce': self._get_nonce()})
        return self._api_query(options=options)

    """
        Method returns detailed information about the chosen order
        Requirements: privileges of key info
        
        :param:
        - order_id: order ID (value: numeral)
        
        :return
        - array key: order ID (in example: 100025362)
        - pair: order pair (example: ltc_btc)
        - type: order type (example: buy or sell)
        - start_amount: starting amount at order creation
        - amount: order amount remaining to buy or to sell
        - rate: price of buying or selling
        - timestamp_created: order creation time
        - status: 0 - active, 1 - fulfilled and closed, 2 - cancelled, 3 - cancelled after partially fulfilled.
    """
    def order_info(self, order_id: str):
        options = dict({'method': 'OrderInfo',
                        'nonce': self._get_nonce(),
                        'order_id': order_id})
        return self._api_query(options=options)

    """
        Method returns list of user's active orders
        Requirements: privileges of key info
        
        :param
        - pair: pair (example: ltc_btc)
        
        :return
        - keys of array: order ID (in example: 100025362)
        - pair: pair (example: ltc_btc)
        - type: transaction type (example: buy or sell)
        - amount: remains to buy or to sell
        - rate: price of buying or selling
        - timestamp_created: order creation time
        - status: always 0 (outdated)
    """
    def active_orders(self, pair: str):
        options = dict({'method': 'ActiveOrders',
                        'nonce': self._get_nonce(),
                        'pair': pair})
        return self._api_query(options=options)

    """
        Method cancels the chosen order
        Requirements: privileges of key info&trade
        
        :param
        - order_id: order ID (value: numeral)
        
        :return
        - order_id: order ID
        - funds: balances active after request
    """
    def cancel_order(self, order_id: str):
        options = dict({'method': 'CancelOrder',
                        'nonce': self._get_nonce(),
                        'order_id': order_id})
        return self._api_query(options=options)

    """
        Method returns transaction history.
        Requirements: privileges of key info
        
        :param
        - from: No. of transaction from which withdrawal starts (value: numeral, on default: 0)
        - count: quantity of withdrawal transactions (value: numeral, on default: 1000)
        - from_id: ID of transaction from which withdrawal starts (value: numeral, on default: 0)
        - end_id: ID of transaction at which withdrawal finishes (value: numeral, on default: ∞)
        - order: sorting at withdrawal (value: ASC or DESC, on default: DESC)
        - since: the time to start the display (value: unix time, on default: 0)
        - end: the time to end the display (value: unix time, on default: ∞)
        - pair: pair (example: ltc_btc)
        
        While using parameters since or end parameter order automatically takes the value ASC.
        While using parameters since the earliest date available to get transaction history is one week ago.
        
        :return
        - array keys: order IDs (in example: 24523)
        - pair: pair (example: ltc_btc)
        - type: transaction type (example: buy or sell)
        - amount: bought or sold amount
        - rate: price of buying or selling
        - order_id: order ID
        - is_your_order: is the order yours (1 or 0)
        - timestamp: transaction time
    """
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

    """
        Method that allows creating new orders for stock exchange trading
        Requirements: privileges of key info&trade
        
        :param
        - pair: pair (example: ltc_btc)
        - type: transaction type (example: buy or sell)
        - rate: exchange rate for buying or selling (value: numeral)
        - amount: amount needed for buying or selling (value: numeral)
        
        :return
        - received: amount of currency bought / sold
        - remains: amount of currency to buy / to sell
        - order_id: created order ID
        - funds: funds active after request
    """
    def trade(self, pair: str = None, order_type: str = None, rate: str = None, amount: str = None):
        options = dict({'method': 'Trade',
                        'pair': pair,
                        'type': order_type,
                        'rate': rate,
                        'amount': amount})
        return self._api_query(options=options)

    """
        Method returns deposit address
        Requirements: privileges of key deposits

        :param
        - coinName: ticker (example: BTC)
        - need_new: value: 0 or 1, on default: 0
    """
    def deposit(self, currency: str, need_new: bool = False):
        options = dict({'method': 'GetDepositAddress',
                        'coinName': currency,
                        'need_new': str(int(need_new))})
        return self._api_query(options=options)

    """
        Method creates withdrawal request
        Requirements: privileges of key withdrawals
        
        :param
        - coinName: ticker (example: BTC)
        - amount: amount to withdraw
        - address: destination address
    """
    def withdraw(self, currency: str, amount: str, address: str):
        options = dict({'method': 'WithdrawCoinsToAddress',
                        'coinName': currency,
                        'amount': amount,
                        'address': address})
        return self._api_query(options=options)

    """
        Method allows you to create Coupons (yobicodes)
        Method alias: CreateYobicode
        Requirements: privileges of key withdrawals
        
        :param
        - currency: ticker (example: BTC)
        - amount: amount of coupon
        
        :return
        - coupon: yobicode
        - transID: always 1 for compatibility with api of other exchanges
        - funds: balances active after request
    """
    def create_coupon(self, currency: str, amount: str):
        options = dict({'method': 'CreateCoupon',
                        'currency': currency,
                        'amount': amount})
        return self._api_query(options=options)

    """
        Method is used to redeem Coupon (yobicodes)
        Method alias: RedeemYobicode
        Requirements: privileges of key deposits
        
        :param
        - coupon: yobicode to redeem (example: YOBITUZ0HHSTB...OQX3H01BTC)
        
        :return
        - couponAmount: The amount that has been redeemed.
        - couponCurrency: The currency of the yobicode that has been redeemed.
        - transID: always 1 for compatibility with api of other exchanges
        - funds: balances active after request
    """
    def redeem_coupon(self, coupon: str):
        options = dict({'method': 'RedeemCoupon',
                        'coupon': coupon})
        return self._api_query(options=options)

    """
        Method is used to get info about Swap before processing of it with DefiSwap function.
        Requirements: privileges of key info&trade
        
        :param
        - pool: pool name in format cur1_cur2 (example: btc_usdt)
        - PayCurrency: currency that you pay for swap. It should be cur1 OR cur2 (example: usdt)
        - PayAmount: amount that you pay for swap (example: 1.123)
        
        :return
        - swap_made: is always 0. It shows that swap hasn't been processed.
        - pay_amount: amount that you pay for swap
        - pay_currency: currency that you pay for swap
        - get_amount: amount that you get during swap
        - get_currency: currency that you get during swap
        - price_of_swap: price of swap
        - fee_total: amount of fee
        - fee_total_currency: currency of fee
        - price1_before: actual price 1 of pool before swap
        - price1_after: actual price 2 of pool before swap
        - price2_before: shows what the price 1 would be if the swap processed
        - price2_after: shows what the price 2 would be if the swap processed
    """
    def defi_swap_info(self, pool: str, currency: str, amount: str):
        options = dict({'method': 'DefiSwapInfo',
                        'pool': pool,
                        'PayCurrency': currency,
                        'PayAmount': amount})
        return self._api_query(options=options)

    """
        Method is used to make Swaps.
        Requirements: privileges of key info&trade
        
        :param
        - pool: pool name in format cur1_cur2 (example: btc_usdt)
        - PayCurrency: currency that you pay for swap. It should be cur1 OR cur2 (example: usdt)
        - PayAmount: amount that you pay for swap (example: 1.123)
        
        :return
        - pay_amount: amount that you pay for swap
        - pay_currency: currency that you pay for swap
        - get_amount: amount that you get during swap
        - get_currency: currency that you get during swap
        - price_of_swap: price of swap
        - fee_total: amount of fee
        - fee_total_currency: currency of fee
        - price1_before: actual price 1 of pool before swap
        - price1_after: actual price 2 of pool before swap
        - price2_before: shows what the price 1 would be if the swap processed
        - price2_after: shows what the price 2 would be if the swap processed
        - new_balance1: your new balance of currency 1 after swap
        - new_balance1_currency: currency 1 name
        - new_balance2: your new balance of currency 2 after swap
        - new_balance2_currency: currency 2 name
        - pooled1: your part of currency 1 in defi pool
        - pooled2: your part of currency 2 in defi pool
        - pooled_est: estimated amount of pooled1+pooled2 in USD
        - pooled_pr: your percentage of defi pool (example: 2.1456 means 2.1456%)
        - comfee1: fees earned (cumulative of currency 1)
        - comfee2: fees earned (cumulative of currency 2)
        - comfee_est: estimated amount of comfee1+comfee2 in USD
    """
    def defi_swap(self, pool: str, currency: str, amount: str):
        options = dict({'method': 'DefiSwap',
                        'pool': pool,
                        'PayCurrency': currency,
                        'PayAmount': amount})
        return self._api_query(options=options)
