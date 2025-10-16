from django.views.generic import FormView
from pydantic.main import BaseModel
from pydantic_django_forms.forms import PydanticModelForm


class IntegrationModel(BaseModel):
    integer: int
    string: str
    boolean: bool = False
    floater: float


class IntegrationModelForm(PydanticModelForm):
    class Meta:
        model = IntegrationModel


class IntegrationTestView(FormView):
    template_name = "integration_test.html"
    form_class = IntegrationModelForm
    success_url = "/integration"
