import os
from typing import Dict, List, Set
import pytz

# Timezone Configuration
EASTERN_TZ = pytz.timezone("America/New_York")

# Business Hours Configuration (8:00 AM - 9:00 PM ET, Mon-Fri)
BUSINESS_START_HOUR = 8   # 08:00 AM
BUSINESS_END_HOUR = 21   # 09:00 PM

# Recognized US Federal Holidays (2026 - 2027)
US_FEDERAL_HOLIDAYS: Set[str] = {
    "2026-01-01", "2026-01-19", "2026-02-16", "2026-05-25", "2026-06-19",
    "2026-07-03", "2026-09-07", "2026-10-12", "2026-11-11", "2026-11-26", "2026-12-25",
    "2027-01-01", "2027-01-18", "2027-02-15", "2027-05-31", "2027-06-18",
    "2027-07-05", "2027-09-06", "2027-10-11", "2027-11-11", "2027-11-25", "2027-12-25"
}

# Initial Participants Configuration with Login Passwords
INITIAL_PARTICIPANTS: Dict[str, Dict[str, str]] = {
    "approver@test.com": {
        "name": "Dmytro Kachurovskyy",
        "department": "Executive",
        "role": "Approver",
        "password": "Password123!"
    },
    "admin@test.com": {
        "name": "Nazarii Kosylo",
        "department": "SwimFast",
        "role": "Requester + Administrator",
        "password": "Password123!"
    },
    "requester1@test.com": {
        "name": "Liza Dragun",
        "department": "Office",
        "role": "Requester",
        "password": "Password123!"
    },
    "requester2@test.com": {
        "name": "Denys Kostromin",
        "department": "SwimRight / SwimSafe",
        "role": "Requester",
        "password": "Password123!"
    }
}

DEFAULT_APPROVER_EMAIL = "approver@test.com"
ADMINISTRATOR_EMAIL = "admin@test.com"

# Application Settings
TENANT_ID = os.getenv("M365_TENANT_ID", "mock-tenant-id")
CLIENT_ID = os.getenv("M365_CLIENT_ID", "mock-client-id")
CLIENT_SECRET = os.getenv("M365_CLIENT_SECRET", "mock-client-secret")
SHAREPOINT_SITE_URL = os.getenv("SHAREPOINT_SITE_URL", "https://swimright.sharepoint.com/sites/Budget")

# Workflow Rules & Deadlines
MONTHLY_COLLECTION_START_DAY = 20
MONTHLY_COLLECTION_END_DAY = 29
MONTHLY_APPROVAL_DEADLINE_DAY = 2

MORE_INFO_BUSINESS_HOURS_LIMIT = 48
MORE_INFO_WARNING_HOURS_BEFORE = 12

ADDITIONAL_EXPENSE_BUSINESS_DAYS_LIMIT = 4
LATE_SUBMISSION_BUSINESS_DAYS_LIMIT = 10
ESCALATION_BUSINESS_DAYS_LIMIT = 4

MAX_ATTACHMENT_SIZE_MB = 25
ALLOWED_ATTACHMENT_EXTENSIONS = {".pdf", ".xlsx", ".docx", ".jpg", ".jpeg", ".png"}
