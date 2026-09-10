# Social Automation & Scheduling Platform — Full Engineering Architecture

A production-grade, multi-tenant SaaS engineering architecture designed for automated post scheduling and social media management across **Facebook Pages** and **LinkedIn Profiles/Pages**, accessible through a **Mobile-First Responsive Web Dashboard**.

---

## 1. High-Level System Architecture

```mermaid
graph TD
    subgraph Clients ["Client Layer (Mobile & Desktop)"]
        Mobile["📱 Mobile Browser / PWA"]
        Desktop["💻 Desktop Browser"]
    end

    subgraph API_Gateway ["Application & Routing Layer (FastAPI)"]
        Router["FastAPI Gateway / Router"]
        AuthMiddleware["JWT & Session Auth Middleware"]
        Router --> AuthMiddleware
    end

    subgraph Core_Services ["Service & Business Logic Layer"]
        AuthService["🔐 Auth Service (Bcrypt + JWT)"]
        OAuthService["🌐 OAuth 2.0 Hub (FB & LinkedIn)"]
        PostService["📝 Post Composer & Validator"]
        Publisher["🚀 Multi-Platform Publisher Engine"]
        FB_Client["📘 Facebook Graph API Client"]
        LI_Client["💼 LinkedIn REST API Client"]
        
        Publisher --> FB_Client
        Publisher --> LI_Client
    end

    subgraph Background_Workers ["Scheduler & Task Engine"]
        Scheduler["⏰ APScheduler Background Daemon"]
        Queue["Polling Worker (Every 30-60s)"]
        Scheduler --> Queue
        Queue --> Publisher
    end

    subgraph Persistence ["Data & Security Layer"]
        DB[(SQLite / PostgreSQL via SQLAlchemy)]
        CryptoEngine["🔒 Fernet Token Encryption"]
    end

    subgraph External_APIs ["External Social Platforms"]
        MetaAPI["Meta Graph API (Facebook)"]
        LinkedInAPI["LinkedIn REST API"]
    end

    Clients -->|HTTP / JSON / HTML| Router
    AuthMiddleware --> AuthService
    AuthMiddleware --> PostService
    AuthMiddleware --> OAuthService

    OAuthService --> CryptoEngine
    CryptoEngine --> DB
    PostService --> DB
    Queue --> DB

    FB_Client -->|REST HTTPS| MetaAPI
    LI_Client -->|REST HTTPS| LinkedInAPI
```

---

## 2. Directory & Module Structure

```text
social_automation_hub/
│
├── app/
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py             # Pydantic BaseSettings (Reads .env, app secrets)
│   │   ├── database.py           # SQLAlchemy Engine, SessionLocal & Base
│   │   └── security.py           # Password hashing (bcrypt) & Fernet Token Encryption
│   │
│   ├── models/                   # Database Entities (ORM)
│   │   ├── __init__.py
│   │   ├── user.py               # User table
│   │   ├── social_account.py     # Connected OAuth accounts (Encrypted tokens)
│   │   └── post.py               # Scheduled & Published posts
│   │
│   ├── schemas/                  # Pydantic Schemas (Request/Response DTOs)
│   │   ├── __init__.py
│   │   ├── user.py               # UserCreate, UserLogin, UserOut
│   │   ├── social.py             # SocialAccountOut, OAuthCallback
│   │   └── post.py               # PostCreate, PostUpdate, PostOut
│   │
│   ├── services/                 # Business Logic & External API Integrations
│   │   ├── __init__.py
│   │   ├── auth_service.py       # User registration, login verification, token issue
│   │   ├── facebook_service.py   # Page selection, post publishing, token exchange
│   │   ├── linkedin_service.py   # Profile/Company selection, UGC post creation
│   │   └── publisher.py          # Unified dispatcher coordinating FB & LinkedIn posts
│   │
│   ├── scheduler/                # Background Job Runner
│   │   ├── __init__.py
│   │   └── worker.py             # Periodic background poller inspecting pending posts
│   │
│   ├── routers/                  # API and View Controllers
│   │   ├── __init__.py
│   │   ├── auth.py               # /api/v1/auth (signup, login, logout)
│   │   ├── oauth.py              # /api/v1/oauth (fb-login, linkedin-login, callbacks)
│   │   ├── posts.py              # /api/v1/posts (CRUD for posts)
│   │   └── views.py              # Front-facing web pages (HTML rendering)
│   │
│   ├── static/                   # Static Frontend Assets
│   │   ├── css/
│   │   │   └── tailwind_custom.css
│   │   ├── js/
│   │   │   ├── app.js            # General UI interactions & toast alerts
│   │   │   └── post_composer.js  # Live character counters, image preview, platform selection
│   │   └── img/
│   │
│   └── templates/                # Mobile-First Responsive Jinja2 Templates
│       ├── base.html             # Shell: Desktop Sidebar + Mobile Bottom Navigation
│       ├── auth/
│       │   ├── login.html
│       │   └── register.html
│       ├── dashboard.html        # Analytics, recent activity, system status
│       ├── create_post.html      # Responsive composer with live social preview
│       ├── schedule.html         # Post queue, timeline, failed/success logs
│       └── accounts.html         # One-click Connect/Disconnect for FB and LinkedIn
│
├── docs/                         # Project Documentation & Architecture
│   ├── implementation_plan.md
│   └── walkthrough.md
│
├── tests/                        # Automated Unit & Integration Tests
│   ├── test_auth.py
│   ├── test_posts.py
│   └── test_scheduler.py
│
├── .env.example                  # Template of environment variables
├── requirements.txt              # Production & dev dependencies
├── Dockerfile                    # Containerization ready
└── main.py                       # Application Entry Point
```

