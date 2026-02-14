"""
Routing service using OpenRouteService API
"""
import requests
from typing import Dict, List, Tuple
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
from django.conf import settings

# Approximate bounding boxes for USA (50 states): continental, Alaska, Hawaii
USA_BOUNDS = [
    (24.5, -125.0, 49.5, -66.0),   # Continental US
    (51.0, -180.0, 71.5, -129.0),  # Alaska
    (18.9, -160.3, 22.3, -154.8),  # Hawaii
]


def is_in_usa(lat: float, lon: float) -> bool:
    """Return True if (lat, lon) is within USA (50 states)."""
    for lat_lo, lon_lo, lat_hi, lon_hi in USA_BOUNDS:
        if lat_lo <= lat <= lat_hi and lon_lo <= lon <= lon_hi:
            return True
    return False


class RoutingService:
    """Service for getting route information from OpenRouteService"""
    
    def __init__(self):
        self.api_key = settings.OPENROUTESERVICE_API_KEY
        self.base_url = "https://api.openrouteservice.org/v2/directions/driving-car/geojson"
        self.geocoder = Nominatim(user_agent="fuel_route_optimizer", timeout=10)
    
    def geocode_location(self, location: str) -> Tuple[float, float]:
        """
        Convert location string to coordinates (latitude, longitude) using OpenRouteService
        Falls back to Nominatim if OpenRouteService fails
        """
        # Try OpenRouteService geocoding first
        try:
            geocode_url = "https://api.openrouteservice.org/geocode/search"
            headers = {
                'Authorization': self.api_key
            }
            params = {
                'text': location,
                'size': 1  # Only return top result
            }
            
            response = requests.get(
                geocode_url,
                headers=headers,
                params=params,
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                if data.get('features') and len(data['features']) > 0:
                    lon, lat = data["features"][0]["geometry"]["coordinates"]
                    lat, lon = float(lat), float(lon)
                    if not is_in_usa(lat, lon):
                        raise ValueError(
                            "Only USA location can be application this kind of"
                        )
                    return (lat, lon)

        except ValueError:
            raise
        except Exception as e:
            # If OpenRouteService fails, try fallback
            pass
        
        # Fallback to Nominatim geocoding (no USA suffix so we get actual place)
        try:
            location_query = f"{location}"
            location_data = self.geocoder.geocode(location_query)
            
            if location_data:
                lat, lon = location_data.latitude, location_data.longitude
                if not is_in_usa(lat, lon):
                    raise ValueError(
                        "Only USA location can be application this kind of"
                    )
                return (lat, lon)
            else:
                raise ValueError(f"Could not geocode location: {location}")
        except ValueError:
            raise
        except Exception as e:
            raise ValueError(f"Geocoding error for '{location}': {str(e)}")
    
    def get_route(self, start_coords: Tuple[float, float], end_coords: Tuple[float, float]) -> Dict:
        """
        Get route information from OpenRouteService
        Returns route with distance, duration, and geometry
        """
        headers = {
            'Authorization': self.api_key,
            'Content-Type': 'application/json'
        }
        
        # OpenRouteService expects [longitude, latitude]
        body = {
            "coordinates": [
                [start_coords[1], start_coords[0]],  # start: [lon, lat]
                [end_coords[1], end_coords[0]]        # end: [lon, lat]
            ]

        }
        try:
            response = requests.post(
                self.base_url,
                json=body,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                route = data['features'][0]
                geometry = route['geometry']['coordinates']
                route_points = [(lat, lon) for lon, lat in geometry]
                summary = route['properties']['summary']

                return {
                    "distance_meters": summary['distance'],
                    "distance_miles": summary['distance'] / 1609.34,
                    "duration_seconds": summary['duration'],
                    "route_points": route_points,
                    "geometry": geometry
                }
            else:
                # Fallback to simple straight-line calculation if API fails
                return self._fallback_route(start_coords, end_coords)
                
        except Exception as e:
            # Fallback to simple calculation if API is unavailable
            return self._fallback_route(start_coords, end_coords)
    
    def _fallback_route(self, start_coords: Tuple[float, float], end_coords: Tuple[float, float]) -> Dict:
        """
        Fallback route calculation using geodesic distance
        Creates a simple straight line with interpolated points
        """
        distance_miles = geodesic(start_coords, end_coords).miles
        
        # Create interpolated points along the route (every ~50 miles)
        num_points = max(int(distance_miles / 50), 2)
        route_points = []
        
        for i in range(num_points + 1):
            fraction = i / num_points
            lat = start_coords[0] + (end_coords[0] - start_coords[0]) * fraction
            lon = start_coords[1] + (end_coords[1] - start_coords[1]) * fraction
            route_points.append((lat, lon))
        
        # Estimate duration (assume 60 mph average)
        duration_seconds = (distance_miles / 60) * 3600
        
        return {
            'distance_meters': distance_miles * 1609.34,
            'distance_miles': distance_miles,
            'duration_seconds': duration_seconds,
            'route_points': route_points,
            'geometry': [[lon, lat] for lat, lon in route_points],
            'fallback': True
        }
