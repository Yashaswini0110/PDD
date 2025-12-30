import os
import certifi
from dotenv import load_dotenv
from pymongo import MongoClient
import json

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = "clauseclear_db"

def check():
    client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
    db = client[DB_NAME]
    
    # Check uploads
    print(f"Checking uploads...")
    count = db["uploads"].count_documents({})
    print(f"Found {count} uploads.")
    
    cursor = db["uploads"].find({})
    for doc in cursor:
        job_id = doc.get('job_id')
        uid = doc.get('user_id')
        filename = doc.get('filename')
        status = doc.get('status')
        print(f"\n- Upload Job: {job_id}")
        print(f"  User ID: {uid}")
        print(f"  File: {filename}")
        print(f"  Status: {status}")

    # Check QA messages
    print(f"\nChecking QA messages...")
    qa_count = db["qa_messages"].count_documents({})
    print(f"Found {qa_count} QA messages.")
    
    qa_cursor = db["qa_messages"].find({}).limit(5)
    for doc in qa_cursor:
        print(f"  - [{doc.get('job_id')}] Q: {doc.get('query')} | A (prefix): {str(doc.get('answer'))[:50]}...")

    # Check Analytics
    print(f"\nChecking Analytics...")
    analytics_count = db["analytics"].count_documents({})
    print(f"Found {analytics_count} analytics records.")

if __name__ == "__main__":
    check()