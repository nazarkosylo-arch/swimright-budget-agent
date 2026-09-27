import asyncio
import httpx
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Dict, List, Optional
from config import DEFAULT_APPROVER_EMAIL, ADMINISTRATOR_EMAIL, INITIAL_PARTICIPANTS
from services.graph_service import GraphService
from services.translation_service import translate_to_english
from workflows.workflow_engine import WorkflowEngine

app = FastAPI(
    title="SwimRight Miami Budget Approval Agent API",
    version="1.3",
    description="Backend API and Teams bot service for SwimRight Miami Budget Approval Assistant"
)

# Global Service Instances
graph_service = GraphService()
workflow_engine = WorkflowEngine(graph_service)

# Keep-Alive Self Ping Loop to prevent Render free instance from sleeping
async def keep_alive_background_ping():
    await asyncio.sleep(10)
    url = "https://swimright-budget-agent.onrender.com/health"
    async with httpx.AsyncClient(timeout=10.0) as client:
        while True:
            try:
                await client.get(url)
            except Exception:
                pass
            await asyncio.sleep(180) # Every 3 minutes

@app.on_event("startup")
async def start_keep_alive():
    asyncio.create_task(keep_alive_background_ping())

# Mount static directory for standalone Web App
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.middleware("http")
async def add_no_cache_header(request: Request, call_next):
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

@app.get("/", response_class=FileResponse)
async def read_index():
    return FileResponse("static/index.html", headers={
        "Cache-Control": "no-cache, no-store, must-revalidate",
        "Pragma": "no-cache",
        "Expires": "0"
    })

class LoginSchema(BaseModel):
    email: str
    password: str

class ExpenseSubmitSchema(BaseModel):
    SubmittedBy: str
    Program: str
    ExpenseName: str
    AmountUSD: float
    PurchasePurpose: str
    ExpenseCategory: str
    OptionalLink: Optional[str] = ""
    is_additional: Optional[bool] = False

class StatusUpdateSchema(BaseModel):
    status: str

SHARED_PASSWORD = "Password123!"

@app.post("/api/auth/login")
async def login_endpoint(payload: LoginSchema):
    email_clean = payload.email.strip().lower()
    
    # Check shared password
    if payload.password != SHARED_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid shared password.")

    user_info = INITIAL_PARTICIPANTS.get(email_clean)
    
    if not user_info:
        # Match by name or username
        for email, info in INITIAL_PARTICIPANTS.items():
            if email_clean in info["name"].lower() or email_clean in email or email_clean in info["name"].split()[0].lower():
                user_info = info
                email_clean = email
                break

    if not user_info:
        # Default fallback to Dmytro if generic username
        user_info = INITIAL_PARTICIPANTS["approver@test.com"]
        email_clean = "approver@test.com"

    return {
        "success": True,
        "email": email_clean,
        "name": user_info["name"],
        "role": user_info["role"],
        "department": user_info["department"]
    }

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "SwimRight Budget Approval Agent",
        "version": "1.3",
        "active_approver": graph_service.active_approver
    }

@app.post("/api/expenses/submit")
async def submit_expense_endpoint(payload: ExpenseSubmitSchema):
    """
    Submits a new expense, performs auto-translation if needed (AC-39, TS-38),
    and creates the operational record.
    """
    translated_name, name_was_trans = await translate_to_english(payload.ExpenseName)
    translated_purpose, purpose_was_trans = await translate_to_english(payload.PurchasePurpose)

    data = payload.model_dump()
    data["ExpenseName"] = translated_name
    data["PurchasePurpose"] = translated_purpose

    try:
        record = await workflow_engine.submit_expense(data)
        return {
            "success": True,
            "record": record,
            "was_translated": name_was_trans or purpose_was_trans
        }
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err))

@app.get("/api/expenses")
async def get_all_expenses_endpoint():
    return list(graph_service._expenses.values())

@app.get("/api/expenses/{expense_id}")
async def get_expense_endpoint(expense_id: str):
    record = await graph_service.get_expense(expense_id)
    if not record:
        raise HTTPException(status_code=404, detail="Expense record not found")
    return record

@app.post("/api/clear-all-expenses")
@app.delete("/api/clear-all-expenses")
async def clear_all_expenses_endpoint():
    await graph_service.clear_all_expenses()
    return {"success": True, "message": "All expenses cleared."}

@app.delete("/api/expenses/{expense_id}")
async def delete_expense_endpoint(expense_id: str):
    deleted = await graph_service.delete_expense(expense_id)
    return {"success": True, "expense_id": expense_id}

@app.patch("/api/expenses/{expense_id}/status")
async def update_expense_status_endpoint(expense_id: str, payload: StatusUpdateSchema):
    record = await graph_service.update_status(expense_id, payload.status)
    if not record:
        raise HTTPException(status_code=404, detail="Expense record not found")
    return {"success": True, "record": record}

@app.post("/api/approver/delegate")
async def delegate_role_endpoint(requested_by: str):
    try:
        active = await workflow_engine.delegate_approver_role(requested_by)
        return {"success": True, "active_approver": active}
    except PermissionError as err:
        raise HTTPException(status_code=403, detail=str(err))

@app.post("/api/approver/return")
async def return_role_endpoint(requested_by: str):
    try:
        active = await workflow_engine.return_approver_role(requested_by)
        return {"success": True, "active_approver": active}
    except PermissionError as err:
        raise HTTPException(status_code=403, detail=str(err))

@app.post("/api/messages")
async def bot_messages_webhook(request: Request):
    """
    Teams Bot webhook receiving Adaptive Card actions and channel messages.
    """
    body = await request.json()
    activity_type = body.get("type", "message")
    
    if activity_type == "message":
        data = body.get("value", {})
        action = data.get("action")
        
        if action == "approve":
            expense_id = data.get("expense_id")
            user_email = body.get("from", {}).get("id", DEFAULT_APPROVER_EMAIL)
            record = await workflow_engine.approve_expense(expense_id, user_email)
            return {"type": "message", "text": f"✅ Expense {expense_id} approved."}
            
        elif action == "reject":
            expense_id = data.get("expense_id")
            user_email = body.get("from", {}).get("id", DEFAULT_APPROVER_EMAIL)
            record = await workflow_engine.reject_expense(expense_id, user_email)
            return {"type": "message", "text": f"❌ Expense {expense_id} rejected."}

    return {"type": "message", "text": "Activity received."}
