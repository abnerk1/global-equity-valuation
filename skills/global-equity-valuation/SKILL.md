---
name: global-equity-valuation
description: Values US stocks and ADRs with four valuation engines (two-stage ROIC compounder, shareholder yield + growth, high required yield, sum of the parts) across the Global Yield, Quality Leaders and Hidden Gems portfolios, returning a price ceiling, expected dividend yield and Buy/Hold call.
---

# Global Equity Valuation (v1.3)

Goal: given an international ticker, reach the price ceiling and the Buy/Hold call by rebuilding the
"1 + 1" (assumptions + formula) behind the result. The method has four valuation engines,
conservatism rules and deterministic output rules.

## 1. Required workflow

1. Pick the portfolio (section 2) and the engine (section 3).
2. Collect current data: share price, **fully diluted** shares outstanding (or ADRs, checking the ADR-to-share ratio), net debt, earnings/NOPAT/FCF for the trailing 12 months and the last 5 years, invested capital, declared dividends, guidance. Sources: 10-K/10-Q/20-F, merger 8-Ks, earnings releases, and a broker connector for the share price when available.
3. Normalize the earnings or cash-flow base with the conservatism rules (section 4).
4. Compute in code: `calc.py` when the repository is available; otherwise the core in section 7. Never by hand.
5. Apply the output rules (section 5).
6. Deliver the report in the fixed format (section 6). If the user supplies an existing reference ceiling, show "reference ceiling" and "recalculated ceiling" side by side.

Source isolation: never consult or cite any third-party thesis, price target, price ceiling, ranking or assumption (independent research, banks, brokers). Use only primary data (10-K/10-Q/20-F, 8-K, company investor relations) and the share price.

## 2. The three portfolios (mandate)

| Portfolio | What it seeks | Typical profile | Engines |
|---|---|---|---|
| **Global Yield** | High, predictable dividends + buybacks | Mature business, little capital needed to grow, high payout (mineral royalties, tobacco, mature hardware, regional banks) | B; A for banks (via ROTCE) |
| **Quality Leaders** | High-quality compounders, long term | Durable competitive advantage, high ROIC, reinvestment runway, management that allocates capital well | A; B for asset-light businesses that grow without capital; C for leveraged businesses; D for conglomerates with insurance operations |
| **Hidden Gems** | Deep discounts | Out-of-cycle commodities, emerging markets in crisis, holding companies at a discount, beaten-down brands | D, C, B (conservative price, g = 0), A |

Qualitative entry checklist (the report must answer every item):
- A named competitive advantage (pricing power, switching costs, network effects, monopoly, low funding cost, lowest production cost, scale).
- Management with a capital-allocation track record; buybacks when the stock is cheap.
- A balance sheet that survives the worst case (net cash, or long-dated fixed-rate debt).
- Cash returned to shareholders (dividends + buybacks = shareholder yield).
- Optionality (new products, new geographies, minority stakes) is valued at ZERO and mentioned only as upside.
- Commodities: enter only when the price is below the marginal cost of several competitors (their supply shuts in first).

## 3. Valuation engines

Real discount rate (r): **10%** by default · 8% for very stable, high-quality financials · 12% for cash flows in high-risk countries.

### Engine A — Two-stage ROIC × reinvestment
```
g      = ROIC (or real ROTCE) × reinvestment rate
payout = 1 − reinvestment rate
M = Σ_{t=1..10} payout·(1+g)^t/(1+r)^t + (1+g)^10 / r / (1+r)^10   (terminal: g = 0, 100% payout)
Fair value     = Base × M        Base = NOPAT, normalized earnings or normalized FCF
Price ceiling  = Fair value per share × (1 − margin of safety)
```
- Margin of safety: **20%** by default (up to 25% when the base is uncertain); 0% for a bank whose assumptions are already below its track record.
- Terminal growth only for a secular leader with clear reinvestment (max 2.5%).
- Estimate g from the last 5 years: reinvestment rate = Δ invested capital ÷ cumulative NOPAT; incremental ROIC = Δ NOPAT ÷ Δ invested capital. Use the conservative end of the range.
- Banks: real ROTCE below the historical average × historical reinvestment rate.
- Reference multiples (r = 10%): g 3% / payout 90% → 11.6x · g 8% / 90% → 16.5x · g 15% / 56% → 22.8x · g 7% / 85% at r = 8% → 19.5x.
- Hypothetical example: earnings US$ 10 bn, ROIC 20%, reinvests 40% → g 8%, payout 60% → M ≈ 13.8x → value US$ 138 bn; with 1 bn shares, fair value US$ 138 and ceiling US$ 110.

