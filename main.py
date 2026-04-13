# Purpose : To boot the system:

import logging
import os

from fastapi import FastAPI
from api.routes import router

from api.debug_routes import router as debug_router

## APP CONFIGURATION :
''' upgrading the RUX to a devagent (02/2026,110 days) changing the
      whole architecture to router-based,

oops forgot as of (4-03-26) : I have successfully integrated the postgresql db with also established the repositories layer for handling the db operations,
  where earlier it was handled directly in the memory manager, 

also integrated observability features like logging the agent runs and outcomes in the database,
  and also added confidence scoring for the tools execution results, which will be stored in the database as well,
     and can be used for monitoring and debugging purposes.

moreover I have added some debug routes for monitoring the agent runs and outcomes, 
  which will be helpful for debugging and improving the system.

lastly working on confidence engine and second opinion engine , will be the x-factor for the system , likely 60-70% achitecture work is done , the 
  remaining work is to implement the confidence engine and second opinion engine, and also to do some testing and fine-tuning of the system.

'''

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
  level=LOG_LEVEL,
  format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

app = FastAPI(
    title="RUX Personal OS AI system",
    version="2.1.0",
    description="This is the backend API for RUX Personal OS AI system. It is built using FastAPI and is responsible for handling API requests, managing the agent's core logic, and interacting with the database.",
)

# connecting the app to api router :

app.include_router(router)
app.include_router(debug_router)


@app.get("/")
def root() :
 return {"message" : "RUX backend is working fine!"}


