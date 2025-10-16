from django.urls import reverse
from django.test import Client


def test_get_form(client: Client):
    response = client.get(reverse("integration"))
    assert response.status_code == 200
    assert response.context["form"].__class__.__name__ == "IntegrationModelForm"


def test_post_form(client: Client):
    data = {"integer": 123, "string": "test_string", "boolean": True, "floater": 123.4}
    response = client.post(reverse("integration"), data)
    assert response.status_code == 302


def test_post_form_error(client: Client):
    data = {"integer": 123}
    response = client.post(reverse("integration"), data, follow=True)
    assert response.status_code == 200
    assert "This field is required." in response.context["form"].errors["string"]
