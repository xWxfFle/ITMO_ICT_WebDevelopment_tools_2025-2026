"""
Сумма 1..N через ``multiprocessing``: несколько процессов, у каждого свой GIL →
реальный параллелизм на CPU (для чистых вычислений на маленьких чанках выигрыш
может быть небольшим относительно накладных расходов на процессы).
"""

from __future__ import annotations

import time
from multiprocessing import Pool

from constants import NUM_CHUNKS, UPPER_BOUND
from math_utils import expected_total, split_ranges


def calculate_sum(start: int, end: int) -> int:
    """Сумма целых от ``start`` до ``end`` включительно (формула, без цикла)."""
    if start > end:
        return 0
    return end * (end + 1) // 2 - (start - 1) * start // 2


def main() -> None:
    ranges = split_ranges(UPPER_BOUND, NUM_CHUNKS)
    t0 = time.perf_counter()
    with Pool(processes=len(ranges)) as pool:
        parts = pool.starmap(calculate_sum, ranges)
    total = sum(parts)
    elapsed = time.perf_counter() - t0
    expected = expected_total(UPPER_BOUND)
    ok = total == expected
    print(f"[multiprocessing] processes={len(ranges)} время={elapsed:.6f}s")
    print(f"результат={total}")
    print(f"ожидалось={expected}; совпадение: {ok}")


if __name__ == "__main__":
    main()
