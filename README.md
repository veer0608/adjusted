# adjusted

Split- and bonus-adjusted daily prices for NSE stocks, written in plain SQL on DuckDB.

## The problem

Exchange price files record what a share traded at that day. When a company splits its
shares or issues a bonus, the price per share falls overnight even though nobody lost any
money. Raw files report that as a crash.

From NSE's own bhavcopy, July to October 2026:

| Stock | Ex-date | Action | Raw move that day |
|---|---|---|---|
| GOODLUCK | 2026-08-21 | Bonus 2:1 | -65.90% |
| TDPOWERSYS | 2026-08-24 | Split Rs 2 to Re 1 | -49.17% |
| MWL | 2026-07-10 | Split Rs 10 to Re 1 | -90.10% |

NSE's `PrvsClsgPric` column is not adjusted on these days either, so any "top losers" list
built straight from the file, including the one in
[bhavcopy-pipeline](https://github.com/veer0608/bhavcopy-pipeline), shows these stocks as
the day's biggest fallers.

This repo joins the prices to NSE's corporate actions feed and rewrites history in today's
share count, so a chart of GOODLUCK has no cliff on 21 August.

## Things the data taught

- **A split changes the ISIN.** TDPOWERSYS trades under a new ISIN from its split day.
  Joining price history on ISIN cuts the stock in two. Join on symbol.
- **A stock can change series.** NSE moved INDIAGLYCO from EQ to BE around its demerger.
  Partitioning by series cuts its history at exactly the day that matters.
- **Demergers cannot be adjusted with a ratio.** NSE lists them with no ratio, and the price
  drop depends on what the spun-off company is worth. They are flagged, not adjusted.
- **13 of the 30 drops of 30% or more have no corporate action in the feed.** Most are ETFs
  (GOLDADD, PSUBANK, about -90%), which look like unit splits that NSE's equities feed does
  not list. The cause is not confirmed yet.

## Layout

```
data/prices.parquet           NSE EQ+BE daily prices, 2026-07-01 to 2026-10-01 (183,960 rows)
data/corporate_actions.csv    NSE corporate actions, 2026-07-01 to 2026-10-09 (1,231 rows)
sql/01..06_*.sql              the work: one SELECT per file, each becomes a view
tests/test_ex1..6.py          checks for each query
db.py                         builds the database from data/ and sql/
fetch_actions.py              refreshes corporate_actions.csv from NSE
snapshot_prices.py            refreshes prices.parquet from the bhavcopy-pipeline warehouse
```

| # | Query | SQL it exercises |
|---|---|---|
| 1 | `action_factors` | CASE, NULL from an unmatched CASE |
| 2 | `busy_symbols` | WHERE vs HAVING |
| 3 | `daily_moves` | LAG, PARTITION BY |
| 4 | `big_drops` | LEFT JOIN, where a right-table filter belongs |
| 5 | `adjusted_prices` | inequality join, product via EXP(SUM(LN())), NULL from an empty aggregate |
| 6 | `adjusted_movers` | RANK vs DENSE_RANK |

## Running it

PowerShell, from this folder:

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m pytest tests/test_ex1.py
.venv\Scripts\python db.py 1
```

`db.py N` builds everything up to query N and prints its first rows.

## Status

Data and tests are in place. Queries 1 to 4 are worked examples, written by Claude with a comment
on every line. Queries 5 and 6 are not written yet.
