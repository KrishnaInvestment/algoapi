
from forexconnect import fxcorepy, Common, ForexConnect
from algoapi.fxconnect.client.fxcmconfig import FXCMClient
import threading

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
            order_row = self.__added_orders[order_id]

        # looking for an changed order
        if order_id not in self.__changed_orders:
            is_order_changed = self.__changed_orders_event.wait(time)

        if is_order_changed:
            order_row = self.__changed_orders[order_id]

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
        
    def get_lots(self,lots):
        if self.is_number(lots):
            return lots
        else:
            return 1
    
    @staticmethod
    def calculate_stop_loss(pip_size, price, transaction_type):
        if transaction_type=='S':
            stop_loss =  price + pip_size
        else:
            stop_loss =  price - pip_size
        return stop_loss
    
    @staticmethod
    def calculate_limit(pip_size, price, transaction_type):
        if transaction_type=='S':
            stop_loss =  price - pip_size
        else:
            stop_loss =  price + pip_size
        return stop_loss
        
    def make_order_input(self,fx,**kwargs):
        
        instrument = kwargs.get('INSTRUMENT')
        lots = self.get_lots(kwargs.get('LOTS'))
        transaction_type = kwargs.get('TRANSACTION_TYPE')
        account = Common.get_account(fx, None)
        amount = self.get_trading_amount(fx, instrument, account, lots)

        kwargs_dict = {
            "ACCOUNT_ID":account.account_id,
            "SYMBOL": instrument,
            "AMOUNT":amount,
            "BUY_SELL":transaction_type,
            }
        
        offer = Common.get_offer(fx, instrument)
        if self.is_number(kwargs.get('RATE')):
            kwargs_dict.update({"RATE":kwargs.get('RATE')})
            price = kwargs.get('RATE')
        else:
            if transaction_type=='B':
                price = offer.ask
            else:
                price = offer.bid

        if self.is_number(kwargs.get('RATE_STOP')):
            stop_loss = self.calculate_stop_loss(kwargs.get('RATE_STOP')*offer.PointSize, price, transaction_type)
            kwargs_dict.update({"RATE_STOP":stop_loss})

        if self.is_number(kwargs.get('RATE_LIMIT')):
            limit = self.calculate_limit(kwargs.get('RATE_LIMIT')*offer.PointSize, price, transaction_type)
            kwargs_dict.update({"RATE_LIMIT":limit})
        
        if self.is_number(kwargs.get('TRAIL_STEP_STOP')):
            kwargs_dict.update({"TRAIL_STEP_STOP":kwargs.get('TRAIL_STEP_STOP')})

        return kwargs_dict


class OpenPosition(FXCMClient):
    def __init__(self,fx):
        super().__init__()
        self.fx = fx
    

    def execute_trade(self, order_input, wait_for_trades=True):

        request = self.fx.create_order_request(
            **order_input
        )
        orders_monitor = OrdersMonitor()
        trades_monitor = TradesMonitor()
        orders_table = self.fx.get_table(ForexConnect.ORDERS)
        trades_table = self.fx.get_table(ForexConnect.TRADES)
        trades_listener = Common.subscribe_table_updates(trades_table, on_add_callback=trades_monitor.on_added_trade)
        orders_listener = Common.subscribe_table_updates(orders_table, on_add_callback=orders_monitor.on_added_order,
                                                         on_delete_callback=orders_monitor.on_deleted_order,
                                                         on_change_callback=orders_monitor.on_changed_order)
        
        try:
            result = self.fx.send_request(request)
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
                print('Response waiting timeout expired')
                None, order_id

            if trade_row is None:
                print("Response waiting timeout expired.\n")
                None, order_id
            else:
                return trade_row.trade_id , order_id
            
            trades_listener.unsubscribe()
            orders_listener.unsubscribe()
       
    def at_market_price(self, **kwargs):
        order_input = PositionUtils().make_order_input(self.fx,**kwargs)
        if 'RATE' in order_input:
            order_input.pop('RATE')
        order_input['order_type'] = fxcorepy.Constants.Orders.TRUE_MARKET_OPEN


        trade_id = self.execute_trade(order_input)
        return trade_id

    def at_entry_price(self, **kwargs):
        order_input = PositionUtils().make_order_input(self.fx,**kwargs)
        if 'RATE' not in order_input:
            raise ValueError("RATE is not defined in the Order Input")
        else:
            order_input['order_type'] = fxcorepy.Constants.Orders.ENTRY

        trade_id = self.execute_trade(order_input, wait_for_trades=False)
        return trade_id


class ClosePosition(FXCMClient):

    def at_market_price(self, instrument, **kwargs):
        pass

    def at_limit_rate(self,instrument, **kwargs):
        pass