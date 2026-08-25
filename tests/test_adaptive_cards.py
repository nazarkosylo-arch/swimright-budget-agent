from bot.adaptive_cards import (
    build_submit_expense_card,
    build_approver_card,
    build_delegation_card,
    build_monthly_confirmation_card,
)

def test_submit_expense_card_structure():
    card = build_submit_expense_card(["Office Supplies", "Travel Expenses"])
    assert card["type"] == "AdaptiveCard"
    assert card["version"] == "1.4"
    assert len(card["actions"]) == 3

def test_monthly_confirmation_card_overflow():
    """
    TS-25 & AC-38: Monthly budget contains 20 expenses (> 15).
    Card shows summary only, full list posted as separate message.
    """
    expenses_20 = [
        {"ExpenseName": f"Item {i}", "AmountUSD": 10.0, "ExpenseCategory": "Office", "Program": "Office"}
        for i in range(20)
    ]
    card_overflow = build_monthly_confirmation_card("September'26", expenses_20)
    
    # Verify card contains warning message about >15 expenses
    text_blocks = [item.get("text", "") for item in card_overflow["body"] if item.get("type") == "TextBlock"]
    has_overflow_text = any("more than 15 expenses" in t for t in text_blocks)
    assert has_overflow_text is True

def test_monthly_confirmation_card_normal():
    """
    Budget with 5 expenses (<= 15) displays itemized list directly.
    """
    expenses_5 = [
        {"ExpenseName": f"Item {i}", "AmountUSD": 10.0, "ExpenseCategory": "Office", "Program": "Office"}
        for i in range(5)
    ]
    card_normal = build_monthly_confirmation_card("September'26", expenses_5)
    
    # Should contain container with itemized text blocks
    container = [item for item in card_normal["body"] if item.get("type") == "Container"][0]
    assert len(container["items"]) == 5
