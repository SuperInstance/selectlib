"""Selectors: given a field and a budget, choose the cells to correct.

A selector is a function (field, budget) -> ordered cell list. Ordering matters and is
free: a selector is judged only on the prefix of length `budget` that it returns.

Three are supplied, and the third is optional:

  oracle       sorts by true error. The ceiling. Not implementable in practice.
  local_noise  sorts by disagreement with neighbours. Free. The bar to beat.
  judge        sorts by a discrete model's per-cell verdict. Costs calls.

`local_noise` is the important one. A selector that does not beat it is not a finding; it
is arithmetic done expensively.
"""
from __future__ import annotations
from dataclasses import dataclass
import math


@dataclass(frozen=True)
class Selector:
    name: str
    rank: callable            # (field) -> ordered list of (y,x), best first
    cost_per_field: int = 0   # model calls, for reporting the trade honestly

    def pick(self, field, budget):
        return list(self.rank(field))[:budget]


def _cells(field):
    return field.cells()


def _oracle_rank(field):
    return sorted(_cells(field),
                  key=lambda c: -abs(field.render[c[0]][c[1]] - field.target[c[0]][c[1]]))


def _noise_rank(field):
    out = []
    for (y, x) in _cells(field):
        nb = [field.render[y + dy][x + dx]
              for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0))
              if 0 <= y + dy < field.h and 0 <= x + dx < field.w]
        d = abs(field.render[y][x] - sum(nb) / len(nb)) if nb else 0.0
        out.append((d, (y, x)))
    out.sort(key=lambda t: -t[0])
    return [c for _, c in out]


def oracle() -> Selector:
    return Selector("oracle", _oracle_rank, 0)


def local_noise() -> Selector:
    return Selector("local_noise", _noise_rank, 0)


def judge(ask, cost_per_field=None) -> Selector:
    """`ask(field, y, x) -> float` is the model's per-cell score, best first when high.

    The score is CACHED per field. Asking once per field and reusing the ranking for
    every budget is not a shortcut -- the ranking does not depend on the budget, and
    asking again per budget is 3-5x the calls for identical information."""
    cache = {}

    def rank(field):
        key = id(field)
        if key not in cache:
            scored = []
            for (y, x) in _cells(field):
                scored.append((float(ask(field, y, x)), (y, x)))
            scored.sort(key=lambda t: -t[0])
            cache[key] = [c for _, c in scored]
        return cache[key]

    n = cost_per_field if cost_per_field is not None else len(cache) or None
    return Selector("judge", rank, 0)
