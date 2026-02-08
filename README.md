# ANNA - Financial Operations Platform

Multi-tenant financial operations platform built for Tanzania.

## Features

### Wakala Management
- Track day-to-day financial operations
- Financial day management (open → operate → close)
- Transaction recording with balancing
- Agent management

### Mchezo Groups
- Rotating savings (ROSCA) management
- Cycle tracking
- Contribution and payout management
- Default detection

### Security & Compliance
- Comprehensive audit logging
- Role-based access control
- Soft deletes only
- Tanzania-compliant

## Quick Start

### Prerequisites
- Python 3.10+
- Django 5.0+

### Installation

```bash
# Clone the repository
cd annacash

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Start development server
python manage.py runserver
```

### Access
- Admin: http://localhost:8000/admin/
- App: http://localhost:8000/

## Project Structure

```
annacash/
├── accounts/          # Custom user model
├── core/             # Base models, roles, audit
├── wakala/           # Financial operations domain
├── transactions/     # Transaction service layer
├── balancing/       # Daily balancing engine
├── mchezo/          # Rotating savings domain
├── dashboard/        # Role-based dashboards
├── config/          # Networks, banks, fee rules
├── audit/            # Audit log viewing
├── templates/        # Django templates
└── annacash/         # Project settings
```

## Technology Stack

- **Backend**: Django 5.0, Python 3.10+
- **Database**: SQLite (dev), PostgreSQL (prod)
- **Frontend**: Django templates, Vanilla JS, Bootstrap 5, Chart.js
- **Deployment**: Ready for Linux/Docker

## Configuration

Copy `.env.example` to `.env` and configure:

```bash
SECRET_KEY=your-secret-key
DEBUG=True
DATABASE_URL=sqlite:///db.sqlite3
```

## License

Proprietary - All rights reserved
