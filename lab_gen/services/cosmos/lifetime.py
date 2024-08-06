from azure.cosmos import CosmosClient, PartitionKey
from fastapi import FastAPI
from loguru import logger

from lab_gen.settings import settings


DATABASE_NAME = "gen-app-data-" + settings.environment.lower()
CONTAINER_NAME = "history"


def init_cosmosdb(app: FastAPI) -> None:
    """
    Initializes the CosmosDB client and creates the necessary database and container if they do not already exist.

    Args:
        app (FastAPI): The FastAPI application object.

    Returns:
        None
    """
    try :
        client = CosmosClient(settings.session_store_uri, credential=settings.session_store_key)
        database = client.create_database_if_not_exists(DATABASE_NAME)
        database.create_container_if_not_exists(
            CONTAINER_NAME,
            partition_key=PartitionKey("/user_id"),
            default_ttl=settings.session_store_ttl,
        )
    except Exception as e:  # noqa: BLE001
        logger.error(f"Error initializing CosmosDB client: {e}")
        client = None
    app.state.cosmos_client = client
