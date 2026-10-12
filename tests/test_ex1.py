import pytest

from conftest import columns, rows


def test_columns(con):
    assert columns(con, "action_factors") == ["symbol", "ex_date", "kind", "factor"]


def test_only_splits_and_bonuses(con):
    kinds = {k for (k,) in rows(con, "select distinct kind from action_factors")}
    assert kinds == {"split", "bonus"}
    assert rows(con, "select count(*) from action_factors") == [(21,)]


def test_no_null_factors(con):
    assert rows(con, "select count(*) from action_factors where factor is null") == [(0,)]


@pytest.mark.parametrize("symbol,factor", [
    ("TDPOWERSYS", 2.0),   # split Rs 2 -> Re 1
    ("MWL", 10.0),         # split Rs 10 -> Re 1
    ("POCL", 2.5),         # split Rs 5 -> Rs 2
    ("GOODLUCK", 3.0),     # Bonus 2:1
    ("PGIL", 2.0),         # Bonus 1:1
    ("HARDWYN", 1.4),      # Bonus 2:5
    ("GOLDIAM", 4 / 3),    # Bonus 1:3
])
def test_factor(con, symbol, factor):
    (got,), = rows(con, f"select factor from action_factors where symbol = '{symbol}'")
    assert got == pytest.approx(factor)
