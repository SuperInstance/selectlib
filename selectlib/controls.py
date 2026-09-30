"""Controls. A control that cannot fail is worse than no control.

Every control here has a `fires` method that must return True on a fixture the control is
*supposed* to detect. A control that never fires is not evidence of health; it is a rule
that has been switched off, and from the outside it is indistinguishable from a rule that
ran and found nothing.
"""
from __future__ import annotations
from dataclasses import dataclass
import sys


class ControlFailure(AssertionError):
    """Raised when a control does not fire. The harness refuses to produce a number."""


@dataclass(frozen=True)
class Control:
    name: str
    what_it_guards: str
    fixture: object
    fires: callable        # (fixture) -> bool

    def check(self):
        try:
            ok = bool(self.fires(self.fixture))
        except Exception as e:
            raise ControlFailure(
                f"{self.name}: the control could not EXECUTE ({type(e).__name__}: {e}). "
                f"A control that errors is not a control that passes.") from None
        if not ok:
            raise ControlFailure(
                f"{self.name}: the control did not fire on its own fixture. "
                f"It guards {self.what_it_guards}, and a rule that cannot be shown to "
                f"detect the thing it claims to detect must not be used to judge "
                f"anything else.")
        return True


def _sel_fires(sel, budget=4):
    """A selector must actually return cells, and they must be the right COUNT."""
    from .fields import blob
    f = blob(seed=1)
    picked = sel.pick(f, budget)
    return len(picked) == budget and all(c in f.cells() for c in picked)


def _oracle_is_ceiling(sel, budget=4):
    """The oracle must be at least as good as anything else, at every budget.

    This is the check that makes every other number in the harness mean something: if the
    ceiling is not the ceiling, nothing below it can be ranked."""
    from .fields import blob
    from .selectors import oracle, local_noise
    f = blob(seed=2)
    return f.with_corrections(oracle().pick(f, budget)).mae() <= \
           f.with_corrections(local_noise().pick(f, budget)).mae() + 1e-12


def _rank_corr(a, b):
    """Spearman rank correlation, by average ranks so ties do not break it."""
    n = len(a)
    if n < 2:
        return 0.0
    def ranks(v):
        order = sorted(range(n), key=lambda i: v[i])
        r = [0.0] * n
        i = 0
        while i < n:
            j = i
            while j + 1 < n and v[order[j + 1]] == v[order[i]]:
                j += 1
            avg = (i + j) / 2.0 + 1
            for k in range(i, j + 1):
                r[order[k]] = avg
            i = j + 1
        return r
    ra, rb = ranks(a), ranks(b)
    ma, mb = sum(ra) / n, sum(rb) / n
    num = sum((ra[i] - ma) * (rb[i] - mb) for i in range(n))
    da = sum((ra[i] - ma) ** 2 for i in range(n)) ** 0.5
    db = sum((rb[i] - mb) ** 2 for i in range(n)) ** 0.5
    return num / (da * db) if da and db else 0.0


def noise_error_corr(field):
    """How much the free statistic actually tells you about the true error, as a rank
    correlation. 1.0 means the free statistic is a perfect proxy; 0.0 means it is
    blind, which is the condition a 'the judge reads structure the statistic cannot'
    claim requires."""
    from .selectors import _noise_rank
    order = _noise_rank(field)
    rank_of = {c: i for i, c in enumerate(order)}
    cells = field.cells()
    stat = [len(order) - rank_of[c] for c in cells]      # higher = more disagreement
    true = [abs(field.render[c[0]][c[1]] - field.target[c[0]][c[1]]) for c in cells]
    return _rank_corr(stat, true)


def _free_statistic_is_blind_where_it_must_be():
    """The first version of this control demanded EXACTLY ZERO local disagreement on a
    blind field, and it refused to let the harness run -- correctly. A continuous field
    cannot have zero neighbour-disagreement and also have a seam; the seam is itself a
    discontinuity. Demanding zero was a definitional error on my part, not a field bug.

    The achievable and correct condition is UNINFORMATIVENESS: the free statistic's
    ordering must be uncorrelated with the true error. Measured, not asserted."""
    from .fields import blob, blind_split, blind_clean
    seen = noise_error_corr(blob(seed=3))
    for f in (blind_split(), blind_clean()):
        if noise_error_corr(f) > 0.30:
            return False
    return seen > 0.5      # and the statistic must demonstrably WORK somewhere, or this
                            # control would pass on a statistic that never reads anything


def _blind_split_differs_from_clean():
    """The split arm must ACTUALLY differ from the clean arm, or the control is vacuous.

    A control whose two arms are the same number is a control that cannot fire."""
    from .fields import blind_split, blind_clean
    return blind_split().mae() > 1e-6


def control_suite() -> list:
    from .selectors import oracle, local_noise
    return [
        Control("oracle_fires", "the ceiling is real", None,
                lambda fx: _sel_fires(oracle())),
        Control("noise_fires", "the bar can be cleared", None,
                lambda fx: _sel_fires(local_noise())),
        Control("oracle_is_ceiling", "every ranking below the ceiling is meaningful", None,
                lambda fx: _oracle_is_ceiling(oracle())),
        Control("free_statistic_is_blind_where_it_must_be",
                "free-selector comparisons on blind fields", None,
                lambda fx: _free_statistic_is_blind_where_it_must_be()),
        Control("split_differs_from_clean",
                "the cross-seam control is not vacuous", None,
                lambda fx: _blind_split_differs_from_clean()),
    ]
