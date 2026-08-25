import pytest
import asyncio
from services.graph_service import GraphService

@pytest.mark.asyncio
async def test_concurrent_expense_id_generation():
    """
    TS-21 & TS-22: Liza and Denys confirm expenses at the exact same moment.
    Two atomic records with unique Expense IDs are created without lost or overwritten data.
    """
    service = GraphService()
    
    # Simulate 50 concurrent expense creations
    tasks = [
        service.create_expense({
            "SubmittedBy": f"user{i}@test.com",
            "Program": "Office",
            "ExpenseName": f"Item {i}",
            "AmountUSD": 100 + i,
            "PurchasePurpose": "Test purpose",
            "ExpenseCategory": "Office Supplies"
        })
        for i in range(50)
    ]
    
    results = await asyncio.gather(*tasks)
    
    expense_ids = [r["ExpenseID"] for r in results]
    
    # Assert all 50 Expense IDs are unique
    assert len(expense_ids) == 50
    assert len(set(expense_ids)) == 50
    
    # Verify sequential format EXP-YYYY-MM-001 ... EXP-YYYY-MM-050
    for i, exp_id in enumerate(sorted(expense_ids), 1):
        assert exp_id.endswith(f"-{i:03d}")

@pytest.mark.asyncio
async def test_category_similarity_warning():
    """
    TS-26: User attempts to create Travel Expenses when Travel already exists.
    Agent warns of similarity and suggests Travel.
    """
    service = GraphService()
    
    # Exact match check
    is_similar, suggestion = await service.check_category_similarity("Office Supplies")
    assert is_similar is True
    assert suggestion == "Office Supplies"

    # Substring / similar match check
    is_similar, suggestion = await service.check_category_similarity("Office")
    assert is_similar is True
    assert suggestion == "Office Supplies"

    # Completely new category
    is_similar, suggestion = await service.check_category_similarity("Unicorn Expenses")
    assert is_similar is False
    assert suggestion is None

@pytest.mark.asyncio
async def test_my_drafts_lifecycle():
    """
    TS-27: User saves a draft, checks My Drafts, and deletes a draft.
    """
    service = GraphService()
    user_email = "requester1@test.com"
    
    draft = await service.save_draft(user_email, {"ExpenseName": "Draft Item", "AmountUSD": 50})
    draft_id = draft["DraftID"]

    # Verify user drafts list
    user_drafts = await service.get_user_drafts(user_email)
    assert len(user_drafts) == 1
    assert user_drafts[0]["DraftID"] == draft_id

    # Verify other user cannot see this draft (isolation)
    other_drafts = await service.get_user_drafts("requester2@test.com")
    assert len(other_drafts) == 0

    # Delete draft
    await service.delete_draft(draft_id)
    user_drafts_after = await service.get_user_drafts(user_email)
    assert len(user_drafts_after) == 0
