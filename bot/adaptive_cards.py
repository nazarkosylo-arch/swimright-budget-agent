from typing import Dict, List, Optional

def build_submit_expense_card(categories: List[str], translation_warning: Optional[str] = None) -> Dict:
    """
    Builds the Adaptive Card for submitting a single expense (Appendix A.1).
    Supports optional translation warning if user entered non-English text (AC-39, TS-38).
    """
    body = [
        {
            "type": "TextBlock",
            "text": "SwimRight Miami — Submit Expense",
            "weight": "Bolder",
            "size": "Medium"
        }
    ]

    if translation_warning:
        body.append({
            "type": "Container",
            "style": "warning",
            "items": [
                {
                    "type": "TextBlock",
                    "text": f"⚠️ {translation_warning}",
                    "wrap": True,
                    "color": "Warning",
                    "weight": "Bolder"
                }
            ]
        })

    category_choices = [{"title": cat, "value": cat} for cat in categories]
    category_choices.append({"title": "+ Add New Category...", "value": "__NEW__"})

    body.extend([
        {
            "type": "TextBlock",
            "text": "Expense Name *",
            "weight": "Bolder"
        },
        {
            "type": "Input.Text",
            "id": "expense_name",
            "placeholder": "Short descriptive name (in English)",
            "isRequired": True
        },
        {
            "type": "TextBlock",
            "text": "Amount (USD) *",
            "weight": "Bolder"
        },
        {
            "type": "Input.Number",
            "id": "amount_usd",
            "placeholder": "0.00",
            "isRequired": True
        },
        {
            "type": "TextBlock",
            "text": "Purchase Purpose *",
            "weight": "Bolder"
        },
        {
            "type": "Input.Text",
            "isMultiline": True,
            "id": "purchase_purpose",
            "placeholder": "Business reason or intended use",
            "isRequired": True
        },
        {
            "type": "TextBlock",
            "text": "Program / Department *",
            "weight": "Bolder"
        },
        {
            "type": "Input.ChoiceSet",
            "id": "program",
            "style": "compact",
            "choices": [
                {"title": "Office", "value": "Office"},
                {"title": "SwimFast", "value": "SwimFast"},
                {"title": "SwimRight / SwimSafe", "value": "SwimRight / SwimSafe"}
            ],
            "value": "Office"
        },
        {
            "type": "TextBlock",
            "text": "Expense Category *",
            "weight": "Bolder"
        },
        {
            "type": "Input.ChoiceSet",
            "id": "category",
            "style": "compact",
            "choices": category_choices,
            "value": categories[0] if categories else ""
        },
        {
            "type": "TextBlock",
            "text": "Optional Link",
            "weight": "Bolder"
        },
        {
            "type": "Input.Text",
            "id": "link",
            "placeholder": "Product link, quote, or invoice URL"
        }
    ])

    return {
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "type": "AdaptiveCard",
        "version": "1.4",
        "body": body,
        "actions": [
            {
                "type": "Action.Submit",
                "title": "Confirm & Submit",
                "data": {"action": "confirm_submit"}
            },
            {
                "type": "Action.Submit",
                "title": "Save as Draft",
                "data": {"action": "save_draft"}
            },
            {
                "type": "Action.Submit",
                "title": "Cancel",
                "data": {"action": "cancel"}
            }
        ]
    }

def build_approver_card(expense: Dict) -> Dict:
    """
    Builds the Approver Card for active approver decisions (Appendix A.2).
    """
    return {
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "type": "AdaptiveCard",
        "version": "1.4",
        "body": [
            {
                "type": "TextBlock",
                "text": f"Expense Approval Request — {expense['ExpenseID']}",
                "weight": "Bolder",
                "size": "Medium"
            },
            {
                "type": "FactSet",
                "facts": [
                    {"title": "Request Type:", "value": expense.get("RequestType", "Monthly Expense Request")},
                    {"title": "Submitted By:", "value": expense["SubmittedBy"]},
                    {"title": "Program:", "value": expense["Program"]},
                    {"title": "Expense Name:", "value": expense["ExpenseName"]},
                    {"title": "Amount (USD):", "value": f"${expense['AmountUSD']:.2f}"},
                    {"title": "Category:", "value": expense["ExpenseCategory"]},
                    {"title": "Purpose:", "value": expense["PurchasePurpose"]},
                    {"title": "Submitted Date:", "value": expense.get("SubmissionDate", "N/A")},
                    {"title": "Status:", "value": expense["CurrentStatus"]}
                ]
            }
        ],
        "actions": [
            {
                "type": "Action.Submit",
                "title": "Approve",
                "style": "positive",
                "data": {"action": "approve", "expense_id": expense["ExpenseID"]}
            },
            {
                "type": "Action.Submit",
                "title": "Reject",
                "style": "destructive",
                "data": {"action": "reject", "expense_id": expense["ExpenseID"]}
            },
            {
                "type": "Action.Submit",
                "title": "Request More Info",
                "data": {"action": "request_more_info", "expense_id": expense["ExpenseID"]}
            }
        ]
    }

