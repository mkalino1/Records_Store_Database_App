import sqlite3
from fastapi import FastAPI, Query, HTTPException, status, Response
from pydantic import BaseModel

app = FastAPI()


class Album(BaseModel):
    title: str
    artist_id: int


class Customer(BaseModel):
    company: str = None
    address: str = None
    city: str = None
    state: str = None
    country: str = None
    postalcode: str = None
    fax: str = None


@app.on_event("startup")
async def startup():
    app.db_connection = sqlite3.connect('chinook.db')


@app.on_event("shutdown")
async def shutdown():
    app.db_connection.close()


@app.get("/tracks/composers/")
async def composers(composer_name: str = Query("")):
    cursor = app.db_connection.cursor()
    cursor.row_factory = lambda cursor, x: x[0]
    titles = cursor.execute(
        "SELECT name FROM tracks WHERE composer = ? ORDER BY name ASC",
        (composer_name,)).fetchall()
    if titles:
        return titles
    raise HTTPException(status_code=404, detail={"error": "Not found"})


@app.get("/tracks/")
async def tracks(page: int = Query(0), per_page: int = Query(10)):
    app.db_connection.row_factory = sqlite3.Row
    tracks = app.db_connection.execute(
        "SELECT * FROM tracks ORDER BY trackid ASC LIMIT ? OFFSET ? ",
        (per_page, page*per_page)).fetchall()

    return tracks


@app.post("/albums/")
async def album(album: Album, response: Response):
    cursor = app.db_connection.cursor()
    artist = cursor.execute("SELECT artistid FROM artists WHERE artistid = ? ", (album.artist_id,)).fetchone()
    if not artist:
        raise HTTPException(status_code=404, detail={"error": "Artist not found"})

    cursor.execute("INSERT INTO albums (title, artistid) VALUES (?, ?)", (album.title, album.artist_id))
    app.db_connection.commit()
    response.status_code = status.HTTP_201_CREATED
    return {
        "AlbumId": cursor.lastrowid,
        "Title": album.title,
        "ArtistId": album.artist_id
    }


@app.get("/albums/{album_id}/")
async def get_album(album_id: int):
    app.db_connection.row_factory = sqlite3.Row
    album = app.db_connection.execute(
        "SELECT * FROM albums WHERE albumid = ?",
        (album_id,)).fetchone()
    return album

# **************************ZAD4*************************

@app.put("/customers/{customer_id}/")
async def customer(customer_id: int, customer: Customer):
    cursor = app.db_connection.cursor()
    cursor.row_factory = sqlite3.Row
    db_customer = cursor.execute("SELECT customerid FROM customers WHERE customerid = ? ", (customer_id,)).fetchone()
    if not db_customer:
        raise HTTPException(status_code=404, detail={"error": "Customer not found"})

    update_data = customer.dict(exclude_unset=True)

    for key, val in update_data.items():
        sql_string = f"UPDATE customers SET {key} = '{val}' WHERE customerid = {customer_id}"
        cursor.execute(sql_string)
        app.db_connection.commit()

    db_customer = cursor.execute("SELECT * FROM customers WHERE customerid = ? ", (customer_id,)).fetchone()
    return db_customer



#   for key, val in update_data.items():
#      instruction = f"{key} = '{val}'"
#        cursor.execute("UPDATE customers SET ? WHERE customerid = ?", (instruction, customer_id,))
#       cursor.commit()