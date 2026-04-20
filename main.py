# Purpose : To boot the system:

import logging
import os

from fastapi import FastAPI
from api.routes import router

from core.migration_guard import ensure_schema_revision

from api.debug_routes import router as debug_router


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
