"""
URL configuration for routes app
"""
from django.urls import path
from .views import OptimalRouteView, HealthCheckView

urlpatterns = [
    path('route/', OptimalRouteView.as_view(), name='optimal-route'),
    path('health/', HealthCheckView.as_view(), name='health-check'),
]
