# selectlib

Choosing which cells to touch — and proving you chose well.

Four experiments in `jev-fusion` measured the same question four ways and disagreed with
each other, because each used a different field and **none of them made the free
statistic blind**. This library is the part that did not change across all four.

## The shape of it

- a **field** is a render plus the exact target it is wrong about
- a **selector** is `(field, budget) -> ordered cells`, judged only on the prefix it returns
- a **free selector** exists (`local_noise`) and **must be beaten** for anything to be worth saying
- a **control** exists that can be made blind — and making it blind is the test

## The refusal is the library

`harness.run()` executes every control **before** it computes a single number, and raises
`ControlFailure` if one does not fire. A number produced by an instrument that has not been
shown to work is worse than no number, because it will be believed. This session produced
four of those.

## The controls, and what each guards

| control | guards |
|---|---|
| `oracle_fires` | the ceiling returns real cells |
| `noise_fires` | the bar can actually be cleared |
| `oracle_is_ceiling` | every ranking below the ceiling means something |
| `free_statistic_is_blind_where_it_must_be` | free-selector comparisons on blind fields |
| `split_differs_from_clean` | the cross-seam control is not vacuous |

## Two controls that caught real bugs in this library while it was being written

1. **The first "blind" control demanded EXACTLY ZERO local disagreement, and refused to
   let the harness run.** It was right. A continuous field cannot have zero
   neighbour-disagreement *and* a seam; the seam is itself a discontinuity. The control
   was a definitional error, not a field bug. It now measures **uninformativeness** — the
   free statistic's rank correlation with true error — and also asserts the statistic
   demonstrably *works* somewhere, because a control that passes because the statistic
   reads nothing is a control that cannot fail.
2. **The first control arm was degenerate.** `blind_clean` had `render == target`, so every
   selector scored `0.0000` and the control passed trivially — looking exactly like a
   result. It now carries the *same total error* applied uniformly, so there is real
   error to find and nothing structural to find it with. `test_no_degenerate_control`
   guards this.

## The result the harness was built to measure

| arm | free-statistic ↔ true error | wide-reader − free selector |
|---|---|---|
| **blind_split** (cross-seam structure) | −0.067 (blind) | **−0.0079 / −0.0259 / −0.0349** |
| **blind_uniform** (same error, no seam) | −0.184 (blind) | **+0.0000 / +0.0000 / +0.0000** |

On the uniform control all three selectors score *identically* — correctly, because with a
uniform offset every cell is equally wrong. On the split arm the wide reader wins and
closes on the oracle. **The difference is attributable to the cross-seam structure and
nothing else**, because the free statistic is provably blind on both arms.

## Run it

```bash
python3 run_tests.py      # 10 tests, no pytest required
python3 run_demo.py       # the offline demonstration above
TYPESAFEAI_KEY=... python3 run_judge.py   # the real discrete model
```

`run_demo.py` runs offline with a deterministic wide-window stand-in. `run_judge.py`
substitutes the real model. The difference between them is the difference between a
mechanism and an instrument, and both run through the same controls.
