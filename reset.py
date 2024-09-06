import os
import asyncio
import httpx
from tinydb import TinyDB

db = TinyDB('./pokemon.json')
pokemon_table = db.table('pokemon')

os.system('rm -rf ./image')

os.makedirs('./image/sprite', exist_ok=True)
os.makedirs('./image/thumbnail', exist_ok=True)
os.makedirs('./image/hi_res', exist_ok=True)

url = "https://raw.githubusercontent.com/Purukitto/pokemon-data.json/master/pokedex.json"

async def fetch_and_save_pokemon_data():
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        pokemon_data = response.json()

    total_pokemon = len(pokemon_data)

    for index, pokemon in enumerate(pokemon_data):
        percentage_done = ((index + 1) / total_pokemon) * 100
        print(f">>> Fetching {pokemon['name']['english']}... [{index + 1} / { total_pokemon }]({percentage_done:.2f}% done)")

        # Download and save image
        async with httpx.AsyncClient() as client:
            if 'sprite' in pokemon['image']:
                print(f"> Fetching sprite for {pokemon['name']['english']}...")
                sprite_response = await client.get(pokemon['image']['sprite'])
                sprite_path = f'./image/sprite/{pokemon["id"]}.png'
                with open(sprite_path, 'wb') as f:
                    f.write(sprite_response.content)
            else:
                continue

            if 'thumbnail' in pokemon['image']:
                print(f"> Fetching thumbnail for {pokemon['name']['english']}...")
                thumbnail_response = await client.get(pokemon['image']['thumbnail'])
                thumbnail_path = f'./image/thumbnail/{pokemon["id"]}.png'
                with open(thumbnail_path, 'wb') as f:
                    f.write(thumbnail_response.content)
            else:
                continue

            if 'hires' in pokemon['image']:
                print(f"> Fetching hi-res for {pokemon['name']['english']}...")
                hi_res_response = await client.get(pokemon['image']['hires'])
                hi_res_path = f'./image/hi_res/{pokemon["id"]}.png'
                with open(hi_res_path, 'wb') as f:
                    f.write(hi_res_response.content)
            else:
                hi_res_path = f'./image/hi_res/{pokemon["id"]}.png'
                with open(hi_res_path, 'wb') as f:
                    f.write(thumbnail_response.content)

            print(f"----- Finished fetching {pokemon['name']['english']} -----")

        # Update image URLs to local paths
        pokemon['image']['sprite'] = f'/image/sprite/{pokemon["id"]}.png'
        pokemon['image']['thumbnail'] = f'/image/thumbnail/{pokemon["id"]}.png'
        pokemon['image']['hi_res'] = f'/image/hi_res/{pokemon["id"]}.png'

        # Update key from 'hires' to 'hi_res'
        if 'hires' in pokemon['image']:
            pokemon['image']['hi_res'] = pokemon['image'].pop('hires')

    pokemon_table.insert_multiple(pokemon_data)

asyncio.run(fetch_and_save_pokemon_data())