"""Deterministic calculator for the global-equity-valuation skill (v1.4).

Four valuation engines plus the output rules. Any consistent unit works
(for example, US$ billions for cash flows and billions of shares -> US$ per share).

CLI quick start:
    python calc.py A --base 10 --roic 0.20 --reinvest 0.40 --shares 1.0
    python calc.py B --fcf 2 --g 0.03 --shares 1.0
    python calc.py C --fcf 1 --shares 0.05 [--high-cost]
    python calc.py D --assets 5 3 2 --net-debt 1.5 --shares 0.2 --haircut 0.10
    (add --price P to get the Buy/Hold call)
    (add --dividends-3y D --net-income-3y N [--fcf-3y F] for the dividend-trap check and thesis status)
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import math

DEFAULT_R = 0.10  # real cost of capital


# ---------------------------------------------------------------- Engine A
def two_stage_multiple(g: float, payout: float, r: float = DEFAULT_R,
                       years: int = 10, g_terminal: float = 0.0) -> float:
    """Fair multiple (value / year-0 earnings).

    Stage 1: `years` years growing at g, paying out `payout` of earnings.
    Stage 2: perpetuity growing at g_terminal with 100% payout.
    """
    if r <= g_terminal:
        raise ValueError("r must be greater than g_terminal")
    earnings, pv = 1.0, 0.0
    for t in range(1, years + 1):
        earnings *= 1 + g
        pv += payout * earnings / (1 + r) ** t
    return pv + earnings / (r - g_terminal) / (1 + r) ** years


def engine_a(base: float, roic: float, reinvestment: float, shares: float,
             r: float = DEFAULT_R, margin: float = 0.20, years: int = 10,
             g_terminal: float = 0.0, g: float | None = None) -> dict:
    """Two-stage compounder. g = ROIC x reinvestment rate (unless given)."""
    g = roic * reinvestment if g is None else g
    payout = 1 - reinvestment
    m = two_stage_multiple(g, payout, r, years, g_terminal)
    fair = base * m / shares
    return {"engine": "A", "g": g, "payout": payout, "multiple": m,
            "fair_per_share": fair, "ceiling": fair * (1 - margin)}


# ---------------------------------------------------------------- Engine B
def engine_b(fcf: float, g: float, shares: float, r: float = DEFAULT_R,
             market_cap: float | None = None) -> dict:
    """Expected return = yield + g. Ceiling = FCF per share / (r - g)."""
    if r <= g:
        raise ValueError("r must be greater than g")
    ceiling = fcf / shares / (r - g)
    out = {"engine": "B", "yield_at_ceiling": r - g, "fair_per_share": ceiling, "ceiling": ceiling}
    if market_cap:
        out["expected_return"] = fcf / market_cap + g
    return out


# ---------------------------------------------------------------- Engine C
def engine_c(normalized_fcf: float, shares: float, low_cost: bool = True,
             required_yield: float | None = None) -> dict:
    """High required yield: 20% by default, 25% if not a low-cost producer."""
    y = required_yield if required_yield is not None else (0.20 if low_cost else 0.25)
    ceiling = normalized_fcf / y / shares
    return {"engine": "C", "required_yield": y, "fair_per_share": ceiling, "ceiling": ceiling}


def sensitivity_c(fcf_by_scenario: dict[str, float], shares: float,
                  y: float = 0.20) -> dict[str, float]:
    """Ceiling for each commodity-price scenario."""
    return {k: v / y / shares for k, v in fcf_by_scenario.items()}


# ---------------------------------------------------------------- Engine D
def engine_d(assets: list[float], net_debt: float, shares: float,
             haircut: float = 0.10, alternative_methods: list[float] | None = None) -> dict:
    """Sum of the parts. Uses the lowest equity value among the methods given."""
    equity = sum(assets) - net_debt
    candidates = [equity] + list(alternative_methods or [])
    used = min(candidates)
    fair = used / shares
    return {"engine": "D", "sotp_equity": equity, "equity_used": used,
            "fair_per_share": fair, "ceiling": fair * (1 - haircut)}


# ---------------------------------------------------------------- Output rules
def round_ceiling(ceiling: float) -> float:
    """Round down to a 'clean' number based on the order of magnitude."""
    if ceiling <= 0:
        return 0.0
    if ceiling >= 1000:
        step = 50
    elif ceiling >= 100:
        step = 10
    elif ceiling >= 20:
        step = 1
    elif ceiling >= 2:
        step = 0.05
    else:
        step = 0.01
    return round(math.floor(ceiling / step + 1e-9) * step, 2)


def call(price: float, ceiling: float) -> str:
    return "Buy" if price <= ceiling else "Hold"


def expected_dividend_yield(last_dividend: float | None, frequency: int, price: float) -> str:
    if not last_dividend:
        return "-"
    return f"{last_dividend * frequency / price:.1%}"


def total_return(price: float, entry: float) -> float:
    return price / entry - 1


def dividend_trap(dividends_3y: float, net_income_3y: float,
                  fcf_3y: float | None = None) -> dict[str, list[str]]:
    """Dividend-trap check over the last three fiscal years (sums, same currency).

    Critical: dividends paid above net income (payout > 100%).
    Monitor: dividends paid above free cash flow (skip for banks and insurers).
    """
    out: dict[str, list[str]] = {"critical": [], "monitor": []}
    if dividends_3y > max(net_income_3y, 0.0):
        out["critical"].append("dividend trap: payout above 100% over 3 years")
    if fcf_3y is not None and dividends_3y > fcf_3y:
        out["monitor"].append("free cash flow below dividends over 3 years")
    return out


def thesis_status(critical: list[str] | tuple = (), monitor: list[str] | tuple = ()) -> str:
    """Separate from the Buy/Hold call. Critical review > Monitoring > Consolidated."""
    if critical:
        return "Critical review (" + "; ".join(critical) + ")"
    if monitor:
        return "Monitoring (" + "; ".join(monitor) + ")"
    return "Consolidated"


@dataclass
class Result:
    ceiling: float
    rounded_ceiling: float
    call: str | None


def finalize(res: dict, price: float | None = None) -> Result:
    c = res["ceiling"]
    rc = round_ceiling(c)
    return Result(c, rc, call(price, rc) if price is not None else None)


# ---------------------------------------------------------------- CLI
def _cli() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="engine", required=True)
    a = sub.add_parser("A", help="two-stage compounder")
    a.add_argument("--base", type=float, required=True, help="normalized earnings, NOPAT or FCF")
    a.add_argument("--roic", type=float, required=True)
    a.add_argument("--reinvest", type=float, required=True, help="reinvestment rate (0 to 1)")
    a.add_argument("--shares", type=float, required=True)
    a.add_argument("--r", type=float, default=DEFAULT_R)
    a.add_argument("--margin", type=float, default=0.20)
    a.add_argument("--g-terminal", type=float, default=0.0)
    a.add_argument("--g", type=float, help="override g instead of ROIC x reinvestment")
    b = sub.add_parser("B", help="shareholder yield + growth (Gordon)")
    b.add_argument("--fcf", type=float, required=True, help="distributable FCF")
    b.add_argument("--g", type=float, required=True)
    b.add_argument("--shares", type=float, required=True)
    b.add_argument("--r", type=float, default=DEFAULT_R)
    b.add_argument("--market-cap", type=float)
    c = sub.add_parser("C", help="high required yield")
    c.add_argument("--fcf", type=float, required=True, help="normalized maintenance FCF")
    c.add_argument("--shares", type=float, required=True)
    c.add_argument("--yield", dest="y", type=float)
    c.add_argument("--high-cost", action="store_true", help="not a low-cost producer (25%% yield)")
    d = sub.add_parser("D", help="sum of the parts")
    d.add_argument("--assets", type=float, nargs="+", required=True)
    d.add_argument("--net-debt", type=float, default=0.0)
    d.add_argument("--shares", type=float, required=True)
    d.add_argument("--haircut", type=float, default=0.10)
    d.add_argument("--alternatives", type=float, nargs="*", help="equity value from other methods")
    for sp in (a, b, c, d):
        sp.add_argument("--price", type=float)
        sp.add_argument("--dividends-3y", type=float, help="dividends paid, sum of the last 3 fiscal years")
        sp.add_argument("--net-income-3y", type=float, help="net income, sum of the same 3 years")
        sp.add_argument("--fcf-3y", type=float, help="free cash flow, sum of the same 3 years (skip for banks)")
        sp.add_argument("--critical", action="append", default=[], help="qualitative thesis-break flag (repeatable)")
        sp.add_argument("--monitor", action="append", default=[], help="qualitative flag to watch (repeatable)")
    x = p.parse_args()
    if x.engine == "A":
        res = engine_a(x.base, x.roic, x.reinvest, x.shares, x.r, x.margin, g_terminal=x.g_terminal, g=x.g)
    elif x.engine == "B":
        res = engine_b(x.fcf, x.g, x.shares, x.r, x.market_cap)
    elif x.engine == "C":
        res = engine_c(x.fcf, x.shares, not x.high_cost, x.y)
    else:
        res = engine_d(x.assets, x.net_debt, x.shares, x.haircut, x.alternatives)
    fin = finalize(res, x.price)
    for k, v in res.items():
        print(f"{k:18}: {v:.4f}" if isinstance(v, float) else f"{k:18}: {v}")
    print(f"{'rounded_ceiling':18}: {fin.rounded_ceiling:.2f}")
    if fin.call:
        print(f"{'call':18}: {fin.call}")
    critical, monitor = list(x.critical), list(x.monitor)
    if fin.rounded_ceiling <= 0:
        critical.append("ceiling at zero")
    if x.dividends_3y is not None and x.net_income_3y is not None:
        trap = dividend_trap(x.dividends_3y, x.net_income_3y, x.fcf_3y)
        critical += trap["critical"]
        monitor += trap["monitor"]
    print(f"{'thesis_status':18}: {thesis_status(critical, monitor)}")


if __name__ == "__main__":
    _cli()
