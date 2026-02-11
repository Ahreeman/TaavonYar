# TaavonYar

TaavonYar is a Django-based cooperative investment platform where users can register as shareholders, contribute to cooperative projects, and buy/sell cooperative shares through both primary and secondary markets.

## What the project does

The platform combines four core domains:

- **Accounts & roles**: user registration, identity profiles, and role-based dashboards (shareholder / board member).
- **Cooperatives**: cooperative listing/detail pages and board-member management.
- **Projects**: fundraising projects under cooperatives with contribution tracking and share distribution.
- **Share marketplace**: primary share sales (from cooperative), secondary listings (peer-to-peer), holdings, and trade history.

## Tech stack

- **Backend**: Django 5.1
- **Database**: PostgreSQL 16
- **Testing**: pytest + pytest-django + factory-boy
- **Containerization**: Docker / Docker Compose
- **Media handling**: Pillow (image uploads for cooperatives/projects)

## Repository structure

```text
.
├── backend/
│   ├── accounts/      # registration, profile, role switching
│   ├── coops/         # cooperatives and board member workflows
│   ├── projects/      # project funding and share distribution logic
│   ├── shares/        # holdings, listings, trades, marketplace flows
│   ├── taavonyar/     # Django settings/urls/wsgi/asgi
│   ├── templates/     # HTML templates per app
│   ├── static/        # CSS/assets
│   ├── requirements.txt
│   └── manage.py
├── docker-compose.yml
├── docker-compose.ci.yml
└── jenkins/
```

## Core business flows

### 1) Registration and user profile

- New users register and automatically get:
  - an `Individual` identity record,
  - a default `Shareholder` profile.
- Users can switch dashboard mode when they have multiple roles.

### 2) Cooperative board management

- Accepted board members can add new board members using a shareholder ID.
- Board operations include CSV exports for shareholder and trade summaries.

### 3) Project funding and distribution

- Shareholders contribute to active projects.
- A project can be marked done; shares are distributed proportionally to contribution amounts.
- Rounding shares are assigned deterministically to highest fractional remainders.

### 4) Share trading

- **Primary market**: buy directly from cooperative `available_primary_shares`.
- **Secondary market**: buy from active peer listings.
- **Auto source mode**: fulfills from primary first, then secondary.
- Every purchase creates immutable `ShareTrade` records and updates `ShareHolding`.

## Prerequisites

- Docker + Docker Compose (recommended)

For non-Docker local development:

- Python 3.12+
- PostgreSQL 16+

## Quick start (Docker)

From repository root:

```bash
docker compose up --build
```

Then open:

- App: http://localhost:8000
- Admin: http://localhost:8000/admin

Default compose services:

- `db`: PostgreSQL (`taavonyar` / `taavonyar` / `admin`)
- `web`: Django dev server (auto-runs migrations on start)

## Quick start (local Python)

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Set environment variables (example):

```bash
export DJANGO_DEBUG=1
export DJANGO_SECRET_KEY='dev-secret-key-change-later'
export DJANGO_ALLOWED_HOSTS='localhost,127.0.0.1'

export POSTGRES_DB='taavonyar'
export POSTGRES_USER='taavonyar'
export POSTGRES_PASSWORD='admin'
export POSTGRES_HOST='localhost'
export POSTGRES_PORT='5432'
```

Run:

```bash
python manage.py migrate
python manage.py runserver
```

## Running tests

### With Docker Compose

```bash
docker compose -f docker-compose.yml -f docker-compose.ci.yml up -d db
sleep 10
docker compose -f docker-compose.yml -f docker-compose.ci.yml run --rm web pytest
```

### Local (if PostgreSQL is configured)

```bash
cd backend
pytest
```

## Main app routes

- `/` home
- `/accounts/` login/register/profile/dashboard
- `/coops/` cooperative pages + board actions
- `/projects/` project listing/detail/contribution + board project management
- `/shares/` shareholder dashboard, marketplace, listings, trades, exports

## CI/CD notes

- Jenkins pipelines are included under `jenkins/`.
- CI build/test flow uses Docker Compose and pytest.

## Development notes

- Database defaults to PostgreSQL in `taavonyar/settings.py`.
- Uploaded media files are served under `/media/` in debug mode.
- Static files are expected in `backend/static/`.

## License

No explicit license file is currently included in this repository.