---

## 3. Database Schema (Multi-Tenant Isolation)

```mermaid
erDiagram
    USERS ||--o{ SOCIAL_ACCOUNTS : "owns"
    USERS ||--o{ POSTS : "creates"
    POSTS ||--o{ POST_DISPATCH_LOGS : "records"

    USERS {
        int id PK
        string email UK
        string hashed_password
        string full_name
        boolean is_active
        datetime created_at
    }

    SOCIAL_ACCOUNTS {
        int id PK
        int user_id FK
        string platform "facebook | linkedin"
        string platform_account_id
        string account_name
        string account_type "page | profile"
        text encrypted_access_token
        text encrypted_refresh_token
        datetime token_expires_at
        datetime created_at
    }

    POSTS {
        int id PK
        int user_id FK
        text content
        string media_url
        datetime scheduled_at
        string status "draft | scheduled | publishing | published | failed"
        json target_platforms "['facebook', 'linkedin']"
        datetime published_at
        datetime created_at
    }

    POST_DISPATCH_LOGS {
        int id PK
        int post_id FK
        string platform "facebook | linkedin"
        string platform_post_id
        string status "success | error"
        text error_message
        datetime executed_at
    }
```

---

## 4. Workflows & Lifecycles

### A. OAuth 2.0 Account Connection Flow
```mermaid
sequenceDiagram
    autonumber
    actor User
    participant Browser as Mobile/Desktop Web
    participant Server as FastAPI Server
    participant Meta as Facebook/LinkedIn OAuth

    User->>Browser: Click "Connect Facebook" or "Connect LinkedIn"
    Browser->>Server: GET /api/v1/oauth/{platform}/connect
    Server-->>Browser: Redirect to Platform Authorization Dialog
    User->>Meta: Grants Permission (pages_manage_posts / w_member_social)
    Meta-->>Server: Redirect back with Auth Code: GET /api/v1/oauth/{platform}/callback?code=XYZ
    Server->>Meta: Exchange Code for Long-Lived Access Token
    Meta-->>Server: Returns Access Token & User/Page Info
    Server->>Server: Encrypt Token using AES-256 (Fernet)
    Server->>Server: Save to SOCIAL_ACCOUNTS table linked to User ID
    Server-->>Browser: Redirect back to /accounts with Success Toast
```

### B. Post Scheduling & Automated Dispatch Lifecycle
```mermaid
sequenceDiagram
    autonumber
    actor User
    participant Web as Web Dashboard
    participant API as FastAPI Post API
    participant Worker as Background Scheduler
    participant Engine as Publisher Engine
    participant Social as Facebook / LinkedIn

    User->>Web: Write post, select FB & LinkedIn, pick date/time
    Web->>API: POST /api/v1/posts (scheduled_at: 2026-09-10 10:00)
    API->>API: Save post to DB with status = 'scheduled'
    Note over Worker: Runs every 30 seconds
    Worker->>Worker: Query DB: WHERE status = 'scheduled' AND scheduled_at <= NOW()
    Worker->>API: Update status to 'publishing'
    Worker->>Engine: dispatch_post(post_id)
    Engine->>Engine: Decrypt user's access tokens for target platforms
    par Publish to Facebook
        Engine->>Social: POST Graph API /v19.0/{page-id}/feed
        Social-->>Engine: Returns FB Post ID
    and Publish to LinkedIn
        Engine->>Social: POST LinkedIn /rest/posts
        Social-->>Engine: Returns LinkedIn Post ID
    end
    Engine->>API: Record success log & set status = 'published'
```

---

## 5. Security & Multi-Tenancy Design
1. **Multi-Tenancy Row-Level Isolation**:
   - Every database query for posts and social accounts includes `WHERE user_id = current_user.id`. Users can never read, modify, or trigger another user's accounts or posts.
2. **Access Token Encryption**:
   - OAuth tokens are never stored in plain text. A dedicated AES-256 (Fernet) encryption key (`ENCRYPTION_KEY`) in the environment encrypts tokens before writing to DB and decrypts them only at the moment of publishing.
3. **Session & Auth Management**:
   - Stateless JWT tokens passed via secure HTTP cookies or `Authorization: Bearer` headers.
   - Passwords hashed using standard `bcrypt` with salt.
4. **Resilience & Rate Limiting**:
   - Exponential backoff for API calls.
   - Distinct error logging per platform in `POST_DISPATCH_LOGS` so a failure on Facebook doesn't abort a LinkedIn post.

---

## 6. Verification & Testing Strategy

### Automated Tests:
1. `tests/test_auth.py`:
   - Registration, login, password hashing verification, JWT generation.
2. `tests/test_posts.py`:
   - CRUD on posts, validation of scheduled times, user isolation checks (User A cannot see User B's posts).
3. `tests/test_scheduler.py`:
   - Mocking Facebook & LinkedIn API responses; verifying the scheduler changes post status from `scheduled` to `published` and records log IDs.

### Manual UI Verification:
- Open dashboard in Chrome DevTools mobile responsive mode (iPhone 14 / Pixel 7 viewports) to verify the bottom navigation bar, post composer preview, and account toggles.
