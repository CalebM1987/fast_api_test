import re
import sqlalchemy

def get_primary_key(table):
    return sqlalchemy.inspection.inspect(table).primary_key[0]
    

def get_columns(table):
    """gets the raw column objects
    Args:
        table: the table
    Returns:
        []: list of column objects
    """
    if not table:
        return []
    return table.__table__.columns if hasattr(table, '__table__') else table.columns


def camel_case_split(s: str):
    return re.findall(r'[A-Z](?:[a-z]+|[A-Z]*(?=[A-Z]|$))', s)

def get_route_name(table) -> str:
    nm = table.__name__ if hasattr(table, '__name__') else table.__class__.__name__
    return '-'.join(list(map(lambda x: x.lower(), camel_case_split(nm))))