from fastapi import APIRouter, Path, Depends, Request
from flask_restx import ValidationError
from flask import jsonify
from marshmallow.exceptions import ValidationError as MAValidationError
from app.models import Brewery, Session, engine
from fastapi.encoders import jsonable_encoder
from typing import List
from ..schema import create_schema
from ..conversions import pydantic_from_marshmallow
from ..orm import query_table
from ..partial import partial
from typing import Optional, Dict

router = APIRouter()

brewery_schema = create_schema(Brewery)
# brewery_pydantic = pydantic_from_marshmallow(brewery_schema)

@partial#('name', 'latitude', 'longitude')
class PartialBrewery(Brewery):
    pass

@router.get('/breweries/find', response_model=List[Brewery])
async def get_breweries(request: Request, params: Brewery = Depends(), _limit: int=None, _fields: str=None, _wildcards: str=''):
    """get list of breweries"""
    kwargs = request.query_params
    # print('limit is: ', _limit)
    # print('params is: ', type(params), params)
    # print('params.city', params.city)
    with Session(engine) as session:
        # results = session.query(Brewery).all()
        # kwargs.update({k: v for k,v in params.dict().items() if v})
        # kwargs['_limit'] = _limit
        # kwargs['_wildcards'] = _wildcards.split(',') or []
        print('kwargs: ', kwargs)
        results = query_table(Brewery, session, **kwargs)
        
        try:
            return brewery_schema(many=True).dump(results)
        except MAValidationError as e:
            return jsonify(e.data), 500
        # return [jsonable_encoder(res) for res in results]
        # statement = select(Hero).where(Hero.name == "Spider-Boy")
        # result = session.exec(statement)
        # hero_spider_boy = result.one()

@router.get('/breweries/{id}', response_model=Brewery)
async def get_brewery(id: int = Path(..., title="The ID of the item to get")):
    """get brewery by id"""
    with Session(engine) as session:
        print('item_id: ', id)
        brewery = session.query(Brewery).get(id)
        print('brewery: ', brewery)
        return jsonable_encoder(brewery)



# @router.get("/users/", tags=["users"])
# async def read_users():
#     return [{"username": "Rick"}, {"username": "Morty"}]


# @router.get("/users/me", tags=["users"])
# async def read_user_me():
#     return {"username": "fakecurrentuser"}


# @router.get("/users/{username}", tags=["users"])
# async def read_user(username: str):
#     return {"username": username}
