from typing import Dict
from YoBitAPI import _YoBitPublic, _YoBitPrivate


class YoBit(_YoBitPublic):
    _exchange_instance: object = None
    _account_list: Dict[object, object] = dict()

    def __new__(cls, *args, **kwargs):
        if cls._exchange_instance is None:
            cls._exchange_instance = super().__new__(cls)
        return cls._exchange_instance

    def __init__(self):
        super(YoBit, self).__init__()

    def add_account(self, title: str, api_key: str, api_secret: str):
        if self._account_list.get(title) is None:
            self._account_list[title] = _Account(title=title, api_key=api_key, api_secret=api_secret)
        return self.account(title)

    @property
    def accounts(self):
        return self._account_list.values()

    def account(self, title: str):
        return self._account_list.get(title)

    def del_account(self, title: str):
        if not self._account_list.get(title) is None:
            self._account_list.pop(title)


class _Account(_YoBitPrivate):
    def __init__(self, title: str, api_key: str, api_secret: str):
        super(_Account, self).__init__(api_key=api_key, api_secret=api_secret)
        self.title = title
        self._tradings_pairs: Dict[object, object] = dict()

    @property
    def markets(self):
        return self._tradings_pairs.values()

    def market(self, pair: str):
        if self._tradings_pairs.get(pair) is None:
            self._tradings_pairs[pair] = _Asset(account=self, pair=pair)
        return self._tradings_pairs[pair]

    def del_market(self, pair: str):
        if not self._tradings_pairs.get(pair) is None:
            self._tradings_pairs.pop(pair)


class _Asset:
    def __init__(self, account: _Account, pair: str):
        self._account = account
        self._pair = pair

    @property
    def title(self):
        return self._pair

    @property
    def active_orders(self):
        return self._account.active_orders(pair=self._pair)

    def sell(self, rate: str, amount: str):
        # self._account.trade(pair=self._pair, order_type='sell', rate=rate, amount=amount)
        pass

    def buy(self):
        pass
