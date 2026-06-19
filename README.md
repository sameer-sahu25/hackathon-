# Housing Stability AI Guide - Backend

A production-grade backend for the Housing Stability AI Guide, built for a global AI hackathon. Helps vulnerable renters facing eviction understand their rights, find resources, and take immediate action.

## Tech Stack

- **Runtime**: Python 3.11
- **Framework**: FastAPI (latest stable)
- **ASGI Server**: Uvicorn
- **ORM**: SQLAlchemy 2.0 (async)
- **Migrations**: Alembic
- **Background Tasks**: Celery + Redis
- **Database**: PostgreSQL (Neon Serverless)
- **Cache**: Redis
- **Auth**: JWT (python-jose + bcrypt)
- **AI**: Anthropic Claude Sonnet API
- **RAG**: LangChain + Pinecone Vector DB
- **Embeddings**: OpenAI text-embedding-3-small
- **SMS**: Twilio Programmable SMS
- **PDF Gen**: WeasyPrint
- **Monitoring**: Sentry + PostHog

## Project Structure

```
housing-stability-backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app entry point
│   ├── config.py               # Pydantic settings
│   ├── api/v1/                 # API endpoints
│   │   ├── auth.py
│   │   ├── intake.py
│   │   ├── action_plan.py
│   │   ├── resources.py
│   │   ├── rights.py
│   │   ├── checklist.py
│   │   ├── sms.py
│   │   ├── tracker.py
│   │   └── router.py
│   ├── core/                   # Core utilities
│   │   ├── security.py         # JWT, password hashing
│   │   ├── dependencies.py     # FastAPI deps (db, auth)
│   │   └── exceptions.py       # Error handling
│   ├── models/                 # SQLAlchemy models
│   ├── schemas/                # Pydantic schemas
│   ├── services/               # Business logic + external integrations
│   ├── tasks/                  # Celery background tasks
│   └── db/                     # DB base + session
├── alembic/                    # DB migrations
├── tests/                      # Pytest tests
├── .env.example                # Env template
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── README.md
```

## Quick Start

### 1. Environment Setup

```bash
# Clone and cd
cd housing-stability-backend

# Copy env template
cp .env.example .env
# Edit .env with your API keys
```

### 2. Run with Docker (Recommended)

```bash
docker-compose up --build
```

The API will be available at http://localhost:8000, docs at http://localhost:8000/docs

### 3. Local Development (Manual)

```bash
# Create virtual env
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run DB (with Docker)
docker-compose up -d db redis

# Run migrations
alembic upgrade head

# Run API
uvicorn app.main:app --reload

# Run Celery worker (in another terminal)
celery -A app.tasks.celery_app worker --loglevel=info
```

## API Endpoints

See full auto-generated docs at http://localhost:8000/docs

### Authentication
- `POST /api/v1/auth/anonymous` - Create anonymous session
- `POST /api/v1/auth/register` - Register user
- `POST /api/v1/auth/login` - Login
- `GET /api/v1/auth/me` - Get current user

### Intake
- `POST /api/v1/intake/submit` - Submit intake form
- `GET /api/v1/intake/{id}` - Get intake
- `PUT /api/v1/intake/{id}` - Update intake

### Action Plan
- `POST /api/v1/action-plan/generate` - Generate AI action plan
- `GET /api/v1/action-plan/{id}` - Get plan
- `GET /api/v1/action-plan/by-intake/{id}` - Get plan by intake

### Resources
- `GET /api/v1/resources/nearby` - Get nearby resources
- `GET /api/v1/resources/state/{code}` - Get state resources
- `GET /api/v1/resources/{id}` - Get resource detail

### Rights
- `GET /api/v1/rights/state/{code}` - State tenant rights
- `GET /api/v1/rights/states` - List states

### Checklist
- `POST /api/v1/checklist/generate` - Generate checklist
- `GET /api/v1/checklist/{id}/pdf` - Download PDF

### SMS
- `POST /api/v1/sms/schedule` - Schedule reminders
- `GET /api/v1/sms/status/{id}` - Check status
- `DELETE /api/v1/sms/cancel/{id}` - Cancel reminders

### Tracker
- `POST /api/v1/tracker/step/complete` - Mark step complete
- `GET /api/v1/tracker/dashboard/{id}` - Get dashboard
- `PUT /api/v1/tracker/outcome` - Update outcome

## Environment Variables

All variables documented in `.env.example`. Key ones:
- `SECRET_KEY`, `JWT_SECRET_KEY` - Secure keys
- `ANTHROPIC_API_KEY` - Claude AI
- `PINECONE_API_KEY`, `PINECONE_INDEX_NAME` - Vector DB
- `OPENAI_API_KEY` - Embeddings
- `TWILIO_*` - SMS
- `GOOGLE_MAPS_API_KEY` - Geocoding
- `DATABASE_URL` - Neon Postgres
- `REDIS_URL`, `CELERY_BROKER_URL` - Redis

## Testing

```bash
pytest -v
```

## Deployment

### Railway (Recommended for Hackathon)

1. Connect your GitHub repo to Railway
2. Add a PostgreSQL service (Neon also works great)
3. Add a Redis service
4. Deploy this backend, set all env vars
5. Set build command: `pip install -r requirements.txt`
6. Set start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

## Integrations & Resilience

### Overview
All third-party integrations are designed with production-grade resilience:
- **Circuit breakers**: Open after 5 consecutive failures to avoid overwhelming services
- **Exponential backoff**: Retry with increasing delays (1s → 4s → 8s)
- **Fallback data**: Hardcoded critical resources if services are unavailable
- **Redis caching**: Minimize repeated calls with centralized TTLs
- **No PII logging**: All logs are PII-free
- **Idempotent background tasks**: Safe to retry with Celery


### Integration Details

| Integration | Rate Limits (Service) | Cache TTL | Fallback |
|---|---|---|---|
| **Twilio SMS** | 1 API call per SMS, queued via Celery | N/A | Local queue + log-only |
| **Google Maps** | Quota controlled by API key | Geocode: 30 days, Places: 30 min, Details:24h | TX/CA/NY/FL/IL hardcoded resources + 211 |
| **HUD API** | Limited by HUD API key | 1 hour | Fallback HUD-like resources + 211 |
| **211 API** | Limited by 211 API key |1 hour | Fallback resources per state |
| **Data.gov** | Limited by Data.gov API key |24 hours | Basic federal housing rights |


### Demo Prep
Before demo, warm up caches and pre-generate assets by running:
```bash
python prep_demo.py
```


### Testing Integrations
All integration tests mock external services (no live API calls!)
```bash
pytest tests/integrations -v
```


## License

MIT
