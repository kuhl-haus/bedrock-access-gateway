import logging

import uvicorn
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from mangum import Mangum

from api.routers import model, chat, embeddings
from api.setting import (
    API_ROUTE_PREFIX,
    TITLE,
    DESCRIPTION,
    SUMMARY,
    VERSION,
    DEFAULT_MODEL,
    DEFAULT_EMBEDDING_MODEL,
    ENABLE_CROSS_REGION_INFERENCE,
    SECRET_ARN_PARAMETER,
)

config = {
    "title": TITLE,
    "description": DESCRIPTION,
    "summary": SUMMARY,
    "version": VERSION,
}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
app = FastAPI(**config)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(model.router, prefix=API_ROUTE_PREFIX)
app.include_router(chat.router, prefix=API_ROUTE_PREFIX)
app.include_router(embeddings.router, prefix=API_ROUTE_PREFIX)


@app.get("/health")
async def health():
    """For health check if needed"""
    return {
        "status": "OK",
        "version": VERSION,
        "api_route_prefix": API_ROUTE_PREFIX,
        "default_model": DEFAULT_MODEL,
        "default_embedding_model": DEFAULT_EMBEDDING_MODEL,
        "enable_cross_region_inference": ENABLE_CROSS_REGION_INFERENCE,
        "secret_arn_parameter": SECRET_ARN_PARAMETER,
    }


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return PlainTextResponse(str(exc), status_code=400)


handler = Mangum(app)

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
