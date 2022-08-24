# from marshmallow import Marshmallow
from .utils import get_columns
from marshmallow import Schema, fields, EXCLUDE, post_load
from geoalchemy2 import Geometry, functions
from typing import Any
import json

# ma = Marshmallow()

class Meta:
    unknown = EXCLUDE

SCHEMA_MAPPING = dict(
    DATE=fields.Date,
    DATETIME=fields.DateTime,
    INTEGER=fields.Integer,
    TEXT=fields.String,
    JSON=fields.Nested,
    FLOAT=fields.Float,
    SMALLINT=fields.Integer,
    BIGINT=fields.Integer,
    INT=fields.Integer,
    BLOB=fields.Raw,
    BINARY=fields.Raw,
    DECIMAL=fields.Float,
)


def create_schema(table, meta=Meta, session=None):

    class GeometryField(fields.Field):
        """support for geometry fields, will only work if session passed in"""
        def _serialize(self, value: Any, attr: str, obj: Any, **kwargs):
            if value is None:
                return None

            if session:
                return json.loads(session.scalar(functions.ST_AsGeoJSON(value)))
            return value
        
        def _deserialize(self, value: Any, attr: str, data: Any, **kwargs):
            if value is None:
                return None
            if session:
                return session.scalar(functions.ST_GeomFromGeoJSON(json.dumps(value)))
            return value

    cols = get_columns(table)

    attrs = {}

    for col in cols:

        if 'VARCHAR' in str(col.type):
            maType = fields.String
        else:
            maType = SCHEMA_MAPPING.get(str(col.type), fields.String)

        if isinstance(col.type, Geometry):
            maType = GeometryField

        opts = dict(
            help=col.doc,
            dump_only=col.primary_key,
            required=False,#not col.nullable,
        )

        if col.nullable and col.default:
            opts['missing'] = col.default.arg

        attrs[col.name] = maType(**opts)
    
    attrs['Meta'] = Meta

    @post_load
    def make_obj(self, data: Any, **kwargs):
        return table(**data)

    attrs['make_obj'] = make_obj

    return type(f'{table.__name__}Schema', (Schema,), attrs)


class FindResponseBase(Schema):
    total = fields.Integer(help='the total number of results')
    count = fields.Integer(help='number of records in current page if paginated, otherwise total number or results')
    paginated = fields.Boolean(help='set to true if the results are paginated')
    page = fields.Integer(help='page number if if paginated', default=None)
    totalPages = fields.Integer(help='total number of pages if results are paginated')