"""selectlib — choosing which cells to touch, and proving you chose well.

Four experiments in `jev-fusion` measured the same question four ways and disagreed about
it, because each used a different field and none of them made the free statistic blind.
The parts that did not change across all four are the parts worth shipping:

  * a field is a GRID plus a TARGET, and the target is known exactly
  * a selector picks cells to move toward the target under a budget
  * a FREE selector exists and must be beaten for anything to be worth saying
  * a control exists that can be made blind, and making it blind is the test

`harness.run()` refuses to return a number until every control has fired. That refusal is
the library. Everything else is bookkeeping.
"""
from .fields import Field, smooth, blob, mirrored_seam, blind_split, blind_clean, blind_uniform
from .selectors import Selector, oracle, local_noise, judge
from .controls import Control, control_suite, ControlFailure
from .harness import run, Result

__all__ = [
    "Field", "smooth", "blob", "mirrored_seam", "blind_split", "blind_clean", "blind_uniform",
    "Selector", "oracle", "local_noise", "judge",
    "Control", "control_suite", "ControlFailure",
    "run", "Result",
]
__version__ = "0.1.0"
