-- Exercise 2: which symbols paid more than one dividend in the window?
-- Practises: WHERE vs HAVING. One filter here acts on rows, the other on
-- groups. Decide which is which before you write the query.
--
-- Source table: corporate_actions
--
-- Count the dividend actions (kind = 'dividend') per symbol.
-- Keep only symbols with 2 or more.
--
-- Output columns, in this order: symbol, n_dividends
--
-- Trap to check after it passes: drop the kind filter and run it again
-- (python db.py 2). The count of symbols goes up. Write one line at the
-- bottom of this file saying which rows got counted that should not have.
--
-- Test: pytest tests/test_ex2.py
--
-- Written by Claude at Veer's request, with comments as a second worked example.

select
    symbol,
    -- count(*) counts the rows in each group. Without GROUP BY it would
    -- count the whole table and return one row.
    count(*) as n_dividends

from corporate_actions

-- Order of work: FROM, then WHERE, then GROUP BY, then HAVING, then SELECT.
-- WHERE judges single rows, before any grouping. "Is this row a dividend?"
-- is a question about one row, so it belongs here.
where kind = 'dividend'

-- One group per stock. Every column in SELECT must either be in this list
-- or be inside an aggregate like count(*).
group by symbol

-- HAVING judges whole groups, after counting. "Did this stock have 2+?"
-- needs the count, which does not exist yet when WHERE runs. That is why
-- count(*) >= 2 cannot go in WHERE: DuckDB rejects it.
having count(*) >= 2

-- The trap: drop the WHERE line and the count includes splits, bonuses,
-- rights and so on. A stock with one dividend and one split would count 2
-- and slip in. That is the 52 the test warns about, instead of 35.

