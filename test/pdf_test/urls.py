from django.urls import path

from .views import IntegrationTestView

urlpatterns = [
    path("integration/", IntegrationTestView.as_view(), name="integration"),
]
