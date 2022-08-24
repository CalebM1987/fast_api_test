from fastapi import FastAPI
from app.routers import brewery

app = FastAPI()

app.include_router(brewery.router)

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/items/{item_id}")
async def read_item(item_id: int):
    return {"item_id": item_id}