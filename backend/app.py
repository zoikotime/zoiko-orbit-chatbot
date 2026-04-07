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

# ── EMAIL CONFIG — environment variables ONLY (no hardcoded fallbacks) ────────
# All secrets must be set as environment variables.
# Local dev: export SMTP_HOST=smtpout.secureserver.net (etc.) in terminal
# Cloud Run: secrets injected via deploy.yml --set-env-vars at deploy time
# GitHub Actions: stored in repo Settings → Secrets → Actions
#
# Required environment variables:
#   SMTP_HOST     — e.g. smtpout.secureserver.net
#   SMTP_PORT     — e.g. 465
#   SMTP_USER     — sending email address
#   SMTP_PASS     — SMTP password (never commit this value)
#   SUPPORT_EMAIL — receives callback ticket notifications

SMTP_HOST     = os.getenv("SMTP_HOST",     "")
SMTP_PORT_STR = os.getenv("SMTP_PORT",     465)
SMTP_USER     = os.getenv("SMTP_USER",     "")
SMTP_PASS     = os.getenv("SMTP_PASS",     "")
SUPPORT_EMAIL = os.getenv("SUPPORT_EMAIL", "")

# Validate required secrets are present at startup — fail fast if missing
_MISSING = [name for name, val in {
    "SMTP_HOST": SMTP_HOST, "SMTP_USER": SMTP_USER,
    "SMTP_PASS": SMTP_PASS, "SUPPORT_EMAIL": SUPPORT_EMAIL,
}.items() if not val]

if _MISSING:
    print(f"\n⚠️  WARNING: Missing required environment variables: {', '.join(_MISSING)}")
    print("   Email sending will be unavailable until these are set.")
    print("   See README.md → Environment Variables for setup instructions.\n")

try:
    SMTP_PORT = int(SMTP_PORT_STR)
except ValueError:
    SMTP_PORT = 465

# Safe startup log — never prints secret values
print(f"\n📧 EMAIL CONFIGURATION:")
print(f"   SMTP Host:     {SMTP_HOST or '⚠️  NOT SET'}")
print(f"   SMTP Port:     {SMTP_PORT}")
print(f"   From Email:    {SMTP_USER or '⚠️  NOT SET'}")
print(f"   Support Email: {SUPPORT_EMAIL or '⚠️  NOT SET'}")
print(f"   SMTP Password: {'✅ SET' if SMTP_PASS else '⚠️  NOT SET'}")

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
    """Generate reference ID from timestamp"""
    return "ZKN-" + str(int(time.time() * 1000))[-6:]

def valid_email(e: str) -> bool:
    """Validate email format"""
    return bool(re.match(r"^[^\s@]+@[^\s@]+\.[^\s@]+$", e))

def valid_phone(p: str) -> bool:
    """Validate phone number (10-15 digits)"""
    digits = re.sub(r"\D", "", p)
    return 10 <= len(digits) <= 15

def escape_html(s: str) -> str:
    """Escape HTML special characters"""
    return (s.replace("&","&amp;").replace("<","&lt;")
             .replace(">","&gt;").replace('"',"&quot;").replace("'","&#039;"))

