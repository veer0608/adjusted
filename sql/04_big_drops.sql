-- Exercise 4: every drop of 30% or more, and the corporate action behind it.
-- Practises: LEFT JOIN, and where a filter on the right-hand table belongs.
--
-- Sources: daily_moves (your exercise 3), corporate_actions
--
-- Start from every row of daily_moves with pct_move <= -30.
-- Attach the corporate action for that symbol whose ex_date is that
-- trade_date, but only actions of kind split, bonus or demerger. A dividend
-- does not explain a 30% drop.
-- A drop with no such action must still appear, with kind NULL. Those are
-- the real crashes, and they are the interesting rows.
--
-- Output columns, in this order: symbol, trade_date, pct_move, kind
-- Rows: one per big drop.
--
-- The trap: there is one place to put the kind filter that silently deletes
-- every unexplained drop. The tests will catch it. Once it passes, write a
-- comment at the bottom saying why the other place breaks it.
--
-- Test: pytest tests/test_ex4.py
--
-- Written by Claude at Veer's request, with comments.

select
    m.symbol,
    m.trade_date,
    m.pct_move,
    -- From the right-hand table. NULL when no action matched: a real crash.
    a.kind
from daily_moves m

-- LEFT JOIN keeps every row of the left table (the drops), matched or not.
-- An INNER JOIN would keep only drops that have an action, and the 13 real
-- crashes would vanish.
left join corporate_actions a
    on  a.symbol  = m.symbol
    and a.ex_date = m.trade_date
    -- The kind filter goes in ON, not WHERE. In ON it only decides which
    -- actions are allowed to match; a drop with no allowed action still
    -- survives, with kind NULL.
    -- It also stops a dividend paid the same day from matching too, which
    -- would give one drop two rows.
    and a.kind in ('split', 'bonus', 'demerger')

-- WHERE runs after the join, on the joined rows. Filtering the LEFT table
-- here is safe: it only removes small moves.
where m.pct_move <= -30

-- Why the kind filter breaks in WHERE: after a LEFT JOIN, an unmatched drop
-- has kind NULL. "NULL in ('split', 'bonus', 'demerger')" is not true, so
-- WHERE throws the row away. That turns the LEFT JOIN back into an INNER
-- JOIN without any error: 30 rows become 17, and every real crash is gone.

