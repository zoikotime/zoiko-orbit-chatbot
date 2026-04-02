# 🌐 Oriko — Zoiko Orbit Intelligent Chatbot System

A modern web-based conversational AI application for **Zoiko Orbit** with a unified FastAPI backend, interactive HTML frontend, professional email integration, and automated CI/CD deployment.

---

## ✨ Features

✅ **Unified Backend** - Single FastAPI application handles all requests  
✅ **Professional Emails** - Support ticket requests trigger HTML-formatted emails  
✅ **Interactive Frontend** - Real-time chatbot with modern UI (powered by Oriko AI)  
✅ **Knowledge Base** - JSON-based response system for eSIM & travel connectivity  
✅ **Hardcoded Credentials** - Secure email setup (no .env file needed)  
✅ **Docker Containerized** - Production-ready deployment  
✅ **GitHub CI/CD** - Automated build and deploy to Google Cloud Run  
✅ **Scalable** - Auto-scaling on Cloud Run (0-3 instances)  
✅ **SSL/TLS** - HTTPS by default on Cloud Run  

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   Frontend (HTML/JS)                    │
│  - Oriko Chatbot Interface                              │
│  - Support Ticket Request Form                          │
│  - Real-time Chat (eSIM & Travel Support)               │
└────────────────────┬────────────────────────────────────┘
                     │ HTTP/REST
                     ▼
┌─────────────────────────────────────────────────────────┐
│         FastAPI Unified Backend (Python)                │
│                                                         │
│  • /ui              → Serve frontend                    │
│  • /send-request    → Process ticket + send emails      │
│  • /chat            → Chatbot responses                 │
│  • /health          → Health check                      │
│                                                         │
│  SMTP Configuration: support@zoikogroup.com             │
│  Hardcoded in app.py (no .env needed)                   │
└─────────────────────────────────────────────────────────┘
                     │
                     ├─── 📧 Email to Zoiko Orbit support team
                     └─── 📧 Confirmation to user
```

---

## 📋 Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend Framework | FastAPI (Python 3.10) |
| Frontend | HTML5 + JavaScript |
| AI Assistant | Oriko (Zoiko Orbit Chatbot) |
| Email Service | SMTP (GoDaddy) |
| Containerization | Docker |
| Cloud Platform | Google Cloud Run |
| CI/CD | GitHub Actions |
| Version Control | Git + GitHub |

---

## 📁 Project Structure

```
Oriko/
├── backend/
│   ├── app.py                 ← Unified FastAPI backend
│   ├── requirements.txt        ← Python dependencies
│   └── __pycache__/
│
├── frontend/
│   └── index.html             ← Oriko Chatbot UI
│
├── data/
│   └── knowledge.json         ← Chatbot responses (eSIM & travel)
│
├── .github/
│   └── workflows/
│       └── deploy.yml         ← GitHub Actions CI/CD
│
├── Dockerfile                 ← Docker configuration
├── README.md                  ← This file
└── .gitignore
```

---

## 🚀 Quick Start - Local Development

### Prerequisites
- Python 3.10+
- pip (Python package manager)

### Installation

```bash
# 1. Clone repository
git clone https://github.com/zoikotime/zoiko-orbit-chatbot.git
cd ORIKO

# 2. Install dependencies
pip install -r backend/requirements.txt

# 3. Run server
python -m uvicorn backend.app:app --reload --port 8000
```

### Access Chatbot

Open in browser:
```
http://127.0.0.1:8000/ui
```

### Test Support Ticket Email

1. Click **"Connect with Support Team"** in the chat
2. Fill in: Name, Email, Issue Description, Priority
3. Submit form
4. Check email inbox for 2 messages:
   - **To support team**: `support@zoikoorbit.com`
   - **To user**: Confirmation email with ticket reference (ZKO-XXXXXX)

---

## 🐳 Docker - Local Testing

### Build Image

```bash
docker build -t oriko .
```

### Run Container

```bash
docker run -p 8080:8080 oriko
```

Access at:
```
http://localhost:8080/ui
```

---

## ☁️ Deploy to Google Cloud Run

### Prerequisites

- Google Cloud account
- GCP Project
- GitHub repository
- GitHub Secrets configured (see below)

### GitHub Secrets Required

Set these in: `GitHub → Settings → Secrets → Actions`

```
✅ GCP_PROJECT_ID         (your GCP project ID)
✅ GCP_SA_KEY             (JSON service account key)
```

**Email is hardcoded**, so no SMTP secrets needed!

### Deploy Steps

```bash
# 1. Push to GitHub main branch
git push origin main

# 2. GitHub Actions automatically:
#    - Builds Docker image
#    - Pushes to Google Container Registry
#    - Deploys to Cloud Run
#    - Shows public URL

