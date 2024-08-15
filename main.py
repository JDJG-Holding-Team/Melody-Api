import enum
import os
import typing
from contextlib import asynccontextmanager

import asyncpg
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel

if not os.getenv("DB_KEY"):
    load_dotenv()


class CustomRecordClass(asyncpg.Record):
    def __getattr__(self, name: str) -> typing.Any:
        if name in self.keys():
            return self[name]
        return super().__getattr__(name)


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with asyncpg.create_pool(os.environ["DB_KEY"], record_class=CustomRecordClass) as app.pool:
        yield


app = FastAPI(lifespan=lifespan)


# Define the BaseModel for the API response
class ContentResponse(BaseModel):
    user_id: int
    url: str
    service: str


class ServiceListResponse(BaseModel):
    music: typing.List[str]
    tech: typing.List[str]
    anime: typing.List[str]
    misc: typing.List[str]
    watch: typing.List[str]
    watched: typing.List[str]
    any_video: typing.List[str]


class ContentType(enum.IntEnum):
    music = 0
    tech = 1
    anime = 2
    misc = 3
    watch = 4
    watched = 5


@app.get("/")
async def root():
    return JSONResponse(content={"message": "Welcome to the Melody API"})


@app.get("/services", response_model=ServiceListResponse)
async def services():
    data = {}
    for content_type in ContentType:
        data[content_type.name] = [
            record.service
            for record in await app.pool.fetch(
                "SELECT DISTINCT service FROM CONTENT where content_type = $1", content_type.value
            )
        ]

    data["any-video"] = [record.service for record in await app.pool.fetch("SELECT DISTINCT service FROM CONTENT")]
    return JSONResponse(content={"data": data})


async def fetch_content(
    number: int, service: typing.Optional[str] = None, content_type: typing.Optional[ContentType] = None
):
    query = "SELECT * FROM CONTENT"
    params = []

    if service and content_type is not None:
        query += " WHERE service = $1 AND content_type = $2 ORDER BY RANDOM() LIMIT $3"
        params.append(service)
        params.append(content_type.value)

    elif service and content_type is None:
        query += " WHERE service = $1 ORDER BY RANDOM() LIMIT $2"
        params.append(service)

    elif not service and content_type is not None:
        query += " WHERE content_type = $1 ORDER BY RANDOM() LIMIT $2"
        params.append(content_type.value)

    else:
        query += " ORDER BY RANDOM() LIMIT $1"

    params.append(number)

    data = [dict(r) for r in await app.pool.fetch(query, *params)]
    if not data:
        raise HTTPException(status_code=404, detail="No content found for the given service.")
    return data


@app.get("/music", response_model=typing.List[ContentResponse])
async def music_content(number: typing.Optional[int] = Query(10, gt=0, le=500), service: typing.Optional[str] = None):
    data = await fetch_content(number, service, ContentType.music)
    return JSONResponse(content={"data": data})


@app.get("/tech", response_model=typing.List[ContentResponse])
async def tech_content(number: typing.Optional[int] = Query(10, gt=0, le=500), service: typing.Optional[str] = None):
    data = await fetch_content(number, service, ContentType.tech)
    return JSONResponse(content={"data": data})


@app.get("/anime", response_model=typing.List[ContentResponse])
async def anime_content(number: typing.Optional[int] = Query(10, gt=0, le=500), service: typing.Optional[str] = None):
    data = await fetch_content(number, service, ContentType.anime)
    return JSONResponse(content={"data": data})


@app.get("/misc", response_model=typing.List[ContentResponse])
async def misc_content(number: typing.Optional[int] = Query(10, gt=0, le=500), service: typing.Optional[str] = None):
    data = await fetch_content(number, service, ContentType.misc)
    return JSONResponse(content={"data": data})


@app.get("/watch", response_model=typing.List[ContentResponse])
async def to_watch_content(
    number: typing.Optional[int] = Query(10, gt=0, le=500), service: typing.Optional[str] = None
):
    data = await fetch_content(number, service, ContentType.watch)
    return JSONResponse(content={"data": data})


@app.get("/watched", response_model=typing.List[ContentResponse])
async def watched_content(number: typing.Optional[int] = Query(10, gt=0, le=500), service: typing.Optional[str] = None):
    data = await fetch_content(number, service, ContentType.watched)
    return JSONResponse(content={"data": data})


@app.get("/any-video", response_model=typing.List[ContentResponse])
async def any_video(number: typing.Optional[int] = Query(10, gt=0, le=500), service: typing.Optional[str] = None):
    data = await fetch_content(number, service)
    return JSONResponse(content={"data": data})


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", port=5200, log_level="debug")
