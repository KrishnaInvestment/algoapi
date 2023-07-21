# AlgoAPi

ALgoAPI is a Python library for dealing with executing trading using FXCM ForexConnect API.

## Installation

```Clone
git clone https://github.com/KrishnaInvestment/algoapi.git
cd algoapi
pip3 install . 
```
Alternatively you can install the package using PIP
```
pip install algoapi

```

## Usage

# Login
```python
from algoapi.fxconnect import FXCMClient

# Login to the API
fx = FXCMClient(
    USER_ID="YOUR_ID",
    USER_PASSWORD="YOUR_PASSWORD",
    URL="http://www.fxcorporate.com/Hosts.jsp",
    CONNECTION="Demo",
).login()

#You can add all the parameters of login in the link below as per the requirements

#to avoid entering the information each time maintain .env with variables
USER_ID = 'YOUR_ID'
USER_PASSWORD = 'YOUR_PASSWORD'
URL = 'http://www.fxcorporate.com/Hosts.jsp'
CONNECTION = 'Real'

```

[You can check other inputs for login](https://fxcodebase.com/bin/forexconnect/1.6.0/python/forexconnect.ForexConnect.ForexConnect.login.html)

# Executing a trade
```python
from algoapi.fxconnect.trade import OpenPosition
#You can place two types of order here at market price and at entry price

#Trading at entry price
op = OpenPosition(fx)
order_id = op.at_entry_price(
    INSTRUMENT="EUR/USD",
    TRANSACTION_TYPE="B",
    LOTS=1,
    RATE=rate,
    RATE_STOP=40,
    TRAIL_STEP_STOP=30,
    RATE_LIMIT=30,
)
#At entry price the rate must be added and stop/target are based on the pip value
#Instrument, TRANSACTION_TYPE, LOTS, RATE are required variable for executing entry trade
#However other variable are optional
# The entry price returns the order_id


#Trading at market price
trade_id, order_id = op.at_market_price(
    INSTRUMENT="EUR/USD", TRANSACTION_TYPE="B", LOTS=1
)

# You can add stop loss , limit , trail_step_stop as per the requirement
```
# Closing a Trade
```python
from algoapi.fxconnect.trade import ClosePosition
cp = ClosePosition(fx)
#Closing a position with the trade id
cp.close_position(trade_id)

#Close all Open position
cp.close_all_open_position()

```

# Updating a Trade
```python
from algoapi.fxconnect.trade import UpdatePosition
up = ClosePosition(fx)
#Update Limit price
up.update_limit_price(limit_price, trade_id)
#Limit price should be the actual price 
up.update_limit_price(1.11875,'75134317')
#Note all the ID's (trade_id, order_id are in string format)

#Update Stop price
up.update_stop_price(stop_price, trade_id, trail_step)
#Stop price should be the actual price
up.update_stop_price(1.11575,'75134317', trail_step)

#Trail step moves the stop limit as the price fluctuates in our desire direction

```
# Deleting an Order
```python
from algoapi.fxconnect.trade import DeleteOrder
do = DeleteOrder(fx)
#Closing a position with the trade id
do.delete_order(order_id)

```

# Fetching Trade and Order Information
```python
from algoapi.fxconnect.utils import get_pandas_table
df = get_pandas_table(fx, table_type)
#Table types like TRADES, OFFERS, ORDERS, CLOSED_POSITION, ACCOUNTS etc
#It will list all the information of that particular table
df_orders = get_pandas_table(fx, 'TRADES')

#You can  filter the tables based on the column value
df_filter_column = get_pandas_table(fx, table_type, key='Columns_name', value='column_value')
df_order_id_filter = get_pandas_table(fx, 'ORDERS', key='order_id', value='75134317')

#To get the latest price of the instrument
from forexconnect import Common
offer = Common.get_offer(fx, "EUR/USD")
# depending on the long and short position you can get the 
ask = offer.ask
bid = offer.bid

```



## Contributing

Pull requests are welcome. For major changes, please open an issue first
to discuss what you would like to change.


## License

[MIT](https://choosealicense.com/licenses/mit/)