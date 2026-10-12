import pytest

from conftest import columns, rows


def test_columns(con):
    assert columns(con, "daily_moves") == ["symbol", "trade_date", "close", "prev_close", "pct_move"]


def test_every_price_row_kept(con):
    assert rows(con, "select count(*) from daily_moves") == rows(con, "select count(*) from prices")


def test_first_day_is_null(con):
    (n_symbols,), = rows(con, "select count(distinct symbol) from prices")
    (n_null,), = rows(con, "select count(*) from daily_moves where prev_close is null")
    assert n_null == n_symbols, "exactly one NULL prev_close per symbol: its first day"


def move(con, symbol, day):
    (prev, pct), = rows(con, f"""
        select prev_close, pct_move from daily_moves
        where symbol = '{symbol}' and trade_date = '{day}'""")
    return prev, pct


def test_bonus_day_looks_like_a_crash(con):
    prev, pct = move(con, "GOODLUCK", "2026-08-21")
    assert prev == pytest.approx(1439.4)
    assert pct == pytest.approx(-65.8955, abs=1e-3)


def test_isin_change_is_same_stock(con):
    # TDPOWERSYS got a new ISIN on its split day.
    prev, pct = move(con, "TDPOWERSYS", "2026-08-24")
    assert prev == pytest.approx(1534.8)
    assert pct == pytest.approx(-49.1725, abs=1e-3)


def test_series_change_is_same_stock(con):
    # INDIAGLYCO moved from EQ to BE on 2026-09-02.
    prev, _ = move(con, "INDIAGLYCO", "2026-09-02")
    assert prev == pytest.approx(1111.7)
