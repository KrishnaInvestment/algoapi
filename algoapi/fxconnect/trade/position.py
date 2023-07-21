from forexconnect import fxcorepy, Common, ForexConnect
from time import sleep

from algoapi.fxconnect.client.fxcmconfig import FXCMClient
from algoapi.fxconnect.trade.position_utils import OrdersMonitor, PositionUtils, OPP_BUY_SELL_MAP
from algoapi.fxconnect.utils.custom_exception import TradeNotFound
from algoapi.fxconnect.utils.utils import get_pandas_table


class OpenPosition(FXCMClient):
    def __init__(self, fx):
        super().__init__()
        self.fx = fx

    def at_market_price(self, **kwargs):
        order_input = PositionUtils().make_order_input(self.fx, **kwargs)
        if "RATE" in order_input:
            order_input.pop("RATE")
        order_input["order_type"] = fxcorepy.Constants.Orders.TRUE_MARKET_OPEN

        trade_id = PositionUtils().execute_trade(self.fx, order_input)
        return trade_id

    def at_entry_price(self, **kwargs):
        order_input = PositionUtils().make_order_input(self.fx, **kwargs)
        if "RATE" not in order_input:
            raise ValueError("RATE is not defined in the Order Input")
        else:
            order_input["order_type"] = fxcorepy.Constants.Orders.ENTRY

        trade_id = PositionUtils().execute_trade(self.fx, order_input, wait_for_trades=False)
        return trade_id


class ClosePosition(FXCMClient):
    def __init__(self, fx):
        super().__init__()
        self.fx = fx

    def close_position(self, trade_id):
        trade_table = self.fx.get_table(ForexConnect.TRADES)
        trade = trade_table.get_rows_by_column_value("trade_id", trade_id)
        if not bool(list(trade)):
            raise TradeNotFound(f"No trades with the trade id {trade_id} found")
        trade = list(trade)[0]
        request = self.fx.create_order_request(
            order_type=fxcorepy.Constants.Orders.TRUE_MARKET_CLOSE,
            OFFER_ID=trade.offer_id,
            ACCOUNT_ID=trade.account_id,
            BUY_SELL=OPP_BUY_SELL_MAP.get(trade.buy_sell),
            AMOUNT=trade.amount,
            TRADE_ID=trade.trade_id,
        )
        orders_table = self.fx.get_table(ForexConnect.ORDERS)
        orders_monitor = OrdersMonitor()
        orders_listener = Common.subscribe_table_updates(
            orders_table, on_delete_callback=orders_monitor.on_deleted_order
        )
        try:
            result = self.fx.send_request(request)
            result.order_id
        except Exception as e:
            orders_listener.unsubscribe()
            raise e

        order_table = self.fx.get_table(ForexConnect.TRADES).get_rows_by_column_value(
            "trade_id", trade_id
        )
        count = 0
        while not bool(list(order_table)):
            if count == 2:
                break
            sleep(10)
            order_table = self.fx.get_table(ForexConnect.TRADES).get_rows_by_column_value(
                "trade_id", trade_id
            )
            count += 1
        if bool(list(order_table)):
            print("The trade has been Closed. Trade ID: {0:s}".format(trade_id))
            trade_id = None
        else:
            print("Not able to confirm about trade closure . Verify it manually")
        orders_listener.unsubscribe()
        return trade_id

    def close_all_open_position(self):
        all_trades = get_pandas_table(self.fx, "TRADES")
        if all_trades.empty:
            print("There are no trades")
        else:
            for trade_id in all_trades.trade_id:
                self.close_position(trade_id)


class UpdatePosition(FXCMClient):
    def __init__(self, fx):
        super().__init__()
        self.fx = fx

    def update_limit_price(self, limit_price, trade_id):
        trade_table = self.fx.get_table(ForexConnect.TRADES)
        trade = trade_table.get_rows_by_column_value("trade_id", trade_id)
        if not bool(list(trade)):
            raise TradeNotFound(f"No trades with the trade id {trade_id} found")

        trade = list(trade)[0]
        order_input = PositionUtils().make_order_input_limit(trade, limit_price)
        trade_id = PositionUtils().execute_edit_trade(self.fx, order_input)
        return trade_id

    def update_stop_price(self, stop_price, trade_id, trail_step=None):
        trade_table = self.fx.get_table(ForexConnect.TRADES)
        trade = trade_table.get_rows_by_column_value("trade_id", trade_id)
        if not bool(list(trade)):
            raise TradeNotFound(f"No trades with the trade id {trade_id} found")

        trade = list(trade)[0]
        order_input = PositionUtils().make_order_input_stop_loss(trade, stop_price, trail_step)
        trade_id = PositionUtils().execute_edit_trade(self.fx, order_input)
        return trade_id
