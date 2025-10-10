# pyright: reportAny=false, reportExplicitAny=false
from types import UnionType
from typing import Annotated, get_origin, get_args, Literal, Any, override
from annotated_types import Ge, Gt, Le, Lt, MaxLen, MinLen
from django import forms
from pydantic import BaseModel, ValidationError
from pydantic.fields import FieldInfo
from logging import getLogger
from datetime import date, datetime


logger = getLogger(__name__)


class PydanticModelForm(forms.Form):
    """A Django form backed by a pydantic model."""

    def __init__(self, *args: Any, **kwargs: Any):
        self.pydantic_model: type[BaseModel] = self._get_pydantic_model()
        self.pydantic_instance: BaseModel | None = None
        super().__init__(*args, **kwargs)
        self._add_pydantic_fields()

    def _get_pydantic_model(self) -> type[BaseModel]:
        meta: Any = getattr(self.__class__, "Meta", None)
        if meta is None:
            raise ValueError(
                f"From class {self.__class__.__name__} is missing Meta class"
            )

        model: Any = getattr(meta, "model", None)
        if model is None:
            raise ValueError(
                f"Meta class of {self.__class__.__name__} is missing model attribute"
            )

        if not issubclass(model, BaseModel):
            raise ValueError(
                f"Meta.model of {self.__class__.__name__} is not a subclass of BaseModel"
            )

        return model

    def _add_pydantic_fields(self):
        """Iterate over every pydantic model field and get a django form field out"""
        for field_name, field_info in self.pydantic_model.model_fields.items():
            django_field = self._convert_pydantic_field(field_name, field_info)
            if django_field is not None:
                self.fields[field_name] = django_field

    def _convert_pydantic_field(
        self, field_name: str, field_info: FieldInfo
    ) -> forms.Field | None:
        """Convert a Pydantic field to a Django form field."""
        field_type = field_info.annotation
        is_required = field_info.is_required()
        default = field_info.get_default() if not is_required else None

        # Optional types like foo: int | None
        if get_origin(field_type) is UnionType:
            args = get_args(field_type)
            # only if one of the types is None
            if len(args) == 2 and type(None) in args:
                field_type = args[0] if args[1] is type(None) else args[1]
                is_required = False

        # Handle literal types (choices) like baz: Literal["a", "b", "c"]
        if get_origin(field_type) is Literal:
            try:
                choices = [(choice, choice) for choice in get_args(field_type)]
                return forms.ChoiceField(
                    choices=choices,
                    required=is_required,
                    initial=default,
                    help_text=field_info.description or "",
                )
            except Exception as e:
                logger.warning(f"Error converting literal field {field_name}: {e}")

        django_field = self._map_type_to_field(
            field_type, field_info, is_required, default
        )
        return django_field

    def _map_type_to_field(
        self,
        field_type: type[Any] | None,
        field_info: FieldInfo,
        is_required: bool,
        default: Any,
    ) -> forms.Field | None:
        # Handle Union types that might contain multiple acceptable types
        if get_origin(field_type) is Annotated:
            args = get_args(field_type)
            # The first argument is the actual type (could be a Union)
            actual_type = args[0]

            # Check if the actual type is a Union
            if get_origin(actual_type) is UnionType:
                field_type = self.union_to_field_type(actual_type)
            else:
                # If it's not a Union, just use the actual type directly
                field_type = actual_type

        elif get_origin(field_type) is UnionType:
            field_type = self.union_to_field_type(field_type)

        # String types
        if field_type is str:
            return self._create_string_field(field_info, is_required, default)

        # Integer types
        elif field_type is int:
            return self._create_integer_field(field_info, is_required, default)

        # Float types
        elif field_type is float:
            return self._create_float_field(field_info, is_required, default)

        # Boolean types
        elif field_type is bool:
            return forms.BooleanField(
                required=is_required,
                initial=default,
                help_text=field_info.description or "",
            )

        # Date/datetime types
        elif field_type is date:
            return forms.DateField(
                required=is_required,
                initial=default,
                help_text=field_info.description or "",
            )
        elif field_type is datetime:
            return forms.DateTimeField(
                required=is_required,
                initial=default,
                help_text=field_info.description or "",
            )

        # None or non-mapped type. Emit a warning and attempt a char field
        else:
            logger.warning("Unsupported type: %s. Creating CharField", field_type)
            return self._create_string_field(field_info, is_required, default)

    def union_to_field_type(self, field_type: type[Any] | None) -> type[Any] | None:
        union_args = get_args(field_type)
        # Filter out None types
        type_classes = [arg for arg in union_args if arg is not type(None)]

        # Priority list of how to handle these types
        # If a type can accept string we should use it. Types like aeonlib.Angle support various
        # string representations, the type of input field doesn't really matter.
        prio = [str, float, int, date, datetime]
        return next((t for t in prio if t in type_classes), None)

    def _create_string_field(
        self, field_info: FieldInfo, is_required: bool, default: Any
    ) -> forms.CharField:
        """Create a string form field with constraints"""
        max_length = 2000
        min_length = 0

        for constraint in field_info.metadata:
            if isinstance(constraint, MaxLen):
                max_length = constraint.max_length
            if isinstance(constraint, MinLen):
                min_length = constraint.min_length

        return forms.CharField(
            required=is_required,
            initial=default,
            min_length=min_length,
            max_length=max_length,
            help_text=field_info.description or "",
        )

    def _create_integer_field(
        self, field_info: FieldInfo, is_required: bool, default: Any
    ) -> forms.IntegerField:
        """Create an integer form field with constraints"""
        min_value: int | None = None
        max_value: int | None = None

        for constraint in field_info.metadata:
            if isinstance(constraint, Ge):
                min_value = constraint.ge
            if isinstance(constraint, Gt):
                min_value = constraint.gt + 1
            if isinstance(constraint, Le):
                max_value = constraint.le
            if isinstance(constraint, Lt):
                max_value = constraint.lt - 1

        return forms.IntegerField(
            required=is_required,
            initial=default,
            min_value=min_value,
            max_value=max_value,
            help_text=field_info.description or "",
        )

    def _create_float_field(
        self, field_info: FieldInfo, is_required: bool, default: Any
    ) -> forms.FloatField:
        """Create a float form field with constraints"""
        min_value = None
        max_value = None

        for constraint in field_info.metadata:
            if isinstance(constraint, Ge):
                min_value = constraint.ge
            if isinstance(constraint, Gt):
                min_value = constraint.gt + 1
            if isinstance(constraint, Le):
                max_value = constraint.le
            if isinstance(constraint, Lt):
                max_value = constraint.lt - 1

        field = forms.FloatField(
            required=is_required,
            initial=default,
            min_value=min_value,
            max_value=max_value,
            help_text=field_info.description or "",
        )
        return field

    @override
    def clean(self) -> dict[Any, Any] | None:
        """Validate the form against the pydantic model"""
        cleaned_data = super().clean()

        try:
            instance = self.pydantic_model.model_validate(cleaned_data)
            self.pydantic_instance = instance
        except ValidationError as e:
            # Convert Pydantic validation errors to Django form errors
            for error in e.errors():
                field_name = ".".join(str(x) for x in error["loc"])
                if field_name in self.fields:
                    self.add_error(field_name, error["msg"])
                else:
                    self.add_error(None, error["msg"])

        return cleaned_data
