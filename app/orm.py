from typing import TypeVar
from .declarative import db
from marshmallow import Schema
from .utils import get_columns
from sqlalchemy.orm import joinedload
from munch import munchify
import sqlalchemy

Column = sqlalchemy.sql.schema.Column
InstrumentedAttribute = sqlalchemy.orm.attributes.InstrumentedAttribute

def get_editable_fields(table):
    """returns a list of editable fields (non pk or fk fields)
    Args:
        table ([type]): [description]
    Returns:
        [type]: [description]
    """
    return [column.name for column in get_columns(table) if not column.primary_key and not column.foreign_keys]


def filter_schema_fields(obj, schema, fields=None, **kwargs):
    """runs a schema through a fields filter
    Args:
        obj: the object to serialize
        schema (marshmallow.Schema): The schema definition
        fields ([type], optional): field list. Defaults to None.
    Returns:
        [type]: [description]
    """
    if isinstance(fields, str):
        fields = list(map(lambda f: f.strip(), fields.split(',')))
    schema = create_or_merge_schema(schema, only=fields, **kwargs)
    return schema.dump(obj)


def apply_fields_filter(table, q, fields=[], maSchema=None, **kwargs):
    """applies a field filter to an existing query object
    Args:
        table (sqlalchemy.ext.declarative.api.DeclarativeMeta): a sqlalchemy declarative table
        q (sqlalchemy.orm.query.Query): an existing sqlalchemy.orm.query.Query object.
        fields (list, optional): list of fields for filter. Defaults to [].
        maSchema (marshmallow_sqlalchemy.schema.sqlalchemy_schema.SQLAlchemySchemaMeta, optional): An optional schema object to serialize data to json. Defaults to None.
        **kwargs: additional options to be passed into schema object
    Returns:
        [type]: [description]
    """
    if isinstance(fields, str):
        fields = list(map(lambda f: f.strip(), fields.split(',')))

    if fields:
        rels = { name: r.mapper.class_ for name, r in sqlalchemy.inspection.inspect(table).relationships.items() }
        relMatch, filterFields, removeFields = [], [], []
        for field in fields:
            if '.' in field:
                base = field.split('.')[0]
                if base in rels:
                    if base not in relMatch:
                        relMatch.append(base)
                else:
                    removeFields.append(field)
            else:
                filterFields.append(field)
        
        # if any children relationships are requested, need to do nested subqueries
        if relMatch:
            q = q.options(*[
                    joinedload(r)
                    for r in relMatch
                ]
            )
            
        else:
            # no need to return schema if supplied, this will already be a dict
            filteredQ = q.with_entities(*[getattr(table, f) for f in filterFields])
            return munchify(
                list(
                    map(
                        lambda r: dict(zip(fields, r)), 
                        filteredQ.all()
                    )
                )
            ) 

    # if a marshmallow schema has been supplied, return it
    # print('SCHEMA IN APPLY FIELDS FILTER: ', maSchema)
    if maSchema:
        fields = [f for f in fields if f not in removeFields] if isinstance(fields, list) else None
        _schema = create_or_merge_schema(maSchema, many=True, only=fields, **kwargs)
        return munchify(_schema.dump(q.all()))

    # return raw query objects
    return q.all()


def create_or_merge_schema(schema, **kwargs):
    """ will create a new marshmallow schema based on a Schema class or by 
    merging an existing instance.
    Args:
        schema (marshmallow.Schema): a marshmallow.Schema or instantiated instance
    Returns:
        marshmallow.Schema: the marshmallow.Schema
    """
    # merge from an existing one
    if isinstance(schema, Schema):
        attrs = ['only', 'exclude', 'load_only', 'many', 'context', 'load_only', 'dump_only', 'partial', 'unkown']
        orig = schema
        _kwargs = { k: getattr(orig, k) for k in attrs if hasattr(orig, k)}
        _kwargs.update(kwargs)
        return schema.__class__(**_kwargs)

    # create new instance based on kwargs
    return schema(**kwargs)


def query_table(table, session=None, _wildcards=[], _limit: int=None, **kwargs):
    session = session or db.session

    conditions = []
    for kwarg, val in kwargs.items():
        # check for like query
        base = kwarg
        hasWildcard = kwarg.endswith('.$like')
        inclusion = kwarg.endswith('.$in')
        if hasWildcard or inclusion:
            base = kwarg.split('.')[0]
        if hasattr(table, base):
            col = getattr(table, base)
            if hasWildcard or base in _wildcards:
                conditions.append(col.ilike(f'%{val}%'))
            elif inclusion:
                if isinstance(val, str):
                    val = val.split(',')
                    if isinstance(col, sqlalchemy.Integer):
                        val = list(map(lambda x: int(x)))
                conditions.append(col.in_(val))
            else:
                conditions.append(col == val)

    print('table has query: ', hasattr(table.__table__, 'query'))
    if hasattr(table, 'query'):
        res = table.query.filter(*conditions)
    else:
        res = session.query(table).filter(*conditions)
    
    return res.limit(_limit).all() if _limit else res.all()
