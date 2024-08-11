import os
from contextlib import asynccontextmanager

import fastapi
import uvicorn
from dotenv import load_dotenv
from fastapi.responses import JSONResponse, Response

if not os.getenv("DB_URL"):
    load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with asyncpg.create_pool(os.env["DB_URL"]) as app.pool:
        yield


app = FastAPI(lifespan=lifespan)


@app.get("/")
async def root():
    return JSONResponse(content={"message": "welcome to melody api"})


if __name__ == "__main__":
    uvicorn.run("main:app", port=2343, log_level="debug")
