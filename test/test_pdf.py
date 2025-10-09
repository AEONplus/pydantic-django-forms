from django.urls import reverse
from django.test import Client


def test_get_simple_form(client: Client):
    response = client.get(reverse("simple_form"))
    assert response.status_code == 200
