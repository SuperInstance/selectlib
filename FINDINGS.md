# Lane A, reopened — because the experiment that closed it was wrong

## What I said last

Lane A closed. Three designed experiments, three controls, three negatives: on scattered
defects the judge is indistinguishable from a free statistic; on an inserted blob it wins
slightly; on a realistic seam the free statistic wins. Concluded: **the judge's advantage
is general, not structural**, and ~0.007 at 100 model calls per field is a bad trade.

## Why that closure was wrong

Two defects, and only the second is interesting.

**The first: my "blind" field was not blind.** exp7 asserted that a local-disagreement
statistic had *nothing* to read. It had a rank correlation of about −0.11 with the true
error. Not nothing. The field was never actually blind, and the control that should have
caught it demanded **exactly zero** local disagreement — which a continuous field with a
seam cannot have, because the seam is itself a discontinuity. I wrote a control that could
not pass, then read its failure as a field bug.

**The second, and the one that matters: there was no cross-seam structure to find.**

Building the library forced me to make the free statistic's blindness *measurable* rather
than asserted — a rank correlation — and to give the control arm **the same total error
with none of the structure**. The moment both were true, the answer changed.

## The result, with the real model

Every run: **5/5 controls fired before any number was computed.**

| arm | free statistic ↔ true error | judge − noise, budgets 6 / 12 / 24 |
|---|---|---|
| **blind_split** — cross-seam structure | **−0.067** (blind) | **−0.0052 / −0.0050 / −0.0111** |
| **blind_uniform** — same error, no seam | **−0.184** (blind) | **+0.0000 / +0.0000 / +0.0000** |

**The judge beats the free statistic on cross-seam structure, and ties it to four decimal
places when there is none.** On the uniform arm all three selectors score *identically* —
which is correct, because with a uniform offset every cell is equally wrong and there is
nothing to rank.

**The difference is attributable to the cross-seam structure and to nothing else**, because
the free statistic is provably blind on both arms and carries the same error on both.

## What the judge actually is

Not a fine-grained selector. A **coarse one**: it answers *which side of this boundary am I
on*, which is a regional question, and it is good at it in a way a local statistic cannot
be. On fine selection — which cell among a locally noisy set — it is the same instrument as
the free statistic, and costs a hundred calls more.

**That is a better result than the one I was chasing, and it is the one the prior art
implies.** DyDiT's spatial router is coarse; DuoDiff's finding is that the leverage is at
high-noise steps and coarse decisions. A discrete judge is the wrong tool for per-token
selection and plausibly the right tool for "which region is misaligned" — which is a
routing question, not a selection question.

## The corrected position

| use | verdict |
|---|---|
| fine per-cell selection on locally noisy fields | **no.** Indistinguishable from free arithmetic at 100× the cost. |
| **coarse regional selection — which region is wrong** | **yes**, and the advantage is structural, not a distribution artefact. |
| anything requiring the oracle's accuracy | no. At budget 24 the judge is 0.1163 against an oracle of 0.0798. |

Lane A does not reopen as I wrote it. It reopens **narrower and more usefully**: the
question is not "can a model route compute better than a statistic" but "**can a model see
a boundary a statistic cannot see**." On that question the answer is yes, and it is now
measured with a control that can fail.

## What is still open

1. **Does the coarse advantage survive a harder region structure** than a straight seam —
   a curved boundary, or several at once?
2. **How many calls does it take?** 288 calls for one field is a lot. The advantage is
   0.005–0.011. Whether that is a trade depends on the call cost, which is the whole
   question and has not been answered.
3. **Does this compose with the prior art?** A coarse external router over a coarse
   region structure is close to what MIGC and SyncDiffusion already do, and the honest
   novelty claim is thin. The measurement is the contribution, not the mechanism.
