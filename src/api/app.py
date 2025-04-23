"""Main FastAPI application entry point."""
from datetime import datetime

import strawberry
from fastapi import FastAPI
from strawberry.fastapi import GraphQLRouter
import logging
import sys

from src.api.config import settings
from src.api.schema.queries import Query
from src.api.schema.mutations import Mutation
from src.api.db.schema import initialize_schema
from src.api.db.client import DgraphClient

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.debug else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

# Create GraphQL schema
schema = strawberry.Schema(
    query=Query,
    mutation=Mutation
)

# Create GraphQL router
graphql_app = GraphQLRouter(schema)

# Create FastAPI application
app = FastAPI(
    title="Job Tracker API",
    description="GraphQL API for tracking job applications",
    version="1.0.0",
)


# Include GraphQL router
app.include_router(graphql_app, prefix="/graphql")


@app.get("/")
def read_root():
    """Root endpoint returning API status."""
    return {"message": "Job Tracker API is running! Go to /graphql for the GraphQL playground"}


@app.get("/health")
async def health_check():
    """Health check endpoint with Dgraph connectivity status."""
    dgraph_client = DgraphClient()
    dgraph_status = "ok" if dgraph_client.wait_for_dgraph(timeout=3) else "error"

    return {
        "status": "ok",
        "dgraph": dgraph_status,
        "timestamp": datetime.now().isoformat()
    }


@app.on_event("startup")
async def startup_event():
    """Run initialization tasks on startup."""
    logger.info("Starting up Job Tracker API...")

    # Initialize DGraph client
    dgraph_client = DgraphClient()

    # Initialize schema
    if not initialize_schema(dgraph_client):
        logger.error("Failed to initialize schema. API may not function correctly.")
    else:
        logger.info("Schema initialized successfully.")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api.app:app", host=settings.api_host, port=settings.api_port, reload=settings.debug)