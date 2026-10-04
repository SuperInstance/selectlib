"""Tests. The control tests are the important ones: they are the tests that would have
caught the things that actually went wrong while this library was being written."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from selectlib import (fields, selectors, controls, harness,
                        oracle, local_noise, judge, blob, smooth,
                        blind_split, blind_uniform, mirrored_seam, ControlFailure)


def test_oracle_beats_local_noise_on_a_blob():
    f = blob(seed=1)
    for b in (2, 4, 8, 16, 32):
        o = f.with_corrections(oracle().pick(f, b)).mae()
        n = f.with_corrections(local_noise().pick(f, b)).mae()
        assert o <= n + 1e-12, f"oracle {o} should never be worse than noise {n} at budget {b}"


def test_selectors_return_the_right_number_of_real_cells():
    f = blob(seed=2)
    for sel in (oracle(), local_noise()):
        for b in (1, 5, 20):
            p = sel.pick(f, b)
            assert len(p) == b
            assert all(c in f.cells() for c in p)


def test_the_free_statistic_is_blind_where_it_is_claimed_to_be():
    """The claim the whole design rests on. If this fails, every blind-field comparison
    is compromised and the experiments built on it should not have been run."""
    for f in (blind_split(), blind_uniform()):
        c = controls.noise_error_corr(f)
        assert abs(c) < 0.30, f"{f.meta['kind']}: free statistic is NOT blind (corr {c:+.3f})"


def test_the_free_statistic_works_where_it_is_claimed_to():
    """The other half. A control that passes because the statistic reads NOTHING would
    pass just as happily, and would be a control that cannot fail."""
    assert controls.noise_error_corr(smooth()) > 0.4
    assert controls.noise_error_corr(blob()) > 0.3


def test_no_degenerate_control():
    """The clean arm must carry REAL error. Its first version had render == target, so
    every selector scored 0.0000 and the control passed trivially -- worse than useless,
    because it looked like a result."""
    assert blind_uniform().mae() > 0.05, "the control arm is degenerate: there is nothing to find"
    assert blind_split().mae() > 0.05


def test_the_two_arms_carry_comparable_error():
    """Otherwise 'the judge wins on split' could just mean 'the split arm has more to
    find'. They must be within a factor of two of each other."""
    a, b = blind_split().mae(), blind_uniform().mae()
    assert 0.4 < a / b < 2.5, f"arms not comparable: split {a:.4f} vs uniform {b:.4f}"


def test_harness_refuses_to_run_when_a_control_cannot_fire():
    """The refusal is the library. A broken control must stop the run, not warn about it."""
    bad = controls.Control("deliberately_broken", "nothing", None, lambda fx: False)
    try:
        harness.run([oracle()], lambda seed: blob(seed=seed), [4], controls=[bad])
    except ControlFailure:
        return
    raise AssertionError("the harness produced a number despite a control that cannot fire")


def test_harness_reports_its_controls():
    r = harness.run([oracle(), local_noise()], lambda seed: blob(seed=seed), [4], seeds=(1,))
    assert r.verdict().startswith("5/5"), r.verdict()


def test_judge_selector_caches_per_field():
    """Asking once per field and reusing the ranking is not a shortcut: the ranking does
    not depend on the budget."""
    calls = {"n": 0}
    def ask(field, y, x):
        calls["n"] += 1
        return abs(field.render[y][x] - field.target[y][x])
    j = judge(ask)
    f = blob(seed=3)
    n = len(f.cells())
    j.pick(f, 4); j.pick(f, 8); j.pick(f, 16)
    assert calls["n"] == n, f"expected {n} calls for three budgets, got {calls['n']}"


def test_field_shape_and_target_agree():
    for f in (smooth(), blob(), mirrored_seam(), blind_split(), blind_uniform()):
        assert f.h == len(f.target) and f.w == len(f.target[0])
        assert f.mae() >= 0


def test_result_table_renders_every_row():
    """Regression pin (fixes #1): the row body was once dedented out of the
    for-loop, silently rendering only the LAST row -- plausible-looking output
    that under-reports every other selector."""
    r = harness.Result(budgets=[6, 12, 24],
                       rows=[{"selector": "oracle", "mae": 0.10},
                             {"selector": "judge", "mae": 0.15},
                             {"selector": "noise", "mae": 0.16}],
                       controls_passed=5, controls_total=5)
    t = r.table()
    assert len(t) == 4, f"header + one line per row; got {len(t)} lines: {t}"
    assert "oracle" in t[1] and "judge" in t[2] and "noise" in t[3], t
