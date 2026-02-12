# rent_ai

AI-powered real estate platform with Django backend and property search functionality.

## Quick Start

For detailed setup instructions, see [SETUP.md](SETUP.md)

### Installation Summary
```bash
# Backend
cd backend/config
python3 -m venv venv
source venv/bin/activate
pip install -r ../requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## Project Structure
- `backend/` - Django REST API
  - `config/` - Main Django project
  - `ai/` - AI chat functionality with Gemini
  - `properties/` - Property management
  - `users/` - User authentication
- `frontend/` - Frontend application