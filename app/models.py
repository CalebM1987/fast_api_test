import os
from typing import Optional, List
from sqlmodel import Field, Session, SQLModel, create_engine

class Beer(SQLModel, table=True):
    __tablename__ = 'beer'
    id: Optional[int] = Field(primary_key=True)
    brewery_id: Optional[int] = Field(foreign_key='brewery.id')
    name: Optional[str] = Field(max_length=150)
    description: Optional[str] = Field(max_length=500)
    style: Optional[str] = Field(max_length=50)
    category: Optional[str] = Field(max_length=100)
    alc: Optional[float]
    ibu: Optional[int]
    color: Optional[str] = Field(max_length=25)
    photo_name: Optional[str] = Field(max_length=100)
    # created_by = Column(Integer, ForeignKey('user.id'))
    # brewery = relationship('Brewery', back_populates='beers')
    # creator = relationship('User', back_populates='submitted_beers')


class Brewery(SQLModel, table=True):
    __tablename__ = 'brewery'
    id: Optional[int] = Field(default=None, primary_key=True)
    name: Optional[str] = Field(description='the brewery name')
    address: Optional[str] = Field(description='the brewery address')
    city: Optional[str] = Field(description='the city the brewery is in')
    state: Optional[str] = Field(description='the state the brewery is in')
    zip: Optional[str] = Field(description='the zip code of the brewery address')
    monday: Optional[str] = Field(description='the hours of operation on Monday')
    tuesday: Optional[str] = Field(description='the hours of operation on Tuesday')
    wednesday: Optional[str] = Field(description='the hours of operation on Wednesday')
    thursday: Optional[str] = Field(description='the hours of operation on Thursday')
    friday: Optional[str] = Field(description='the hours of operation on Friday')
    saturday: Optional[str] = Field(description='the hours of operation on Saturday')
    sunday: Optional[str] = Field(description='the hours of operation on Sunday')
    comments: Optional[str] = Field(description='comments about the brewery')
    brew_type: Optional[str] = Field(description='the type', default='Brewery')
    website: Optional[str] = Field(description='the brewery website')
    longitude: Optional[float] = Field(description='the longitude or X coordinate')
    latitude: Optional[float] = Field(description='the longitude or X coordinate')
    # created_by = Column(Integer, ForeignKey('user.id'))
    # creator = relationship('User', back_populates='submitted_breweries')
    # beers = relationship('Beer', back_populates='brewery', cascade="all, delete-orphan")
    # beers: Optional[List[Beer]]

    # @property
    # def geometry(self): # -> Dict:
    #     return to_geometry_geojson(self)

    # def __repr__(self):
    #     return basic_repr(self, 'name')



thisDir = os.path.dirname(__file__)
db_path = os.path.join(thisDir, 'breweries.db')
print(f'db exists: {os.path.exists(db_path)}')
conn_str = f'sqlite:///{db_path}'
engine = create_engine(conn_str)


