from django.urls import path

from .views import health_view, metrics_view

app_name = "monitoring"

urlpatterns = [
    path("metrics", metrics_view, name="metrics"),
    path("health/", health_view, name="health"),
]
