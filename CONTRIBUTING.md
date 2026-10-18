# Contributing

Thanks for wanting to improve the method. A few rules keep it deterministic.

## Principles

1. **`SKILL.md` is the source of truth.** Rules live in `skills/global-equity-valuation/SKILL.md`. `calc.py` implements them, and the fallback core in section 7 of `SKILL.md` must return the same numbers (CI checks this).
2. **Primary sources only.** 10-K, 10-Q, 20-F, 8-K, company investor relations and the share price. Do not send a pull request that relies on a third-party thesis, price target or assumption, or on paywalled data.
3. **Conservatism over precision.** A change that raises valuations has to explain why the current default is too strict.
4. **No silent rules.** A new rule needs a number, a rationale and a hypothetical example.

## Proposing a change

The engines are fixed so results stay comparable across companies. A method change ships as a **new version**, not a quiet tweak:

- Open an issue describing the case where the current rule gives a wrong or ambiguous answer, with two or three tickers and the result you expected.
- In the pull request, bump the version in the `SKILL.md` title (for example, v1.3 → v1.4) and show the before/after numbers.
- Do not bend a rule for a single company. If a case falls outside the method, the right answer is a warning in the report.

## Checklist

- [ ] `python -m unittest discover -s tests` passes
- [ ] The fallback core in `SKILL.md` still matches `calc.py`
- [ ] No source other than SEC filings, company investor relations and the share price
- [ ] No personal data, API keys or credentials in the diff
