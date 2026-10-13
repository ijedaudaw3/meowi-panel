import os
import uuid
import sqlite3
from datetime import datetime, timedelta
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse

# ---------- تنظیمات ----------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "panel.db")

ADMIN_USER = "admin"
ADMIN_PASS = "admin"
SUPPORT_ID = "@meov2ray"

app = FastAPI(title="ابر پنل میویی پاسارگارد")

# ---------- دیتابیس ----------
def init_db():
    conn = sqlite3.connect(DB_PATH)
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
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# ---------- HTML ها به صورت رشته ----------
def page_index():
    return f"""
    <!DOCTYPE html>
    <html lang="fa" dir="rtl">
    <head><meta charset="UTF-8"><title>ابر پنل میویی پاسارگارد</title>
    <style>
        body {{ font-family: Tahoma; background:#111; color:#eee; text-align:center; padding:50px; }}
        h1 {{ color:#ff4444; }}
        a {{ color:#4fc3f7; text-decoration:none; margin:0 10px; }}
        .box {{ background:#222; padding:30px; border-radius:15px; max-width:500px; margin:auto; }}
        input {{ padding:10px; margin:5px; width:80%; border-radius:8px; border:none; }}
        button {{ padding:10px 30px; background:#ff4444; color:white; border:none; border-radius:8px; cursor:pointer; }}
    </style></head><body>
    <div class="box">
        <h1>🔥 ابر پنل میویی پاسارگارد</h1>
        <p>بهترین پنل کانفیگ با کیفیت بالا</p>
        <a href="/login">ورود</a> | <a href="/register-page">ثبت‌نام</a>
        <hr><p>پشتیبانی: {SUPPORT_ID}</p>
    </div></body></html>
    """

def page_login():
    return f"""
    <!DOCTYPE html>
    <html lang="fa" dir="rtl">
    <head><meta charset="UTF-8"><title>ورود</title>
    <style>
        body {{ font-family: Tahoma; background:#111; color:#eee; text-align:center; padding:50px; }}
        .box {{ background:#222; padding:30px; border-radius:15px; max-width:400px; margin:auto; }}
        input {{ padding:10px; margin:5px; width:80%; border-radius:8px; border:none; }}
        button {{ padding:10px 30px; background:#ff4444; color:white; border:none; border-radius:8px; cursor:pointer; }}
        a {{ color:#4fc3f7; }}
    </style></head><body>
    <div class="box"><h2>ورود به پنل</h2>
        <form action="/login" method="post">
            <input name="username" placeholder="یوزرنیم" required><br>
            <input name="password" type="password" placeholder="رمز" required><br>
            <button type="submit">ورود</button>
        </form><br>
        <a href="/register-page">ثبت‌نام</a> | <a href="/">بازگشت</a>
        <p>پشتیبانی: {SUPPORT_ID}</p>
    </div></body></html>
    """

def page_register():
    return f"""
    <!DOCTYPE html>
    <html lang="fa" dir="rtl">
    <head><meta charset="UTF-8"><title>ثبت‌نام</title>
    <style>
        body {{ font-family: Tahoma; background:#111; color:#eee; text-align:center; padding:50px; }}
        .box {{ background:#222; padding:30px; border-radius:15px; max-width:400px; margin:auto; }}
        input {{ padding:10px; margin:5px; width:80%; border-radius:8px; border:none; }}
        button {{ padding:10px 30px; background:#ff4444; color:white; border:none; border-radius:8px; cursor:pointer; }}
        a {{ color:#4fc3f7; }}
    </style></head><body>
    <div class="box"><h2>ثبت‌نام</h2>
        <form action="/register" method="post">
            <input name="username" placeholder="یوزرنیم" required><br>
            <input name="password" type="password" placeholder="رمز" required><br>
            <button type="submit">ثبت‌نام</button>
        </form><br>
        <a href="/login">ورود</a> | <a href="/">بازگشت</a>
        <p>پشتیبانی: {SUPPORT_ID}</p>
    </div></body></html>
    """

