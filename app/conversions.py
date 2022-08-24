"""
https://gist.github.com/kmatarese/a5492f4a02449e13ea85ace8801b8dfb

WARNING: not thoroughly tested and does not support full translation
between the two libraries.
Uses a pydantic root_validator to init the marshmallow schema. It attempts
to map marshmallow field types to pydantic field types as well, but not all
field types are supported.
You can either use the pydantic_from_marshmallow function that does all of
the above or just subclass MarshmallowModel and manually define your pydantic
fields/types/etc.
"""

from datetime import date, datetime, timedelta, time
from decimal import Decimal
from typing import Any, Callable, Dict, List, Mapping, Optional, Union

from marshmallow import Schema, fields, missing
from pprint import pprint
from pydantic import (
    BaseModel,
    root_validator,
    create_model,
    AnyUrl,
    EmailStr,
    StrictFloat,
    StrictInt,
    ValidationError
)
from pydantic.utils import validate_field_name


CUSTOM_FIELD_DEFAULT = Any
# Fields in the marshmallow schema may fail the call to pydantic's
# validate_field_name if they conflict with base fields. To work around this
# we mark illegal fields with this and then strip it later to create an alias
# using an alias_generator. Bleh.
ALIAS_MARKER = "__alias__"


def get_dict_type(x):
    """For dicts we need to look at the key and value type"""
    key_type = get_pydantic_type(x.key_field)
    if x.value_field:
        value_type = get_pydantic_type(x.value_field)
        return Dict[key_type, value_type]
    return Dict[key_type, Any]


def get_list_type(x):
    """For lists we need to look at the value type"""
    if x.inner:
        c_type = get_pydantic_type(x.inner)
        return List[c_type]
    return List


def get_nested_model(x):
    """Return a model from a nested marshmallow schema"""
    return pydantic_from_marshmallow(x.schema)


FIELD_CONVERTERS = {
    fields.Bool: bool,
    fields.Boolean: bool,
    fields.Date: date,
    fields.DateTime: datetime,
    fields.Decimal: Decimal,
    fields.Dict: get_dict_type,
    fields.Email: EmailStr,
    fields.Float: float,
    fields.Function: Callable,
    fields.Int: int,
    fields.Integer: int,
    fields.List: get_list_type,
    fields.Mapping: Mapping,
    fields.Method: Callable,
    fields.Nested: get_nested_model,
    fields.Number: Union[StrictFloat, StrictInt],
    fields.Str: str,
    fields.String: str,
    fields.Time: time,
    fields.TimeDelta: timedelta,
    fields.URL: AnyUrl,
    fields.Url: AnyUrl,
    fields.UUID: str,
}


def is_custom_field(field):
    """If this is a subclass of marshmallow's Field and not in our list, we
    assume its a custom field"""
    ftype = type(field)
    if issubclass(ftype, fields.Field) and ftype not in FIELD_CONVERTERS:
        return True
    return False


def get_pydantic_type(field):
    """Get pydantic type from a marshmallow field"""
    if is_custom_field(field):
        conv = Any
    else:
        conv = FIELD_CONVERTERS[type(field)]

    # TODO: Is there a cleaner way to check for annotation types?
    if isinstance(conv, type) or conv.__module__ == "typing":
        pyd_type = conv
    else:
        pyd_type = conv(field)

    # if not field.required:
    #     pyd_type = Optional[pyd_type]
    return Optional[pyd_type]


def is_valid_field_name(bases, x):
    try:
        validate_field_name(bases, x)
        return True
    except NameError as e:
        return False


def get_alias(x):
    if x.endswith(ALIAS_MARKER):
        return x.replace(ALIAS_MARKER, "")
    return x


class MarshmallowModel(BaseModel):
    """A pydantic model that uses a marshmallow schema for object-wide validation"""

    _schema = None

    # @root_validator(pre=True)
    # def _schema_validate(cls, values):
    #     if not cls._schema:
    #         raise AssertionError("Must define a marshmallow schema")
    #     return cls._schema().load(values)

    class Config:
        alias_generator = get_alias


def pydantic_from_marshmallow(schema):
    """Convert a marshmallow schema to a pydantic model. May only
    work for fairly simple cases. Barely tested. Enjoy."""

    pyd_fields = {}
    for field_name, field in schema._declared_fields.items():
        pyd_type = get_pydantic_type(field)
        default = field.default if field.default != missing else None
        if not is_valid_field_name([BaseModel], field_name):
            field_name = field_name + ALIAS_MARKER
        pyd_fields[field_name] = (pyd_type, default)

    if isinstance(schema, Schema):
        name = schema.__class__.__name__
    else:
        name = schema.__name__

    return create_model(name, _schema=schema, **pyd_fields, __base__=MarshmallowModel)


if __name__ == "__main__":
    # Simple test...
    def is_valid_str(val):
        if not isinstance(val, str):
            raise ValidationError(f"value is not a string: {val}")
        return val

    class MyField(fields.Field):
        pass

    class TestSchema(Schema):
        some_str = fields.String(required=True, validate=is_valid_str)
        some_dict = fields.Dict(keys=fields.Str(), default=None, missing={})
        some_list = fields.List(fields.Integer)
        fields = fields.Str()  # illegal field name for pydantic

    class TestSubSchema(TestSchema):
        some_int = fields.Integer(required=False, missing=5)
        some_custom_field = MyField()

    for schema in [TestSchema, TestSubSchema]:
        model = pydantic_from_marshmallow(schema)
        x = model(some_str="a string!")
        print(f"\n{model}:{x}")
        pprint(model.schema())