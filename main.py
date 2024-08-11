import os
import typing
from contextlib import asynccontextmanager

import asyncpg
import fastapi
import uvicorn
from dotenv import load_dotenv
from fastapi.responses import JSONResponse, Response

if not os.getenv("DB_KEY"):
    load_dotenv()


class CustomRecordClass(asyncpg.Record):
    def __getattr__(self, name: str) -> Any:
        if name in self.keys():
            return self[name]
        return super().__getattr__(name)


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with asyncpg.create_pool(os.environ["DB_KEY"], record_class=CustomRecordClass) as app.pool:
        yield


app = FastAPI(lifespan=lifespan)


@app.get("/")
async def root():
    return JSONResponse(content={"message": "welcome to melody api"})

@app.get("/music")
async def music(number: typing.Optional[int] = 10):
    if number > 500:
        return JSONResponse(content={error:"Too many Urls requested. Limit is 500"}, status_code=403)

    elif number <= 0:
        return JSONResponse(content={error:"You need to grab at least one url"}, status_code=403)
    
    # figure out how music it should give maybe make it give a different response for only one url grab.
    data = [dict(r) for r in await app.pool.fetch("SELECT * FROM MUSIC ORDER BY RANDOM() LIMIT $1", number)]
    return JSONResponse(content={"data": data})


# so far so good.


if __name__ == "__main__":
    uvicorn.run("main:app", port=2343, log_level="debug")
