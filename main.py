import sqlite3
from fastapi import FastAPI, Query, HTTPException, status, Response
from pydantic import BaseModel

app = FastAPI()


class Album(BaseModel):
    title: str
    artist_id: int


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
