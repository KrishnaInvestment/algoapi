
from forexconnect import ForexConnect
import pandas as pd

def get_pandas_table(fx, table_type):
    table_manager = fx.table_manager
    table_type = f"ForexConnect.{table_type}"
    o2gtable = table_manager.get_table(eval(table_type))
    table_rows = []
    for row in o2gtable:
        table_rows += [list(row)]
    
    columns = [column.id for column in o2gtable.columns]

    df = pd.DataFrame(data = table_rows, columns=columns)
    return df