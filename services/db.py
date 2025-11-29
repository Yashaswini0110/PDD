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
        # Explicitly disable SSL validation for MongoDB Atlas connection
        # This is a common workaround for SSL handshake issues, but should be
        # reviewed for production environments. For a full solution,
        # trusted CA certificates should be provided.
        client = MongoClient(MONGO_URI, tls=True, tlsAllowInvalidCertificates=True, tlsAllowInvalidHostnames=True)
        db = client[DB_NAME]
        # Check connection
        client.admin.command('ping')
        logger.info(f"Connected to MongoDB at {MONGO_URI}")
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        # Log the error but continue, effectively disabling DB for the current session
        client = None
        db = None
        logger.warning("MongoDB connection disabled. Endpoints requiring DB will use mock data or fail gracefully.")

def get_db():
    # Return None if DB connection failed, allowing mock data or graceful failure
    return db