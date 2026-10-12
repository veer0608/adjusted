import pytest

from conftest import columns, rows


def test_columns(con):
    assert columns(con, "adjusted_prices") == ["symbol", "trade_date", "close", "adj_factor", "adj_close"]


def test_every_price_row_kept(con):
    assert rows(con, "select count(*) from adjusted_prices") == rows(con, "select count(*) from prices")


def test_no_null_factor(con):
    assert rows(con, "select count(*) from adjusted_prices where adj_factor is null") == [(0,)]


def test_untouched_stock_is_unchanged(con):
    # ABB had a dividend, not a split. Dividends are not adjusted here.
    assert rows(con, """
        select count(*) from adjusted_prices
        where symbol = 'ABB' and (adj_factor <> 1 or adj_close <> close)""") == [(0,)]


def adj(con, symbol, day):
    (factor, close), = rows(con, f"""
        select adj_factor, adj_close from adjusted_prices
        where symbol = '{symbol}' and trade_date = '{day}'""")
    return factor, close


@pytest.mark.parametrize("symbol,day,factor,close", [
    ("GOODLUCK", "2026-08-20", 3.0, 479.80),    # day before Bonus 2:1
    ("GOODLUCK", "2026-08-21", 1.0, 490.90),    # ex-date itself is already in new shares
    ("TDPOWERSYS", "2026-08-21", 2.0, 767.40),  # before the split, across the ISIN change
    ("MOLDTECH", "2026-10-01", 2.0, 102.39),    # ex-date 2026-10-09 is after the data ends
])
def test_adjusted(con, symbol, day, factor, close):
    got_factor, got_close = adj(con, symbol, day)
    assert got_factor == pytest.approx(factor)
    assert got_close == pytest.approx(close)


def test_split_cliff_is_gone(con):
    before, after = (adj(con, "TDPOWERSYS", d)[1] for d in ("2026-08-21", "2026-08-24"))
    assert abs(after / before - 1) < 0.05
