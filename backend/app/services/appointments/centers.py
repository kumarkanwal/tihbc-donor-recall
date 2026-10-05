"""Demo-center selection rules."""

KORANGI_CENTER = "Korangi Campus Blood Center"
NORTH_NAZIMABAD_CENTER = "North Nazimabad Donor Center"
DEMO_CENTERS = (KORANGI_CENTER, NORTH_NAZIMABAD_CENTER)


def center_for_city(city: str | None) -> str:
    """Choose the nearest demo center, defaulting to Korangi."""
    normalized = (city or "").strip().casefold()
    if "nazimabad" in normalized:
        return NORTH_NAZIMABAD_CENTER
    return KORANGI_CENTER
