import pytest
from datetime import datetime
from config import EASTERN_TZ, DEFAULT_APPROVER_EMAIL, ADMINISTRATOR_EMAIL
from services.graph_service import GraphService
from workflows.workflow_engine import WorkflowEngine

@pytest.mark.asyncio
async def test_ts03_confirm_no_expenses():
    graph = GraphService()
    engine = WorkflowEngine(graph)
    user = ADMINISTRATOR_EMAIL
    month = "September'26"

    await engine.confirm_no_expenses(user, month)
    assert engine.has_confirmed_no_expenses(user, month) is True

@pytest.mark.asyncio
async def test_ts04_approve_all_regular_monthly_only():
    """
    TS-04: Active approver has 5 Pending monthly requests, 2 Approved requests, 1 Additional request.
    Approve All changes ONLY the Pending regular monthly requests to Approved.
    """
    graph = GraphService()
    engine = WorkflowEngine(graph)

    # Create 5 pending monthly requests
    for i in range(5):
        await engine.submit_expense({
            "SubmittedBy": "requester1@test.com",
            "Program": "Office",
            "ExpenseName": f"Monthly Item {i}",
            "AmountUSD": 50.0,
            "PurchasePurpose": "Purpose",
            "ExpenseCategory": "Office Supplies"
        })

    # Create 1 Additional request
    await engine.submit_expense({
        "SubmittedBy": "requester2@test.com",
        "Program": "SwimFast",
        "ExpenseName": "Additional Item",
        "AmountUSD": 120.0,
        "PurchasePurpose": "Urgent purpose",
        "ExpenseCategory": "Travel Expenses",
        "is_additional": True
    })

    # Execute Approve All by default approver
    approved = await engine.approve_all_monthly_pending(DEFAULT_APPROVER_EMAIL)
    
    assert len(approved) == 5
    for record in approved:
        assert record["RequestType"] == "Monthly Expense Request"
        assert record["CurrentStatus"] == "Approved"

    # Additional request remains Pending
    add_record = await graph.get_expense("EXP-2026-08-006")
    assert add_record["RequestType"] == "Additional Expense Request"
    assert add_record["CurrentStatus"] == "Pending"

@pytest.mark.asyncio
async def test_ts07_and_ts08_request_classification():
    graph = GraphService()
    engine = WorkflowEngine(graph)

    # Regular day (e.g. 22nd)
    dt_22 = datetime(2026, 8, 22, 12, 0, tzinfo=EASTERN_TZ)
    exp_reg = await engine.submit_expense({
        "SubmittedBy": "requester1@test.com",
        "Program": "Office",
        "ExpenseName": "Paper",
        "AmountUSD": 20.0,
        "PurchasePurpose": "Office paper",
        "ExpenseCategory": "Office Supplies"
    }, submission_time=dt_22)
    assert exp_reg["RequestType"] == "Monthly Expense Request"

    # Late submission day (e.g. 30th)
    dt_30 = datetime(2026, 8, 30, 14, 0, tzinfo=EASTERN_TZ)
    exp_late = await engine.submit_expense({
        "SubmittedBy": "requester1@test.com",
        "Program": "Office",
        "ExpenseName": "Late Toner",
        "AmountUSD": 80.0,
        "PurchasePurpose": "Printer toner",
        "ExpenseCategory": "Office Supplies"
    }, submission_time=dt_30)
    assert exp_late["RequestType"] == "Late Submission"

@pytest.mark.asyncio
async def test_ts09_and_ts11_late_escalation_and_unlock():
    """
    TS-09 & TS-11: Late escalation rejection sets RejectedAfterEscalation = Yes.
    Subsequent submission with same name/amount/program is blocked until Admin unlocks.
    """
    graph = GraphService()
    engine = WorkflowEngine(graph)

    dt_30 = datetime(2026, 8, 30, 14, 0, tzinfo=EASTERN_TZ)
    exp = await engine.submit_expense({
        "SubmittedBy": "requester1@test.com",
        "Program": "Office",
        "ExpenseName": "Special Software",
        "AmountUSD": 500.0,
        "PurchasePurpose": "Annual license",
        "ExpenseCategory": "Software & Subscriptions"
    }, submission_time=dt_30)

    # Escalation rejection
    rejected_rec = await engine.process_late_escalation_rejection(exp["ExpenseID"])
    assert rejected_rec["CurrentStatus"] == "Rejected"
    assert rejected_rec["RejectedAfterEscalation"] == "Yes"

    # Attempt resubmitting same expense -> should raise ValueError (TS-11)
    with pytest.raises(ValueError, match="blocked due to prior rejected escalation"):
        await engine.submit_expense({
            "SubmittedBy": "requester1@test.com",
            "Program": "Office",
            "ExpenseName": "Special Software",
            "AmountUSD": 500.0,
            "PurchasePurpose": "Retry annual license",
            "ExpenseCategory": "Software & Subscriptions"
        }, submission_time=dt_30)

    # Admin unlocks expense
    unlocked = await engine.unlock_expense(
        admin_email=ADMINISTRATOR_EMAIL,
        expense_name="Special Software",
        amount_usd=500.0,
        program="Office",
        reason="Approved after review"
    )
    assert unlocked is True

    # Resubmission succeeds after unlock
    exp_retry = await engine.submit_expense({
        "SubmittedBy": "requester1@test.com",
        "Program": "Office",
        "ExpenseName": "Special Software",
        "AmountUSD": 500.0,
        "PurchasePurpose": "Retry annual license",
        "ExpenseCategory": "Software & Subscriptions"
    }, submission_time=dt_30)
    assert exp_retry["ExpenseID"] is not None

@pytest.mark.asyncio
async def test_ts18_and_ts18a_approver_delegation_and_self_approval():
    """
    TS-18 & TS-18A: Approver delegates role to Admin.
    Admin can approve pending requests, including self-approval of his own request.
    Only Approver can return the role.
    """
    graph = GraphService()
    engine = WorkflowEngine(graph)

    # Approver delegates role
    new_approver = await engine.delegate_approver_role(DEFAULT_APPROVER_EMAIL)
    assert new_approver == ADMINISTRATOR_EMAIL
    assert graph.active_approver == ADMINISTRATOR_EMAIL

    # Unauthorized user trying to return raises PermissionError
    with pytest.raises(PermissionError):
        await engine.return_approver_role("requester1@test.com")

    # Admin submits his own request and approves it (Self-approval TS-18A)
    admin_exp = await engine.submit_expense({
        "SubmittedBy": ADMINISTRATOR_EMAIL,
        "Program": "SwimFast",
        "ExpenseName": "SwimFast Equipment",
        "AmountUSD": 300.0,
        "PurchasePurpose": "Pool gear",
        "ExpenseCategory": "Equipment & Maintenance"
    })

    approved = await engine.approve_expense(admin_exp["ExpenseID"], ADMINISTRATOR_EMAIL)
    assert approved["CurrentStatus"] == "Approved"

    # Approver returns the role
    returned = await engine.return_approver_role(DEFAULT_APPROVER_EMAIL)
    assert returned == DEFAULT_APPROVER_EMAIL
    assert graph.active_approver == DEFAULT_APPROVER_EMAIL
