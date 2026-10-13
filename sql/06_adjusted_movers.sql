-- Exercise 6: rank each day's movers on adjusted prices.
-- Practises: RANK vs DENSE_RANK, and window functions over a view built from
-- another window function.
--
-- Source: adjusted_prices (your exercise 5)
--
-- adj_pct_move = the day's move computed from adj_close (the same way as
--                exercise 3 but on adj_close), rounded to 2 decimals.
-- Within each trade_date, rank by adj_pct_move, biggest gain first:
--   rnk        = RANK()
--   dense_rnk  = DENSE_RANK()
-- Rounding to 2 decimals makes ties common (many stocks stop at the same
-- price band), which is what makes the two rankings differ.
--
-- Output columns, in this order: trade_date, symbol, adj_pct_move, rnk, dense_rnk
-- Rows: every symbol-day that has an adj_pct_move (leave out the NULL ones).
--
-- When it passes, run: python db.py 6
-- and find a day where rnk jumps (1, 1, 3). Write one line at the bottom
-- explaining why dense_rnk on that day says 2 instead.
--
-- Test: pytest tests/test_ex6.py
--
-- Written by Claude at Veer's request, with comments.

select
    trade_date,
    symbol,
    adj_pct_move,
    -- Both rank within one day (PARTITION BY trade_date), biggest gain first
    -- (ORDER BY ... DESC). They differ only when there are ties:
    --   moves  20.00, 20.00, 20.00, 20.00, 19.99
    --   RANK        1,     1,     1,     1,     5   skips: 4 stocks are ahead
    --   DENSE_RANK  1,     1,     1,     1,     2   no gaps: 1 value is ahead
    --   ROW_NUMBER  1,     2,     3,     4,     5   ignores ties, picks an order
    -- "Top 3 gainers" with RANK can return 4 rows; with DENSE_RANK it can
    -- return many more. Say which one you mean in an interview.
    rank()       over (partition by trade_date order by adj_pct_move desc) as rnk,
    dense_rank() over (partition by trade_date order by adj_pct_move desc) as dense_rnk
from (
    -- Same LAG as query 3, but on adj_close, so split and bonus days
    -- become ordinary days. Rounded to 2 decimals, which is what makes ties
    -- common: many small stocks stop at the same +20% price band.
    select
        trade_date,
        symbol,
        round((adj_close / lag(adj_close) over (partition by symbol order by trade_date) - 1) * 100, 2)
            as adj_pct_move
    from adjusted_prices
)
-- A window function cannot sit in WHERE (WHERE runs before windows are
-- computed), which is another reason for the subquery. Out here the LAG is
-- already done, so each symbol's first day, with no move, can be dropped.
where adj_pct_move is not null

