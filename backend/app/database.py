"""Database connection management via Prisma Client Python.

Exposes a single shared `Prisma` client instance plus helper functions used
by the FastAPI lifespan handler to connect/disconnect on startup/shutdown.
"""

import logging

from prisma import Prisma

logger = logging.getLogger("app.database")

# Single shared Prisma client for the whole process.
prisma_client = Prisma(auto_register=True)


async def connect_db() -> None:
    """Connect to the database if not already connected."""
    if not prisma_client.is_connected():
        await prisma_client.connect()
        logger.info("Database connection established")


async def disconnect_db() -> None:
    """Disconnect from the database if currently connected."""
    if prisma_client.is_connected():
        await prisma_client.disconnect()
        logger.info("Database connection closed")


def get_client() -> Prisma:
    """Return the shared Prisma client instance."""
    return prisma_client
