from typing import Annotated, Literal
from annotated_types import Le, Ge, Lt, Gt
from django import forms
from pydantic_django_forms.forms import PydanticModelForm
from pydantic import BaseModel, ConfigDict, Field
from datetime import date, datetime, UTC


class OptionalModel(BaseModel):
    field: str
    optional_field: str | None


class OptionalForm(PydanticModelForm):
    class Meta:
        model = OptionalModel


def test_optional_model_form():
    form = OptionalForm()
    assert form.fields["field"].required
    assert not form.fields["optional_field"].required


def test_valid_optional_model_form():
    form = OptionalForm({"field": "test"})
    assert form.is_valid()
    assert form.cleaned_data["field"] == "test"
    assert form.cleaned_data["optional_field"] == ""


def test_invalid_optional_model_form():
    form = OptionalForm({"field": ""})
    assert not form.is_valid()
    assert "This field is required." in form.errors["field"]


class LiteralModel(BaseModel):
    field: Literal["Foo", "Bar"]


class LiteralForm(PydanticModelForm):
    class Meta:
        model = LiteralModel


def test_literal_field_is_choice():
    form = LiteralForm()
    assert form.fields["field"].__class__ == forms.ChoiceField
    assert form.fields["field"].choices == [("Foo", "Foo"), ("Bar", "Bar")]  # pyright: ignore[reportAttributeAccessIssue, reportUnknownMemberType]


def test_valid_literal_model_form():
    form = LiteralForm({"field": "Foo"})
    assert form.is_valid()
    assert form.cleaned_data["field"] == "Foo"


def test_invalid_literal_model_form():
    form = LiteralForm({"field": "Baz"})
    assert not form.is_valid()
    assert (
        "Select a valid choice. Baz is not one of the available choices."
        in form.errors["field"]
    )


class DescriptiveModel(BaseModel):
    model_config = ConfigDict(use_attribute_docstrings=True)

    docstring: str
    """A descriptive field"""
    pydantic_field: str = Field(description="Another descriptive field")
    nothing: str


class DescriptiveForm(PydanticModelForm):
    class Meta:
        model = DescriptiveModel


def test_field_descriptions():
    form = DescriptiveForm()
    assert form.fields["docstring"].help_text == "A descriptive field"
    assert form.fields["pydantic_field"].help_text == "Another descriptive field"
    assert form.fields["nothing"].help_text == ""


class StringModel(BaseModel):
    field: str
    """A concise descrption"""


class StringForm(PydanticModelForm):
    class Meta:
        model = StringModel


def test_string_field_is_char():
    form = StringForm()
    assert form.fields["field"].__class__ == forms.CharField


class IntegerModel(BaseModel):
    field: Annotated[int, Ge(0), Le(10)]


class IntegerForm(PydanticModelForm):
    class Meta:
        model = IntegerModel


def test_integer_field_is_integer():
    form = IntegerForm()
    assert form.fields["field"].__class__ == forms.IntegerField


def test_valid_integer_model_form():
    form = IntegerForm({"field": 10})
    assert form.is_valid()
    assert form.cleaned_data["field"] == 10

    # Coerce string to integer
    form = IntegerForm({"field": "1"})
    assert form.is_valid()
    assert form.cleaned_data["field"] == 1


def test_invalid_integer_model_form():
    form = IntegerForm({"field": -1})
    assert not form.is_valid()
    assert "Input should be greater than or equal to 0" in form.errors["field"]

    form = IntegerForm({"field": "foo"})
    assert not form.is_valid()
    assert "Enter a whole number." in form.errors["field"]


class FloatModel(BaseModel):
    field: Annotated[float, Gt(0), Lt(1000)]


class FloatForm(PydanticModelForm):
    class Meta:
        model = FloatModel


def test_float_field_is_float():
    form = FloatForm()
    assert form.fields["field"].__class__ == forms.FloatField


def test_valid_float_model_form():
    form = FloatForm({"field": 9.9})
    assert form.is_valid()
    assert form.cleaned_data["field"] == 9.9

    form = FloatForm({"field": "1.1e2"})
    assert form.is_valid()
    assert form.cleaned_data["field"] == 110.0


def test_invalid_float_model_form():
    form = FloatForm({"field": 9000.0})
    assert not form.is_valid()
    assert "Input should be less than 1000" in form.errors["field"]


class BooleanModel(BaseModel):
    # A required boolean field just means that it has to be checked
    field: bool | None


class BooleanForm(PydanticModelForm):
    class Meta:
        model = BooleanModel


def test_boolean_field_is_boolean():
    form = BooleanForm()
    assert form.fields["field"].__class__ == forms.BooleanField


def test_boolean_field_valid():
    # Boolean feilds are a little werid, I believe a value is only present
    # when a checkbox is checked, thus it is true if any value is present and false
    # if not. Will need to test this with actual forms later.
    form = BooleanForm({"field": True})
    assert form.is_valid()
    assert form.cleaned_data["field"] is True

    form = BooleanForm({"field": "anything"})
    assert form.is_valid()
    assert form.cleaned_data["field"] is True

    form = BooleanForm({})
    assert form.is_valid()
    assert form.cleaned_data["field"] is False


class DateAndDateTimeModel(BaseModel):
    date: date
    datetime: datetime


class DateAndDateTimeForm(PydanticModelForm):
    class Meta:
        model = DateAndDateTimeModel


def test_date_and_datetime_field_is_date_and_datetime():
    form = DateAndDateTimeForm()
    assert form.fields["date"].__class__ == forms.DateField
    assert form.fields["datetime"].__class__ == forms.DateTimeField


def test_date_and_datetime_field_valid():
    form = DateAndDateTimeForm(
        {"date": "2025-01-01", "datetime": "2025-01-01T12:00:00"}
    )
    assert form.is_valid()
    assert form.cleaned_data["date"] == date(2025, 1, 1)
    assert form.cleaned_data["datetime"] == datetime(2025, 1, 1, 12, 0, 0, tzinfo=UTC)


class SimpleUnionModel(BaseModel):
    field: int | str


class SimpleUnionModelForm(PydanticModelForm):
    class Meta:
        model = SimpleUnionModel


def test_simple_union_model():
    # String is part of the union, so we prioritize it to allow the most
    # flexible set of inputs
    form = SimpleUnionModelForm()
    assert form.fields["field"].__class__ == forms.CharField
    assert form.fields["field"].required
