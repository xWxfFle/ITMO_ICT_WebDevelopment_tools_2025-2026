from __future__ import annotations


def split_into_chunks(urls: list[str], num_parts: int) -> list[list[str]]:
    if num_parts < 1:
        raise ValueError("num_parts must be >= 1")
    if not urls:
        return []
    n = len(urls)
    base, rem = divmod(n, num_parts)
    out: list[list[str]] = []
    idx = 0
    for i in range(num_parts):
        take = base + (1 if i < rem else 0)
        if take == 0:
            continue
        out.append(urls[idx : idx + take])
        idx += take
    return out
