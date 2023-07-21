from forexconnect import Common, ForexConnect, fxcorepy
import threading
from time import sleep

OPP_BUY_SELL_MAP = {"B": "S", "S": "B"}


class TradesMonitor:
    def __init__(self):
        self.__open_order_id = None
        self.__trades = {}
        self.__event = threading.Event()

    def on_added_trade(self, _, __, trade_row):
        open_order_id = trade_row.open_order_id
        self.__trades[open_order_id] = trade_row
        if self.__open_order_id == open_order_id:
            self.__event.set()

    def wait(self, time, open_order_id):
        self.__open_order_id = open_order_id

        trade_row = self.find_trade(open_order_id)
        if trade_row is not None:
            return trade_row

        self.__event.wait(time)

        return self.find_trade(open_order_id)

    def find_trade(self, open_order_id):
        if open_order_id in self.__trades:
            return self.__trades[open_order_id]
        return None

    def reset(self):
        self.__open_order_id = None
        self.__trades.clear()
        self.__event.clear()


class OrdersMonitor:
    def __init__(self):
        self.__order_id = None
        self.__added_orders = {}
        self.__deleted_orders = {}
        self.__changed_orders = {}
        self.__added_order_event = threading.Event()
        self.__changed_orders_event = threading.Event()
        self.__deleted_order_event = threading.Event()

    def on_added_order(self, _, __, order_row):
        order_id = order_row.order_id
        self.__added_orders[order_id] = order_row
        if self.__order_id == order_id:
            self.__added_order_event.set()

    def on_changed_order(self, _, __, order_row):
        order_id = order_row.order_id
        self.__changed_orders[order_id] = order_row
        if self.__order_id == order_id:
            self.__changed_orders_event.set()

    def on_deleted_order(self, _, __, order_row):
        order_id = order_row.order_id
        self.__deleted_orders[order_id] = order_row
        if self.__order_id == order_id:
            self.__deleted_order_event.set()

    def wait(self, time, order_id):
        self.__order_id = order_id

        is_order_added = True
        is_order_changed = True
        is_order_deleted = True

        # looking for an added order
        if order_id not in self.__added_orders:
            is_order_added = self.__added_order_event.wait(time)

        if is_order_added:
            self.__added_orders[order_id]

        # looking for an changed order
        if order_id not in self.__changed_orders:
            is_order_changed = self.__changed_orders_event.wait(time)

        if is_order_changed:
            self.__changed_orders[order_id]

        # looking for a deleted order
        if order_id not in self.__deleted_orders:
            is_order_deleted = self.__deleted_order_event.wait(time)

        return is_order_added and is_order_changed and is_order_deleted

    def reset(self):
        self.__order_id = None
        self.__added_orders.clear()
        self.__deleted_orders.clear()
        self.__added_order_event.clear()
        self.__deleted_order_event.clear()


