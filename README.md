# Fuel Route Optimizer API

A Django REST API that calculates optimal fuel stops along a route between two US locations, considering fuel prices and vehicle range constraints.

## Features

- **Route Planning**: Get detailed route information between any two US locations
- **Optimal Fuel Stops**: Automatically calculates the best fuel stops based on:
  - Vehicle range (500 miles maximum)
  - Fuel prices from a comprehensive database
  - Cost optimization (selects cheapest stations along route)
- **Fuel Cost Calculation**: Calculates total trip cost assuming 10 MPG fuel efficiency
- **Map Visualization**: Returns encoded route polyline for mapping applications
- **Fast Performance**: Minimizes external API calls (1 routing API call per request)

## Technical Stack

- **Framework**: Django 4.2.9
- **API**: Django REST Framework 3.14.0
- **Routing Service**: OpenRouteService API (with fallback)
- **Geocoding**: OpenRouteService (Nominatim fallback via Geopy)
- **Distance Calculations**: GeoPy geodesic

## Installation

### Option A: Run locally

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment** (optional, for OpenRouteService routing):
   ```bash
   cp .env.example .env
   # Edit .env and set OPENROUTESERVICE_API_KEY=your_key
   ```
   Without an API key, the app uses fallback geodesic routing.

3. **Run migrations**:
   ```bash
   python manage.py migrate
   ```

4. **Start the development server**:
   ```bash
   python manage.py runserver
   ```

   The API will be available at **`http://localhost:8000/api/`**.

### Option B: Run with Docker

1. **Create environment file** (optional):
   ```bash
   cp .env.example .env
   # Edit .env and set OPENROUTESERVICE_API_KEY=your_key
   ```

2. **Build and start**:
   ```bash
   docker-compose up --build
   ```

3. **Optional – run migrations** (if you add database models):
   ```bash
   docker-compose exec web python manage.py migrate
   ```

4. **Optional – development server** (auto-reload):
   ```bash
   docker-compose run --service-ports web python manage.py runserver 0.0.0.0:8000
   ```

   Stop with `docker-compose down`. The CSV file is mounted so you can update fuel data without rebuilding.

## API Endpoints

### 1. Health Check

```http
GET /api/health/
```

**Response** (`200 OK`):

```json
{
    "status": "healthy",
    "service": "Fuel Route Optimizer API",
    "version": "1.0.0"
}
```

### 2. Optimal Route Planning

```http
POST /api/route/
Content-Type: application/json
```

**Request body**:

```json
{
    "start": "New York, NY",
    "finish": "Los Angeles, CA"
}
```

**Response** (`200 OK`):

```json
{
    "route": {
        "start_location": "New York, NY",
        "end_location": "Los Angeles, CA",
        "total_distance_miles": 2789.0,
        "estimated_duration_minutes": 2450
    },
    "fuel_strategy": {
        "vehicle_range_miles": 500,
        "vehicle_mpg": 10,
        "total_fuel_needed_gallons": 278.9
    },
    "fuel_stops": [
        {
            "stop_number": 1,
            "station_name": "Shell",
            "city": "Columbus, OH",
            "latitude": 39.9612,
            "longitude": -82.9988,
            "distance_from_start_miles": 470.0,
            "fuel_price_per_gallon": 3.15,
            "fuel_added_gallons": 50.0,
            "cost_for_this_stop": 157.5
        }
    ],
    "total_fuel_cost": 875.35
}
```

**Error – non-USA location** (`400 Bad Request`):

```json
{
    "error": "Location error",
    "details": "Only USA location can be application this kind of"
}
```

**Error – invalid input** (`400 Bad Request`):

```json
{
    "error": "Invalid input",
    "details": {"start": ["This field is required."]}
}
```

## Example Usage

### cURL

```bash
# Health check
curl http://localhost:8000/api/health/

# Plan route (Chicago to Denver)
curl -X POST http://localhost:8000/api/route/ \
  -H "Content-Type: application/json" \
  -d '{"start": "Chicago, IL", "finish": "Denver, CO"}'

# Cross-country route
curl -X POST http://localhost:8000/api/route/ \
  -H "Content-Type: application/json" \
  -d '{"start": "New York, NY", "finish": "Los Angeles, CA"}'
```

### Python

```python
import requests

url = "http://localhost:8000/api/route/"
payload = {"start": "Chicago, IL", "finish": "Denver, CO"}

response = requests.post(url, json=payload)
response.raise_for_status()
result = response.json()

print(f"Distance: {result['route']['total_distance_miles']} miles")
print(f"Duration: {result['route']['estimated_duration_minutes']} min")
print(f"Total fuel cost: ${result['total_fuel_cost']:.2f}")
print(f"Fuel stops: {len(result['fuel_stops'])}")
for stop in result["fuel_stops"]:
    print(f"  {stop['stop_number']}. {stop['station_name']} — {stop['city']}")
```

### Handling errors

```python
import requests

response = requests.post(
    "http://localhost:8000/api/route/",
    json={"start": "Delhi", "finish": "Mumbai"}
)
if response.status_code == 400:
    err = response.json()
    print(err["error"], err["details"])  # USA-only validation
```


## Project Structure

```
.
├── fuel_route_api/              # Django project
│   ├── settings.py              # Project settings
│   ├── urls.py                  # Root URL routing
│   └── wsgi.py                  # WSGI entry (Gunicorn)
├── routes/                      # Route planning app
│   ├── services/
│   │   ├── routing_service.py   # Geocoding & routing (OpenRouteService)
│   │   ├── fuel_optimizer.py    # Fuel stop optimization (CSV)
│   │   └── us_state_coords.py   # US state centroids
│   ├── serializers.py          # Request/response validation
│   ├── views.py                # API views (route, health)
│   └── urls.py                 # App URL routing
├── manage.py
├── fuel_prices_uploaded.csv     # Fuel station data
├── requirements.txt
├── .env.example                 # OPENROUTESERVICE_API_KEY
├── Dockerfile
├── docker-compose.yml
└── README.md
```


## License

This project is provided as-is for evaluation purposes.

## Support

For questions or issues, please refer to the inline code documentation or examine the API response error messages.
