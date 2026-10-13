"""Build an in-memory DuckDB from data/ and the queries in sql/.

Each sql/NN_name.sql holds one SELECT. It becomes a view called `name`, so a
later query can select from an earlier one. A file with nothing but comments
is treated as not written yet.

    python db.py 3        # build up to exercise 3 and print its first rows
"""
import re
import sys
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parent
SQL_DIR = ROOT / "sql"
DATA = ROOT / "data"


class NotWritten(Exception):
    pass


def exercises() -> list[tuple[int, str, Path]]:
    out = []
    for p in sorted(SQL_DIR.glob("[0-9][0-9]_*.sql")):
        num, name = p.stem.split("_", 1)
        out.append((int(num), name, p))
    return out


def query_text(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    body = re.sub(r"--[^\n]*", "", text).strip().rstrip(";").strip()
    return body


def build(upto: int) -> duckdb.DuckDBPyConnection:
    con = duckdb.connect()
    con.execute(f"create table prices as select * from '{(DATA / 'prices.parquet').as_posix()}'")
    con.execute(f"""
        create table corporate_actions as
        select * from read_csv('{(DATA / 'corporate_actions.csv').as_posix()}', header = true,
            columns = {{
                'feed': 'VARCHAR', 'symbol': 'VARCHAR', 'series': 'VARCHAR', 'isin': 'VARCHAR',
                'ex_date': 'DATE', 'kind': 'VARCHAR', 'num_a': 'DOUBLE',
                'num_b': 'DOUBLE', 'subject': 'VARCHAR'
            }})
    """)
    for num, name, path in exercises():
        if num > upto:
            break
        body = query_text(path)
        if not body:
            raise NotWritten(f"{path.relative_to(ROOT)} is still empty")
        try:
            con.execute(f"create view {name} as {body}")
        except duckdb.Error as e:
            raise RuntimeError(f"{path.relative_to(ROOT)} failed: {e}") from None
    return con


def main() -> None:
    n = int(sys.argv[1])
    name = next(name for num, name, _ in exercises() if num == n)
    try:
        con = build(n)
    except NotWritten as e:
        sys.exit(f"{e}. Open it, write the query under the comments, save, then run this again.")
    except RuntimeError as e:
        sys.exit(str(e))
    print(con.sql(f"select * from {name}").limit(20))
    print(con.sql(f"select count(*) as rows from {name}"))


if __name__ == "__main__":
    main()
