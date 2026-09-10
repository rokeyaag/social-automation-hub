# SocialPulse Hub — System Walkthrough & Deployment Guide

We have engineered and implemented the full architecture for **SocialPulse Hub**, a production-grade, multi-user social media scheduling and automation platform supporting **Facebook Pages** and **LinkedIn Profiles/Pages** with a **Mobile-First Responsive Web Dashboard**.

---

## 📁 Implemented Components & File Registry

The project is built at:
`C:\Users\HP\.gemini\antigravity\scratch\social_automation_hub\`

| Path | Description |
| :--- | :--- |
| [`main.py`](file:///C:/Users/HP/.gemini/antigravity/scratch/social_automation_hub/main.py) | Application entrypoint with lifecycle hooks (DB init & APScheduler daemon) |
| [`app/core/config.py`](file:///C:/Users/HP/.gemini/antigravity/scratch/social_automation_hub/app/core/config.py) | Configuration manager reading `.env` (API keys, JWT & AES-256 secrets) |
| [`app/core/database.py`](file:///C:/Users/HP/.gemini/antigravity/scratch/social_automation_hub/app/core/database.py) | SQLAlchemy engine, session maker, and FastAPI dependency (`get_db`) |
| [`app/core/security.py`](file:///C:/Users/HP/.gemini/antigravity/scratch/social_automation_hub/app/core/security.py) | `bcrypt` password hashing, JWT creation/decoding, and **Fernet AES-256** token encryption |
| [`app/models/`](file:///C:/Users/HP/.gemini/antigravity/scratch/social_automation_hub/app/models/) | Database ORM schemas: `User`, `SocialAccount`, `Post`, `PostDispatchLog` |
| [`app/services/facebook_service.py`](file:///C:/Users/HP/.gemini/antigravity/scratch/social_automation_hub/app/services/facebook_service.py) | Meta Graph API client with OAuth code exchange and page feed publishing |
| [`app/services/linkedin_service.py`](file:///C:/Users/HP/.gemini/antigravity/scratch/social_automation_hub/app/services/linkedin_service.py) | LinkedIn REST API client with OAuth code exchange and UGC post publishing |
| [`app/services/publisher.py`](file:///C:/Users/HP/.gemini/antigravity/scratch/social_automation_hub/app/services/publisher.py) | Multi-platform publishing orchestrator with token decryption & error logging |
| [`app/scheduler/worker.py`](file:///C:/Users/HP/.gemini/antigravity/scratch/social_automation_hub/app/scheduler/worker.py) | Background `APScheduler` job polling every 15s to dispatch due posts |
| [`app/routers/`](file:///C:/Users/HP/.gemini/antigravity/scratch/social_automation_hub/app/routers/) | REST APIs for Auth, OAuth 2.0 connection, Post CRUD, and HTML view controllers |
| [`app/templates/`](file:///C:/Users/HP/.gemini/antigravity/scratch/social_automation_hub/app/templates/) | Mobile-first responsive UI (Tailwind CSS) with mobile bottom navigation bar & desktop sidebar |
| [`tests/test_core.py`](file:///C:/Users/HP/.gemini/antigravity/scratch/social_automation_hub/tests/test_core.py) | Automated test suite verifying hashing, encryption, models, and publisher dispatch |

---

## 📱 Mobile-First Web Experience

The UI was crafted specifically for mobile and desktop screens:
- **Mobile Bottom Navigation Bar**: Fixed at the bottom for thumbs-friendly switching between **Home**, **Post**, **Queue**, and **Accounts**.
- **Interactive Composer**:
  - Live character counter.
  - Multi-channel selector checkboxes (**Facebook Page**, **LinkedIn Profile**).
  - Real-time social card preview replicating how the post appears on social feeds.
  - Flexible scheduling (Immediate publish or custom date-time picker).
- **Post Queue & Timeline**:
  - Visual status chips (`Published`, `Scheduled`, `Failed`).
  - Delivery logs indicating exact post IDs or error feedback from platforms.
  - One-click immediate manual dispatch for scheduled posts.

---

## 🔒 Multi-Tenant Security & Isolation

- **Row-Level Tenancy**: All post creation, listing, account connections, and publishing routines strictly enforce `user_id == current_user.id`.
- **Fernet AES-256 Symmetric Encryption**: Access tokens received from Meta and LinkedIn are immediately encrypted before being written to the database. They are only decrypted in memory at the exact instant a post is dispatched.

---

## ⚡ How to Run the Platform

### Step 1: Open the Project Directory
```powershell
cd C:\Users\HP\.gemini\antigravity\scratch\social_automation_hub
```

### Step 2: Install Dependencies
```powershell
pip install -r requirements.txt
```

### Step 3: Run the Application
```powershell
python main.py
```

### Step 4: Access the Dashboard
Open your browser and navigate to:
👉 **`http://localhost:8000`**

> [!TIP]
> **Simulation / Demo Mode is Active Out of the Box:**
> You can immediately register an account, connect simulated Facebook & LinkedIn accounts with a single click, schedule posts, and watch the background worker dispatch them—without waiting to obtain Meta or LinkedIn developer app approval!
>
> When you are ready for live social media posting, simply update `META_APP_ID`, `META_APP_SECRET`, `LINKEDIN_CLIENT_ID`, and `LINKEDIN_CLIENT_SECRET` in `.env` and switch `DEMO_MODE=False`.
