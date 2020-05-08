import sqlite3
from fastapi import FastAPI, Query, HTTPException, status, Response
from pydantic import BaseModel

app = FastAPI()


@app.on_event("startup")
async def startup():
    app.db_connection = sqlite3.connect('chinook.db')


@app.on_event("shutdown")
async def shutdown():
    app.db_connection.close()


# ***********************ZAD1********************

@app.get("/tracks/")
async def tracks(page: int = Query(0), per_page: int = Query(10)):
    app.db_connection.row_factory = sqlite3.Row
    tracks = app.db_connection.execute(
        "SELECT * FROM tracks ORDER BY trackid ASC LIMIT ? OFFSET ? ",
        (per_page, page*per_page)).fetchall()
    return tracks


# ***********************ZAD2********************

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


# ***********************ZAD3********************

class Album(BaseModel):
    title: str
    artist_id: int


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

class Customer(BaseModel):
    company: str = None
    address: str = None
    city: str = None
    state: str = None
    country: str = None
    postalcode: str = None
    fax: str = None


@app.put("/customers/{customer_id}/")
async def customer(customer_id: int, customer: Customer):
    cursor = app.db_connection.cursor()
    cursor.row_factory = sqlite3.Row
    db_customer = cursor.execute("SELECT customerid FROM customers WHERE customerid = ? ", (customer_id,)).fetchone()
    if not db_customer:
        raise HTTPException(status_code=404, detail={"error": "Customer not found"})

    cursor.execute('''
        UPDATE customers SET 
            Company=COALESCE(?, Company),
            Address=COALESCE(?, Address),
            City=COALESCE(?, City),
            State=COALESCE(?, State), 
            Country=COALESCE(?, Country), 
            PostalCode=COALESCE(?, PostalCode), 
            Fax=COALESCE(?, Fax) 
        WHERE CustomerId=?''', (customer.company, customer.address, customer.city, customer.state, customer.country,
                                customer.postalcode, customer.fax, customer_id))
    app.db_connection.commit()

    updated_customer = cursor.execute("SELECT * FROM customers WHERE customerid = ? ", (customer_id,)).fetchone()
    return updated_customer


# **************************ZAD5*************************

@app.get("/sales/")
async def sales(category: str = Query("")):
    if category != "customers":
        raise HTTPException(status_code=404, detail={"error": "Category not found"})
    cursor = app.db_connection.cursor()
    cursor.row_factory = sqlite3.Row
    sales = cursor.execute('''
        SELECT customers.CustomerId, Email, Phone, round(SUM(invoices.Total),2) AS Sum 
        FROM customers JOIN invoices ON invoices.CustomerId = customers.CustomerId 
        GROUP BY customers.CustomerId 
        ORDER BY Sum DESC, customers.CustomerId''').fetchall()

    return sales
