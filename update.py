
from tinydb import TinyDB

db = TinyDB('./pokemon.json')
pokemon_table = db.table('pokemon')


def update_pokemon_images():
    for pokemon in pokemon_table.all():
        pokemon['image']['sprite'] = f'/image/sprite/{pokemon["id"]}.png'
        pokemon['image']['thumbnail'] = f'/image/thumbnail/{pokemon["id"]}.png'
        pokemon['image']['hi_res'] = f'/image/hi_res/{pokemon["id"]}.png'
        pokemon_table.update(pokemon, doc_ids=[pokemon.doc_id])


update_pokemon_images()