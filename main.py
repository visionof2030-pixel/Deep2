# main.py
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import os
import itertools
import google.generativeai as genai

from database import init_db, get_connection
from create_key import create_key
from security import activation_required

# ================== إعدادات عامة ==================

ADMIN_TOKEN = os.getenv("ADMIN_TOKEN")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db()

# ================== النماذج ==================

class AskReq(BaseModel):
    prompt: str

class GenerateKeyReq(BaseModel):
    expires_at: str | None = None
    usage_limit: int | None = None

# ================== مفاتيح Gemini ==================

api_keys = [
    os.getenv("GEMINI_API_KEY_1"),
    os.getenv("GEMINI_API_KEY_2"),
    os.getenv("GEMINI_API_KEY_3"),
    os.getenv("GEMINI_API_KEY_4"),
    os.getenv("GEMINI_API_KEY_5"),
    os.getenv("GEMINI_API_KEY_6"),
    os.getenv("GEMINI_API_KEY_7"),
]

api_keys = [k for k in api_keys if k]

if not api_keys:
    raise RuntimeError("No GEMINI API keys found")

key_cycle = itertools.cycle(api_keys)

def get_api_key():
    return next(key_cycle)

# ================== حماية الأدمن ==================

def admin_auth(x_admin_token: str = Header(...)):
    if x_admin_token != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")

# ================== Health (محمي) ==================

@app.get("/health", dependencies=[Depends(activation_required)])
def health():
    return {"status": "active"}

# ================== AI Endpoint ==================

@app.post("/ask", dependencies=[Depends(activation_required)])
def ask(req: AskReq):
    try:
        genai.configure(api_key=get_api_key())
        model = genai.GenerativeModel("models/gemini-2.5-flash-lite")
        response = model.generate_content(req.prompt)
        return {"answer": response.text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ================== Admin APIs ==================

@app.post("/admin/generate", dependencies=[Depends(admin_auth)])
def admin_generate(req: GenerateKeyReq):
    code = create_key(req.expires_at, req.usage_limit)
    return {"code": code}

@app.get("/admin/codes", dependencies=[Depends(admin_auth)])
def admin_codes():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, code, is_active, usage_count, expires_at
        FROM activation_codes
    """)
    rows = cur.fetchall()
    conn.close()
    return [
        {
            "id": r[0],
            "code": r[1],
            "active": bool(r[2]),
            "usage": r[3],
            "expires_at": r[4],
        }
        for r in rows
    ]

@app.put("/admin/code/{code_id}/toggle", dependencies=[Depends(admin_auth)])
def admin_toggle(code_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE activation_codes SET is_active = CASE WHEN is_active=1 THEN 0 ELSE 1 END WHERE id=?",
        (code_id,)
    )
    conn.commit()
    conn.close()
    return {"status": "ok"}

@app.delete("/admin/code/{code_id}", dependencies=[Depends(admin_auth)])
def admin_delete(code_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM activation_codes WHERE id=?", (code_id,))
    conn.commit()
    conn.close()
    return {"status": "deleted"}

# ================== Admin Panel ==================

@app.get("/admin", response_class=HTMLResponse)
def admin_page():
    return """
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Admin Panel</title>
<style>
body{font-family:sans-serif;padding:10px}
input,button{width:100%;padding:10px;margin:5px 0}
table{width:100%;border-collapse:collapse}
td,th{border:1px solid #ccc;padding:5px;font-size:12px}
</style>
</head>
<body>
<h3>Admin Panel</h3>
<input id="token" placeholder="Admin Token">
<button onclick="saveToken()">Save Token</button>
<button onclick="generate()">Generate Key</button>
<table id="tbl"></table>
<script>
const api='/admin';
function saveToken(){localStorage.setItem('t',document.getElementById('token').value);load();}
function h(){return {'X-Admin-Token':localStorage.getItem('t')}}
function generate(){
fetch(api+'/generate',{method:'POST',headers:{...h(),'Content-Type':'application/json'},body:'{}'}).then(load)
}
function toggle(id){
fetch(api+'/code/'+id+'/toggle',{method:'PUT',headers:h()}).then(load)
}
function del(id){
fetch(api+'/code/'+id,{method:'DELETE',headers:h()}).then(load)
}
function load(){
fetch(api+'/codes',{headers:h()}).then(r=>r.json()).then(d=>{
let t='<tr><th>Code</th><th>Use</th><th>Active</th><th>Action</th></tr>';
d.forEach(c=>{
t+=`<tr>
<td>${c.code}</td>
<td>${c.usage}</td>
<td>${c.active}</td>
<td>
<button onclick="toggle(${c.id})">Toggle</button>
<button onclick="del(${c.id})">Del</button>
</td>
</tr>`;
});
document.getElementById('tbl').innerHTML=t;
})
}
load();
</script>
</body>
</html>
"""