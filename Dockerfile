# LUCA Command Center (Django CRM) Dockerfile
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=telis.settings

# Install system dependencies
# gcc, build-essential for compiling Python packages
# libpq-dev for PostgreSQL support (if needed later)
# curl for healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    make \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Copy requirements files
COPY requirements.txt .
COPY telis_recruitment/requirements.txt telis_recruitment/

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -r telis_recruitment/requirements.txt

# Copy project files
COPY . .

# Set working directory to Django app
WORKDIR /app/telis_recruitment

# Collect static files
RUN python manage.py collectstatic --noinput

# Create directories for data persistence
RUN mkdir -p /app/telis_recruitment/media /app/telis_recruitment/staticfiles

# Expose port
EXPOSE 8000

# Run gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "120", "telis.wsgi:application"]
