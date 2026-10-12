"""Copy NSE mainboard daily prices out of the bhavcopy-pipeline warehouse.

    python snapshot_prices.py ../bhavcopy-pipeline/warehouse.duckdb

Writes data/prices.parquet so this repo runs without the pipeline. Series EQ
and BE are both kept: NSE moves a stock to BE (trade-for-trade) around some
corporate actions, and dropping BE would cut those stocks' history in half.
On NSE a symbol trades in one of the two on any day, so (symbol, trade_date)
is unique. Prices are cast to DOUBLE so division never returns a DECIMAL.
"""
import sys
from pathlib import Path

import duckdb

OUT = Path(__file__).resolve().parent / "data" / "prices.parquet"


def main() -> None:
    con = duckdb.connect(sys.argv[1], read_only=True)
    con.execute(f"""
        copy (
            select
                symbol, series, isin, trade_date,
                cast(open_price  as double) as open,
                cast(high_price  as double) as high,
                cast(low_price   as double) as low,
                cast(close_price as double) as close,
                volume
            from fct_daily_prices
            where exchange = 'NSE' and series in ('EQ', 'BE')
            order by symbol, trade_date
        ) to '{OUT.as_posix()}' (format parquet, compression zstd)
    """)
    n, days = duckdb.sql(
        f"select count(*), count(distinct trade_date) from '{OUT.as_posix()}'").fetchone()
    print(f"{n} rows over {days} trading days -> {OUT}")


if __name__ == "__main__":
    main()
