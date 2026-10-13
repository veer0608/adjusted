from conftest import columns, rows


def test_columns(con):
    assert columns(con, "big_drops") == ["symbol", "trade_date", "pct_move", "kind"]


def test_every_big_drop_kept(con):
    assert rows(con, "select count(*) from big_drops") == [(30,)]
    assert rows(con, "select count(*) from big_drops where pct_move > -30") == [(0,)]


def test_unexplained_drops_survive(con):
    # If this is 0, the kind filter is in the wrong place.
    assert rows(con, "select count(*) from big_drops where kind is null") == [(7,)]


def test_one_row_per_drop(con):
    assert rows(con, """
        select count(*) - count(distinct (symbol, trade_date)) from big_drops""") == [(0,)]


def test_no_dividends_attached(con):
    assert rows(con, "select count(*) from big_drops where kind = 'dividend'") == [(0,)]


def test_known_causes(con):
    got = dict(rows(con, """
        select symbol, kind from big_drops
        where symbol in ('GOODLUCK', 'TDPOWERSYS', 'INDIAGLYCO', 'HEG')"""))
    assert got == {"GOODLUCK": "bonus", "TDPOWERSYS": "split",
                   "INDIAGLYCO": "demerger", "HEG": None}
