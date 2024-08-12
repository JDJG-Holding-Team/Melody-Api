import typing
from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import os
import asyncpg
from contextlib import asynccontextmanager
from dotenv import load_dotenv

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


@app.get("/")
async def root():
    return JSONResponse(content={"message": "Welcome to the Melody API"})


@app.get("/services", response_model=ServiceListResponse)
async def services():
    data = {}
    music_services = [record.service for record in await app.pool.fetch("SELECT DISTINCT service FROM music")]
    tech_services = [record.service for record in await app.pool.fetch("SELECT DISTINCT service FROM tech_videos")]
    anime_services = [record.service for record in await app.pool.fetch("SELECT DISTINCT service FROM anime_videos")]
    misc_services = [record.service for record in await app.pool.fetch("SELECT DISTINCT service FROM misc_videos")]
    watch_services = [record.service for record in await app.pool.fetch("SELECT DISTINCT service FROM to_watch")]
    watched_services = [
        record.service for record in await app.pool.fetch("SELECT DISTINCT service FROM watched_videos")
    ]

    data["music"] = music_services
    data["tech"] = tech_services
    data["anime"] = anime_services
    data["misc"] = misc_services
    data["watch"] = watch_services
    data["watched"] = watched_services
    return JSONResponse(content={"data": data})


async def fetch_content(table_name: str, number: int, service: typing.Optional[str] = None):
    query = f"SELECT * FROM {table_name}"
    params = []

    if service:
        query += " WHERE service = $1"
        params.append(service)
        query += "ORDER BY RANDOM() LIMIT $2"

    else:
        query += "ORDER BY RANDOM() LIMIT $1"

    params.append(number)

    data = [dict(r) for r in await app.pool.fetch(query, *params)]
    if not data:
        raise HTTPException(status_code=404, detail="No content found for the given service.")
    return data


@app.get("/music", response_model=typing.List[ContentResponse])
async def music_content(number: typing.Optional[int] = Query(10, gt=0, le=500), service: typing.Optional[str] = None):
    data = await fetch_content("music", number, service)
    return JSONResponse(content={"data": data})


@app.get("/tech", response_model=typing.List[ContentResponse])
async def tech_content(number: typing.Optional[int] = Query(10, gt=0, le=500), service: typing.Optional[str] = None):
    data = await fetch_content("tech_videos", number, service)
    return JSONResponse(content={"data": data})


@app.get("/anime", response_model=typing.List[ContentResponse])
async def anime_content(number: typing.Optional[int] = Query(10, gt=0, le=500), service: typing.Optional[str] = None):
    data = await fetch_content("anime_videos", number, service)
    return JSONResponse(content={"data": data})


@app.get("/misc", response_model=typing.List[ContentResponse])
async def misc_content(number: typing.Optional[int] = Query(10, gt=0, le=500), service: typing.Optional[str] = None):
    data = await fetch_content("misc_videos", number, service)
    return JSONResponse(content={"data": data})


@app.get("/watch", response_model=typing.List[ContentResponse])
async def to_watch_content(
    number: typing.Optional[int] = Query(10, gt=0, le=500), service: typing.Optional[str] = None
):
    data = await fetch_content("to_watch", number, service)
    return JSONResponse(content={"data": data})


@app.get("/watched", response_model=typing.List[ContentResponse])
async def watched_content(number: typing.Optional[int] = Query(10, gt=0, le=500), service: typing.Optional[str] = None):
    data = await fetch_content("watched_videos", number, service)
    return JSONResponse(content={"data": data})


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", port=5200, log_level="debug")
