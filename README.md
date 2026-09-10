# ⚡ SocialPulse Hub — Multi-Tenant Social Automation Platform

A production-ready Python & FastAPI automation platform for scheduling and auto-publishing content to **Facebook Pages** and **LinkedIn Profiles/Pages**, featuring a **Mobile-First Responsive Web Dashboard**.

---

## 🚀 Key Features

- **Multi-Tenant Architecture**: Multiple users can register, connect their own accounts, and manage their own queues independently with complete data isolation.
- **Facebook & LinkedIn Support**:
  - Facebook Page auto-posting via Meta Graph API.
  - LinkedIn Profile/Page sharing via LinkedIn REST API.
- **Mobile-First Web UI**:
  - Responsive layout with bottom navigation on mobile devices and sidebar on desktop.
  - Live preview of posts formatted for social feeds.
  - One-click account linking and post scheduling.
- **Automated Background Scheduler**:
  - Integrated `APScheduler` daemon checking every 15 seconds for due posts.
  - Dispatches posts automatically without requiring manual triggers.
- **Enterprise-Grade Security**:
  - User passwords hashed with `bcrypt`.
  - Social media OAuth access tokens encrypted in SQLite/PostgreSQL with **AES-256 Fernet**.
- **Ready-to-Use Simulation / Demo Mode**:
  - `DEMO_MODE=True` allows full end-to-end testing (signup, connecting accounts, scheduling, previewing, and mock-publishing) immediately, even before you enter official Meta or LinkedIn API keys!

---

## 🛠️ Project Structure

```text
social_automation_hub/
├── app/
│   ├── core/           # Config, database setup, Fernet AES-256 & bcrypt security
│   ├── models/         # User, SocialAccount, Post, PostDispatchLog (SQLAlchemy)
│   ├── schemas/        # Pydantic DTO validation schemas
│   ├── services/       # Facebook Graph API, LinkedIn API, Auth, and Publisher engine
│   ├── scheduler/      # APScheduler background worker
│   ├── routers/        # API endpoints (Auth, OAuth, Posts) and HTML views
│   └── templates/      # Mobile-first Jinja2 templates styled with Tailwind CSS
├── .env                # Configured environment variables
├── .env.example        # Environment template
├── requirements.txt    # Python dependencies
├── main.py             # Application entrypoint with lifespan events
└── README.md
```

---

## 💻 Quick Start & Running the Project

### 1. Install Dependencies
```bash
cd C:\Users\HP\.gemini\antigravity\scratch\social_automation_hub
pip install -r requirements.txt
```

### 2. Start the Server
```bash
python main.py
```
Or with uvicorn:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Open in Browser
Visit: **`http://localhost:8000`** (or open on mobile browser using your local IP, e.g. `http://192.168.x.x:8000`).

---

## 🔑 Setting Up Live Meta & LinkedIn APIs

To switch from Demo/Simulation Mode to live posting:
1. Open `.env`
2. Set `DEMO_MODE=False`
3. Add your developer credentials:
   ```env
   META_APP_ID=your_facebook_app_id
   META_APP_SECRET=your_facebook_app_secret
   LINKEDIN_CLIENT_ID=your_linkedin_client_id
   LINKEDIN_CLIENT_SECRET=your_linkedin_client_secret
   ```
4. Save and restart the app.
