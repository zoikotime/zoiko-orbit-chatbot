from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import json, smtplib, re, time, os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from fastapi import Form
from datetime import datetime

app = FastAPI()

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── EMAIL CONFIG — env vars first, hardcoded fallback ─────────────────────────
SMTP_HOST     = os.getenv("SMTP_HOST",     "smtpout.secureserver.net")
SMTP_PORT     = int(os.getenv("SMTP_PORT", "465"))
SMTP_USER     = os.getenv("SMTP_USER",     "support@zoikogroup.com")
SMTP_PASS     = os.getenv("SMTP_PASS",     "NoxxMC26070%!LGM")
SUPPORT_EMAIL = os.getenv("SUPPORT_EMAIL", "info@zoikoorbit.com")

print(f"\n📧 EMAIL CONFIGURATION:")
print(f"   SMTP Host: {SMTP_HOST}")
print(f"   SMTP Port: {SMTP_PORT}")
print(f"   From Email: {SMTP_USER}")
print(f"   Support Email: {SUPPORT_EMAIL}")

# ── STATIC FRONTEND - MULTIPLE PATH STRATEGIES ─────────────────────────────────
possible_paths = [
    Path(__file__).resolve().parent.parent / "frontend",
    Path(__file__).resolve().parent / "frontend",
    Path("frontend"),
    Path("../frontend"),
]

frontend_path = None
for path in possible_paths:
    if path.exists() and (path / "index.html").exists():
        frontend_path = path
        print(f"✅ Frontend found at: {frontend_path}")
        break

if not frontend_path:
    print(f"⚠️  Frontend not found. Checked:")
    for path in possible_paths:
        print(f"   - {path}")
    frontend_path = possible_paths[0]

# ── MODELS ────────────────────────────────────────────────────────────────────
class CallbackRequest(BaseModel):
    name:  str
    email: str
    phone: str
    issue: str

class Message(BaseModel):
    message: str

# ── HELPERS ───────────────────────────────────────────────────────────────────
def gen_ref_id():
    """Generate Zoiko Orbit reference ID from timestamp"""
    return "ORB-" + str(int(time.time() * 1000))[-6:]

