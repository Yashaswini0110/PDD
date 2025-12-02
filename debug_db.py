import os
import certifi
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = "clauseclear_db"

def check():
    client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
    db = client[DB_NAME]
    
    uid = "Uu9PszHbMCbK1BZxT9JJVB2JyUu1"
    print(f"Checking jobs for uid: {uid}")
    
    count = db["jobs"].count_documents({"uid": uid})
    print(f"Found {count} jobs.")
    
    cursor = db["jobs"].find({"uid": uid})
    for doc in cursor:
        print(f" - Job: {doc.get('job_id')}, File: {doc.get('filename')}")

if __name__ == "__main__":
    check()