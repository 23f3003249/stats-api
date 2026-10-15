
import os
import time
import uuid

from fastapi import FastAPI, Query, Request
from fastapi.responses import JSONResponse, Response

app = FastAPI()

ALLOWED_ORIGIN = "https://dash-kp2ui5.example.com"
EMAIL = os.environ.get("EMAIL", "REPLACE_WITH_YOUR_EMAIL")


@app.middleware("http")
async def request_middleware(request: Request, call_next):
    start = time.perf_counter()
    request_id = str(uuid.uuid4())

    origin = request.headers.get("origin")

    # Handle CORS preflight requests explicitly.
    if request.method == "OPTIONS":
        if origin != ALLOWED_ORIGIN:
            response = Response(status_code=403)
        else:
            response = Response(status_code=204)
            response.headers["Access-Control-Allow-Origin"] = ALLOWED_ORIGIN
            response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = (
                request.headers.get("access-control-request-headers", "Content-Type")
            )
            response.headers["Vary"] = "Origin"

    elif origin and origin != ALLOWED_ORIGIN:
        # Reject cross-origin requests from unapproved origins.
        response = JSONResponse(
            status_code=403,
            content={"detail": "Origin not allowed"},
        )

    else:
        response = await call_next(request)

        if origin == ALLOWED_ORIGIN:
            response.headers["Access-Control-Allow-Origin"] = ALLOWED_ORIGIN
            response.headers["Vary"] = "Origin"

    elapsed = time.perf_counter() - start
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time"] = f"{elapsed:.6f}"

    return response


@app.get("/stats")
async def stats(values: str = Query(...)):
    try:
        numbers = [int(value.strip()) for value in values.split(",")]

        if not numbers or any(value == "" for value in values.split(",")):
            raise ValueError("Empty value")

    except ValueError:
        return JSONResponse(
            status_code=400,
            content={"detail": "values must be comma-separated integers"},
        )

    return {
        "email": EMAIL,
        "count": len(numbers),
        "sum": sum(numbers),
        "min": min(numbers),
        "max": max(numbers),
        "mean": sum(numbers) / len(numbers),
    }
