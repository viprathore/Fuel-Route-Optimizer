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

## API Endpoints

### 1. Health Check
```
GET /api/health/
```

**Response**:
```json
{
    "status": "healthy",
    "service": "Fuel Route Optimizer API",
    "version": "1.0.0"
}
```

### 2. Optimal Route Planning
```
POST /api/route/
```

**Request Body**:
```json
{
    "start": "New York, NY",
    "finish": "Los Angeles, CA"
}
```

**Response**:
```json
{
    "route": {
        "start_location": "New York, NY",
        "end_location": "Los Angeles, CA",
        "total_distance_miles": 2789,
        "estimated_duration_minutes": 2450,
        "route_polyline": "encoded_polyline_string_for_map"
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
            "distance_from_start_miles": 470,
            "fuel_price_per_gallon": 3.15,
            "fuel_added_gallons": 50,
            "cost_for_this_stop": 157.50
        }
    ],
    "total_fuel_cost": 875.35
}
```

## Example Usage

### Using cURL

```bash
# Simple route
curl -X POST http://localhost:8000/api/route/ \
  -H "Content-Type: application/json" \
  -d '{"start": "Chicago, IL", "finish": "Denver, CO"}'

# Cross-country route
curl -X POST http://localhost:8000/api/route/ \
  -H "Content-Type: application/json" \
  -d '{"start": "New York, NY", "finish": "Los Angeles, CA"}'
```

### Using Python

```python
import requests

url = "http://localhost:8000/api/route/"
data = {
    "start": "Chicago, IL",
    "finish": "Denver, CO"
}

response = requests.post(url, json=data)
result = response.json()

print(f"Total distance: {result['route']['total_distance_miles']} miles")
print(f"Total fuel cost: ${result['total_fuel_cost']}")
print(f"Number of fuel stops: {len(result['fuel_stops'])}")
```


## Project Structure

```
.
├── fuel_route_api/          # Django project settings
│   ├── settings.py          # Configuration
│   └── urls.py              # Main URL routing
├── routes/                  # Main application
│   ├── services/            # Business logic
│   │   ├── routing_service.py   # Route calculation & geocoding
│   │   └── fuel_optimizer.py    # Fuel stop optimization (CSV-based)
│   ├── polyline_utils.py    # Encoded polyline for map display
│   ├── serializers.py       # Request validation
│   ├── views.py             # API endpoints
│   └── urls.py              # App URL routing
├── fuel_prices_uploaded.csv # Fuel station prices (CSV)
├── requirements.txt         # Python dependencies
└── README.md                # This file
```

## Future Enhancements

Potential improvements:

1. **Real-time Fuel Prices**: Integration with live fuel price APIs
2. **Multiple Routes**: Compare different route options
3. **User Preferences**: Allow custom MPG, range, and price preferences
4. **Caching**: Cache route calculations for popular routes
5. **WebSocket Updates**: Real-time route updates
6. **Database Storage**: Move fuel prices to PostgreSQL/MySQL
7. **Authentication**: API key authentication for production use
8. **Rate Limiting**: Prevent API abuse
9. **Map UI**: Web interface with interactive map
10. **EV Support**: Add electric vehicle charging station support

## License

This project is provided as-is for evaluation purposes.

## Support

For questions or issues, please refer to the inline code documentation or examine the API response error messages.
