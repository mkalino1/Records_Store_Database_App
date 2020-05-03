import sqlite3
from fastapi import FastAPI, Query, HTTPException

app = FastAPI()


@app.on_event("startup")
async def startup():
    app.db_connection = sqlite3.connect('chinook.db')


@app.on_event("shutdown")
async def shutdown():
    app.db_connection.close()


@app.get("/tracks/composers/")
async def composer(composer_name: str = Query("")):
    cursor = app.db_connection.cursor()
    cursor.row_factory = lambda cursor, x: x[0]
    titles = cursor.execute(
        "SELECT name FROM tracks WHERE composer = ? ORDER BY name ASC",
        (composer_name,)).fetchall()
    if titles:
        return titles
    raise HTTPException(status_code=404, detail={"error": "Not Found"})


@app.get("/tracks/")
async def single_track(page: int = Query(0), per_page: int = Query(10)):
    app.db_connection.row_factory = sqlite3.Row
    tracks = app.db_connection.execute(
        "SELECT * FROM tracks ORDER BY trackid ASC LIMIT ? OFFSET ? ",
        (per_page, page*per_page)).fetchall()

    return tracks

'''app.db_connection = sqlite3.connect('chinook.db')
cursor = app.db_connection.cursor()
cursor.row_factory = sqlite3.Row
titles = app.db_connection.execute("SELECT composer FROM tracks").fetchall()
print(titles)
app.db_connection.close()'''