def page_dashboard(user, config):
    return f"""
    <!DOCTYPE html>
    <html lang="fa" dir="rtl">
    <head><meta charset="UTF-8"><title>داشبورد</title>
    <style>
        body {{ font-family: Tahoma; background:#111; color:#eee; text-align:center; padding:30px; }}
        .box {{ background:#222; padding:25px; border-radius:15px; max-width:600px; margin:auto; }}
        .config {{ background:#000; padding:15px; border-radius:8px; word-break:break-all; direction:ltr; text-align:left; }}
        .info {{ display:flex; justify-content:space-between; padding:10px; border-bottom:1px solid #333; }}
        a {{ color:#4fc3f7; }}
    </style></head><body>
    <div class="box">
        <h2>👤 {user['username']}</h2>
        <div class="info"><span>حجم کل:</span><span>{user['data_limit'] // 1024**3} GB</span></div>
        <div class="info"><span>مصرف شده:</span><span>{user['used'] // 1024**3} GB</span></div>
        <div class="info"><span>انقضا:</span><span>{user['expire_at']}</span></div>
        <hr><h3>کانفیگ شما:</h3>
        <div class="config">{config}</div><br>
        <a href="/">بازگشت</a>
        <p>پشتیبانی: {SUPPORT_ID}</p>
    </div></body></html>
    """

def page_admin(users):
    rows = ""
    for u in users:
        rows += f"""
        <tr>
            <td>{u['id']}</td>
            <td>{u['username']}</td>
            <td>{u['uuid'][:8]}...</td>
            <td>{u['data_limit'] // 1024**3} GB</td>
            <td>{u['used'] // 1024**3} GB</td>
            <td>{u['expire_at']}</td>
        </tr>
        """
    return f"""
    <!DOCTYPE html>
    <html lang="fa" dir="rtl">
    <head><meta charset="UTF-8"><title>پنل ادمین</title>
    <style>
        body {{ font-family: Tahoma; background:#111; color:#eee; padding:30px; }}
        table {{ width:100%; border-collapse:collapse; background:#222; }}
        th, td {{ padding:10px; border:1px solid #333; text-align:center; }}
        th {{ background:#ff4444; }}
        a {{ color:#4fc3f7; }}
    </style></head><body>
    <h1>👑 پنل ادمین</h1>
    <table>
        <tr><th>ID</th><th>یوزرنیم</th><th>UUID</th><th>حجم کل</th><th>مصرف</th><th>انقضا</th></tr>
        {rows}
    </table><br>
    <a href="/">بازگشت به صفحه اصلی</a>
    <p>پشتیبانی: {SUPPORT_ID}</p>
    </body></html>
    """

# ---------- Routes ----------
@app.get("/", response_class=HTMLResponse)
async def home():
    return page_index()

@app.get("/login", response_class=HTMLResponse)
async def login_page():
    return page_login()

@app.get("/register-page", response_class=HTMLResponse)
async def register_page():
    return page_register()

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
        return HTMLResponse("<h3>این یوزرنیم قبلا گرفته شده</h3><a href='/register-page'>بازگشت</a>", status_code=400)
    conn.close()
    return RedirectResponse("/login", status_code=303)

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
    return HTMLResponse("<h3>یوزرنیم یا رمز اشتباهه</h3><a href='/login'>بازگشت</a>", status_code=401)

@app.get("/dashboard/{username}", response_class=HTMLResponse)
async def dashboard(username: str):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = c.fetchone()
    conn.close()
    if not user:
        return HTMLResponse("<h3>کاربر پیدا نشد</h3><a href='/'>بازگشت</a>", status_code=404)
    config_link = f"vless://{user['uuid']}@your-server:443?type=ws&security=tls#Meowi-{user['username']}"
    return page_dashboard(user, config_link)

@app.get("/admin", response_class=HTMLResponse)
async def admin_panel():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM users ORDER BY id DESC")
    users = c.fetchall()
    conn.close()
    return page_admin(users)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
