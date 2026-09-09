def decade(year: int | None) -> str | None:
    if not year:
        return None
    return f"{(year // 10) * 10}er"


_AREA_BINS = [(50, "< 50 m²"), (100, "50–99 m²"), (200, "100–199 m²"), (10**9, "≥ 200 m²")]


def area_bucket(m2: int | None) -> str | None:
    if m2 is None:
        return None
    for upper, label in _AREA_BINS:
        if m2 < upper:
            return label
    return None
