#!/usr/bin/env python3
"""
Test script for Fuel Route Optimizer API

This script tests various routes and displays the results.
"""

import requests
import json
import time


def print_section(title):
    """Print a formatted section header"""
    print("\n" + "=" * 80)
    print(f" {title}")
    print("=" * 80 + "\n")


def test_health_check():
    """Test the health check endpoint"""
    print_section("Testing Health Check Endpoint")
    
    try:
        response = requests.get("http://localhost:8000/api/health/")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False


def test_route(start, finish, description):
    """Test a route and display results"""
    print_section(f"Testing Route: {description}")
    print(f"Start: {start}")
    print(f"Finish: {finish}\n")
    
    try:
        start_time = time.time()
        
        response = requests.post(
            "http://localhost:8000/api/route/",
            json={"start": start, "finish": finish},
            headers={"Content-Type": "application/json"}
        )
        
        elapsed_time = time.time() - start_time
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Time: {elapsed_time:.2f} seconds\n")
        
        if response.status_code == 200:
            data = response.json()
            
            print("ROUTE SUMMARY:")
            print(f"  Total Distance: {data['total_distance_miles']:.2f} miles")
            print(f"  Estimated Duration: {data['estimated_duration_hours']:.2f} hours")
            print(f"  Number of Fuel Stops: {data['number_of_fuel_stops']}")
            print(f"  Total Fuel Cost: ${data['total_fuel_cost']:.2f}")
            print(f"  Total Gallons: {data['total_gallons']:.2f} gallons")
            print(f"  Vehicle MPG: {data['vehicle_info']['mpg']}")
            print(f"  Vehicle Range: {data['vehicle_info']['max_range_miles']} miles")
            
            if data['fuel_stops']:
                print("\nFUEL STOPS:")
                for i, stop in enumerate(data['fuel_stops'], 1):
                    print(f"  Stop {i}: {stop['station_name']}")
                    print(f"    Location: {stop['location']['city']}, {stop['location']['state']}")
                    print(f"    Distance from start: {stop['distance_from_start']:.2f} miles")
                    print(f"    Price: ${stop['price_per_gallon']:.2f}/gallon")
                    print(f"    Gallons: {stop['gallons_purchased']:.2f}")
                    print(f"    Cost: ${stop['cost']:.2f}")
                    if 'note' in stop:
                        print(f"    Note: {stop['note']}")
                    print()
            else:
                print("\nNo fuel stops needed (distance under vehicle range)")
            
            print(f"API Calls: {data['api_info']['routing_api_calls']}")
            print(f"Used Fallback: {data['api_info']['used_fallback']}")
            
            return True
        else:
            print("ERROR:")
            print(json.dumps(response.json(), indent=2))
            return False
            
    except Exception as e:
        print(f"Error: {e}")
        return False


def main():
    """Run all tests"""
    print("\n" + "#" * 80)
    print("# FUEL ROUTE OPTIMIZER API - TEST SUITE")
    print("#" * 80)
    
    results = []
    
    # Test 1: Health Check
    results.append(("Health Check", test_health_check()))
    
    # Test 2: Short route (no fuel stops needed)
    results.append((
        "Short Route",
        test_route("Los Angeles, CA", "Las Vegas, NV", "Short Route (LA to Vegas)")
    ))
    
    # Test 3: Medium route (1-2 fuel stops)
    results.append((
        "Medium Route",
        test_route("Chicago, IL", "Denver, CO", "Medium Route (Chicago to Denver)")
    ))
    
    # Test 4: Long route (multiple fuel stops)
    results.append((
        "Long Route",
        test_route("New York, NY", "Los Angeles, CA", "Long Cross-Country Route (NY to LA)")
    ))
    
    # Test 5: Another route
    results.append((
        "Regional Route",
        test_route("Seattle, WA", "San Francisco, CA", "West Coast Route (Seattle to SF)")
    ))
    
    # Print summary
    print_section("TEST SUMMARY")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed successfully!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
    
    print("\n" + "#" * 80 + "\n")


if __name__ == "__main__":
    main()
