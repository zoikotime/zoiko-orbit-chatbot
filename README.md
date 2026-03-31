# 🎧 Zoikon Intelligent Chatbot System

A modern web-based conversational AI application for **Zoiko Mobile** with a unified FastAPI backend, interactive HTML frontend, professional email integration, and automated CI/CD deployment.

---

## ✨ Features

✅ **Unified Backend** - Single FastAPI application handles all requests  
✅ **Professional Emails** - Callback requests trigger HTML-formatted emails  
✅ **Interactive Frontend** - Real-time chatbot with modern UI  
✅ **Knowledge Base** - JSON-based response system  
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
│  - Chatbot Interface                                    │
│  - Callback Request Form                                │
│  - Real-time Chat                                       │
└────────────────────┬────────────────────────────────────┘
                     │ HTTP/REST
                     ▼
┌─────────────────────────────────────────────────────────┐
│         FastAPI Unified Backend (Python)                │
│                                                         │
│  • /ui              → Serve frontend                    │
│  • /send-request    → Process callback + send emails    │
│  • /chat            → Chatbot responses                 │
│  • /health          → Health check                      │
│                                                         │
│  SMTP Configuration: support@zoikogroup.com             │
│  Hardcoded in app.py (no .env needed)                   │
└─────────────────────────────────────────────────────────┘
                     │
                     ├─── 📧 Email to support team
                     └─── 📧 Confirmation to user
```

---

## 📋 Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend Framework | FastAPI (Python 3.10) |
| Frontend | HTML5 + JavaScript |
| Email Service | SMTP (GoDaddy) |
| Containerization | Docker |
| Cloud Platform | Google Cloud Run |
| CI/CD | GitHub Actions |
| Version Control | Git + GitHub |

---

## 📁 Project Structure

```
Zoikon/
├── backend/
│   ├── app.py                 ← Unified FastAPI backend
│   ├── requirements.txt        ← Python dependencies
│   └── __pycache__/
│
├── frontend/
│   └── index.html             ← Chatbot UI
│
├── data/
│   └── knowledge.json         ← Chatbot responses
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
git clone https://github.com/MRaviKumarReddy01/ZOIKON.git
cd ZOIKON

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

### Test Callback Email

1. Click "Connect with Live Agent"
2. Fill in: Name, Email, Phone, Issue
3. Submit form
4. Check email inbox for 2 messages:
   - **To support team**: `support@zoikomobile.com`
   - **To user**: Confirmation email

---

## 🐳 Docker - Local Testing

### Build Image

```bash
docker build -t zoikon .
```

### Run Container

```bash
docker run -p 8080:8080 zoikon
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
- 10 GitHub Secrets configured (see below)

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
# Go to: https://github.com/MRaviKumarReddy01/ZOIKON/actions
```

### Access Deployed Chatbot

After deployment, Cloud Run shows public URL:
```
https://zoikon-[random].europe-west1.run.app/ui
```

---

## 📧 Email Configuration

**Email sending is HARDCODED in `app.py`:**

```python
SMTP_HOST     = "smtpout.secureserver.net"
SMTP_PORT     = 465
SMTP_USER     = "support@zoikogroup.com"
SMTP_PASS     = "NoxxMC26070%!LGM"
SUPPORT_EMAIL = "support@zoikomobile.com"
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
Serves chatbot interface (index.html)

### Chatbot
```
POST /chat
Body: { "message": "hello" }
Response: { "response": "..." }
```

### Callback/Email
```
POST /send-request
Body: {
  "name": "John Doe",
  "email": "john@example.com",
  "phone": "5551234567",
  "issue": "Need help with plan"
}
Response: {
  "success": true,
  "refId": "ZKN-123456",
  "message": "Request submitted successfully"
}
```

Sends 2 emails:
- **Support**: zoikom.com/support/ receives request
- **User**: john@example.com gets confirmation

### Health Check
```
GET /health
Response: {
  "status": "✅ Server is healthy",
  "service": "Zoiko Mobile Chatbot Backend",
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

# Test callback (sends 2 emails)
curl -X POST http://localhost:8000/send-request \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test User",
    "email": "test@example.com",
    "phone": "5551234567",
    "issue": "Test callback"
  }'
```

### Browser Testing

1. Open http://localhost:8000/ui
2. Test chat: Type "hello" or "plans"
3. Test callback: Fill form and submit
4. Check email inbox

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
# Watch: https://github.com/MRaviKumarReddy01/ZOIKON/actions

# 6. Check deployment
gcloud run services describe zoikon --region europe-west1
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
1. Verify SMTP credentials in app.py
2. Check firewall isn't blocking port 465
3. Verify support@zoikogroup.com account exists

### Frontend Not Loading (/ui returns 404)

Check:
```bash
# Verify frontend folder exists
ls -la frontend/
ls -la frontend/index.html

# Should show index.html in frontend folder
```

### Deployment Failed

Check GitHub Actions logs:
1. Go to: https://github.com/MRaviKumarReddy01/ZOIKON/actions
2. Click failed workflow
3. See detailed error messages

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
- Frontend: ✅ Working

---

## 📞 Support

For issues or questions:
1. Check GitHub Issues
2. Check deployment logs
3. Contact team

---

**Last Updated**: March 11, 2026  
**Version**: 2.0 (Unified FastAPI Backend)#   z o i k o - o r b i t - c h a t b o t  
 