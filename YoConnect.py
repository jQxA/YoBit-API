from typing import Dict
from YoBitAPI import _YoBitPublic, _YoBitPrivate


class YoBit(_YoBitPublic):
    """
        Basic class to use YoBit API
        YoBit Public API methods available
    """
    _exchange_instance: object = None
    _account_list: Dict[object, object] = dict()

    """
        It doesn't make sense to create more than one class instance
    """
    def __new__(cls, *args, **kwargs):
        if cls._exchange_instance is None:
            cls._exchange_instance = super().__new__(cls)
        return cls._exchange_instance

    def __init__(self):
        super(YoBit, self).__init__()

    """
        Add an account function. An instance of a class can contain any count of accounts.

        After adding an account, you should refer to its class instance. This is necessary for the correct 
        formation of the nonce when working with several trading pairs.
        
        :param
        - title - title for account calling
        - api_key - YoBit API Key
        - api_secret - YoBit API Secret
        
        :return
        - Object : _Account
    """
    def add_account(self, title: str, api_key: str, api_secret: str):
        if self._account_list.get(title) is None:
            self._account_list[title] = _Account(title=title, api_key=api_key, api_secret=api_secret)
        return self.account(title)

    @property
    def accounts(self):
        return self._account_list.values()

    def account(self, title: str):
        return self._account_list.get(title)

    def delete_account(self, title: str):
        if not self._account_list.get(title) is None:
            self._account_list.pop(title)


class _Account(_YoBitPrivate):
    def __new__(cls, *args, **kwargs):
        if _YoBitPrivate(api_key=kwargs.get('api_key'), api_secret=kwargs.get('api_secret')).getinfo() is not None:
            return super().__new__(cls)

    def __init__(self, title: str, api_key: str, api_secret: str):
        super(_Account, self).__init__(api_key=api_key, api_secret=api_secret)
        self.main_info = self.getinfo()
        self.rights: dict = self.main_info['rights']
        self.funds: dict = self.main_info['funds']
        self.all_funds: dict = self.main_info['funds_incl_orders']

        self.title: str = title
        self._markets: Dict[object, object] = dict()
        self._pools: Dict[object, object] = dict()

    @property
    def markets(self):
        return self._markets.values()

    def market(self, pair: str):
        if self._markets.get(pair) is None:
            yobit_market_list: dict = self.info()['pairs']
            if yobit_market_list.get(pair) is not None:
                self._markets[pair] = _Market(account=self, pair=pair)
        return self._markets.get(pair)

    def delete_market(self, pair: str):
        if not self._markets.get(pair) is None:
            self._markets.pop(pair)

    @property
    def pools(self):
        return self._pools.values()

    def pool(self, pool: str):
        if self._pools.get(pool) is None:
            self._pools[pool] = _DeFiMarket(account=self, pool=pool)
        return self._pools.get(pool)

    def delete_pool(self, pool: str):
        if not self._pools.get(pool) is None:
            self._pools.pop(pool)


class _Market:
    def __init__(self, account: _Account, pair: str):
        self._account: _Account = account
        self._title: str = pair

        self._orders_list: dict = dict()
        self.active_orders()

        self._bids: dict = self.bids()
        self._asks: dict = self.asks()

        self._depth: dict = dict()
        self.market_depth()

    @property
    def market(self) -> str:
        return self._title

    def market_depth(self) -> dict:
        self._depth = self._account.depth(pair=self._title, ignore_invalid=True, limit=2000)
        return self._depth

    def active_orders(self) -> dict:
        self._orders_list = self._account.active_orders(pair=self.market)
        return self._orders_list

    def sell(self, rate: str, amount: str) -> bool:
        return self._account.trade(pair=self.market, order_type='sell', rate=rate, amount=amount)

    def buy(self, rate: str, amount: str) -> bool:
        return self._account.trade(pair=self.market, order_type='buy', rate=rate, amount=amount)

    def bids(self) -> dict:
        result: dict = dict()
        for key in self._orders_list:
            if self._orders_list[key]['type'] == 'buy':
                result[key] = self._orders_list.get(key)
        return result

    def max_bid(self) -> dict:
        result: dict = dict()
        max_rate: float = 0
        for order in self._bids:
            if self._bids[order]['rate'] >= max_rate:
                max_rate = self._bids[order]['rate']
                result[order] = self._bids[order]
        return result

    def asks(self) -> dict:
        result: dict = dict()
        for key in self._orders_list:
            if self._orders_list[key]['type'] == 'sell':
                result[key] = self._orders_list.get(key)
        return result

    def min_ask(self) -> dict:
        result: dict = dict()
        min_rate: float = 0
        for order in self._asks:
            if min_rate == 0:
                min_rate = self._asks[order]['rate']
            if self._asks[order]['rate'] <= min_rate:
                min_rate = self._asks[order]['rate']
                result[order] = self._asks[order]
        return result


class _DeFiMarket:
    def __init__(self, account: _Account, pool: str):
        self._account: _Account = account
        self._pool = pool

    @property
    def pool(self):
        return self._pool

    def swap_info(self, currency: str, amount: str):
        return self._account.defi_swap_info(pool=self.pool, currency=currency, amount=amount)

    def swap(self, currency: str, amount: str):
        return self._account.defi_swap(pool=self.pool, currency=currency, amount=amount)
