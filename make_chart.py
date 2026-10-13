"""Draw docs/before_after.svg: raw vs adjusted closes around two ex-dates.

    python make_chart.py

Plain SVG, no plotting library. Needs all six queries written, since it reads
the adjusted_prices view.
"""
from datetime import date
from pathlib import Path

import db

OUT = Path(__file__).resolve().parent / "docs" / "before_after.svg"
PANELS = [
    ("GOODLUCK", date(2026, 8, 21), "Bonus 2:1"),
    ("TDPOWERSYS", date(2026, 8, 24), "Split Rs 2 to Re 1"),
]
W, H = 420, 260            # one panel
PAD_L, PAD_R, PAD_T, PAD_B = 56, 16, 44, 36
RAW, ADJ, INK, MUTED, GRID = "#b4232a", "#1f5fa8", "#1a1a1a", "#6b6b6b", "#e4e4e4"


def panel(con, symbol: str, ex_date: date, label: str, x0: int) -> str:
    rows = con.execute("""
        select trade_date, close, adj_close from adjusted_prices
        where symbol = ? order by trade_date""", [symbol]).fetchall()
    days = [d for d, _, _ in rows]
    lo = min(min(c, a) for _, c, a in rows)
    hi = max(max(c, a) for _, c, a in rows)
    lo, hi = lo * 0.95, hi * 1.05
    pw, ph = W - PAD_L - PAD_R, H - PAD_T - PAD_B

    def x(i):
        return x0 + PAD_L + pw * i / (len(days) - 1)

    def y(v):
        return PAD_T + ph * (hi - v) / (hi - lo)

    def line(values, color):
        pts = " ".join(f"{x(i):.1f},{y(v):.1f}" for i, v in enumerate(values))
        return f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="2"/>'

    out = [f'<text x="{x0 + PAD_L}" y="22" font-size="15" font-weight="600" fill="{INK}">'
           f'{symbol}</text>',
           f'<text x="{x0 + PAD_L}" y="36" font-size="11" fill="{MUTED}">{label}, '
           f'ex-date {ex_date:%d %b %Y}</text>']
    for k in range(5):
        v = lo + (hi - lo) * k / 4
        out.append(f'<line x1="{x0 + PAD_L}" x2="{x0 + W - PAD_R}" y1="{y(v):.1f}" '
                   f'y2="{y(v):.1f}" stroke="{GRID}"/>')
        out.append(f'<text x="{x0 + PAD_L - 6}" y="{y(v) + 4:.1f}" font-size="10" '
                   f'text-anchor="end" fill="{MUTED}">{v:,.0f}</text>')
    ex = x(days.index(ex_date))
    out.append(f'<line x1="{ex:.1f}" x2="{ex:.1f}" y1="{PAD_T}" y2="{H - PAD_B}" '
               f'stroke="{MUTED}" stroke-dasharray="4 3"/>')
    for i in (0, len(days) - 1):
        anchor = "start" if i == 0 else "end"
        out.append(f'<text x="{x(i):.1f}" y="{H - PAD_B + 16}" font-size="10" '
                   f'text-anchor="{anchor}" fill="{MUTED}">{days[i]:%d %b}</text>')
    out.append(line([c for _, c, _ in rows], RAW))
    out.append(line([a for _, _, a in rows], ADJ))
    return "\n".join(out)


def main() -> None:
    con = db.build(6)
    total_w, total_h = W * len(PANELS), H + 28
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {total_w} {total_h}" '
             f'width="{total_w}" height="{total_h}" font-family="Segoe UI, Helvetica, Arial, sans-serif">',
             f'<rect width="100%" height="100%" fill="#ffffff"/>']
    for i, (sym, ex_date, label) in enumerate(PANELS):
        parts.append(panel(con, sym, ex_date, label, i * W))
    ly = H + 14
    parts.append(f'<line x1="{PAD_L}" x2="{PAD_L + 22}" y1="{ly}" y2="{ly}" stroke="{RAW}" stroke-width="2"/>'
                 f'<text x="{PAD_L + 28}" y="{ly + 4}" font-size="11" fill="{INK}">Raw close (as NSE reports it)</text>'
                 f'<line x1="{PAD_L + 220}" x2="{PAD_L + 242}" y1="{ly}" y2="{ly}" stroke="{ADJ}" stroke-width="2"/>'
                 f'<text x="{PAD_L + 248}" y="{ly + 4}" font-size="11" fill="{INK}">Adjusted close (in today\'s shares)</text>')
    parts.append("</svg>")
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text("\n".join(parts) + "\n", encoding="utf-8")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
