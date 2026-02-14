"""
Serializers for route planning API
"""
from rest_framework import serializers


class RouteRequestSerializer(serializers.Serializer):
    """Serializer for route planning request"""
    start = serializers.CharField(
        max_length=200,
        help_text="Starting location (e.g., 'New York, NY' or 'Los Angeles, CA')"
    )
    finish = serializers.CharField(
        max_length=200,
        help_text="Destination location (e.g., 'Miami, FL' or 'Seattle, WA')"
    )
    
    def validate_start(self, value):
        """Validate start location"""
        if not value or len(value.strip()) == 0:
            raise serializers.ValidationError("Start location cannot be empty")
        return value.strip()
    
    def validate_finish(self, value):
        """Validate finish location"""
        if not value or len(value.strip()) == 0:
            raise serializers.ValidationError("Finish location cannot be empty")
        return value.strip()
