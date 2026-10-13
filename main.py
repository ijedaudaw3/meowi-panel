import os
import uuid
import sqlite3
from datetime import datetime, timedelta
from fastapi import FastAPI, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

app = FastAPI(title="ابر پنل میویی پاسارگارد")
templates = Jinja2Templates(directory="templates")

ADMIN_USER = "admin"
ADMIN_PASS = "admin"  # بعدا عوض کن
SUPPORT_ID = "@meov2ray"

# ---------- دیتابیس ----------
def init_db():
    conn = sqlite3.connect("panel.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            uuid TEXT,
            data_limit INTEGER DEFAULT 0,
            used INTEGER DEFAULT 0,
            expire_at TEXT,
            created_at TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

def get_db():
    conn = sqlite3.connect("panel.db")
    conn.row_factory = sqlite3.Row
    return conn

# ---------- صفحه اصلی ----------
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "support": SUPPORT_ID
    })

# ---------- ثبت‌نام ----------
@app.post("/register")
async def register(username: str = Form(...), password: str = Form(...)):
    conn = get_db()
    c = conn.cursor()
    try:
        user_uuid = str(uuid.uuid4())
        expire = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        c.execute(
            "INSERT INTO users (username, password, uuid, data_limit, expire_at, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (username, password, user_uuid, 50 * 1024**3, expire, datetime.now().strftime("%Y-%m-%d"))
        )
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(status_code=400, detail="این یوزرنیم قبلا گرفته شده")
    conn.close()
    return RedirectResponse("/login", status_code=303)

# ---------- صفحه ورود ----------
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def login(username: str = Form(...), password: str = Form(...)):
    if username == ADMIN_USER and password == ADMIN_PASS:
        return RedirectResponse("/admin", status_code=303)
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
    user = c.fetchone()
    conn.close()
    if user:
        return RedirectResponse(f"/dashboard/{user['username']}", status_code=303)
    raise HTTPException(status_code=401, detail="یوزرنیم یا رمز اشتباهه")

# ---------- داشبورد کاربر ----------
@app.get("/dashboard/{username}", response_class=HTMLResponse)
async def dashboard(request: Request, username: str):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = c.fetchone()
    conn.close()
    if not user:
        raise HTTPException(status_code=404, detail="کاربر پیدا نشد")
    
    # اینجا بعدا کانفیگ واقعی ساخته میشه
    config_link = f"vless://{user['uuid']}@your-server:443?type=ws&security=tls#Meowi-{user['username']}"
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "user": user,
        "config": config_link,
        "support": SUPPORT_ID
    })

# ---------- پنل ادمین ----------
@app.get("/admin", response_class=HTMLResponse)
async def admin_panel(request: Request):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM users ORDER BY id DESC")
    users = c.fetchall()
    conn.close()
    return templates.TemplateResponse("admin.html", {
        "request": request,
        "users": users,
        "support": SUPPORT_ID
    })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
