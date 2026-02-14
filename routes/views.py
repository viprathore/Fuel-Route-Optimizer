"""
Views for route planning API
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from .serializers import RouteRequestSerializer
from .services.routing_service import RoutingService
from .services.fuel_optimizer import FuelOptimizer


@method_decorator(csrf_exempt, name='dispatch')
class OptimalRouteView(APIView):
    """
    Calculate optimal route with fuel stops between two US locations.
    Vehicle range 500 miles, 10 MPG; uses real fuel prices from CSV.
    """

    def post(self, request):
        """Handle POST request for route planning"""
        # Validate input
        serializer = RouteRequestSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                {'error': 'Invalid input', 'details': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        start_location = serializer.validated_data['start']
        finish_location = serializer.validated_data['finish']
        
        try:
            # Initialize services
            routing_service = RoutingService()
            fuel_optimizer = FuelOptimizer()
            # Step 1: Geocode locations (uses OpenRouteService API)
            start_coords = routing_service.geocode_location(start_location)
            end_coords = routing_service.geocode_location(finish_location)
            # Step 2: Get route information (uses OpenRouteService API)
            route_data = routing_service.get_route(start_coords, end_coords)
            
            # Step 3: Find optimal fuel stops
            fuel_data = fuel_optimizer.find_optimal_fuel_stops(
                route_points=route_data['route_points'],
                total_distance_miles=route_data['distance_miles']
            )
            
            # Step 4: Build response in the required format
            route_geometry = route_data['geometry']

            fuel_stops_formatted = []
            for i, stop in enumerate(fuel_data['fuel_stops'], start=1):
                loc = stop.get('location', {})
                city = loc.get('city', '') or 'Unknown'
                state = loc.get('state', '') or ''
                city_display = f"{city}, {state}".strip(", ") if state else city
                fuel_stops_formatted.append({
                    'stop_number': i,
                    'station_name': stop.get('station_name', ''),
                    'city': city_display,
                    'latitude': loc.get('latitude'),
                    'longitude': loc.get('longitude'),
                    'distance_from_start_miles': round(stop.get('distance_from_start', 0), 2),
                    'fuel_price_per_gallon': round(stop.get('price_per_gallon', 0), 2),
                    'fuel_added_gallons': round(stop.get('gallons_purchased', 0), 2),
                    'cost_for_this_stop': round(stop.get('cost', 0), 2),
                })

            response_data = {
                'route': {
                    'start_location': start_location,
                    'end_location': finish_location,
                    'total_distance_miles': round(route_data['distance_miles'], 2),
                    'estimated_duration_minutes': int(round(route_data['duration_seconds'] / 60)),
                },
                'fuel_strategy': {
                    'vehicle_range_miles': fuel_data['vehicle_range'],
                    'vehicle_mpg': fuel_data['vehicle_mpg'],
                    'total_fuel_needed_gallons': round(fuel_data['total_gallons'], 2),
                },
                'fuel_stops': fuel_stops_formatted,
                'total_fuel_cost': round(fuel_data['total_fuel_cost'], 2),
            }

            return Response(response_data, status=status.HTTP_200_OK)
            
        except ValueError as e:
            return Response(
                {'error': 'Location error', 'details': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': 'Server error', 'details': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@method_decorator(csrf_exempt, name='dispatch')
class HealthCheckView(APIView):
    """Health check endpoint to verify API is running."""

    def get(self, request):
        """Return API health status"""
        return Response({
            'status': 'healthy',
            'service': 'Fuel Route Optimizer API',
            'version': '1.0.0'
        })
