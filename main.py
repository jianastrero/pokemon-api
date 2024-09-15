from datetime import timedelta, datetime, timezone
from typing import Optional, Annotated

import jwt
from fastapi import FastAPI, HTTPException, Depends
from fastapi.encoders import jsonable_encoder
from fastapi.security import OAuth2PasswordBearer
from jwt import InvalidTokenError
from passlib.context import CryptContext
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from starlette import status
from starlette.staticfiles import StaticFiles
from tinydb import TinyDB, Query


SECRET_KEY = "1bca290decde137600b8fa73bafa35484b96c785c2407b1054ce6689d274ae52"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 10


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

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


class User(BaseModel):
    username: str
    password: str
    name: str
    address: str
    age: int
    auth_token: Optional[str] = None


class UserLogin(BaseModel):
    username: str
    password: str


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_user(username: str):
    user_table = db.table('users')
    user = Query()
    result = user_table.search(user.username == username)
    if result:
        return result[0]
    else:
        return None


def authenticate_user(username: str, password: str):
    user = get_user(username)
    if not user:
        return False
    if not pwd_context.verify(password, user['password']):
        return False
    return user


def check_token(
        token: Annotated[str, Depends(oauth2_scheme)],
        credentials_exception: HTTPException = None
) -> str:
    if not credentials_exception:
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token_blacklist_table = db.table('token_blacklist')
    if token_blacklist_table.search(Query().token == token):
        raise credentials_exception

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except InvalidTokenError:
        raise credentials_exception

    return username


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.post("/login")
async def login(user: UserLogin):
    user = jsonable_encoder(user)
    user = authenticate_user(user['username'], user['password'])

    if not user:
        raise HTTPException(status_code=401, detail="Incorrect username or password")

    access_token = create_access_token({"sub": user['username']})
    user_table = db.table('users')

    user_table.update({'auth_token': access_token}, Query().username == user['username'])

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


@app.post("/signup")
async def signup(user: User):
    user_table = db.table('users')
    user = jsonable_encoder(user)

    hashed_password = pwd_context.hash(user['password'])

    if get_user(user['username']):
        raise HTTPException(status_code=400, detail="User already exists")

    user_data = {
        "username": user['username'],
        "password": hashed_password,
        "name": user.get('name'),
        "address": user.get('address'),
        "age": user.get('age'),
        "auth_token": create_access_token({"sub": user['username']}, expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    }
    user_table.insert(user_data)

    return {
        "access_token": user_data['auth_token'],
        "token_type": "bearer"
    }


@app.post("/logout")
async def logout(token: Annotated[str, Depends(oauth2_scheme)]):
    token_blacklist_table = db.table('token_blacklist')
    token_blacklist_table.insert({'token': token})
    return {"message": "Successfully logged out"}


@app.get("/user/me")
async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    username = check_token(token, credentials_exception)

    user = get_user(username)
    if user is None:
        raise credentials_exception
    user.pop('password', None)
    return user


@app.put("/user/update")
async def update_user(user: User, token: Annotated[str, Depends(oauth2_scheme)]):
    username = check_token(token)
    user_table = db.table('users')

    update_data = jsonable_encoder(user)
    update_data.pop('username', None)  # Ensure username is not updated
    update_data['password'] = pwd_context.hash(update_data['password'])

    user_table.update(update_data, Query().username == username)

    return {"message": "User updated successfully"}


@app.get("/pokemon")
async def get_pokemon(token: Annotated[str, Depends(oauth2_scheme)]):
    check_token(token)

    pokemon_table = db.table('pokemon')
    return pokemon_table.all()


@app.get("/pokemon/{pokemon_id}")
async def get_pokemon_by_id(token: Annotated[str, Depends(oauth2_scheme)], pokemon_id: int):
    check_token(token)

    pokemon_table = db.table('pokemon')
    pokemon = Query()
    result = pokemon_table.search(pokemon.id == pokemon_id)
    if result:
        return result[0]
    else:
        raise HTTPException(status_code=404, detail="Pokemon not found")


@app.put("/pokemon/add")
async def add_pokemon(token: Annotated[str, Depends(oauth2_scheme)], pokemon: dict):
    check_token(token)

    pokemon_table = db.table('pokemon')
    pokemon_table.insert(pokemon)
    return {"message": "Pokemon added successfully"}


@app.patch("/pokemon/{pokemon_id}")
async def update_pokemon(token: Annotated[str, Depends(oauth2_scheme)], pokemon_id: int, new_pokemon: dict):
    check_token(token)

    pokemon_table = db.table('pokemon')
    pokemon = Query()
    result = pokemon_table.search(pokemon.id == pokemon_id)
    if result:
        new_pokemon.pop('id', None)
        pokemon_table.update(new_pokemon, pokemon.id == pokemon_id)
        return {"message": "Pokemon updated successfully"}
    else:
        raise HTTPException(status_code=404, detail="Pokemon not found")


@app.delete("/pokemon/{pokemon_id}")
async def delete_pokemon(token: Annotated[str, Depends(oauth2_scheme)], pokemon_id: int):
    check_token(token)

    pokemon_table = db.table('pokemon')
    pokemon = Query()
    result = pokemon_table.search(pokemon.id == pokemon_id)
    if result:
        pokemon_table.remove(pokemon.id == pokemon_id)
        return {"message": "Pokemon deleted successfully"}
    else:
        raise HTTPException(status_code=404, detail="Pokemon not found")
