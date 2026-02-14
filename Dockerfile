# Fuel Route Optimizer API
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create placeholder for fuel CSV if missing (app may expect the file)
RUN touch fuel_prices_uploaded.csv 2>/dev/null || true

EXPOSE 8000

# Run with gunicorn; override with docker-compose command for dev (e.g. runserver)
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "fuel_route_api.wsgi:application"]
