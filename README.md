# NEXAS - NGO Management System

A comprehensive Django-based management system for NGOs, featuring role-based dashboards for administrators, campaign managers, donation managers, and volunteers.

## Features

- **Multi-role Dashboard System**
  - Admin Dashboard - Complete system oversight
  - Campaign Dashboard - Campaign management and tracking
  - Donation Dashboard - Donation tracking and management  
  - Volunteer Dashboard - Volunteer coordination

- **User Management**
  - Role-based access control
  - Secure authentication system
  - User profile management

- **Core Functionality**
  - Campaign management
  - Donation tracking
  - Volunteer coordination
  - Administrative oversight

## Tech Stack

- **Backend**: Django 4.2.7
- **Database**: SQLite (default) / PostgreSQL support
- **Task Queue**: Celery with Redis
- **Frontend**: Django Templates with Bootstrap 5
- **Authentication**: Django built-in auth with custom user model

## Quick Start

### Prerequisites

- Python 3.8+
- pip

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd nexas_backend
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run database migrations**
   ```bash
   python manage.py migrate
   ```

4. **Start the application**
   ```bash
   python start_nexas.py
   ```

   Or use the traditional Django approach:
   ```bash
   python manage.py runserver
   ```

## Login Credentials

The application comes with pre-configured test users:

| Role | Email | Password |
|------|--------|----------|
| Admin | admin@nexas.com | nexas123 |
| Campaign Manager | campaign@nexas.com | nexas123 |
| Donation Manager | donation@nexas.com | nexas123 |
| Volunteer | volunteer@nexas.com | nexas123 |

## Access URLs

- **Login**: http://localhost:8000/
- **Admin Dashboard**: http://localhost:8000/dashboard/admin/
- **Django Admin**: http://localhost:8000/admin/

## Project Structure

```
nexas_backend/
├── apps/                          # Application modules
│   ├── accounts/                  # User management
│   ├── admin_dashboard/           # Admin functionality
│   ├── campaign_dashboard/        # Campaign management
│   ├── donation_dashboard/        # Donation tracking
│   └── volunteer_dashboard/       # Volunteer coordination
├── nexas_project/                 # Django project settings
├── static/                        # Static files
├── staticfiles/                   # Collected static files
├── templates/                     # HTML templates
├── logs/                          # Application logs
├── db.sqlite3                     # SQLite database
├── manage.py                      # Django management script
├── requirements.txt               # Python dependencies
├── start_nexas.py                # Application startup script
└── start_server.bat              # Windows batch file
```

## Development

### Running Tests
```bash
python manage.py test
```

### Collecting Static Files
```bash
python manage.py collectstatic
```

### Creating Superuser
```bash
python manage.py createsuperuser
```

## Production Deployment

1. **Set environment variables**
   - Configure database settings
   - Set DEBUG=False
   - Configure allowed hosts
   - Set secret key

2. **Database Setup**
   - Configure PostgreSQL for production
   - Run migrations

3. **Static Files**
   - Configure static file serving
   - Run collectstatic

4. **Web Server**
   - Use Gunicorn with Nginx
   - Configure SSL certificates

## Dependencies

Key dependencies include:
- Django 4.2.7 - Web framework
- Django REST Framework - API development
- Pillow - Image processing
- Celery - Task queue
- Redis - Message broker
- PostgreSQL adapter - Database
- Gunicorn - WSGI server
- WhiteNoise - Static file serving

## Support

For support and questions, please contact the development team.
