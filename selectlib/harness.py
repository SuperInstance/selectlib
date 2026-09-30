"""The harness. It refuses to produce a number until the controls have fired.

This refusal is the point of the library. Four separate experiments in `jev-fusion`
produced confident, publishable numbers from instruments that could not fail. The
instrument being refactored here is the one that should have been in front of all four.
"""
from __future__ import annotations
from dataclasses import dataclass, field as _f
from .controls import control_suite, ControlFailure


@dataclass
class Result:
    budgets: list
    rows: list
    controls_passed: int
    controls_total: int

    def table(self, width=9):
        out = []
        if not self.rows:
            return out
        cols = list(self.rows[0].keys())
        out.append("  " + "".join(f"{c:>{width}s}" for c in cols))
        for r in self.rows:
            cells = []
        for c in cols:
            v = r[c]
            cells.append(f"{v:>{width}s}" if isinstance(v, str)
                         else f"{(round(v, 4) if isinstance(v, float) else v):>{width}d}"
                         if isinstance(v, int)
                         else f"{v:>{width}.4f}")
        out.append("  " + "".join(cells))
        return out

    def verdict(self):
        """A verdict is only issued when a control could have failed. This method exists
        so a caller cannot accidentally report one from a run that never checked."""
        if not self.controls_total:
            return "NO CONTROLS RAN -- this is not a result"
        return (f"{self.controls_passed}/{self.controls_total} controls fired")


def run(selectors, field_factory, budgets, seeds=(0,), ask=None, controls=None):
    """Run every selector over every budget and every seed.

    Controls run FIRST. A ControlFailure propagates and no numbers are returned, because
    a number produced by an instrument that has not been shown to work is worse than no
    number: it will be believed."""
    ctrls = controls if controls is not None else control_suite()
    passed = 0
    for c in ctrls:
        c.check()
        passed += 1

    rows = []
    for b in budgets:
        for s in seeds:
            f = field_factory(seed=s)
            for sel in selectors:
                corrected = f.with_corrections(sel.pick(f, b))
                rows.append({"budget": b, "seed": s, "selector": sel.name,
                             "calls": sel.cost_per_field, "mae": corrected.mae()})
    return Result(budgets, rows, passed, len(ctrls))
