import threading
import inspect
from pydantic import BaseModel
from typing import Type, Dict, Tuple, Any

def partial(*fields):
    """ Make the object "partial": i.e. mark all fields as "skippable"

    In Pydantic terms, this means that they're not nullable, but not required either.

    Example:

        @partial
        class User(pd.BaseModel):
            id: int

        # `id` can be skipped, but cannot be `None`
        User()
        User(id=1)

    Example:

        @partial('id')
        class User(pd.BaseModel):
            id: int
            login: str

        # `id` can be skipped, but not `login`
        User(login='johnwick')
        User(login='johnwick', id=1)
    """
    # Call pattern: @partial class Model(pd.BaseModel):
    if len(fields) == 1 and issubclass(fields[0], BaseModel):
        Model = fields[0]
        field_names = ()
    # Call pattern: @partial('field_name') class Model(pd.BaseModel):
    else:
        Model = None
        field_names = fields

    # Decorator
    def decorator(Model: type[BaseModel] = Model, field_names: frozenset[str] = frozenset(field_names)):
        # Iter fields, set `required=False`
        for field in Model.__fields__.values():
            # All fields, or specific named fields
            if not field_names or field.name in field_names:
                field.required = False

        # Exclude unset
        # Otherwise non-nullable fields would have `{'field': None}` which is unacceptable
        dict_orig = Model.dict
        def dict_excludes_unset(*args, exclude_unset: bool = None, **kwargs):
            exclude_unset = True
            return dict_orig(*args, **kwargs, exclude_unset=exclude_unset)
        Model.dict = dict_excludes_unset

        # Done
        return Model

# class PartialModelMetaclass(ModelMetaclass):
#     def __new__(
#         meta: Type["PartialModelMetaclass"], *args: Any, **kwargs: Any
#     ) -> "PartialModelMetaclass":
#         cls = super(PartialModelMetaclass, meta).__new__(meta, *args, *kwargs)
#         cls_init = cls.__init__
#         # Because the class will be modified temporarily, need to lock __init__
#         init_lock = threading.Lock()

#         def __init__(self: BaseModel, *args: Any, **kwargs: Any) -> None:
#             with init_lock:
#                 fields = self.__class__.__fields__
#                 fields_map: Dict[ModelField, Tuple[Any, bool]] = {}

#                 def optionalize(
#                     fields: Dict[str, ModelField], *, restore: bool = False
#                 ) -> None:
#                     for _, field in fields.items():
#                         if not restore:
#                             assert not isinstance(field.required, UndefinedType)
#                             fields_map[field] = (field.type_, field.required)
#                             field.required = False
#                             if inspect.isclass(field.type_) and issubclass(
#                                 field.type_, BaseModel
#                             ):
#                                 # Create a temporary type to optionalize to avoid
#                                 # modifying *other* classes
#                                 field.type_ = ModelMetaclass(
#                                     f"TemporaryPartial{field.type_.__name__}",
#                                     (field.type_,),
#                                     {},
#                                 )
#                                 optionalize(field.type_.__fields__)
#                                 # After replacing the field type, regenerate validators
#                                 field.populate_validators()
#                         else:
#                             # No need to recursively de-optionalize once original types
#                             # are restored
#                             field.type_, field.required = fields_map[field]

#                 # Make fields and fields of nested model types optional
#                 optionalize(fields)

#                 # Validation is performed in __init__, for which all fields are now optional
#                 cls_init(self, *args, **kwargs)

#                 # Restore requiredness
#                 optionalize(fields, restore=True)

#                 # Exclude unset (`None`) from dict(), which isn't allowed in the schema
#                 # but will be the default for non-required fields. This enables
#                 # PartialModel(**PartialModel().dict()) to work correctly.
#                 self_dict = self.dict

#                 def dict_exclude_unset(*args: Any, exclude_unset: bool = None, **kwargs: Any) -> Dict[str, Any]:
#                     return self_dict(*args, **kwargs, exclude_unset=True)

#                 # Bypass `BaseModel.setattr`
#                 object.__setattr__(self, "dict", dict_exclude_unset)

#         setattr(cls, "__init__", __init__)
#         return cls