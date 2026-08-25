from datetime import datetime
import pytz
from config import EASTERN_TZ
from services.time_service import (
    is_business_day,
    is_business_hour,
    add_business_hours,
    add_business_days,
    count_business_hours,
)

def test_weekend_and_holiday_exclusion():
    # 2026-05-25 is Memorial Day (Monday holiday)
    memorial_day = datetime(2026, 5, 25, 10, 0, tzinfo=EASTERN_TZ).date()
    assert not is_business_day(memorial_day)

    # 2026-05-24 is Sunday
    sunday = datetime(2026, 5, 24, 10, 0, tzinfo=EASTERN_TZ).date()
    assert not is_business_day(sunday)

    # 2026-05-26 is Tuesday (regular business day)
    tuesday = datetime(2026, 5, 26, 10, 0, tzinfo=EASTERN_TZ).date()
    assert is_business_day(tuesday)

def test_ts19_business_hour_deadline():
    """
    TS-19: A More Information Required request is created Friday at 8:00 PM ET
    before a federal holiday Monday (e.g. Memorial Day 2026-05-25).
    Only valid business-hour time from 8:00 AM–9:00 PM ET is counted;
    weekend and federal holiday hours are excluded.
    """
    # Friday 2026-05-22 at 8:00 PM (20:00) ET
    friday_night = datetime(2026, 5, 22, 20, 0, tzinfo=EASTERN_TZ)
    
    # 48 business hours limit
    deadline = add_business_hours(friday_night, 48)
    
    # Friday night has 1 business hour remaining (20:00 - 21:00).
    # Sat (May 23) - Sun (May 24) - Mon (May 25, Holiday) = 0 business hours.
    # Tue (May 26): 13 business hours (8 AM - 9 PM). Total = 14 hrs.
    # Wed (May 27): 13 business hours. Total = 27 hrs.
    # Thu (May 28): 13 business hours. Total = 40 hrs.
    # Fri (May 29): 8 business hours needed (8 AM + 8 hrs = 4 PM / 16:00). Total = 48 hrs.
    expected = datetime(2026, 5, 29, 16, 0, tzinfo=EASTERN_TZ)

    assert deadline == expected
    assert count_business_hours(friday_night, deadline) == 48.0
