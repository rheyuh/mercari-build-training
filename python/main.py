import os
import logging
import pathlib
from typing import List
from fastapi import FastAPI, Form, HTTPException, Depends
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
from pydantic import BaseModel
from contextlib import asynccontextmanager
import json
import hashlib


# Define the path to the images & sqlite3 database
images = pathlib.Path(__file__).parent.resolve() / "images"
db = pathlib.Path(__file__).parent.resolve() / "db" / "mercari.sqlite3"


def get_db():
    if not db.exists():
        yield

    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row  # Return rows as dictionaries
    try:
        yield conn
    finally:
        conn.close()

# STEP 5-1: set up the database connection
def setup_database():
    conn = sqlite3.connect(db)
    cursor = conn.cursor()
    logger.info("Cursor created")

    with open('db/items.sql', 'r') as f:
        cursor.executescript(f.read())
        logger.info("Executed script")

    conn.commit()

    logger.info("Committed")

    conn.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_database()
    yield

# TODO: Create items.json if it does not exist

app = FastAPI(lifespan=lifespan)

logger = logging.getLogger("uvicorn")
# change logger level to display varying levels of logs displayed on console
logger.level = logging.DEBUG
images = pathlib.Path(__file__).parent.resolve() / "images"
origins = [os.environ.get("FRONT_URL", "http://localhost:3000")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)


class HelloResponse(BaseModel):
    message: str


@app.get("/", response_model=HelloResponse)
def hello():
    return HelloResponse(**{"message": "Hello, world!"})

class Item(BaseModel):
    name: str
    category: str
    image: str | None

    @staticmethod
    def from_row(row):
        item = Item(
            name=row["item_name"],
            category=row["category_name"],
            image=row["image"]
        )
        return item

class AddItemResponse(BaseModel):
    message: str

class GetItemResponse(BaseModel):
    items: List[Item]


# add_item is a handler to add a new item for POST /items .
@app.post("/items", response_model=AddItemResponse)
def add_item(
    name: str = Form(...),
    category: str = Form(...),
    # Form(None) for non-required fields
    image: str | None = Form(None),
    
    db: sqlite3.Connection = Depends(get_db),
):
    logger.info("DB connection established")

    print(name, category, image)
    if not name:
        raise HTTPException(status_code=400, detail="name is required")

    if not category:
        raise HTTPException(status_code=400, detail="category is required")

    if image != None:
        # print(image)
        image = hash_image(image)

    insert_item(Item(name=name, category=category, image=image))
    return AddItemResponse(**{"message": f"item received: name={name}, category={category}, image={image}"})

    insert_item_json(Item(name=name, category=category, image=image))
    insert_item_db(db, Item(name=name, category=category, image=image))
    
    return AddItemResponse(**{"message": f"item received: name={name}, category={category}, image={image}"})

@app.get("/items", response_model=GetItemResponse)
def get_items(db: sqlite3.Connection = Depends(get_db)):
    # # JSON implementation
    # with open('items.json', 'r') as json_file:
    #     try:
    #         data = json.load(json_file)
    #     except json.JSONDecodeError:
    #         data = {}
    # return data

    cur = db.cursor()
    cur.execute("""
        SELECT 
            items.name AS item_name, 
            categories.name AS category_name, 
            items.image AS image
        FROM items 
        JOIN categories 
        ON items.category_id = categories.id
    """)
    rows = cur.fetchall()
    items = [Item.from_row(row) for row in rows]
    
    return GetItemResponse(items=items)

@app.get("/items/{item_id}")
def get_item(item_id):
    # check if item_id is a valid integer
    try:
        item_id = int(item_id)
    except:
        raise HTTPException(status_code=400, detail="Item ID is not a valid number")
    
    with open('items.json', 'r') as json_file:
        try:
            data = json.load(json_file)
        except json.JSONDecodeError:
            data = {}

    #TODO: error handling - items might be empty
    if not data:
        raise HTTPException(Status_code=400, detail="Item ID does not exist")
    items = data['items']
    item = items[item_id - 1]
    return item

@app.get("/search/{keyword}", response_model=GetItemResponse)
def get_search(keyword, db: sqlite3.Connection = Depends(get_db)):
    logger.info("Searching ...")
    cur = db.cursor()
    cur.execute('''
        SELECT items.name AS item_name, categories.name AS category_name, items.image
        FROM items 
        JOIN categories ON items.category_id = categories.id
        WHERE item_name = ? or category_name = ?
    ''', (keyword, keyword,))

    rows = cur.fetchall()

    if rows:
        items = [Item.from_row(row) for row in rows]
        return GetItemResponse(items=items)
    else:
        raise HTTPException(status_code=400, detail="No existing data with specified search word")

# get_image is a handler to return an image for GET /images/{filename} .
@app.get("/image/{image_name}")
async def get_image(image_name):
    # Create image path
    image = images / image_name

    if not image_name.endswith(".jpg"):
        raise HTTPException(status_code=400, detail="Image path does not end with .jpg")

    if not image.exists():
        # changed logger level from debug to higher log level (info, error etc.)
        logger.debug(f"Image not found: {image}")
        image = images / "default.jpg"

    return FileResponse(image)


def insert_item_json(item: Item):
    # STEP 4-2: add an implementation to store an item
    new_data = {
        "name": item.name,
        "category": item.category,
        "image": item.image
    }

    with open('items.json', 'r') as json_file:
        try:
            data = json.load(json_file)
        except json.JSONDecodeError:
            data = {}

        # print(data)
    
    if 'items' not in data:
        data['items'] = []

    data['items'].append(new_data)

    # print(data)

    with open('items.json', 'w') as json_file:
        json.dump(data, json_file, indent=4)    


def insert_item_db(db, item: Item):
    cur = db.cursor()
    cur.execute("SELECT id from categories WHERE name = ?", (item.category,))

    category_row = cur.fetchone()

    if category_row is None:
        cur.execute("INSERT INTO categories (name) VALUES (?)", (item.category,))
        category_id = cur.lastrowid
    else:
        category_id = category_row["id"]

    cur.execute("INSERT INTO items (name, category_id, image) VALUES (?, ?, ?)", (item.name, category_id, item.image))
                    
    db.commit()


def hash_image(image):
    with open(image, "rb") as f:
        try:
            image_bytes = f.read()
        except:
            raise HTTPException(status_code=400, detail="Image not found")
        image_hash = hashlib.sha256(image_bytes).hexdigest()
        image_hash = image_hash + ".jpg"
    return image_hash
