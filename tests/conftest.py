import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import db  # noqa: E402


@pytest.fixture
def con(request):
    """A database built up to the exercise named by the test module (test_exN)."""
    n = int(request.module.__name__.rsplit("ex", 1)[1])
    try:
        return db.build(n)
    except db.NotWritten as e:
        pytest.fail(f"{e}. Write that query first.", pytrace=False)
    except RuntimeError as e:
        pytest.fail(str(e), pytrace=False)


def rows(con, sql):
    return con.sql(sql).fetchall()


def columns(con, view):
    return [r[0] for r in con.sql(f"describe {view}").fetchall()]
