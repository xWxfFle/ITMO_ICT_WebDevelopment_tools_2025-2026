"""
Сумма 1..N через ``threading``: каждый поток считает свой отрезок.
CPU-bound на CPython даёт мало выигрыша из-за GIL, но демонстрирует API потоков.
"""

from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor, as_completed

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
    total = 0
    with ThreadPoolExecutor(max_workers=len(ranges)) as ex:
        futures = [ex.submit(calculate_sum, a, b) for a, b in ranges]
        for fut in as_completed(futures):
            total += fut.result()
    elapsed = time.perf_counter() - t0
    expected = expected_total(UPPER_BOUND)
    ok = total == expected
    print(f"[threading] workers={len(ranges)} время={elapsed:.6f}s")
    print(f"результат={total}")
    print(f"ожидалось={expected}; совпадение: {ok}")


if __name__ == "__main__":
    main()
