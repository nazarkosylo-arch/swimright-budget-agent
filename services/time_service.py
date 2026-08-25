from datetime import datetime, date, timedelta
import pytz
from config import (
    EASTERN_TZ,
    BUSINESS_START_HOUR,
    BUSINESS_END_HOUR,
    US_FEDERAL_HOLIDAYS,
)

def get_current_eastern_time() -> datetime:
    """Returns current datetime aware in Eastern Time zone."""
    return datetime.now(EASTERN_TZ)

def is_business_day(d: date) -> bool:
    """Check if a date is a business day (Monday-Friday and not a US Federal Holiday)."""
    # 0 = Monday, 4 = Friday, 5 = Saturday, 6 = Sunday
    if d.weekday() >= 5:
        return False
    date_str = d.strftime("%Y-%m-%d")
    if date_str in US_FEDERAL_HOLIDAYS:
        return False
    return True

def is_business_hour(dt: datetime) -> bool:
    """Check if a given datetime falls within business hours (8:00 AM - 9:00 PM ET on business days)."""
    dt_et = dt.astimezone(EASTERN_TZ)
    if not is_business_day(dt_et.date()):
        return False
    return BUSINESS_START_HOUR <= dt_et.hour < BUSINESS_END_HOUR

def add_business_hours(start_dt: datetime, hours_to_add: float) -> datetime:
    """
    Adds business hours to start_dt, respecting the 8:00 AM - 9:00 PM ET window and business days.
    """
    current = start_dt.astimezone(EASTERN_TZ)
    remaining_minutes = int(hours_to_add * 60)

    while remaining_minutes > 0:
        # Move to business hours start if current is before business hours on a business day
        if is_business_day(current.date()):
            if current.hour < BUSINESS_START_HOUR:
                current = current.replace(hour=BUSINESS_START_HOUR, minute=0, second=0, microsecond=0)
            elif current.hour >= BUSINESS_END_HOUR:
                # Move to next day start
                current = (current + timedelta(days=1)).replace(
                    hour=BUSINESS_START_HOUR, minute=0, second=0, microsecond=0
                )
                continue
        else:
            # Move to next day 8:00 AM
            current = (current + timedelta(days=1)).replace(
                hour=BUSINESS_START_HOUR, minute=0, second=0, microsecond=0
            )
            continue

        # Now current is inside business hours
        day_end = current.replace(hour=BUSINESS_END_HOUR, minute=0, second=0, microsecond=0)
        minutes_left_today = int((day_end - current).total_seconds() / 60)

        if remaining_minutes <= minutes_left_today:
            current += timedelta(minutes=remaining_minutes)
            remaining_minutes = 0
        else:
            remaining_minutes -= minutes_left_today
            current = (current + timedelta(days=1)).replace(
                hour=BUSINESS_START_HOUR, minute=0, second=0, microsecond=0
            )

    return current

def add_business_days(start_dt: datetime, days_to_add: int) -> datetime:
    """
    Adds N business days to start_dt.
    Each business day contains (BUSINESS_END_HOUR - BUSINESS_START_HOUR) hours = 13 hours.
    """
    hours = days_to_add * (BUSINESS_END_HOUR - BUSINESS_START_HOUR)
    return add_business_hours(start_dt, hours)

def count_business_hours(start_dt: datetime, end_dt: datetime) -> float:
    """
    Calculates total business hours accrued between start_dt and end_dt.
    """
    start = start_dt.astimezone(EASTERN_TZ)
    end = end_dt.astimezone(EASTERN_TZ)

    if start >= end:
        return 0.0

    total_minutes = 0
    current = start

    while current < end:
        if is_business_day(current.date()):
            day_start = current.replace(hour=BUSINESS_START_HOUR, minute=0, second=0, microsecond=0)
            day_end = current.replace(hour=BUSINESS_END_HOUR, minute=0, second=0, microsecond=0)

            window_start = max(current, day_start)
            window_end = min(end, day_end)

            if window_start < window_end:
                total_minutes += (window_end - window_start).total_seconds() / 60.0

        # Move to start of next day
        current = (current + timedelta(days=1)).replace(
            hour=BUSINESS_START_HOUR, minute=0, second=0, microsecond=0
        )

    return total_minutes / 60.0
