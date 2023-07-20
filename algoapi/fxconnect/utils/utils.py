from forexconnect import ForexConnect
import pandas as pd


def get_pandas_table(fx, table_type, key=None, value=None):
    table_manager = fx.table_manager
    table_type = getattr(ForexConnect, table_type)
    o2gtable = table_manager.get_table(table_type)
    if key and value:
        o2gtable = o2gtable.get_rows_by_column_value(key, value)
    table_rows = []
    columns = []
    for row in o2gtable:
        table_rows += [list(row)]
        if not bool(columns):
            columns = [column.id for column in row.columns]

    df = pd.DataFrame(data=table_rows, columns=columns)
    return df
