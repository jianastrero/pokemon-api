import httpx
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
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

db = TinyDB('./pokemon.json')

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/reset")
async def reset_pokemon_list():
    pokemon_table = db.table('pokemon')
    pokemon_table.truncate()
    url = "https://raw.githubusercontent.com/Purukitto/pokemon-data.json/master/pokedex.json"
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        pokemon_data = response.json()

    pokemon_table.insert_multiple(pokemon_data)

    return {"message": "Pokemon list has been reset"}

@app.get("/pokemon")
async def get_pokemon():
    pokemon_table = db.table('pokemon')
    return pokemon_table.all()
