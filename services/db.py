import os
from dotenv import load_dotenv
from pymongo import MongoClient
from loguru import logger

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = "clauseclear_db"

client = None
db = None

def init_db():
    global client, db
    try:
        client = MongoClient(MONGO_URI)
        db = client[DB_NAME]
        # Check connection
        client.admin.command('ping')
        logger.info(f"Connected to MongoDB at {MONGO_URI}")
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        # We might want to raise here or just log depending on strictness
        # For this MVP, we'll log but let the app continue (endpoints using DB will fail)

def get_db():
    return db