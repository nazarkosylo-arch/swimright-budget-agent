import asyncio
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from config import EASTERN_TZ, DEFAULT_APPROVER_EMAIL

DB_FILE = "expenses_db.json"

class GraphService:
    """
    Service for interacting with SharePoint Lists (Operational Store) and managing Expense records.
    Implements atomic Expense ID allocation, status transitions, category checks, and draft management.
    """
    def __init__(self):
        self._lock = asyncio.Lock()
        self._expenses: Dict[str, Dict] = {}
        self._categories: List[str] = [
            "Office Supplies",
            "Travel Expenses",
            "Software & Subscriptions",
            "Equipment & Maintenance",
            "Marketing & Events"
        ]
        self._drafts: Dict[str, Dict] = {}
        self._id_counters: Dict[str, int] = {}
        self._active_approver: str = DEFAULT_APPROVER_EMAIL
        self._load_from_disk()

    def _load_from_disk(self):
        if os.getenv("TESTING") or os.getenv("PYTEST_CURRENT_TEST"):
            return
        if os.path.exists(DB_FILE):
            try:
                with open(DB_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        self._expenses = data.get("expenses", {})
                        self._id_counters = data.get("counters", {})
            except Exception:
                pass

    def _save_to_disk(self):
        if os.getenv("TESTING") or os.getenv("PYTEST_CURRENT_TEST"):
            return
        try:
            with open(DB_FILE, "w", encoding="utf-8") as f:
                json.dump({
                    "expenses": self._expenses,
                    "counters": self._id_counters
                }, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    @property
    def active_approver(self) -> str:
        return self._active_approver

    def set_active_approver(self, approver_email: str):
        self._active_approver = approver_email

    async def generate_expense_id(self, year: int, month: int) -> str:
        """
        Atomically generates a unique Expense ID in the format EXP-YYYY-MM-###.
        Guarantees thread-safe / concurrent allocation (AC-24, AC-25, TS-21, TS-22).
        """
        async with self._lock:
            key = f"{year:04d}-{month:02d}"
            current_seq = self._id_counters.get(key, 0) + 1
            self._id_counters[key] = current_seq
            self._save_to_disk()
            return f"EXP-{key}-{current_seq:03d}"

    async def create_expense(self, data: Dict) -> Dict:
        """
        Creates a new expense record atomically.
        """
        now = datetime.now(EASTERN_TZ)
        expense_id = await self.generate_expense_id(now.year, now.month)
        
        record = {
            "ExpenseID": expense_id,
            "RequestType": data.get("RequestType", "Monthly Expense Request"),
            "SubmittedBy": data["SubmittedBy"],
            "Program": data["Program"],
            "ExpenseName": data["ExpenseName"],
            "AmountUSD": float(data["AmountUSD"]),
            "PurchasePurpose": data["PurchasePurpose"],
            "ExpenseCategory": data["ExpenseCategory"],
            "OptionalLink": data.get("OptionalLink", ""),
            "AttachmentRef": data.get("AttachmentRef", ""),
            "SubmissionDate": now.isoformat(),
            "DecisionDate": None,
            "CurrentStatus": "Pending",
            "AddedAfterApproval": data.get("AddedAfterApproval", "No"),
            "RejectedAfterEscalation": "No",
            "UnlockReason": None,
            "BudgetMonth": data.get("BudgetMonth", f"{now.strftime('%B')}'{now.strftime('%y')}")
        }

        async with self._lock:
            self._expenses[expense_id] = record
            self._save_to_disk()
        return record

    async def get_expense(self, expense_id: str) -> Optional[Dict]:
        return self._expenses.get(expense_id)

    async def delete_expense(self, expense_id: str) -> bool:
        async with self._lock:
            if expense_id in self._expenses:
                del self._expenses[expense_id]
                self._save_to_disk()
                return True
            return False

    async def update_status(self, expense_id: str, status: str, decision_date: Optional[str] = None, unlock_reason: Optional[str] = None) -> Optional[Dict]:
        async with self._lock:
            if expense_id in self._expenses:
                self._expenses[expense_id]["CurrentStatus"] = status
                if decision_date:
                    self._expenses[expense_id]["DecisionDate"] = decision_date
                if unlock_reason:
                    self._expenses[expense_id]["UnlockReason"] = unlock_reason
                self._save_to_disk()
                return self._expenses[expense_id]
            return None

    async def check_category_similarity(self, category_name: str) -> Tuple[bool, Optional[str]]:
        """
        Checks exact and similar category names (AC-28, TS-26).
        Returns (is_similar, existing_suggestion).
        """
        name_clean = category_name.strip().lower()
        for cat in self._categories:
            cat_clean = cat.lower()
            if name_clean == cat_clean:
                return True, cat
            # Substring / similarity check
            if name_clean in cat_clean or cat_clean in name_clean:
                return True, cat
        return False, None

    async def add_category(self, category_name: str):
        if category_name not in self._categories:
            self._categories.append(category_name)

    async def get_categories(self) -> List[str]:
        return list(self._categories)

    # Draft Management (AC-29, TS-27)
    async def save_draft(self, user_email: str, draft_data: Dict) -> Dict:
        now = datetime.now(EASTERN_TZ)
        draft_id = f"DRAFT-{user_email}-{int(now.timestamp())}"
        deletion_date = (now + timedelta(days=7)).isoformat()
        
        draft_record = {
            "DraftID": draft_id,
            "UserEmail": user_email,
            "Data": draft_data,
            "CreatedAt": now.isoformat(),
            "AutomaticDeletionDate": deletion_date
        }
        
        async with self._lock:
            self._drafts[draft_id] = draft_record
        return draft_record

    async def get_user_drafts(self, user_email: str) -> List[Dict]:
        now = datetime.now(EASTERN_TZ).isoformat()
        return [
            d for d in self._drafts.values()
            if d["UserEmail"] == user_email and d["AutomaticDeletionDate"] > now
        ]

    async def delete_draft(self, draft_id: str):
        async with self._lock:
            self._drafts.pop(draft_id, None)
