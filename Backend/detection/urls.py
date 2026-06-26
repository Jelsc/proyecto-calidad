from django.urls import path

from .views import DetectionSimulationView, DetectionTrainView

urlpatterns = [
    path("detection/simulate/", DetectionSimulationView.as_view(), name="detection-simulate"),
    path("detection/train/", DetectionTrainView.as_view(), name="detection-train"),
]
