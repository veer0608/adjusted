"""Checks the adjustment against the market itself, on every action at once.

On an ex-date the exchange quotes in new shares from the first trade, so the
day's OPEN should sit near the ADJUSTED previous close. A wrong factor shows up
as a big opening gap. Raw gaps on these days run from -24% to -90%.
"""
from conftest import rows

GAPS = """
    with prev as (
        select symbol, trade_date,
               lag(adj_close) over w as adj_prev,
               lag(close)     over w as raw_prev
        from adjusted_prices
        window w as (partition by symbol order by trade_date)
    )
    select f.symbol,
           p.open / pv.adj_prev - 1 as adj_gap,
           p.open / pv.raw_prev - 1 as raw_gap
    from action_factors f
    join prices p on p.symbol = f.symbol and p.trade_date = f.ex_date
    join prev pv  on pv.symbol = f.symbol and pv.trade_date = f.ex_date
"""


def test_every_action_in_range_is_checked(con):
    # 27 actions, 4 of them after the price data ends on 2026-10-01.
    assert len(rows(con, GAPS)) == 23


def test_open_is_near_adjusted_previous_close(con):
    # Widest real gap is NARMADA, +10.5%: a volatile opening, not a bad factor.
    bad = [(s, round(g * 100, 2)) for s, g, _ in rows(con, GAPS) if abs(g) >= 0.15]
    assert bad == []


def test_adjusting_always_shrinks_the_gap(con):
    worse = [s for s, adj, raw in rows(con, GAPS) if abs(adj) >= abs(raw)]
    assert worse == []