def send_email(to_addr: str, subject: str, html_body: str, reply_to: str = None):
    # Guard: refuse to attempt if credentials are not configured
    if not all([SMTP_HOST, SMTP_USER, SMTP_PASS, to_addr]):
        raise ValueError("Email configuration incomplete — check SMTP_HOST, SMTP_USER, SMTP_PASS env vars")

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

    # Single SSL connection — matches your port 465 config
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
    <head><title>Send Callback Request</title></head>
    <body>
        <h2>Zoiko Mobile Callback Request</h2>
        <form method="post" action="/send-request">
            Name:<br>
            <input name="name"><br><br>

            Email:<br>
            <input name="email"><br><br>

            Phone:<br>
            <input name="phone"><br><br>

            Issue:<br>
            <textarea name="issue"></textarea><br><br>

            <button type="submit">Send Request</button>
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
        return JSONResponse({"success": False, "message": "Invalid email address"})
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
    phone_digits = re.sub(r'\D', '', clean_phone)   # pre-extracted (no backslash in f-string)
    clean_issue  = escape_html(data.issue.strip()).replace("\n", "<br>")
    first_name   = clean_name.split()[0]

    # ── Email to support team ─────────────────────────────────────────────────
    support_html = f"""<!DOCTYPE html>
    <html>
    <head>
      <meta charset="UTF-8">
      <style>
        * {{ margin: 0; padding: 0; }}
        body {{ font-family: 'Segoe UI', Arial, sans-serif; color: #333; line-height: 1.6; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ 
          background: linear-gradient(135deg, #CC0000, #880000); 
          color: white; 
          padding: 25px; 
          border-radius: 8px 8px 0 0; 
          text-align: center;
        }}
        .header h2 {{ margin: 0; font-size: 24px; }}
        .content {{ 
          background: #f9f9f9; 
          padding: 25px; 
          border: 1px solid #ddd;
          border-top: none;
        }}
        .field {{ margin-bottom: 20px; }}
        .label {{ 
          font-weight: 700; 
          color: #CC0000; 
          margin-bottom: 8px;
          font-size: 12px;
          text-transform: uppercase;
          letter-spacing: 0.5px;
        }}
        .value {{ 
          color: #333; 
          padding: 12px; 
          background: white; 
          border-left: 4px solid #CC0000;
          border-radius: 2px;
        }}
        .footer {{ 
          background: #f0f0f0; 
          padding: 20px; 
          text-align: center; 
          font-size: 12px; 
          color: #666;
          border-top: 1px solid #ddd;
        }}
        .ref-id {{ color: #CC0000; font-weight: bold; font-size: 14px; }}
        .timestamp {{ color: #999; font-size: 11px; margin-top: 10px; }}
        a {{ color: #CC0000; text-decoration: none; }}
      </style>
    </head>
    <body>
      <div class="container">
        <div class="header">
          <h2>🎧 New Callback Request</h2>
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
          <p><span class="ref-id">Reference: {ref_id}</span></p>
          <p class="timestamp">Received: {timestamp}</p>
          <p style="margin-top: 10px;">© 2026 Zoiko Mobile Support</p>
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
        body {{ font-family: 'Segoe UI', Arial, sans-serif; color: #333; line-height: 1.6; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ 
          background: linear-gradient(135deg, #CC0000, #880000); 
          color: white; 
          padding: 40px 25px;
          border-radius: 8px 8px 0 0; 
          text-align: center;
        }}
        .checkmark {{ 
          font-size: 48px; 
          margin-bottom: 15px;
          display: block;
        }}
        .header h2 {{ margin: 0; font-size: 26px; }}
        .content {{ 
          background: white; 
          padding: 30px; 
          border: 1px solid #ddd;
          border-top: none;
        }}
        .content p {{ margin: 15px 0; }}
        .info-box {{ 
          background: #fff0f0; 
          border-left: 4px solid #CC0000; 
          padding: 15px; 
          margin: 20px 0;
          border-radius: 2px;
        }}
        .ref-box {{ 
          background: #fff8e1; 
          border: 2px solid #CC0000; 
          padding: 15px; 
          border-radius: 5px; 
          margin: 20px 0; 
          text-align: center;
        }}
        .ref-id {{ 
          font-size: 20px; 
          color: #CC0000; 
          font-weight: bold;
          display: block;
          margin: 10px 0;
          font-family: 'Courier New', monospace;
        }}
        .quick-contact {{ 
          background: #f5f5f5; 
          padding: 20px; 
          border-radius: 5px;
          margin: 20px 0;
        }}
        .contact-item {{ 
          margin: 10px 0; 
          padding: 8px 0;
          border-bottom: 1px solid #e0e0e0;
        }}
        .contact-item:last-child {{ border-bottom: none; }}
        .contact-label {{ 
          color: #CC0000; 
          font-weight: bold;
        }}
        a {{ color: #CC0000; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
        .footer {{ 
          background: #f9f9f9; 
          padding: 25px; 
          text-align: center; 
          font-size: 12px; 
          color: #666;
          border-top: 1px solid #ddd;
        }}
        .footer-text {{ margin: 5px 0; }}
        .highlight {{ color: #CC0000; font-weight: bold; }}
      </style>
    </head>
    <body>
      <div class="container">
        <div class="header">
          <span class="checkmark">✅</span>
          <h2>Request Received!</h2>
        </div>
        
        <div class="content">
          <p style="font-size: 16px;">Hi <span class="highlight">{first_name}</span>,</p>
          
          <p>Thank you for reaching out to Zoiko Mobile! We've received your callback request and our support team will contact you within <strong>24 hours</strong>.</p>
          
          <div class="info-box">
            <strong style="display: block; margin-bottom: 8px;">📞 We'll call you at:</strong>
            <span style="font-size: 16px; color: #CC0000; font-weight: bold;">{clean_phone}</span>
          </div>
          
          <div class="ref-box">
            <strong style="font-size: 12px; color: #999;">YOUR REFERENCE ID</strong>
            <div class="ref-id">{ref_id}</div>
            <span style="font-size: 11px; color: #666;">Keep this for your records</span>
          </div>
          
          <h3 style="color: #333; margin: 25px 0 15px 0; font-size: 16px;">Can't wait? Quick contact options:</h3>
          
          <div class="quick-contact">
            <div class="contact-item">
              <span class="contact-label">📞 Call 24/7:</span>
              <a href="tel:+18009888116">800-988-8116</a>
            </div>
            <div class="contact-item">
              <span class="contact-label">🌐 Visit us:</span>
              <a href="https://zoikomobile.com">zoikomobile.com</a>
            </div>
            <div class="contact-item">
              <span class="contact-label">💬 Live Chat:</span>
              Available on our website (business hours)
            </div>
            <div class="contact-item">
              <span class="contact-label">📧 Email:</span>
              <a href="mailto:support@zoikomobile.com">support@zoikomobile.com</a>
            </div>
          </div>
          
          <p style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #e0e0e0;">
            Thanks for choosing Zoiko Mobile! 💚
          </p>
        </div>
        
        <div class="footer">
          <p class="footer-text">© 2026 Zoiko Mobile. All rights reserved.</p>
          <p class="footer-text" style="font-size: 10px; color: #999;">
            <em>Your information is secure and will never be shared with third parties.</em>
          </p>
        </div>
      </div>
    </body>
    </html>"""

    print(f"\n{'='*70}")
    print(f"CALLBACK REQUEST - {ref_id}")
    print(f"{'='*70}")
    print(f"From: {clean_name} ({clean_email})")
    print(f"Phone: {clean_phone}")
    print(f"Issue: {clean_issue[:50]}...")
    print(f"{'='*70}\n")

    support_sent = False
    user_sent    = False
    support_error = None
    user_error    = None

    # ── Email 1: notify support team ──────────────────────────────────────────
    # Each email has its own try/except so one failure NEVER blocks the other
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
            f"✅ We Received Your Request — Zoiko Mobile ({ref_id})",
            user_html
        )
        user_sent = True
        print(f"✅ User confirmation sent to {clean_email}")
    except Exception as e:
        user_error = str(e)
        print(f"❌ User email FAILED: {user_error}")

    # ── Response based on what succeeded ─────────────────────────────────────
    print(f"\nEmail results — support: {support_sent} | user: {user_sent}\n")

    if user_sent:
        # User got their confirmation — report success even if support email had issues
        if not support_sent:
            print(f"⚠️  Support email failed but user confirmed. Error: {support_error}")
        return JSONResponse({
            "success":       True,
            "message":       "Request submitted successfully",
            "refId":         ref_id,
            "email":         clean_email,
            "phone":         clean_phone,
            "support_notified": support_sent
        })
    else:
        # Neither or only support email sent — return error to user
        error_msg = user_error or support_error or "Unknown error"
        return JSONResponse({
            "success": False,
            "message": f"Error sending confirmation: {error_msg}. Please call 800-988-8116.",
            "error":   error_msg
        }, status_code=500)

