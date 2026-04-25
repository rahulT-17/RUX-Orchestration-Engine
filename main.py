# Purpose : To boot the system:

import time 
import logging
import os

from fastapi import FastAPI, Request
from api.routes import router

from core.migration_guard import ensure_schema_revision

from api.debug_routes import router as debug_router

request_logger = logging.getLogger("rux.request_timing")

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
  level=LOG_LEVEL,
  format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

app = FastAPI(
    title="RUX Personal OS AI system",
    version="v0.2",
    description="This is the backend API RUX. /chat | /debug | /feedback",
)

# connecting the app to api router :
@app.middleware("http")
async def request_timing_middleware(request: Request, call_next):
    start = time.perf_counter()
    try:
      response = await call_next(request)
    except Exception as e:
      total_ms = round((time.perf_counter() - start) * 1000, 2)
      request_logger.error(
        "request_timing method=%s path=%s status=%s total_ms=%.2f",
        request.method,
        request.url.path,
        500,
        total_ms,
    )
      raise
  
    total_ms = round((time.perf_counter() - start) * 1000, 2)
    response.headers["X-Process-Time-ms"] = str(total_ms) 
    request_logger.info(
          "request_timing method=%s path=%s status=%s total_ms=%.2f",
          request.method,
          request.url.path,
          response.status_code,
          total_ms,
    )
    
    return response

app.include_router(router)
app.include_router(debug_router)

@app.on_event("startup")
async def verify_schema_revision():
  await ensure_schema_revision()

@app.get("/")
def root() :
  return {"message" : "RUX backend is working fine!"}

@app.get("/health")
def health_check():
  return {"status" : "healthy"}