class PositionUtils:
    @staticmethod
    def get_trading_amount(fx, instrument, account, lots):
        login_rules = fx.login_rules
        trading_settings_provider = login_rules.trading_settings_provider
        base_unit_size = trading_settings_provider.get_base_unit_size(instrument, account)
        amount = base_unit_size * lots
        return amount

    @staticmethod
    def is_number(number):
        if type(number) in [float, int]:
            return True
        else:
            return False

    def get_lots(self, lots):
        if self.is_number(lots):
            return lots
        else:
            return 1

    @staticmethod
    def calculate_stop_loss(pip_size, price, transaction_type):
        if transaction_type == "S":
            stop_loss = price + pip_size
        else:
            stop_loss = price - pip_size
        return stop_loss

    @staticmethod
    def calculate_limit(pip_size, price, transaction_type):
        if transaction_type == "S":
            stop_loss = price - pip_size
        else:
            stop_loss = price + pip_size
        return stop_loss

    def execute_trade(self, fx, order_input, wait_for_trades=True):

        request = fx.create_order_request(**order_input)
        orders_monitor = OrdersMonitor()
        trades_monitor = TradesMonitor()
        orders_table = fx.get_table(ForexConnect.ORDERS)
        trades_table = fx.get_table(ForexConnect.TRADES)
        trades_listener = Common.subscribe_table_updates(
            trades_table, on_add_callback=trades_monitor.on_added_trade
        )
        orders_listener = Common.subscribe_table_updates(
            orders_table,
            on_add_callback=orders_monitor.on_added_order,
            on_delete_callback=orders_monitor.on_deleted_order,
            on_change_callback=orders_monitor.on_changed_order,
        )

        try:
            result = fx.send_request(request)
            order_id = result.order_id
            if not wait_for_trades:
                return order_id
        except Exception as e:
            raise e
        else:
            # Waiting for an order to appear/delete or timeout (default 30)
            is_success = orders_monitor.wait(30, order_id)
            trade_row = None
            if is_success:
                # Waiting for an trade to appear or timeout (default 30)
                trade_row = trades_monitor.wait(30, order_id)
            else:
                None, order_id

            if trade_row is None:
                None, order_id
            else:
                return trade_row.trade_id, order_id

            trades_listener.unsubscribe()
            orders_listener.unsubscribe()

    def execute_edit_trade(self, fx, order_input):

        request = fx.create_order_request(**order_input)
        orders_monitor = OrdersMonitor()
        orders_table = fx.get_table(ForexConnect.ORDERS)
        orders_listener = Common.subscribe_table_updates(
            orders_table,
            on_add_callback=orders_monitor.on_added_order,
            on_delete_callback=orders_monitor.on_deleted_order,
            on_change_callback=orders_monitor.on_changed_order,
        )

        try:
            resp = fx.send_request(request)

            if order_input.get("ORDER_ID"):
                order_id = order_input.get("ORDER_ID")
            else:
                order_id = resp.order_id
        except Exception as e:
            raise e

        sleep(5)
        order_table = fx.get_table(ForexConnect.ORDERS).get_rows_by_column_value(
            "order_id", order_id
        )

        if list(order_table)[0].rate == order_input.get("RATE"):
            print("The order has been Updated Successfully. Order ID: {0:s}".format(order_id))
            order_id = None
        else:
            print("Not able to confirm the trade status. Please verify using tables")

        orders_listener.unsubscribe()
        return order_id

    def make_order_input(self, fx, **kwargs):

        instrument = kwargs.get("INSTRUMENT")
        lots = self.get_lots(kwargs.get("LOTS"))
        transaction_type = kwargs.get("TRANSACTION_TYPE")
        account = Common.get_account(fx, None)
        amount = self.get_trading_amount(fx, instrument, account, lots)

        kwargs_dict = {
            "ACCOUNT_ID": account.account_id,
            "SYMBOL": instrument,
            "AMOUNT": amount,
            "BUY_SELL": transaction_type,
        }

        offer = Common.get_offer(fx, instrument)
        if self.is_number(kwargs.get("RATE")):
            kwargs_dict.update({"RATE": kwargs.get("RATE")})
            price = kwargs.get("RATE")
        else:
            if transaction_type == "B":
                price = offer.ask
            else:
                price = offer.bid

        if self.is_number(kwargs.get("RATE_STOP")):
            stop_loss = self.calculate_stop_loss(
                kwargs.get("RATE_STOP") * offer.PointSize, price, transaction_type
            )
            kwargs_dict.update({"RATE_STOP": stop_loss})

        if self.is_number(kwargs.get("RATE_LIMIT")):
            limit = self.calculate_limit(
                kwargs.get("RATE_LIMIT") * offer.PointSize, price, transaction_type
            )
            kwargs_dict.update({"RATE_LIMIT": limit})

        if self.is_number(kwargs.get("TRAIL_STEP_STOP")):
            kwargs_dict.update({"TRAIL_STEP_STOP": kwargs.get("TRAIL_STEP_STOP")})

        return kwargs_dict

    def make_order_input_limit(self, trade, limit_price):

        if self.is_number(limit_price):
            kwargs_dict = {
                "order_type": fxcorepy.Constants.Orders.LIMIT,
                "command": fxcorepy.Constants.Commands.CREATE_ORDER,
                "OFFER_ID": trade.offer_id,
                "ACCOUNT_ID": trade.account_id,
                "RATE": limit_price,
                "TRADE_ID": trade.trade_id,
            }
            if trade.limit_order_id:
                kwargs_dict["ORDER_ID"] = trade.limit_order_id
                kwargs_dict["command"] = fxcorepy.Constants.Commands.EDIT_ORDER
            else:
                kwargs_dict["BUY_SELL"] = OPP_BUY_SELL_MAP.get(trade.buy_sell)
                kwargs_dict["AMOUNT"] = trade.amount

            return kwargs_dict
        else:
            raise ValueError(f"Limit price {limit_price} is not a number")

    def make_order_input_stop_loss(self, trade, stop_price, trail_step=None):
        if self.is_number(stop_price):
            kwargs_dict = {
                "order_type": fxcorepy.Constants.Orders.STOP,
                "command": fxcorepy.Constants.Commands.CREATE_ORDER,
                "OFFER_ID": trade.offer_id,
                "ACCOUNT_ID": trade.account_id,
                "RATE": stop_price,
                "TRADE_ID": trade.trade_id,
            }
            if trade.stop_order_id:
                kwargs_dict["ORDER_ID"] = trade.stop_order_id
                kwargs_dict["command"] = fxcorepy.Constants.Commands.EDIT_ORDER
            else:
                kwargs_dict["BUY_SELL"] = OPP_BUY_SELL_MAP.get(trade.buy_sell)
                kwargs_dict["AMOUNT"] = trade.amount

            if self.is_number(trail_step):
                kwargs_dict["TRAIL_STEP"] = trail_step
            return kwargs_dict
        else:
            raise ValueError(f"Stop price {stop_price} is not a number")

    def make_order_input_close_position(self, trade):
        kwargs_dict = {
            "order_type": fxcorepy.Constants.Orders.TRUE_MARKET_CLOSE,
            "OFFER_ID": trade.offer_id,
            "ACCOUNT_ID": trade.account_id,
            "BUY_SELL": self.opp_buy_sell_map.get(trade.buy_sell),
            "AMOUNT": trade.amount,
            "TRADE_ID": trade.trade_id,
        }
        return kwargs_dict
