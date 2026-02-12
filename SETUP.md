# Project Setup Guide

## Prerequisites
- Python 3.9+
- PostgreSQL
- Node.js and npm (for frontend)

## Backend Setup

### 1. Navigate to backend/config directory
```bash
cd backend/config
```

### 2. Create and activate virtual environment
```bash
python3 -m venv venv
source venv/bin/activate  # On macOS/Linux
# or
venv\Scripts\activate  # On Windows
```

### 3. Install Python dependencies
```bash
pip install -r ../requirements.txt
```

### 4. Configure environment variables
Create a `.env` file in `backend/config/` with:
```
SECRET_KEY=your-secret-key
DEBUG=True
DOMRIA_API_KEY=your-api-key
GEMINI_API_KEY=your-gemini-api-key
```

### 5. Setup PostgreSQL database
Create a database named `realty_db`:
```bash
psql -U postgres
CREATE DATABASE realty_db;
\q
```

Update database settings in `config/settings.py` if needed.

### 6. Run migrations
```bash
python manage.py migrate
```

### 7. Create superuser
```bash
python manage.py createsuperuser
```

### 8. Run development server
```bash
python manage.py runserver
```

The API will be available at `http://127.0.0.1:8000/`

## Frontend Setup

### 1. Navigate to frontend directory
```bash
cd frontend
```

### 2. Install dependencies
```bash
npm install
```

### 3. Run development server
```bash
npm start
```

## Common Issues

### "No module named 'django'"
- Make sure your virtual environment is activated
- Check you're using the correct venv: `which python`

### Database connection errors
- Verify PostgreSQL is running
- Check database credentials in `settings.py`
- Ensure database `realty_db` exists

### Port already in use
- Kill the process using the port or use a different port:
  ```bash
  python manage.py runserver 8001
  ```
