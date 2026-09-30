"""Fields: a render plus the exact target it is wrong about.

Every field is a pair (render, target) with the SAME shape, and the target is known exactly.
That exactness is what lets an oracle bound any selector, and without a bound you cannot
tell a good selector from a lucky one.
"""
from __future__ import annotations
from dataclasses import dataclass
import math, random


@dataclass(frozen=True)
class Field:
    render: list          # H x W, what the observer sees
    target: list          # H x W, what it should be
    meta: dict            # what kind of field this is, for the record

    @property
    def h(self): return len(self.render)
    @property
    def w(self): return len(self.render[0])
    def cells(self): return [(y, x) for y in range(self.h) for x in range(self.w)]
    def mae(self, other=None):
        r = other or self.render
        return sum(abs(r[y][x] - self.target[y][x])
                   for y in range(self.h) for x in range(self.w)) / (self.h * self.w)

    def with_corrections(self, picks) -> "Field":
        r = [row[:] for row in self.render]
        for (y, x) in picks:
            r[y][x] = self.target[y][x]
        return Field(r, self.target, self.meta)


def _base(h, w, rng, amp=0.25, coarse=(3, 2)):
    """Bilinear upsample from a coarse grid. Every cell is locally consistent BY
    CONSTRUCTION, which is the only way to make a local statistic genuinely blind
    rather than approximately blind."""
    cw, ch = coarse
    c = [[rng.uniform(0.5 - amp, 0.5 + amp) for _ in range(cw)] for _ in range(ch)]
    out = [[0.0] * w for _ in range(h)]
    for y in range(h):
        fy = y / max(1, h - 1) * (ch - 1)
        y0 = int(fy); y1 = min(y0 + 1, ch - 1); ty = fy - y0
        for x in range(w):
            fx = x / max(1, w - 1) * (cw - 1)
            x0 = int(fx); x1 = min(x0 + 1, cw - 1); tx = fx - x0
            a = c[y0][x0] * (1 - tx) + c[y0][x1] * tx
            b = c[y1][x0] * (1 - tx) + c[y1][x1] * tx
            out[y][x] = a * (1 - ty) + b * ty
    return out


def smooth(h=8, w=12, seed=0):
    """A correct render, plus a small amount of render noise. A local statistic CAN
    read this, which is what makes it the positive control for the blind fields."""
    rng = random.Random(seed)
    target = _base(h, w, rng)
    render = [row[:] for row in target]
    for y in range(h):
        for x in range(w):
            render[y][x] = min(1.0, max(0.0, render[y][x] + rng.gauss(0, 0.02)))
    return Field(render, target, {"kind": "smooth", "locally_blind": False})


def blob(h=8, w=12, seed=0, r=2):
    """A contiguous blob of errors in an otherwise consistent field.

    This is the distribution that flattered every selector in exp5. Kept, with a warning,
    because the reason it flatters is the interesting part."""
    rng = random.Random(seed)
    t = _base(h, w, rng)
    r_ = [row[:] for row in t]
    cy, cx = h // 2, w // 2
    for y in range(max(0, cy - r), min(h, cy + r + 1)):
        for x in range(max(0, cx - r), min(w, cx + r + 1)):
            if (y - cy) ** 2 + (x - cx) ** 2 <= r * r:
                r_[y][x] = rng.uniform(0.0, 1.0)
    return Field(r_, t, {"kind": "blob", "locally_blind": False})


def mirrored_seam(h=8, w=12, seed=0, seam=None, depth=2):
    """A seam whose error is mirrored across the join.

    Both sides are wrong in the SAME direction, so neither side disagrees with its own
    neighbours -- but the cells on the seam do, because the offset peaks there. That leak
    is why this distribution does not actually blind a local statistic, and why
    `blind_split` exists."""
    rng = random.Random(seed)
    seam = seam if seam is not None else w // 2
    t = _base(h, w, rng)
    r_ = [row[:] for row in t]
    off = rng.uniform(-0.35, 0.35)
    for y in range(h):
        for d in range(1, depth + 1):
            for x in (seam - d, seam + d - 1):
                if 0 <= x < w:
                    r_[y][x] = min(1.0, max(0.0, r_[y][x] + off * (1 - 0.2 * d)))
    return Field(r_, t, {"kind": "mirrored_seam", "seam": seam, "locally_blind": False})


def _split_field(h, w, seed, on):
    """Left and right are each internally consistent; the ONLY inconsistency is between
    them, reached through a smooth ramp so no cell ever jumps against its neighbours.

    The ramp matters. A hard step at the seam is itself a local discontinuity, which is
    why the first version of this field left the free statistic able to read it."""
    rng = random.Random(seed)
    seam = w // 2
    ramp = max(1.5, w / 12.0)
    target = _base(h, w, rng)
    render = [row[:] for row in target]
    if on:
        for y in range(h):
            for x in range(w):
                # a smooth logistic offset: 0 far left, 0.35 far right, no jump anywhere
                z = (x - seam) / ramp
                off = 0.35 / (1.0 + math.exp(-z))
                render[y][x] = min(1.0, max(0.0, render[y][x] + off))
    else:
        # THE CONTROL, and its first version was degenerate: the clean arm had render
        # == target, so every selector scored 0.0000 and the control passed trivially.
        # A control that cannot fail is not a control, and a degenerate one is worse --
        # it looked like a result.
        #
        # The clean arm now carries THE SAME total error as the split arm, applied
        # UNIFORMLY: every cell is wrong by the same amount, so there is no seam, no
        # cross-region disagreement, and no local signal either. Both statistics are
        # blind. If a wide-reading selector wins HERE as well as on split, its advantage
        # is the wide window and not the structure.
        amp = 0.175
        for y in range(h):
            for x in range(w):
                render[y][x] = min(1.0, max(0.0, render[y][x] + amp))
    kind = "blind_split" if on else "blind_uniform"
    return Field(render, target, {"kind": kind, "seam": seam, "locally_blind": True})


def blind_split(h=8, w=12, seed=0):
    """Left and right disagree; every cell is locally consistent. The free statistic is
    blind BY CONSTRUCTION."""
    return _split_field(h, w, seed, on=True)


def blind_clean(h=8, w=12, seed=0):
    """The control: same field, no cross-seam disagreement. Also locally consistent.
    If a selector wins here and on `blind_split` by the same margin, it is not reading the
    seam -- it is just better at the base task."""
    return _split_field(h, w, seed, on=False)


def blind_uniform(h=8, w=12, seed=0):
    """The control for `blind_split`: THE SAME total error, applied uniformly.

    Every cell is wrong by the same amount, so there is no seam and no cross-region
    disagreement -- and, crucially, no local signal either. Both the free statistic and
    any wide-reading selector are blind here. A selector that wins on this arm as well as
    on split is reading the WIDE WINDOW, not the structure."""
    return _split_field(h, w, seed, on=False)
