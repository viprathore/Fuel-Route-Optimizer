"""
Fuel stop optimizer service
Finds optimal fuel stops along a route based on price and vehicle range
"""
import csv
import logging
from typing import Dict, List, Tuple
from geopy.distance import geodesic
from django.conf import settings
from .us_state_coords import US_STATE_COORDS

logger = logging.getLogger(__name__)


class FuelOptimizer:
    """Service for optimizing fuel stops along a route"""
    
    def __init__(self):
        self.fuel_stations = []  # Will be loaded lazily
        self.raw_stations_data = None  # Cache the raw CSV data
        self.max_range_miles = 500  # Maximum vehicle range
        self.mpg = 10  # Miles per gallon
    
    def _load_raw_stations_data(self) -> List[Dict]:
        """Load raw fuel stations data from CSV (without geocoding)"""
        if self.raw_stations_data is not None:
            return self.raw_stations_data
        
        stations = []
        try:
            with open(settings.FUEL_PRICES_CSV, 'r') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    stations.append({
                        'name': row['Truckstop Name'].strip(),
                        'city': row['City'].strip(),
                        'state': row['State'].strip(),
                        'address': row.get('Address', '').strip(),
                        'price': float(row['Retail Price'])
                    })
            self.raw_stations_data = stations
            logger.info("Loaded %s fuel stations from %s", len(stations), settings.FUEL_PRICES_CSV)
        except Exception as e:
            logger.exception("Error loading fuel prices from %s: %s", settings.FUEL_PRICES_CSV, e)
            raise Exception(f"Error loading fuel prices: {str(e)}")

        return stations
    
    def _get_stations_near_route(self, route_points: List[Tuple[float, float]], max_distance_miles: float = 100) -> List[Dict]:
        """
        Get stations near the route using state centroids only (no geocoding).
        Uses a generous state-to-route distance (250 mi) so we include all states
        the route passes through; stations use state centroid as position.
        """
        raw_stations = self._load_raw_stations_data()
        # Sample route points
        step = max(1, len(route_points) // 15)
        route_sample = list(route_points[::step])
        if route_points and route_sample[-1] != route_points[-1]:
            route_sample.append(route_points[-1])

        # States whose centroid is within 250 mi of the route (generous: route may
        # only clip a corner of a large state)
        state_route_miles = 250
        states_near_route = set()
        for rp in route_sample:
            for state, coords in US_STATE_COORDS.items():
                if geodesic(coords, rp).miles <= state_route_miles:
                    states_near_route.add(state)

        # All stations in those states; position = state centroid
        # Dedupe by (name, city, state), keep lowest price
        by_key = {}
        for station in raw_stations:
            state = station['state'].upper().strip()
            if state not in states_near_route or state not in US_STATE_COORDS:
                continue
            coords = US_STATE_COORDS[state]
            city = station['city'].strip()
            key = (station['name'], city, state)
            entry = {
                'name': station['name'],
                'latitude': coords[0],
                'longitude': coords[1],
                'price': station['price'],
                'city': station['city'],
                'state': state
            }
            if key not in by_key or station['price'] < by_key[key]['price']:
                by_key[key] = entry

        result = list(by_key.values())
        logger.info("Stations near route: %s states, %s stations", len(states_near_route), len(result))
        return result
    
    def find_optimal_fuel_stops(
        self, 
        route_points: List[Tuple[float, float]], 
        total_distance_miles: float
    ) -> Dict:
        """
        Find optimal fuel stops along the route
        
        Args:
            route_points: List of (latitude, longitude) tuples representing the route
            total_distance_miles: Total distance of the route in miles
        
        Returns:
            Dictionary with fuel stops and cost information
        """
        # Load stations from states along the route (generous radius so we don't miss states)
        self.fuel_stations = self._get_stations_near_route(route_points, max_distance_miles=100)
        
        fuel_stops = []
        total_fuel_cost = 0.0
        
        # Start position
        current_position = route_points[0]
        remaining_range = self.max_range_miles
        distance_covered = 0.0
        
        # Track position along route
        route_index = 0
        
        while distance_covered < total_distance_miles:
            # Calculate how far we can go before needing fuel
            distance_to_next_fuel = min(remaining_range, total_distance_miles - distance_covered)
            
            # Find the position where we need to refuel
            target_position, new_route_index, segment_distance = self._advance_along_route(
                route_points, 
                route_index, 
                distance_to_next_fuel
            )
            
            route_index = new_route_index
            distance_covered += segment_distance
            remaining_range -= segment_distance
            
            # If we haven't reached the end, we need to refuel
            if distance_covered < total_distance_miles and remaining_range < 100:  # Refuel with 100 miles buffer
                # Find stations near the current position
                nearby_stations = self._find_nearby_stations(target_position, max_distance_miles=50)
                
                if nearby_stations:
                    # Select the cheapest station
                    best_station = min(nearby_stations, key=lambda s: s['price'])
                    
                    # Calculate fuel needed (fill up to max range)
                    gallons_needed = (self.max_range_miles - remaining_range) / self.mpg
                    fuel_cost = gallons_needed * best_station['price']
                    
                    fuel_stops.append({
                        'station_name': best_station['name'],
                        'location': {
                            'latitude': best_station['latitude'],
                            'longitude': best_station['longitude'],
                            'city': best_station['city'],
                            'state': best_station['state']
                        },
                        'price_per_gallon': best_station['price'],
                        'gallons_purchased': round(gallons_needed, 2),
                        'cost': round(fuel_cost, 2),
                        'distance_from_start': round(distance_covered, 2)
                    })
                    
                    total_fuel_cost += fuel_cost
                    remaining_range = self.max_range_miles  # Tank is full
                else:
                    # No stations found nearby, use estimated price
                    if self.fuel_stations:
                        average_price = sum(s['price'] for s in self.fuel_stations) / len(self.fuel_stations)
                    else:
                        average_price = 3.5  # fallback default $/gallon
                    gallons_needed = (self.max_range_miles - remaining_range) / self.mpg
                    fuel_cost = gallons_needed * average_price
                    
                    fuel_stops.append({
                        'station_name': 'Estimated Station',
                        'location': {
                            'latitude': target_position[0],
                            'longitude': target_position[1],
                            'city': 'Unknown',
                            'state': 'Unknown'
                        },
                        'price_per_gallon': round(average_price, 2),
                        'gallons_purchased': round(gallons_needed, 2),
                        'cost': round(fuel_cost, 2),
                        'distance_from_start': round(distance_covered, 2),
                        'note': 'No stations found nearby, using estimated price'
                    })
                    
                    total_fuel_cost += fuel_cost
                    remaining_range = self.max_range_miles
        
        # Calculate total fuel consumption
        total_gallons = total_distance_miles / self.mpg
        logger.info(
            "Optimal fuel stops: %s stops, total_cost=%.2f, total_gallons=%.2f",
            len(fuel_stops), total_fuel_cost, total_gallons
        )
        return {
            'fuel_stops': fuel_stops,
            'total_fuel_cost': round(total_fuel_cost, 2),
            'total_gallons': round(total_gallons, 2),
            'number_of_stops': len(fuel_stops),
            'vehicle_mpg': self.mpg,
            'vehicle_range': self.max_range_miles
        }
    
    def _advance_along_route(
        self, 
        route_points: List[Tuple[float, float]], 
        start_index: int, 
        target_distance: float
    ) -> Tuple[Tuple[float, float], int, float]:
        """
        Advance along the route for a given distance
        
        Returns:
            (final_position, final_index, actual_distance_traveled)
        """
        current_index = start_index
        distance_traveled = 0.0
        current_position = route_points[current_index]
        
        while current_index < len(route_points) - 1:
            next_position = route_points[current_index + 1]
            segment_distance = geodesic(current_position, next_position).miles
            
            if distance_traveled + segment_distance >= target_distance:
                # We've reached our target distance
                # Interpolate the exact position
                remaining_distance = target_distance - distance_traveled
                fraction = remaining_distance / segment_distance if segment_distance > 0 else 0
                
                interpolated_lat = current_position[0] + (next_position[0] - current_position[0]) * fraction
                interpolated_lon = current_position[1] + (next_position[1] - current_position[1]) * fraction
                
                return ((interpolated_lat, interpolated_lon), current_index, target_distance)
            
            distance_traveled += segment_distance
            current_position = next_position
            current_index += 1
        
        # Reached the end of the route
        return (route_points[-1], len(route_points) - 1, distance_traveled)
    
    def _find_nearby_stations(
        self, 
        position: Tuple[float, float], 
        max_distance_miles: float = 50
    ) -> List[Dict]:
        """
        Find fuel stations near the given position. Since station positions are
        state centroids, we treat "nearby" as: station is in a state whose
        centroid is within 250 mi of position (matches state loading radius).
        """
        # Stations use state centroid as position. "Nearby" = in a state whose
        # centroid is within this radius of the refuel point (250 mi handles
        # large states where the route is far from the state center).
        state_radius_miles = 250
        states_near_position = {
            state for state, coords in US_STATE_COORDS.items()
            if geodesic(coords, position).miles <= state_radius_miles
        }

        nearby_stations = []
        for station in self.fuel_stations:
            if station['state'] not in states_near_position:
                continue
            station_position = (station['latitude'], station['longitude'])
            distance = geodesic(position, station_position).miles
            station_with_distance = station.copy()
            station_with_distance['distance_from_route'] = distance
            nearby_stations.append(station_with_distance)

        nearby_stations.sort(key=lambda s: s['price'])
        return nearby_stations
