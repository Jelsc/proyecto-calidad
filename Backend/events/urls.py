from django.urls import path

from .views import TrafficEventIntakeView, TrafficEventListCreateView

urlpatterns = [
    path("events/", TrafficEventListCreateView.as_view(), name="event-list-create"),
    path("events/intake/", TrafficEventIntakeView.as_view(), name="event-intake"),
]