# 3. Check deployment:
# Go to: https://github.com/MRaviKumarReddy01/ORIKO/actions
```

### Access Deployed Chatbot

After deployment, Cloud Run shows public URL:
```
(https://zoiko-orbit-chatbot-git-722985113446.europe-west1.run.app/ui/)
```

---

## 📧 Email Configuration

**Email sending is HARDCODED in `app.py`:**

```python
SMTP_HOST     = "smtpout.secureserver.net"
SMTP_PORT     = 465
SMTP_USER     = "support@zoikogroup.com"
SMTP_PASS     = 
SUPPORT_EMAIL = "support@zoikoorbit.com"
```

✅ **NO .env file needed!**  
✅ **Secure** - Credentials in code only (not in GitHub)  
✅ **Simple** - Just deploy and it works!

---

## 🔌 API Endpoints

### Frontend
```
GET /ui
```
Serves the Oriko chatbot interface (index.html)

### Chatbot
```
POST /chat
Body: { "message": "hello" }
Response: { "response": "..." }
```

### Support Ticket / Email
```
POST /send-request
Body: {
  "name": "Jane Smith",
  "email": "jane@example.com",
  "phone": "5551234567",
  "issue": "eSIM not activating on iPhone 15"
}
Response: {
  "success": true,
  "refId": "ZKO-123456",
  "message": "Request submitted successfully"
}
```

Sends 2 emails:
- **Support team**: `support@zoikoorbit.com` receives the ticket details
- **User**: `jane@example.com` gets a confirmation with reference number `ZKO-XXXXXX`

### Health Check
```
GET /health
Response: {
  "status": "✅ Server is healthy",
  "service": "Zoiko Orbit Chatbot Backend",
  "version": "2.0",
  "email_configured": true,
  "smtp_host": "smtpout.secureserver.net",
  "smtp_user": "support@zoikogroup.com"
}
```

---

## 🧪 Testing

### Local Testing

```bash
# Start server
python -m uvicorn backend.app:app --reload --port 8000

# Test health endpoint
curl http://localhost:8000/health

# Test chat
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "hello"}'

# Test support ticket (sends 2 emails)
curl -X POST http://localhost:8000/send-request \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test User",
    "email": "test@example.com",
    "phone": "5551234567",
    "issue": "eSIM activation test"
  }'
```

### Browser Testing

1. Open `http://localhost:8000/ui`
2. Test chat: Type `"hello"` or `"I want to buy an eSIM"`
3. Test ticket: Click **"Connect with Support Team"**, fill form and submit
4. Check email inbox for confirmation with `ZKO-XXXXXX` reference

---

## 🔐 Security

✅ CORS enabled for all origins  
✅ SMTP credentials hardcoded (not in .env)  
✅ Input validation on all endpoints  
✅ HTML escaping for user input  
✅ HTTPS on Cloud Run (automatic)  
✅ Secrets in GitHub (not in code)  

---

## 📊 Deployment Architecture

```
Your Computer (Local)
        │
        ▼
  GitHub Repository
        │
        └─→ GitHub Actions
              │
              ├─→ Build Docker image
              ├─→ Push to Google Container Registry
              └─→ Deploy to Cloud Run
                      │
                      ▼
                Google Cloud Run
                (Public HTTPS URL)
                      │
                      └─→ Auto-scales 0-3 instances
```

---

## 📝 Git Workflow

```bash
# 1. Make changes locally
# 2. Test locally
python -m uvicorn backend.app:app --reload --port 8000

# 3. Commit changes
git add -A
git commit -m "Your message"

# 4. Push to GitHub
git push origin main

# 5. GitHub Actions auto-deploys
# Watch: https://github.com/MRaviKumarReddy01/ORIKO/actions

# 6. Check deployment
gcloud run services describe oriko --region europe-west1
```

---

## 🛠️ Troubleshooting

### Email Not Sending

Check in terminal logs:
```
❌ FAILED TO SEND EMAIL
Error: Connection unexpectedly closed
```

Solutions:
1. Verify SMTP credentials in `app.py`
2. Check firewall isn't blocking port 465
3. Verify `support@zoikogroup.com` account exists

### Frontend Not Loading (/ui returns 404)

```bash
# Verify frontend folder exists
ls -la frontend/
ls -la frontend/index.html

# Should show index.html in the frontend folder
```

### Deployment Failed

Check GitHub Actions logs:
1. Go to: `https://github.com/MRaviKumarReddy01/ORIKO/actions`
2. Click the failed workflow
3. Review the detailed error messages

---

## 📚 Documentation

- **API Documentation**: `http://localhost:8000/docs` (Swagger UI)
- **ReDoc**: `http://localhost:8000/redoc`
- **Frontend Code**: `frontend/index.html`
- **Backend Code**: `backend/app.py`

---

## 🤝 Contributing

1. Create feature branch: `git checkout -b feature/awesome-feature`
2. Commit changes: `git commit -m "Add awesome feature"`
3. Push to branch: `git push origin feature/awesome-feature`
4. Open Pull Request

---

## 👨‍💼 Author

**M. Ravi Kumar Reddy**  
AI/ML Intern – Zoiko Industries Pvt. Limited

---

## 📄 License

This project is for educational and commercial use by Zoiko Industries.

---

## 🎉 Status

✅ **Production Ready**
- Local testing: ✅ Working
- Docker build: ✅ Working
- Cloud Run deployment: ✅ Working
- Email integration: ✅ Working
- Frontend (Oriko UI): ✅ Working

---

## 📞 Support

For issues or questions:
1. Check GitHub Issues
2. Check deployment logs
3. Contact the team at `support@zoikoorbit.com`

---

**Last Updated**: April 2, 2026  
**Version**: 2.0 (Unified FastAPI Backend)  
**Product**: Oriko — Zoiko Orbit AI Chatbot
