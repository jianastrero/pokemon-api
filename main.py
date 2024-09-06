import os

import httpx
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles
from tinydb import TinyDB, Query

app = FastAPI()
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/image", StaticFiles(directory="image"), name="image")

db = TinyDB('./pokemon.json')

@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/pokemon")
async def get_pokemon():
    pokemon_table = db.table('pokemon')
    return pokemon_table.all()


@app.get("/pokemon/{pokemon_id}")
async def get_pokemon_by_id(pokemon_id: int):
    pokemon_table = db.table('pokemon')
    pokemon = Query()
    return pokemon_table.search(pokemon.id == pokemon_id)
