from django.urls import path

from .views import TrafficEventListCreateView

urlpatterns = [
    path("events/", TrafficEventListCreateView.as_view(), name="event-list-create"),
]
