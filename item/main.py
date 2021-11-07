# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.
import decimal
from typing import List
from unicodedata import numeric

from databases import Database
import sqlalchemy
from fastapi import FastAPI
from pydantic import BaseModel
from datetime import date


import uvicorn

# SQLAlchemy specific code, as with any other app
# DATABASE_URL = "sqlite:///./test2.db"
# DATABASE_URL = "postgresql://postgres:regan1@127.0.0.1/remrp"
DATABASE_URL_ALC = 'mysql+pymysql://root:regan1@localhost:3306/remrp'
DATABASE_URL = 'mysql://root:regan1@localhost:3306/remrp'
database = Database(DATABASE_URL, min_size =5, max_size = 20, ssl = False)

metadata = sqlalchemy.MetaData()

notes = sqlalchemy.Table(
    "notes",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("text", sqlalchemy.String(50)),
    sqlalchemy.Column("completed", sqlalchemy.Boolean),
    sqlalchemy.Column("lastupdate", sqlalchemy.Date),
    sqlalchemy.Column("amount", sqlalchemy.DECIMAL),
)

engine = sqlalchemy.create_engine(
    DATABASE_URL_ALC, echo=True
)
metadata.create_all(engine)


class NoteIn(BaseModel):
    text: str
    completed: bool


class Note(BaseModel):
    id: int
    text: str
    completed: bool
    lastupdate: date
    amount: decimal.Decimal

app = FastAPI()


@app.on_event("startup")
async def startup():
    await database.connect()


@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()


@app.get("/notes/", response_model=List[Note])
async def read_notes():
    query = notes.select()
    return await database.fetch_all(query)



@app.post("/notes/")
async def create_note(note: NoteIn):
    query = notes.insert().values(text=note.text, completed=note.completed, lastupdate=date.today(), amount=0.0)
    last_record_id = await database.execute(query)
    return {**note.dict(), "id": last_record_id}


@app.delete("/notes/{id}")
async def del_note(id: int):
    stmt = notes.select(notes.c.id == id)
    rs = await database.fetch_one(stmt)
    if rs[2] == False:
        print(f'id {id} already deleted')
    else:
        stmt = notes.update().where(notes.c.id == id).values(completed = False)
        transaction = await database.transaction()
        try:
            counter = await database.execute(stmt)
        except:
            await transaction.rollback()
        else:
            await transaction.commit()
    return rs

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=5000, log_level="info")
