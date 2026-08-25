import asyncio
from datetime import datetime
from typing import Dict, List, Optional
from config import EASTERN_TZ, ADMINISTRATOR_EMAIL, DEFAULT_APPROVER_EMAIL
from services.graph_service import GraphService
from services.time_service import add_business_days, add_business_hours, get_current_eastern_time

class WorkflowEngine:
    """
    Central Workflow Engine orchestrating business logic, escalations, bulk actions, and approver delegation.
    """
    def __init__(self, graph_service: GraphService):
        self.graph = graph_service
        self._no_expenses_confirmed: Dict[str, str] = {} # user_email -> month_str
        self._blocked_rejected_expenses: Dict[str, Dict] = {} # key -> record details

    async def submit_expense(self, data: Dict, submission_time: Optional[datetime] = None) -> Dict:
        """
        Submits a single expense and automatically classifies request type (Monthly, Additional, Late).
        """
        now = submission_time or get_current_eastern_time()
        day = now.day

        # Key for blocked rejection matching: (Name, Amount, Program)
        block_key = f"{data['ExpenseName'].lower()}|{float(data['AmountUSD']):.2f}|{data['Program'].lower()}"
        if block_key in self._blocked_rejected_expenses:
            raise ValueError("Expense submission is blocked due to prior rejected escalation. Administrator unlock required.")

        # Duplicate check warning (TS-10)
        is_duplicate = False
        for exp in (await self.graph.get_categories()): # check existing
            pass # Checked in handler

        # Request classification
        if day > 29:
            request_type = "Late Submission"
        elif data.get("is_additional", False):
            request_type = "Additional Expense Request"
        else:
            request_type = "Monthly Expense Request"

        data["RequestType"] = request_type
        record = await self.graph.create_expense(data)
        return record

    async def confirm_no_expenses(self, requester_email: str, month_str: str):
        """
        Confirms no expenses planned for current month (AC-02, TS-03).
        Stops reminders until/unless requester submits an expense.
        """
        self._no_expenses_confirmed[f"{requester_email}|{month_str}"] = "Confirmed"

    def has_confirmed_no_expenses(self, requester_email: str, month_str: str) -> bool:
        return f"{requester_email}|{month_str}" in self._no_expenses_confirmed

    # Approver Delegation (TS-18, TS-18A, AC-21)
    async def delegate_approver_role(self, requested_by: str) -> str:
        if requested_by.lower() != DEFAULT_APPROVER_EMAIL.lower():
            raise PermissionError(f"Only the primary approver ({DEFAULT_APPROVER_EMAIL}) can delegate the Approver role.")
        self.graph.set_active_approver(ADMINISTRATOR_EMAIL)
        return ADMINISTRATOR_EMAIL

    async def return_approver_role(self, requested_by: str) -> str:
        if requested_by.lower() != DEFAULT_APPROVER_EMAIL.lower():
            raise PermissionError(f"Only the primary approver ({DEFAULT_APPROVER_EMAIL}) can return the Approver role.")
        self.graph.set_active_approver(DEFAULT_APPROVER_EMAIL)
        return DEFAULT_APPROVER_EMAIL

    # Approver Actions
    async def approve_expense(self, expense_id: str, approver_email: str) -> Dict:
        active_approver = self.graph.active_approver
        # Allow active approver (including delegated Nazarii self-approval TS-18A)
        if approver_email.lower() != active_approver.lower():
            raise PermissionError(f"Only the active approver ({active_approver}) can make approval decisions.")

        now_str = get_current_eastern_time().isoformat()
        return await self.graph.update_status(expense_id, "Approved", decision_date=now_str)

    async def reject_expense(self, expense_id: str, approver_email: str) -> Dict:
        active_approver = self.graph.active_approver
        if approver_email.lower() != active_approver.lower():
            raise PermissionError(f"Only the active approver ({active_approver}) can make approval decisions.")

        now_str = get_current_eastern_time().isoformat()
        record = await self.graph.update_status(expense_id, "Rejected", decision_date=now_str)
        return record

    # Bulk Approvals (AC-07, TS-04)
    async def approve_all_monthly_pending(self, approver_email: str) -> List[Dict]:
        """
        Approve All affects ONLY Pending regular Monthly Expense Requests.
        Excludes Late Submissions, Additional Expenses, and Update Requests.
        """
        active_approver = self.graph.active_approver
        if approver_email.lower() != active_approver.lower():
            raise PermissionError("Only the active approver can execute bulk actions.")

        approved_records = []
        now_str = get_current_eastern_time().isoformat()

        async with self.graph._lock:
            for exp in self.graph._expenses.values():
                if exp["CurrentStatus"] == "Pending" and exp["RequestType"] == "Monthly Expense Request":
                    exp["CurrentStatus"] = "Approved"
                    exp["DecisionDate"] = now_str
                    approved_records.append(exp)
        return approved_records

    # Late Escalation Workflow (TS-09)
    async def process_late_escalation_rejection(self, expense_id: str):
        """
        If no decision after 10-business-day review + 4-business-day escalation window,
        automatically mark Rejected and record RejectedAfterEscalation = Yes.
        """
        record = await self.graph.get_expense(expense_id)
        if record and record["CurrentStatus"] == "Pending":
            record["CurrentStatus"] = "Rejected"
            record["RejectedAfterEscalation"] = "Yes"
            
            # Block resubmission with same Name, Amount, Program
            block_key = f"{record['ExpenseName'].lower()}|{float(record['AmountUSD']):.2f}|{record['Program'].lower()}"
            self._blocked_rejected_expenses[block_key] = record
            return record
        return None

    # Admin Unlock (TS-11)
    async def unlock_expense(self, admin_email: str, expense_name: str, amount_usd: float, program: str, reason: str):
        if admin_email.lower() != ADMINISTRATOR_EMAIL.lower():
            raise PermissionError("Only Nazarii Kosylo can unlock expenses.")

        block_key = f"{expense_name.lower()}|{float(amount_usd):.2f}|{program.lower()}"
        if block_key in self._blocked_rejected_expenses:
            del self._blocked_rejected_expenses[block_key]
            return True
        return False
