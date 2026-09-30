"""Run the REAL discrete judge through the harness, on fields where the free statistic
is provably blind. The hand-written wide-window function in run_demo.py is the control
for the harness; this is the thing the harness exists to measure.

    python3 run_judge.py
"""
import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from selectlib import harness, oracle, local_noise, judge, blind_split, blind_uniform
from selectlib.controls import noise_error_corr
from jev_client import jev_judge

BUDGETS = [6, 12, 24]
SEEDS = (1,)

if __name__ == "__main__":
    import os as _os
    if not _os.environ.get("TYPESAFEAI_KEY"):
        print("  no TYPESAFEAI_KEY; the offline demo in run_demo.py is the reproducible run")
        raise SystemExit(0)
    for name, factory in (("BLIND_SPLIT", blind_split), ("BLIND_UNIFORM", blind_uniform)):
        f0 = factory(seed=SEEDS[0])
        print(f"\n  {name}   free-statistic rank correlation: {noise_error_corr(f0):+.3f}")
        calls = {"n": 0}
        def ask(field, y, x, _c=calls):
            _c["n"] += 1
            w = field.w
            l = [(xx, field.render[y][xx], field.target[y][xx])
                 for xx in range(max(0, x - 2), x + 1)]
            r = [(xx, field.render[y][xx], field.target[y][xx])
                 for xx in range(x + 1, min(w, x + 3))]
            def desc(side):
                if not side:
                    return "nothing on that side"
                return "; ".join(f"col {c} renders {rv:.2f} but the scene calls for {tv:.2f}"
                                 for c, rv, tv in side)
            st = (f"A cell sits between two regions of a scene.\n"
                  f"LEFT of it: {desc(l)}\n"
                  f"RIGHT of it: {desc(r)}\n"
                  f"The cell itself is at column {x}.")
            return jev_judge(st)
        j = judge(ask)
        r = harness.run([oracle(), j, local_noise()],
                        lambda seed: factory(seed=seed), BUDGETS, seeds=SEEDS)
        print(f"  {r.verdict()}   model calls: {calls['n']}")
        for b in BUDGETS:
            got = {row["selector"]: row["mae"] for row in r.rows if row["budget"] == b}
            print(f"    budget {b:>3}:  judge {got['judge']:.4f}  noise {got['local_noise']:.4f}"
                  f"  judge-noise {got['judge'] - got['local_noise']:+.4f}"
                  f"  (oracle {got['oracle']:.4f})")
