# pydantic-django-forms
Create Django forms defined and validated by Pydantic models.
Like Django's ModelForm but Pydantic instead. See tests for examples.

```python
from pydantic_django_forms.forms import PydanticModelForm
from pydantic import BaseModel

class MyPydanticModel(BaseModel):
    foo: str
    bar: int

class MyFormClass(PydanticModelForm):
    class Meta:
        model = MyPydanticModel

form = MyFormClass({"foo": "fooval", bar: 12})
assert form.is_valid()
assert form.cleaned_data["foo"] == "fooval"
assert form.cleaned_data["bar"] == 12
```
