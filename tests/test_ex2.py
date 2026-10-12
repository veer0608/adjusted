from conftest import columns, rows


def test_columns(con):
    assert columns(con, "busy_symbols") == ["symbol", "n_dividends"]


def test_count(con):
    # 52 here means non-dividend actions are being counted too.
    assert rows(con, "select count(*) from busy_symbols") == [(35,)]


def test_every_row_qualifies(con):
    assert rows(con, "select count(*) from busy_symbols where n_dividends < 2") == [(0,)]


def test_one_symbol_per_row(con):
    assert rows(con, "select count(*) - count(distinct symbol) from busy_symbols") == [(0,)]
