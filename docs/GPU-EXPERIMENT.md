# GPU experiment brief — `selectlib`

**What a discrete judge is good at**

This is the slice of the master queue that concerns this repository. The full document,
with all ten experiments and their decision trees, is at
[`SuperInstance/fleet-triage` → `docs/GPU-EXPERIMENTS.md`](https://github.com/SuperInstance/fleet-triage/blob/main/docs/GPU-EXPERIMENTS.md).

1. **State whether CUDA or CPU actually ran.** A CPU fallback reported as a GPU result is a
   fabricated measurement. Record the device string with the number.
2. **Report the variance, not just the mean.** If the measured quantity has `std == 0` over
   the sample, the result is **INCONCLUSIVE, never PASSED**. This is a hard rule: an earlier
   sharding experiment scored `PASSED` on the literal comparison `0 < 0`.
3. **The ground truth must be computed, not asserted.** Every game number below is exact.
   If a label is approximate, say by how much.
4. **Non-degeneracy is a precondition, not a result.** Assert that the data has variance
   *before* evaluating any relational claim about it.
5. **A control must vary the thing it audits, by a different path than the audited thing.**
   The most expensive mistake in this project's history: a control built from the same call
   path as the probes, which therefore confirmed a fault instead of auditing it.
6. **A ratio whose denominator can be zero is a construction, not a measurement.** It always
   produces a finding, and the finding is always false.
7. **Seed everything and record the seed.** Two runs of the same experiment that differ are
   a finding about the seed, not about the method.
8. **Cross-port arithmetic must preserve the reference loop/summation order.** Float addition
   is not associative; a port that vectorises changes the answer.

---

### Experiment 5 — What a discrete judge is good at

**Repo:** `selectlib`, `jev-fusion`. **Result: settled, and it is a negative result.**

Measured: a real Jev judge **beats a blind local-noise statistic on cross-seam structure**
(`blind_split`: −0.0052, −0.0050, −0.0111 across three budgets) and **ties exactly on
same-error structure** (`blind_uniform`: +0.0000 at every budget). 288 model calls per field.

**What it means:** discrete judges are **coarse structural instruments** — useful for
boundaries and regions, not for fine per-cell selection. A judge that gates a whole region's
work is earning its cost. A judge that picks which of 400 individual cells to fix is not.

The GPU-relevant extension: if the judge is useful at *coarse* selection, the interesting
question becomes whether a **learned** coarse selector — trained on the judge's region-level
labels — can replace 288 API calls with one forward pass. That is a legitimate distillation
experiment, and its ground truth is already collected.

| Result | What it means |
|---|---|
| Student matches the judge on held-out fields | **The judge is compressible.** One forward pass replaces 288 calls. This is a real win and it is publishable. |
| Student matches only on `blind_split` | The judge encodes something about *error structure* that a local loss does not capture. Then the label set must carry cross-cell information — which the sparse-signal objection says it probably does not. |
| Student fails on both | The judge is not a function of the local representation at all. Report that plainly; it is a statement about the information content of the observation. |

---

## 4. Reporting format

Every experiment reports, in this order:

1. **Device.** Did CUDA actually run? Paste the device string.
2. **Data provenance.** Which commit, which digest, how many states/positions, and the
   FNV-1a 64 of the input file.
3. **The ceiling.** What is perfect, and what did you get as a fraction of it.
4. **Variance.** Mean ± std over N seeds, with the seeds listed. **std == 0 means INCONCLUSIVE.**
5. **The branch.** Which row of which decision tree above you landed on, quoted.
6. **Controls.** What ran that could have failed. If nothing could have failed, say that —
   it is the finding.
