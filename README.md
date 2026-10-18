# Global Equity Valuation

**A rules-based valuation skill for US stocks and ADRs. Every price ceiling comes from a written formula, not from a model's mood.**

Four valuation engines, three portfolio mandates and a fixed set of conservatism and output rules turn a ticker into a fair value, a price ceiling, an expected dividend yield and a Buy/Hold call, in the same report format every time.

## The problem it solves

Ask a large language model what a stock is worth and you get a confident number with no audit trail. Ask again and the number moves. For anything that touches someone's savings, that is a bug.

This skill makes the agent show its work:

- **Pick the mandate first.** Every stock is classified into one of three portfolios, and each portfolio has a short list of allowed engines.
- **One formula per engine.** The price ceiling is the output of a written formula with documented defaults (10% real discount rate, 20% margin of safety, 20–25% required yield for cyclical or leveraged names).
- **Conservatism by default.** Earnings below the recent average, no growth after year 10, optionality valued at zero.
- **Deterministic output.** Buy when the price is at or below the ceiling, Hold when it is above. Ceilings are rounded with a fixed rule.
- **Primary sources only.** 10-K, 10-Q, 20-F, 8-K and company investor relations. No third-party price targets.

## The three portfolios

| Portfolio | What it seeks | Engines |
|---|---|---|
| **Global Yield** | High, predictable dividends and buybacks from mature businesses | B, and A for banks |
| **Quality Leaders** | Long-term compounders with durable moats and high ROIC | A, plus B, C or D for special cases |
| **Hidden Gems** | Deep discounts: out-of-cycle commodities, holding-company discounts, crisis markets | D, C, B, A |

## The four engines

| Engine | Idea | Price ceiling |
|---|---|---|
| **A** | Two-stage compounder: 10 years growing at ROIC × reinvestment, then a no-growth perpetuity | fair value × (1 − 20%) |
| **B** | Expected return = shareholder yield + growth (Gordon) | FCF per share ÷ (r − g) |
| **C** | High required yield for normalized cyclical or leveraged cash flows | normalized FCF ÷ 20% (25% if not a low-cost producer) |
| **D** | Sum of the parts, replacement cost or look-through value | lowest method × (1 − 10–15%) |

Engine A's fair multiple:

```
M = Σ_{t=1..10} payout·(1+g)^t/(1+r)^t + (1+g)^10 / r / (1+r)^10
g = ROIC × reinvestment rate,  payout = 1 − reinvestment rate
```

Reference values at r = 10%: g 3% / payout 90% → 11.6x · g 8% / 90% → 16.5x · g 15% / 56% → 22.8x.

## Example

A hypothetical company earns US$ 10 bn, earns a 20% ROIC and reinvests 40% of its profit:

```bash
$ python skills/global-equity-valuation/calc.py A --base 10 --roic 0.20 --reinvest 0.40 --shares 1.0 --price 95
engine            : A
g                 : 0.0800
payout            : 0.6000
multiple          : 13.7552
fair_per_share    : 137.5516
ceiling           : 110.0413
rounded_ceiling   : 110.00
call              : Buy
```

g = 20% × 40% = 8%, the fair multiple is 13.8x, fair value is US$ 138 per share, and the 20% margin of safety puts the ceiling at US$ 110. At US$ 95 the call is Buy.

## Repository layout

```
skills/global-equity-valuation/SKILL.md   the skill (methodology, rules, report format)
skills/global-equity-valuation/calc.py    deterministic calculator for the four engines + CLI
tests/test_calc.py                        engine tests with hypothetical cases
tests/test_skill_core.py                  checks the fallback core in SKILL.md matches calc.py
```

## How to use

**As a skill.** Load `skills/global-equity-valuation/` into any client that supports the `SKILL.md` format, then ask for a valuation of a ticker.

**From the terminal.** `calc.py` uses only the Python 3 standard library.

```bash
python skills/global-equity-valuation/calc.py A --base 10 --roic 0.20 --reinvest 0.40 --shares 1.0
python skills/global-equity-valuation/calc.py B --fcf 3 --g 0.04 --shares 1.0
python skills/global-equity-valuation/calc.py C --fcf 1 --shares 0.05 [--high-cost]
python skills/global-equity-valuation/calc.py D --assets 5 3 2 --net-debt 1 --shares 0.1 --haircut 0.10
python -m unittest discover -s tests
```

## Known limits

- The "normalized" earnings base and commodity price are analyst judgment. The report always shows the number chosen and a sensitivity table.
- The skill does not rank stocks within a portfolio.
- Ceilings are sticky by design: they are revisited after a material event, not on every price move.

## Related projects

- [skills-b3](https://github.com/abnerk1/skills-b3): the same rules-based approach for Brazilian stocks and REITs (FIIs).
- [anchor-and-tilt](https://github.com/abnerk1/anchor-and-tilt): a deterministic ETF allocation rubric.

## Disclaimer

This project is educational. Each result comes from fixed quantitative rules applied to public data and **is not personalized investment advice**. Investment decisions are the investor's responsibility.

## License

[MIT](LICENSE).
