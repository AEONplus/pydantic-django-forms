from django.urls import path

from .views import SimpleFormView

urlpatterns = [
    path("simple/", SimpleFormView.as_view(), name="simple_form"),
]
