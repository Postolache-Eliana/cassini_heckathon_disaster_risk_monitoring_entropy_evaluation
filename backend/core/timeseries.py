from datetime import datetime, timedelta


def build_time_range_series(center_date: str, window_days: int = 30, step_days: int = 5):
    """
    RFC3339-compliant time windows for Copernicus STAC API.
    """

    center = datetime.fromisoformat(center_date)

    windows = []
    start = center - timedelta(days=window_days)

    current = start

    while current < center:
        next_date = current + timedelta(days=step_days)

        windows.append({
            "start": current.strftime("%Y-%m-%dT00:00:00Z"),
            "end": next_date.strftime("%Y-%m-%dT23:59:59Z")
        })

        current = next_date

    # ensure minimum coverage
    if len(windows) < 6:
        for i in range(6 - len(windows)):
            fallback_start = (center - timedelta(days=i+1)).strftime("%Y-%m-%dT00:00:00Z")
            fallback_end = center.strftime("%Y-%m-%dT23:59:59Z")

            windows.append({
                "start": fallback_start,
                "end": fallback_end
            })

    return windows