-- Exercise 5: rewrite history in today's shares.
-- Practises: joining on an inequality, aggregating a product, and NULL from an
-- aggregate over zero rows.
--
-- Sources: prices, action_factors (your exercise 1)
--
-- GOODLUCK closed at 1439.40 on 2026-08-20. On 2026-08-21 (Bonus 2:1, factor 3)
-- every share became 3 shares. In today's shares, that 1439.40 was worth
-- 1439.40 / 3 = 479.80. That is the adjusted close.
--
-- For each price row:
--   adj_factor = product of the factors of every action for that symbol with
--                ex_date AFTER this trade_date. A row with no later action
--                has adj_factor 1, never NULL.
--   adj_close  = close / adj_factor
--
-- SQL has no PRODUCT() aggregate. Think about what log turns a product into.
--
-- Output columns, in this order: symbol, trade_date, close, adj_factor, adj_close
-- Rows: every row of prices.
--
-- Test: pytest tests/test_ex5.py
--
-- Written by Claude at Veer's request, with comments.

select
    p.symbol,
    p.trade_date,
    p.close,
    -- SQL has SUM but no PRODUCT. Logs turn one into the other:
    --   ln(a * b) = ln(a) + ln(b), so a * b = exp(ln(a) + ln(b)).
    -- So exp(sum(ln(factor))) multiplies every matched factor together.
    -- Safe here because every factor is positive; ln(0) or ln(-1) would fail.
    --
    -- A price row with no later action matches nothing, so the LEFT JOIN
    -- gives it one row with f.factor NULL. SUM over only NULLs is NULL, not
    -- 0, and exp(NULL) is NULL. COALESCE(x, 1) swaps that NULL for 1, which
    -- means "no adjustment".
    coalesce(exp(sum(ln(f.factor))), 1) as adj_factor,
    p.close / coalesce(exp(sum(ln(f.factor))), 1) as adj_close
from prices p

-- LEFT JOIN so every price row survives, matched or not (same idea as query 4).
left join action_factors f
    on  f.symbol = p.symbol
    -- An inequality join: every action AFTER this day applies to this day.
    -- GOODLUCK on 2026-08-20 matches its 2026-08-21 bonus, so 1439.40 / 3.
    -- Strictly greater, not >=: on the ex-date itself the price is already
    -- quoted in new shares, so 490.90 on 2026-08-21 stays 490.90.
    and f.ex_date > p.trade_date

-- One price row can match several actions (a split and a later bonus), so
-- collapse back to one row per price row. Every non-aggregated column in
-- SELECT has to be listed here.
group by p.symbol, p.trade_date, p.close