### Engine B — Return = shareholder yield + growth (Gordon)
```
Expected return = distributable FCF / market cap + g   (multiple change = 0)
Price ceiling   = distributable FCF per share / (r − g)   → the price that delivers exactly r
```
- Buy when the expected return is ≥ 10% real.
- Asset-light business that grows without capital: "pay up to an X% yield" ⇔ r − g = X.
- Commodity at a conservative price (official forecast or below spot): g = 0 → ceiling = FCF / 10%.
- Distributable FCF = sustainable NOPAT − interest − growth capex; net capex = 0 when capex < D&A; deduct stock-based compensation (SBC).
- Hypothetical example: FCF US$ 3 per share, g 4% → ceiling 3 / 6% = US$ 50.

### Engine C — High required yield (normalized cyclical or leveraged)
```
Price ceiling = normalized maintenance FCF / required yield / diluted shares
Required yield: 20% by default (5-year payback) · 25% if NOT a low-cost producer
```
- Use it when FCF exists only at a normalized commodity price ABOVE spot, or when debt exceeds ~3.5x net debt/EBITDA (FCF before expansion capex).
- Required: a scenario sensitivity (breakeven, current price, normalized, upside) and a note recommending a small position and a horizon of at least 5 years.
- In mergers, count the shares issued to the seller (including partnership units and convertible preferred) in the diluted base.
- Hypothetical example: normalized FCF US$ 1 bn, 50 mn shares, low-cost producer → 1 / 20% / 0.05 = US$ 100.

### Engine D — Sum of the parts / replacement cost / look-through
```
Equity value  = Σ conservatively valued assets − net debt
Price ceiling = lowest method per share/ADR × (1 − 10–15% haircut), rounded down
```
- Replacement cost: cost per unit BELOW what transactions and peers show; assets with expiring concessions = 0.
- Listed stakes: market value × % owned.
- Reserves: price per acre from private transactions, or the present value of proved reserves with no replacement.
- Segments with no profit or no reliable method: zero.
- Holding company: ceiling = market value of the main stake per share/ADR, with no holding discount and the rest of the portfolio at zero.
- Conglomerate with insurance operations: present value of the float (zero cost, 10% return, 2% growth, 10% discount rate) + statutory capital + 10x pre-tax earnings of the other operations.

## 4. Conservatism rules
- Earnings base below the recent average; exclude one-offs (tax benefits, fines, gains on sale).
- No growth after year 10 (except the Engine A exception).
- Segment margins normalized below peers; zero margin for loss-making segments.
- Commodities: reference price = official forecast or below spot; keep today's inflated costs.
- State explicitly what was left out of the valuation and why that is conservative.

## 5. Output rules (deterministic)
- **Call**: price ≤ ceiling → **Buy**; price > ceiling → **Hold** (do not add at this price).
- **Total return** = current price ÷ entry price − 1.
- **Expected dividend yield** = last declared dividend (including variable) × frequency ÷ current price; "-" when there is no regular dividend.
- Round the ceiling down: ≥ 1,000 → multiple of 50; ≥ 100 → of 10; ≥ 20 → whole dollar; ≥ 2 → 0.05; below that → cent.
- Ceilings are "sticky": set at entry and revised only after a material event (merger, spin-off, split, thesis change).

## 6. Report format
1. Header: ticker, company, portfolio, engine, date, share price.
2. Thesis (3–5 paragraphs) covering the checklist in section 2.
3. Recent results: diluted shares, market cap, revenue, margins, FCF, debt, buybacks/dividends.
4. Valuation: numbered assumptions → calculation (code output) → fair value → ceiling; sensitivity for commodities or leveraged cases.
5. Risks (3–5) and what mitigates each one.
6. Summary table: expected dividend yield | entry | current price | price ceiling | total return | call.

## 7. Calculation core (use when `calc.py` is not available)
```python
import math
def multiple(g, payout, r=0.10, years=10, g_terminal=0.0):
    E, pv = 1.0, 0.0
    for t in range(1, years + 1):
        E *= 1 + g; pv += payout * E / (1 + r) ** t
    return pv + E / (r - g_terminal) / (1 + r) ** years
def engine_a(base, roic, reinvest, shares, r=0.10, margin=0.20, g_terminal=0.0):
    fair = base * multiple(roic * reinvest, 1 - reinvest, r, g_terminal=g_terminal) / shares
    return fair * (1 - margin)
def engine_b(fcf, g, shares, r=0.10): return fcf / shares / (r - g)
def engine_c(fcf, shares, low_cost=True): return fcf / (0.20 if low_cost else 0.25) / shares
def engine_d(assets, net_debt, shares, haircut=0.10, alternatives=()):
    return min([sum(assets) - net_debt, *alternatives]) / shares * (1 - haircut)
def round_ceiling(c):
    s = 50 if c >= 1000 else 10 if c >= 100 else 1 if c >= 20 else 0.05 if c >= 2 else 0.01
    return round(math.floor(c / s + 1e-9) * s, 2)
def call(price, ceiling): return "Buy" if price <= ceiling else "Hold"
```

## 8. Limits (analyst judgment that no formula replicates)
- The choice of the "normalized" base and the "normalized" commodity price; that is why the report always shows the number chosen and the sensitivity.
- The priority order among stocks in the same portfolio.
- When to revisit a ceiling that is already set.