def valid_email(e: str) -> bool:
    """Validate email format — strict check matching the frontend"""
    return bool(re.match(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$", e))

def valid_phone(p: str) -> bool:
    """Validate phone number (10-15 digits)"""
    digits = re.sub(r"\D", "", p)
    return 10 <= len(digits) <= 15

def escape_html(s: str) -> str:
    """Escape HTML special characters"""
    return (s.replace("&","&amp;").replace("<","&lt;")
             .replace(">","&gt;").replace('"',"&quot;").replace("'","&#039;"))

def send_email(to_addr: str, subject: str, html_body: str, reply_to: str = None):
    print(f"\n📧 Sending email to: {to_addr}")
    print(f"   Subject: {subject}")
    print(f"   Via: {SMTP_HOST}:{SMTP_PORT}")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = SMTP_USER
    msg["To"]      = to_addr
    if reply_to:
        msg["Reply-To"] = reply_to
    msg.attach(MIMEText(html_body, "html"))

    # Single SSL connection — matches port 465 config
    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=10) as server:
        print("   Connected! Logging in...")
        server.login(SMTP_USER, SMTP_PASS)
        print("   Logged in! Sending email...")
        server.sendmail(SMTP_USER, to_addr, msg.as_string())
        print(f"   ✅ Email sent successfully to {to_addr}")

from fastapi.responses import HTMLResponse

@app.get("/send-request", response_class=HTMLResponse)
async def send_request_form():
    return """
    <html>
    <head>
      <title>Zoiko Orbit — Callback Request</title>
      <style>
        body { font-family: Arial, sans-serif; max-width: 500px; margin: 40px auto; padding: 20px; background: #f9f9f9; }
        h2 { color: #fc8019; }
        label { font-size: 13px; color: #555; font-weight: 600; }
        input, textarea { width: 100%; padding: 9px 11px; margin: 5px 0 14px;
                          border: 1px solid #ddd; border-radius: 6px; font-size: 14px;
                          box-sizing: border-box; }
        input:focus, textarea:focus { border-color: #fc8019; outline: none;
                                       box-shadow: 0 0 0 3px rgba(252,128,25,0.1); }
        button { background: linear-gradient(135deg, #fc8019, #e8722a); color: #fff;
                 border: none; padding: 11px 28px; border-radius: 8px; cursor: pointer;
                 font-size: 14px; font-weight: 700; }
        button:hover { background: #e8722a; }
      </style>
    </head>
    <body>
      <h2>🎧 Zoiko Orbit — Callback Request</h2>
      <form method="post" action="/send-request">
        <label>Full Name</label>
        <input name="name" placeholder="Your full name"><br>
        <label>Email Address</label>
        <input name="email" type="email" placeholder="your@email.com"><br>
        <label>Phone Number</label>
        <input name="phone" placeholder="10-15 digit phone number"><br>
        <label>How can we help?</label>
        <textarea name="issue" rows="4" placeholder="Describe your request..."></textarea><br>
        <button type="submit">📨 Send Request</button>
      </form>
    </body>
    </html>
    """

# ── /send-request ─────────────────────────────────────────────────────────────
@app.post("/send-request")
async def send_request(data: CallbackRequest):

    # ── Validation ────────────────────────────────────────────────────────────
    if not data.name.strip():
        return JSONResponse({"success": False, "message": "Name is required"})
    if not data.email.strip():
        return JSONResponse({"success": False, "message": "Email is required"})
    if not valid_email(data.email):
        return JSONResponse({"success": False, "message": "Invalid email address (e.g. user@example.com)"})
    if not data.phone.strip():
        return JSONResponse({"success": False, "message": "Phone number is required"})
    if not valid_phone(data.phone):
        return JSONResponse({"success": False, "message": "Phone number must be 10-15 digits"})
    if not data.issue.strip():
        return JSONResponse({"success": False, "message": "Please describe how we can help"})

    # ── Prepare data ──────────────────────────────────────────────────────────
    ref_id       = gen_ref_id()
    timestamp    = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    clean_name   = escape_html(data.name.strip())
    clean_email  = data.email.strip()
    clean_phone  = data.phone.strip()
    phone_digits = re.sub(r'\D', '', clean_phone)
    clean_issue  = escape_html(data.issue.strip()).replace("\n", "<br>")
    first_name   = clean_name.split()[0]

    # ── Email to support team ─────────────────────────────────────────────────
    support_html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <style>
    * {{ margin: 0; padding: 0; }}
    body {{ font-family: 'Segoe UI', Arial, sans-serif; color: #333; line-height: 1.6; background: #f4f4f4; }}
    .container {{ max-width: 600px; margin: 20px auto; padding: 0; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.08); }}
    .header {{
      background: linear-gradient(135deg, #fc8019, #e8722a);
      color: white; padding: 28px 25px; text-align: center;
    }}
    .header h2 {{ margin: 0; font-size: 22px; }}
    .header-sub {{ font-size: 12px; opacity: 0.9; margin-top: 5px; }}
    .content {{ background: #f9f9f9; padding: 25px; border: 1px solid #ddd; border-top: none; }}
    .field {{ margin-bottom: 18px; }}
    .label {{
      font-weight: 700; color: #fc8019; margin-bottom: 6px;
      font-size: 11px; text-transform: uppercase; letter-spacing: 0.6px;
    }}
    .value {{
      color: #333; padding: 11px 13px; background: white;
      border-left: 4px solid #fc8019; border-radius: 3px; font-size: 14px;
    }}
    .footer {{
      background: #fff; padding: 18px 25px; text-align: center;
      font-size: 12px; color: #888; border-top: 1px solid #eee;
    }}
    .ref-id {{ color: #fc8019; font-weight: bold; }}
    a {{ color: #fc8019; text-decoration: none; }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h2>🎧 New Callback Request</h2>
      <div class="header-sub">Zoiko Orbit — Oriko AI Assistant</div>
    </div>
    <div class="content">
      <div class="field">
        <div class="label">👤 Customer Name</div>
        <div class="value">{clean_name}</div>
      </div>
      <div class="field">
        <div class="label">📧 Email Address</div>
        <div class="value"><a href="mailto:{clean_email}">{clean_email}</a></div>
      </div>
      <div class="field">
        <div class="label">📱 Phone Number</div>
        <div class="value"><a href="tel:{phone_digits}">{clean_phone}</a></div>
      </div>
      <div class="field">
        <div class="label">❓ Request Details</div>
        <div class="value" style="white-space: pre-wrap;">{clean_issue}</div>
      </div>
    </div>
    <div class="footer">
      <p><span class="ref-id">Reference: {ref_id}</span> &nbsp;|&nbsp; Received: {timestamp}</p>
      <p style="margin-top: 8px;">© 2026 Zoiko Orbit — <a href="https://zoikoorbit.com">zoikoorbit.com</a></p>
    </div>
  </div>
</body>
</html>"""

    # ── Confirmation email to customer ────────────────────────────────────────
    user_html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <style>
    * {{ margin: 0; padding: 0; }}
    body {{ font-family: 'Segoe UI', Arial, sans-serif; color: #333; line-height: 1.6; background: #f4f4f4; }}
    .container {{ max-width: 600px; margin: 20px auto; padding: 0; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.08); }}
    .header {{
      background: linear-gradient(135deg, #fc8019, #e8722a);
      color: white; padding: 40px 25px; text-align: center;
    }}
    .checkmark {{ font-size: 52px; display: block; margin-bottom: 12px; }}
    .header h2 {{ margin: 0; font-size: 26px; }}
    .header-brand {{ font-size: 13px; opacity: 0.85; margin-top: 6px; }}
    .content {{ background: white; padding: 30px; border: 1px solid #eee; border-top: none; }}
    .content p {{ margin: 14px 0; font-size: 14px; }}
    .info-box {{
      background: #fff4e6; border-left: 4px solid #fc8019;
      padding: 15px 18px; margin: 20px 0; border-radius: 3px;
    }}
    .ref-box {{
      background: #fffbf2; border: 2px solid #fc8019;
      padding: 18px; border-radius: 8px; margin: 20px 0; text-align: center;
    }}
    .ref-id {{
      font-size: 22px; color: #fc8019; font-weight: bold;
      display: block; margin: 8px 0; font-family: 'Courier New', monospace;
    }}
    .quick-contact {{ background: #f8f8f8; padding: 20px; border-radius: 8px; margin: 20px 0; }}
    .contact-item {{ margin: 9px 0; padding: 8px 0; border-bottom: 1px solid #ebebeb; font-size: 13px; }}
    .contact-item:last-child {{ border-bottom: none; }}
    .contact-label {{ color: #fc8019; font-weight: 700; }}
    a {{ color: #fc8019; text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
    .footer {{
      background: #f9f9f9; padding: 22px 25px; text-align: center;
      font-size: 12px; color: #888; border-top: 1px solid #eee;
    }}
    .highlight {{ color: #fc8019; font-weight: bold; }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <span class="checkmark">✅</span>
      <h2>Request Received!</h2>
      <div class="header-brand">Zoiko Orbit — Global eSIM Provider 🌍</div>
    </div>

    <div class="content">
      <p style="font-size: 16px;">Hi <span class="highlight">{first_name}</span>,</p>

      <p>Thank you for reaching out to <strong>Zoiko Orbit</strong>! We've received your callback request and our support team will contact you within <strong>24 hours</strong>.</p>

      <div class="info-box">
        <strong style="display: block; margin-bottom: 6px;">📞 We'll call you at:</strong>
        <span style="font-size: 17px; color: #fc8019; font-weight: bold;">{clean_phone}</span>
      </div>

      <div class="ref-box">
        <strong style="font-size: 11px; color: #aaa; letter-spacing: 0.5px; text-transform: uppercase;">Your Reference ID</strong>
        <div class="ref-id">{ref_id}</div>
        <span style="font-size: 11px; color: #999;">Keep this for your records</span>
      </div>

      <h3 style="color: #333; margin: 25px 0 14px 0; font-size: 15px;">Can't wait? Reach us directly:</h3>

      <div class="quick-contact">
        <div class="contact-item">
          <span class="contact-label">📧 Email (24/7):</span>
          <a href="mailto:info@zoikoorbit.com">info@zoikoorbit.com</a>
        </div>
        <div class="contact-item">
          <span class="contact-label">❓ FAQs:</span>
          <a href="https://zoikoorbit.com/faqs/">zoikoorbit.com/faqs/</a>
        </div>
        <div class="contact-item">
          <span class="contact-label">📋 Help Center:</span>
          <a href="https://zoikoorbit.com/support/">zoikoorbit.com/support/</a>
        </div>
        <div class="contact-item">
          <span class="contact-label">🌐 Website:</span>
          <a href="https://zoikoorbit.com">zoikoorbit.com</a>
        </div>
      </div>

      <p style="margin-top: 28px; padding-top: 18px; border-top: 1px solid #f0f0f0; color: #555;">
        Thanks for choosing <strong>Zoiko Orbit</strong> — stay connected everywhere! 🌍✈️
      </p>
    </div>

    <div class="footer">
      <p>© 2026 Zoiko Orbit. All rights reserved.</p>
      <p style="margin-top: 4px;"><a href="https://zoikoorbit.com">zoikoorbit.com</a></p>
      <p style="font-size: 10px; color: #bbb; margin-top: 10px;">
        <em>Your information is secure and will never be shared with third parties.</em>
      </p>
    </div>
  </div>
</body>
</html>"""

    print(f"\n{'='*70}")
    print(f"CALLBACK REQUEST — {ref_id}")
    print(f"{'='*70}")
    print(f"From: {clean_name} ({clean_email})")
    print(f"Phone: {clean_phone}")
    print(f"Issue: {clean_issue[:50]}...")
    print(f"{'='*70}\n")

    support_sent  = False
    user_sent     = False
    support_error = None
    user_error    = None

    # ── Email 1: notify support team ──────────────────────────────────────────
    try:
        send_email(
            SUPPORT_EMAIL,
            f"🎧 New Callback Request — {clean_name} ({ref_id})",
            support_html,
            reply_to=clean_email     # support hits Reply → goes straight to customer
        )
        support_sent = True
        print(f"✅ Support email sent to {SUPPORT_EMAIL}")
    except Exception as e:
        support_error = str(e)
        print(f"❌ Support email FAILED: {support_error}")

    # ── Email 2: confirmation to customer ─────────────────────────────────────
    try:
        send_email(
            clean_email,
            f"✅ We Received Your Request — Zoiko Orbit ({ref_id})",
            user_html
        )
        user_sent = True
        print(f"✅ User confirmation sent to {clean_email}")
    except Exception as e:
        user_error = str(e)
        print(f"❌ User email FAILED: {user_error}")

    # ── Response based on what succeeded ──────────────────────────────────────
    print(f"\nEmail results — support: {support_sent} | user: {user_sent}\n")

    if user_sent:
        if not support_sent:
            print(f"⚠️  Support email failed but user confirmed. Error: {support_error}")
        return JSONResponse({
            "success":          True,
            "message":          "Request submitted successfully",
            "refId":            ref_id,
            "email":            clean_email,
            "phone":            clean_phone,
            "support_notified": support_sent
        })
    else:
        error_msg = user_error or support_error or "Unknown error"
        return JSONResponse({
            "success": False,
            "message": f"Error sending confirmation: {error_msg}. Please email us at info@zoikoorbit.com",
            "error":   error_msg
        }, status_code=500)

# ── /health ───────────────────────────────────────────────────────────────────
@app.get("/health")
async def health():
    return {
        "status":           "✅ Server is healthy",
        "time":             datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "service":          "Zoiko Orbit Chatbot Backend",
        "version":          "2.0",
        "email_configured": True,
        "smtp_host":        SMTP_HOST,
        "smtp_user":        SMTP_USER
    }

# ── Knowledge base chat ───────────────────────────────────────────────────────
def load_knowledge():
    p = Path("data/knowledge.json")
    if p.exists():
        with open(p) as f:
            return json.load(f)
    return {}

knowledge = load_knowledge()

@app.post("/chat")
def chat(msg: Message):
    user_msg = msg.message.lower()
    for k, v in knowledge.items():
        if k in user_msg:
            return {"response": v}
    return {"response": "I don't know yet."}

# ── Serve frontend ─────────────────────────────────────────────────────────────
if frontend_path.exists() and (frontend_path / "index.html").exists():
    app.mount("/ui", StaticFiles(directory=str(frontend_path), html=True), name="frontend")
    print(f"✅ Frontend mounted at /ui from {frontend_path}\n")
else:
    print(f"⚠️  WARNING: Frontend folder or index.html not found!\n")

# ── Startup message ───────────────────────────────────────────────────────────
print("\n╔════════════════════════════════════════════════════════════╗")
print("║  🌍 ZOIKO ORBIT CHATBOT BACKEND                            ║")
print("║  Oriko AI eSIM Assistant — Backend Service                 ║")
print("╠════════════════════════════════════════════════════════════╣")
print("║  ✅ Status:  Running                                       ║")
print("║  📧 Email:   SMTP (Credentials Configured)                 ║")
print(f"║  🖥  SMTP:   {SMTP_HOST:<47}║")
print(f"║  📤 From:   {SMTP_USER:<47}║")
print(f"║  📬 To:     {SUPPORT_EMAIL:<47}║")
print("╠════════════════════════════════════════════════════════════╣")
print("║  API ENDPOINTS:                                            ║")
print("║  POST   /send-request       Callback requests              ║")
print("║  GET    /health             Health check                   ║")
print("║  POST   /chat               Chatbot responses              ║")
print("║  GET    /ui                 Frontend (Oriko chat UI)       ║")
print("╚════════════════════════════════════════════════════════════╝")
print("\n✅ Zoiko Orbit backend ready!\n")
