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

```python
from algoapi.fxconnect import FXCMClient

# Login to the API
fx = FXCMClient(USER_ID = 'YOUR_ID',
                USER_PASSWORD = 'YOUR_PASSWORD', 
                URL = 'http://www.fxcorporate.com/Hosts.jsp',
                CONNECTION = 'Demo').login()

[You can check the meaning of the input mention above](https://fxcodebase.com/bin/forexconnect/1.6.0/python/forexconnect.ForexConnect.ForexConnect.login.html)

#You can add all the parameters of login mentioned above as per the requirements

#to avoid entering the information each time maintain .env with variables
USER_ID = 'YOUR_ID'
USER_PASSWORD = 'YOUR_PASSWORD'
URL = 'http://www.fxcorporate.com/Hosts.jsp'
CONNECTION = 'Real'

```
# Executing a trade
```python
from algoapi.fxconnect.trade import OpenPosition
#You can place two types of order here at market price and at entry price

#Trading at entry price
op = OpenPosition(fx)
order_id = op.at_entry_price(INSTRUMENT="EUR/USD",
                                    TRANSACTION_TYPE='B',
                                    LOTS=1,
                                    RATE = rate,
                                    RATE_STOP= 40,
                                    TRAIL_STEP = 30,
                                    RATE_LIMIT = 30
                                    )
#At entry price the rate must be added and stop/target are based on the pip value
#Instrument, TRANSACTION_TYPE, LOTS, RATE are required variable for executing entry trade
#However other variable are optional
# The entry price returns the order_id


#Trading at market price
trade_id, order_id = op.at_market_price(INSTRUMENT="EUR/USD",
                                    TRANSACTION_TYPE='B',
                                    LOTS=1
                                    )
# You can add stop loss , limit , trail_step as per the requirement 
# 
```

## Contributing

Pull requests are welcome. For major changes, please open an issue first
to discuss what you would like to change.


## License

[MIT](https://choosealicense.com/licenses/mit/)