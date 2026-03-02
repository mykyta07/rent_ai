# Project Setup Guide

## Prerequisites
- Python 3.9+
- PostgreSQL
- Node.js and npm (for frontend)

## Backend Setup

### 1. Navigate to backend directory
```bash
cd backend
```

### 2. Create and activate virtual environment
```bash
python -m venv venv

# Activate on Windows
venv\Scripts\activate

# Activate on macOS/Linux
source venv/bin/activate
```

### 3. Install Python dependencies
```bash
pip install -r ../requirements.txt
```

If you encounter missing dependencies, install them manually:
```bash
# Core Django packages
pip install django djangorestframework django-cors-headers django-filter
pip install djangorestframework-simplejwt drf-spectacular

# Database
pip install psycopg[binary]  # PostgreSQL adapter

# AI and data processing
pip install google-generativeai python-dotenv
pip install numpy pandas scikit-learn

# HTML parsing (for import script)
pip install beautifulsoup4 lxml
```

### 4. Configure environment variables
Create a `.env` file in `backend/config/` with:
```
# Django Settings
SECRET_KEY=your-secret-key
DEBUG=True

# Database
DB_NAME=realty_db
DB_USER=user
DB_PASSWORD=1234
DB_HOST=localhost
DB_PORT=5432

# DOM.RIA API
DOMRIA_API_KEY=your-api-key

# Gemini API (for AI embeddings)
GEMINI_API_KEY=your-gemini-api-key
```

### 5. Setup PostgreSQL database
Create a database and user:
```bash
psql -U postgres
```

Then in PostgreSQL:
```sql
-- Create user
CREATE USER "user" WITH PASSWORD '1234';

-- Create database
CREATE DATABASE realty_db OWNER "user";

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE realty_db TO "user";

-- For PostgreSQL 15+, grant schema privileges
\c realty_db
GRANT ALL ON SCHEMA public TO "user";

-- Exit
\q
```

**Note:** Make sure the credentials match your `.env` file.

### 6. Run migrations
Navigate to the config directory where `manage.py` is located:
```bash
cd config
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

## Data Management

### Import Properties from HTML Files

Place your DOM.RIA HTML files in the `html/` folder (in project root, next to `backend/`), then run:

```bash
# Import from all HTML files
python manage.py import_from_html

# Import from a specific file
python manage.py import_from_html --file lviv_flat_rent.html

# Limit number of properties to import
python manage.py import_from_html --limit 50

# Combine options
python manage.py import_from_html --file lviv_flat_rent.html --limit 20
```

The script will:
- Parse DOM.RIA HTML property listings
- Extract property details (price, rooms, area, location)
- Automatically detect sale type (rent/sale) from URL
- Save properties with photos and locations to database
- Skip duplicates based on DOM.RIA ID
- Display progress with ✓/✗ and statistics

HTML files location: `d:\UNIVER\diploma\rent_ai\html\`

### Generate AI Embeddings for Semantic Search

After importing properties, generate embeddings for AI-powered search:

```bash
# Generate embeddings for new properties (without embeddings)
python manage.py generate_embeddings

# Regenerate all embeddings (force refresh)
python manage.py generate_embeddings --force

# Process limited number of properties
python manage.py generate_embeddings --limit 10
```

The script will:
- Use Gemini AI to create vector embeddings
- Enable semantic search functionality
- Show progress and coverage statistics
- Skip properties that already have embeddings (unless `--force`)

**Note:** Requires valid `GEMINI_API_KEY` in `.env` file.

### Typical Workflow

1. Add HTML files to `html/` folder
2. Import properties: `python manage.py import_from_html`
3. Generate embeddings: `python manage.py generate_embeddings`
4. Start server: `python manage.py runserver`

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
