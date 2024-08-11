import os
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
    async with asyncpg.create_pool(os.env["DB_KEY"], record_class=CustomRecordClass) as app.pool:
        yield


app = FastAPI(lifespan=lifespan)


@app.get("/")
async def root():
    return JSONResponse(content={"message": "welcome to melody api"})


# so far so good.


if __name__ == "__main__":
    uvicorn.run("main:app", port=2343, log_level="debug")
