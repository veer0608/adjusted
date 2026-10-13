-- Exercise 3: each day's move against the stock's previous trading day.
-- Practises: LAG, PARTITION BY, and the NULL that LAG returns on a first row.
--
-- Source table: prices (NSE, one row per symbol per trading day)
--   symbol, series, isin, trade_date, open, high, low, close, volume
--
-- For every row, find the close of the same symbol's previous row by date.
-- pct_move = (close - prev_close) / prev_close * 100, not rounded.
--
-- Output columns, in this order: symbol, trade_date, close, prev_close, pct_move
-- Rows: every row of prices, including each symbol's first day (where
-- prev_close and pct_move are NULL).
--
-- Two traps the tests check:
--   - A stock can move between series EQ and BE. That is still the same stock.
--   - A split changes the ISIN (TDPOWERSYS does on 2026-08-24). Also the same stock.
--
-- Test: pytest tests/test_ex3.py
--
-- Written by Claude at Veer's request, with comments.

-- Two steps. The inner query finds prev_close; the outer one does the
-- arithmetic. A window function's result cannot be reused by name in the
-- same SELECT, so splitting it saves writing LAG(...) out twice.
select
    symbol,
    trade_date,
    close,
    prev_close,
    -- On a symbol's first day prev_close is NULL, and any arithmetic with
    -- NULL gives NULL. That is exactly what the brief wants, so no special
    -- case is needed.
    (close - prev_close) / prev_close * 100 as pct_move
from (
    select
        symbol,
        trade_date,
        close,
        -- LAG(close) = "close from the row before this one".
        -- OVER (...) defines what "before" means:
        --   PARTITION BY symbol: restart for every stock, so GOODLUCK's first
        --     day never reads the last close of the stock above it.
        --   ORDER BY trade_date: "before" means the previous trading day.
        -- Unlike GROUP BY, a window keeps every row. 183,960 in, 183,960 out.
        --
        -- Why symbol and not isin or series: TDPOWERSYS got a new ISIN on its
        -- split day, and INDIAGLYCO moved from EQ to BE. Partitioning on
        -- either would start a "new stock" on exactly the day that matters
        -- and give it a NULL prev_close.
        lag(close) over (partition by symbol order by trade_date) as prev_close
    from prices
)