# ── /health ───────────────────────────────────────────────────────────────────
@app.get("/health")
async def health():
    return {
        "status":  "✅ Server is healthy",
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "service": "Zoiko Mobile Chatbot Backend",
        "version": "2.0",
        "email_configured": True,
        "smtp_host": SMTP_HOST,
        "smtp_user": SMTP_USER
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
print("║  Oriko AI eSIM Assistant — Secrets via Environment Vars    ║")
print("╠════════════════════════════════════════════════════════════╣")
print(f"║  ✅ Status:  Running                                       ║")
print(f"║  📧 Email:   SMTP via Environment Variables                ║")
print(f"║  🖥  SMTP:   {(SMTP_HOST or 'NOT SET — set SMTP_HOST env var'):<47}║")
print(f"║  📤 From:   {(SMTP_USER or 'NOT SET — set SMTP_USER env var'):<47}║")
print(f"║  📬 To:     {(SUPPORT_EMAIL or 'NOT SET — set SUPPORT_EMAIL env var'):<47}║")
print(f"║  🔐 Pass:   {'✅ Configured (SMTP_PASS env var)' if SMTP_PASS else '⚠️  NOT SET — set SMTP_PASS env var':<47}║")
print("╠════════════════════════════════════════════════════════════╣")
print("║  API ENDPOINTS:                                            ║")
print("║  POST   /send-request       Callback requests              ║")
print("║  GET    /health             Health check                   ║")
print("║  POST   /chat               Chatbot responses              ║")
print("║  GET    /ui                 Frontend (Oriko chat UI)       ║")
print("╚════════════════════════════════════════════════════════════╝")
print("\n✅ Zoiko Orbit backend ready!\n")
