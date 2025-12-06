# src/app/main.py
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse

from src.app.config import settings
from src.app.services.amo_client import AmoClient
from src.app.services.token_store import FileTokenStore

app = FastAPI()

token_store = FileTokenStore("/app/tokens/token.json")
amo_client = AmoClient(token_store=token_store)


@app.get("/amo/login")
def amo_login():
    # Редиректим пользователя в Amo для авторизации
    return RedirectResponse(url=amo_client.get_auth_url())

@app.get("/amo/callback")
def amo_callback(code: str = None, error: str = None):
    if error:
        raise HTTPException(status_code=400, detail=f"Amo error: {error}")
    if not code:
        raise HTTPException(status_code=400, detail="No code provided")

    data = amo_client.exchange_code(code)
    return JSONResponse({"status": "ok", "tokens_saved": True, "data": data})

@app.post("/amo/refresh")
def manual_refresh():
    amo_client.refresh_tokens()
    return {"status": "ok", "message": "tokens refreshed"}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/amo/account")
def amo_account():
    resp = amo_client.api_call("GET", "/api/v4/account")
    return resp.json()

from pydantic import BaseModel

class NoteInput(BaseModel):
    text: str


@app.post("/amo/lead/{lead_id}/comment")
def add_comment(lead_id: int, body: NoteInput):
    result = amo_client.add_note_to_lead(lead_id, body.text)
    return result
