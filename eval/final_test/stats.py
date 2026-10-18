"""Interval estimates for the final test (standard library only). Protocol: docs/FINAL_TEST_PROTOCOL.md section 3."""
import math
import random
from collections import Counter
from typing import Callable, Sequence

Z95 = 1.959963984540054
BOOTSTRAP_SEED = 20261018  # fixed in advance
BOOTSTRAP_N = 2000


def wilson(k: int, n: int, z: float = Z95) -> tuple[float, float] | None:
    """Wilson score interval for a proportion k/n; None when n is 0."""
    if n <= 0:
        return None
    p = k / n
    d = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / d
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0.0, centre - half), min(1.0, centre + half)


def percentile(sorted_xs: Sequence[float], q: float) -> float:
    """Linear-interpolation percentile of an already sorted sequence."""
    if not sorted_xs:
        raise ValueError("empty")
    pos = q * (len(sorted_xs) - 1)
    lo, hi = math.floor(pos), math.ceil(pos)
    return sorted_xs[lo] + (sorted_xs[hi] - sorted_xs[lo]) * (pos - lo)


def bootstrap_ci(docs: Sequence[Counter], stat: Callable[[Counter], float | None], n: int = BOOTSTRAP_N, seed: int = BOOTSTRAP_SEED) -> tuple[float, float] | None:
    """Document-level bootstrap (percentile) 95% interval of stat(sum of the resampled per-document counters). Resamples whose statistic is undefined are skipped."""
    if not docs:
        return None
    rng = random.Random(seed)
    vals = []
    for _ in range(n):
        total: Counter = Counter()
        for _ in docs:
            total += docs[rng.randrange(len(docs))]
        v = stat(total)
        if v is not None:
            vals.append(v)
    if len(vals) < n // 2:
        return None
    vals.sort()
    return percentile(vals, 0.025), percentile(vals, 0.975)
