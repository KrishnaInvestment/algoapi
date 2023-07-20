from forexconnect import fxcorepy, ForexConnect, Common
from time import sleep

from algoapi.fxconnect.client.fxcmconfig import FXCMClient
from algoapi.fxconnect.trade.position_utils import OrdersMonitor


class DeleteOrder(FXCMClient):
    def __init__(self, fx):
        super().__init__()
        self.fx = fx

    def delete_order(self, order_id):
        orders_table = self.fx.get_table(ForexConnect.ORDERS)
        order = orders_table.get_rows_by_column_value("order_id", order_id)
        if not bool(list(order)):
            raise
        order = list(order)[0]
        request = self.fx.create_request(
            {
                fxcorepy.O2GRequestParamsEnum.COMMAND: fxcorepy.Constants.Commands.DELETE_ORDER,
                fxcorepy.O2GRequestParamsEnum.ACCOUNT_ID: order.account_id,
                fxcorepy.O2GRequestParamsEnum.ORDER_ID: order_id,
            }
        )
        orders_table = self.fx.get_table(ForexConnect.ORDERS)
        orders_monitor = OrdersMonitor()
        orders_listener = Common.subscribe_table_updates(
            orders_table, on_delete_callback=orders_monitor.on_deleted_order
        )
        try:
            self.fx.send_request(request)
        except Exception as e:
            orders_listener.unsubscribe()
            raise e
        sleep(5)
        order_table = self.fx.get_table(ForexConnect.ORDERS).get_rows_by_column_value(
            "order_id", order_id
        )
        if bool(list(order_table)):
            print("The order has been deleted. Order ID: {0:s}".format(order.order_id))
        else:
            print("Timeout on fetching order info")
