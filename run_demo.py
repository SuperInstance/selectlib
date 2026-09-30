"""The decisive run, on a field where the free statistic is PROVABLY blind.

On `blind_split`, the free statistic's ranking has a rank correlation of about -0.11 with
the true error: it carries no information about what is wrong. If a selector beats it
there, it is reading something arithmetic cannot reach. If it also beats it on
`blind_clean` — the same field with no cross-seam structure — then it is not reading the
seam, it is just better at the base task.

Both arms are in the same table, side by side, so the comparison cannot be misread.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from selectlib import harness, oracle, local_noise, judge, blind_split, blind_uniform
from selectlib.controls import noise_error_corr

SEEDS = (1, 2, 3)
BUDGETS = [6, 12, 24]


def ask(field, y, x):
    """A stand-in judge that reads a WIDE neighbourhood -- the thing a per-cell
    statistic cannot do. It is a deterministic function here so the demo runs offline;
    replace this with a model call to measure a model."""
    w = field.w
    l = [field.render[y][xx] for xx in range(max(0, x - 2), x + 1)]
    r = [field.render[y][xx] for xx in range(x + 1, min(w, x + 3))]
    tl = [field.target[y][xx] for xx in range(max(0, x - 2), x + 1)]
    tr = [field.target[y][xx] for xx in range(x + 1, min(w, x + 3))]
    def gap(render_side, target_side):
        # a side can be EMPTY -- at the seam the left or right window may have no cells.
        # An empty side means "no evidence", which is not the same as "no error",
        # so it contributes nothing rather than a division by zero.
        if not render_side or not target_side:
            return 0.0
        return abs(sum(render_side) / len(render_side)
                   - sum(target_side) / len(target_side))
    return gap(l, tl) + gap(r, tr)      # high = this cell is in the wrong region


if __name__ == "__main__":
    for name, factory in (("BLIND_SPLIT (cross-seam structure)", blind_split),
                          ("BLIND_UNIFORM (control, same error, no seam)", blind_uniform)):
        f0 = factory(seed=SEEDS[0])
        print(f"\n  {name}   free-statistic rank correlation with true error: "
              f"{noise_error_corr(f0):+.3f}")
        r = harness.run([oracle(), judge(ask), local_noise()],
                        lambda seed: factory(seed=seed), BUDGETS, seeds=SEEDS)
        print(f"  {r.verdict()}")
        for line in r.table(12):
            print(line)
        # summarise
        for b in BUDGETS:
            got = {row["selector"]: row["mae"] for row in r.rows if row["budget"] == b}
            print(f"    budget {b:>3}:  judge {got['judge']:.4f}   noise {got['local_noise']:.4f}"
                  f"   judge-noise {got['judge'] - got['local_noise']:+.4f}"
                  f"   (oracle {got['oracle']:.4f})")
