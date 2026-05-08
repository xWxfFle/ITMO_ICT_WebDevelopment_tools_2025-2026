def expected_total(upper: int) -> int:
    return upper * (upper + 1) // 2


def split_ranges(upper: int, num_chunks: int) -> list[tuple[int, int]]:
    """Разбивает [1, upper] на ``num_chunks`` последовательных отрезков."""
    if num_chunks < 1:
        raise ValueError("num_chunks must be >= 1")
    chunk_size, rem = divmod(upper, num_chunks)
    ranges: list[tuple[int, int]] = []
    current = 1
    for i in range(num_chunks):
        length = chunk_size + (1 if i < rem else 0)
        if length == 0:
            continue
        end = current + length - 1
        ranges.append((current, end))
        current = end + 1
    return ranges
