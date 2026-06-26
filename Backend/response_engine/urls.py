from django.urls import path

from .views import ResponseActionListCreateView

urlpatterns = [
    path("responses/", ResponseActionListCreateView.as_view(), name="response-action-list-create"),
]
