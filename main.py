import time
from uuid import uuid4
from fastapi import FastAPI, Request, Response
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from api.api import api_v1_router

app = FastAPI()

@app.middleware("http")
async def request_middleware(request: Request, call_next):
    _headers = request.headers
    if not _headers.get("x-transaction-ref"):
        x_transaction = uuid4()
        request.headers.__dict__["_list"].append(
            (
                "x-transaction-ref".encode(),
                str(x_transaction).encode(),
            )
        )
    else:
        x_transaction = _headers.get("x-transaction-ref")


    start_time = time.time()
    response: Response = await call_next(request)
    process_time = str(round((time.time() - start_time), 2))
    response.headers["x-process-time"] = process_time
    response.headers["access-control-allow-origin"] = _headers.get("origin") or "*"
    return response


origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    api_v1_router,
    prefix="/app/login",
)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=6001,reload=True)