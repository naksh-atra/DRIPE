import os
import logging
from typing import Dict, List, Optional
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure

logger = logging.getLogger(__name__)

class MongoStore:
    def __init__(self):
        self.uri = os.getenv("MONGO_URI")
        self.db_name = os.getenv("MONGO_DB_NAME", "DRIPE")
        self.client = None
        self.db = None

    async def connect(self):
        if not self.uri:
            logger.error("MONGO_URI not set.")
            return False
        try:
            self.client = AsyncIOMotorClient(self.uri)
            # Verify connection
            await self.client.admin.command('ping')
            self.db = self.client[self.db_name]
            logger.info(f"Connected to MongoDB Atlas: {self.db_name}")
            return True
        except Exception as e:
            logger.error(f"MongoDB connection failed: {e}")
            return False

    async def close(self):
        if self.client:
            self.client.close()

    async def save_record(self, collection_name: str, record: Dict):
        """Saves a single record to the specified collection."""
        if self.db is None: return
        collection = self.db[collection_name]
        try:
            # Upsert based on a unique ID if present, otherwise just insert
            # Assuming records have a 'uid' or similar
            uid = record.get("uid") or record.get("id") or record.get("chembl_id")
            if uid:
                await collection.replace_one({"uid": uid}, record, upsert=True)
            else:
                await collection.insert_one(record)
        except Exception as e:
            logger.error(f"Error saving to MongoDB: {e}")

    async def save_batch(self, collection_name: str, records: List[Dict]):
        """Saves a batch of records."""
        if self.db is None or not records: return
        collection = self.db[collection_name]
        try:
            # Simplified batch save
            await collection.insert_many(records)
        except Exception as e:
            logger.error(f"Error saving batch to MongoDB: {e}")

    async def get_records(self, collection_name: str, query: Dict = None, limit: int = 100):
        """Retrieves records from a collection."""
        if self.db is None: return []
        collection = self.db[collection_name]
        cursor = collection.find(query or {}).limit(limit)
        return await cursor.to_list(length=limit)
