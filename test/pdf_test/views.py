from django import forms
from django.views.generic import FormView


class SimpleForm(forms.Form):
    name = forms.CharField(max_length=100)


class SimpleFormView(FormView):
    template_name = "simple_form.html"
    form_class = SimpleForm
    success_url = "/simple"
