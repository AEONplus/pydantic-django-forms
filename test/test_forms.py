from django import forms
from pydantic_django_forms.forms import PydanticModelForm
from pydantic import BaseModel, Field


class PersonModel(BaseModel):
    id: int = Field(gt=0)
    name: str = Field(min_length=1, max_length=200)
    nothere: str


class PersonModelForm(PydanticModelForm):
    name = forms.ChoiceField(choices=[("mark", "Mark"), ("lindy", "Lindy")])

    def clean_name(self):
        if self.cleaned_data["name"] != "mark":
            raise forms.ValidationError("This is not mark!")

    class Meta:
        model = PersonModel
        fields = ["id", "name"]


def test_form_override():
    """Tests that fields defined on the form override model fields"""
    form = PersonModelForm()
    assert form.fields["name"].__class__ == forms.ChoiceField


def test_form_validate_methods():
    """Test that validators defined on the form still apply"""
    form = PersonModelForm({"name": "lindy"})
    assert not form.is_valid()
    assert "This is not mark!" in form.errors["name"]


def test_form_fields():
    """Test that fields not included in Meta.fields are not included in the form"""
    form = PersonModelForm()
    assert "nothere" not in form.fields
