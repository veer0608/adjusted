import pytest

from conftest import columns, rows


def test_columns(con):
    assert columns(con, "adjusted_movers") == ["trade_date", "symbol", "adj_pct_move", "rnk", "dense_rnk"]


def test_row_count(con):
    # 183,960 price rows minus one first day per symbol.
    assert rows(con, "select count(*) from adjusted_movers") == [(181007,)]
    assert rows(con, "select count(*) from adjusted_movers where adj_pct_move is null") == [(0,)]


def test_bonus_day_is_a_normal_day(con):
    (pct,), = rows(con, """
        select adj_pct_move from adjusted_movers
        where symbol = 'GOODLUCK' and trade_date = '2026-08-21'""")
    assert pct == pytest.approx(2.31)


def test_ranked_within_each_day(con):
    assert rows(con, "select count(distinct trade_date) from adjusted_movers") == [(65,)]
    assert rows(con, """
        select count(*) from (
            select trade_date from adjusted_movers group by trade_date
            having min(rnk) <> 1 or min(dense_rnk) <> 1)""") == [(0,)]


def test_rank_semantics_on_a_tied_day(con):
    # 2026-08-21: four stocks tied at +20.00, then three at +19.99.
    day = rows(con, """
        select adj_pct_move, rnk, dense_rnk from adjusted_movers
        where trade_date = '2026-08-21'""")
    moves = [m for m, _, _ in day]
    distinct = sorted(set(moves), reverse=True)
    for m, rnk, dense in day:
        assert rnk == 1 + sum(x > m for x in moves), f"RANK wrong at {m}"
        assert dense == 1 + distinct.index(m), f"DENSE_RANK wrong at {m}"
