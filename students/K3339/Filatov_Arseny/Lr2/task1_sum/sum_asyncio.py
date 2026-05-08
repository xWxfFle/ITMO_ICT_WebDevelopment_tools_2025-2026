"""
Сумма 1..N через ``asyncio``: параллельный запуск ``calculate_sum`` в пуле потоков
(`asyncio.to_thread`), чтобы не блокировать цикл событий. Чистые вычисления в одном
потоке без пула выполнились бы последовательно.
"""

from __future__ import annotations

import asyncio
import time

from constants import NUM_CHUNKS, UPPER_BOUND
from math_utils import expected_total, split_ranges


def calculate_sum(start: int, end: int) -> int:
    """Сумма целых от ``start`` до ``end`` включительно (формула, без цикла)."""
    if start > end:
        return 0
    return end * (end + 1) // 2 - (start - 1) * start // 2


async def main() -> None:
    ranges = split_ranges(UPPER_BOUND, NUM_CHUNKS)
    t0 = time.perf_counter()
    tasks = [asyncio.to_thread(calculate_sum, a, b) for a, b in ranges]
    parts = await asyncio.gather(*tasks)
    total = sum(parts)
    elapsed = time.perf_counter() - t0
    expected = expected_total(UPPER_BOUND)
    ok = total == expected
    print(f"[asyncio+threads] задач={len(ranges)} время={elapsed:.6f}s")
    print(f"результат={total}")
    print(f"ожидалось={expected}; совпадение: {ok}")


if __name__ == "__main__":
    asyncio.run(main())