def build_delegation_card(active_approver: str) -> Dict:
    """
    Builds Approver Delegation Card (Appendix A.2A). Available to Dmytro Kachurovskyy only.
    """
    is_dmytro_active = "dmytro" in active_approver.lower()
    
    actions = []
    if is_dmytro_active:
        actions.append({
            "type": "Action.Submit",
            "title": "Delegate Approver Role to Nazarii Kosylo",
            "data": {"action": "delegate_role"}
        })
    else:
        actions.append({
            "type": "Action.Submit",
            "title": "Return Approver Role to Dmytro Kachurovskyy",
            "data": {"action": "return_role"}
        })

    return {
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "type": "AdaptiveCard",
        "version": "1.4",
        "body": [
            {
                "type": "TextBlock",
                "text": "Approver Role Management",
                "weight": "Bolder",
                "size": "Medium"
            },
            {
                "type": "TextBlock",
                "text": f"Current Active Approver: **{active_approver}**",
                "wrap": True
            }
        ],
        "actions": actions
    }

def build_monthly_confirmation_card(month_str: str, expenses: List[Dict]) -> Dict:
    """
    Builds Monthly Budget Confirmation Card.
    If expenses > 15 lines, shows summary card only (AC-27, AC-38, TS-25).
    """
    total_amount = sum(e["AmountUSD"] for e in expenses)
    count = len(expenses)

    if count > 15:
        # Summary overflow card
        return {
            "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
            "type": "AdaptiveCard",
            "version": "1.4",
            "body": [
                {
                    "type": "TextBlock",
                    "text": f"Monthly Budget Summary — {month_str}",
                    "weight": "Bolder",
                    "size": "Medium"
                },
                {
                    "type": "FactSet",
                    "facts": [
                        {"title": "Budget Month:", "value": month_str},
                        {"title": "Total Expense Count:", "value": str(count)},
                        {"title": "Total Amount (USD):", "value": f"${total_amount:.2f}"},
                        {"title": "Status:", "value": "Pending Approval"}
                    ]
                },
                {
                    "type": "TextBlock",
                    "text": "ℹ️ This budget contains more than 15 expenses. The full itemized list has been posted as a separate message below.",
                    "wrap": True,
                    "isSubtle": True
                }
            ],
            "actions": [
                {
                    "type": "Action.Submit",
                    "title": "Confirm Budget",
                    "style": "positive",
                    "data": {"action": "confirm_monthly_budget"}
                },
                {
                    "type": "Action.Submit",
                    "title": "Edit",
                    "data": {"action": "edit_monthly_budget"}
                },
                {
                    "type": "Action.Submit",
                    "title": "Cancel",
                    "data": {"action": "cancel_monthly_budget"}
                }
            ]
        }

    # Itemized card (15 lines or fewer)
    items_body = []
    for exp in expenses:
        items_body.append({
            "type": "TextBlock",
            "text": f"• **{exp['ExpenseName']}** (${exp['AmountUSD']:.2f}) — {exp['ExpenseCategory']} ({exp['Program']})",
            "wrap": True
        })

    return {
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "type": "AdaptiveCard",
        "version": "1.4",
        "body": [
            {
                "type": "TextBlock",
                "text": f"Monthly Budget Confirmation — {month_str}",
                "weight": "Bolder",
                "size": "Medium"
            },
            {
                "type": "FactSet",
                "facts": [
                    {"title": "Expenses Count:", "value": str(count)},
                    {"title": "Total Amount (USD):", "value": f"${total_amount:.2f}"}
                ]
            },
            {
                "type": "Container",
                "items": items_body
            }
        ],
        "actions": [
            {
                "type": "Action.Submit",
                "title": "Confirm Budget",
                "style": "positive",
                "data": {"action": "confirm_monthly_budget"}
            },
            {
                "type": "Action.Submit",
                "title": "Edit",
                "data": {"action": "edit_monthly_budget"}
            },
            {
                "type": "Action.Submit",
                "title": "Cancel",
                "data": {"action": "cancel_monthly_budget"}
            }
        ]
    }
