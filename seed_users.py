from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = "clauseclear_db"

users = [
    {
        "uid": "user_alpha",
        "firstName": "Alice",
        "lastName": "Smith",
        "email": "alice@example.com",
        "phone": "9876543210",
        "address": "123 Baker Street, London",
        "dob": "1990-05-15",
        "pan": "ABCDE1234A",
        "aadhaar": "111122223333"
    },
    {
        "uid": "user_beta",
        "firstName": "Bob",
        "lastName": "Jones",
        "email": "bob@example.com",
        "phone": "8765432109",
        "address": "456 Pine Avenue, New York",
        "dob": "1985-10-20",
        "pan": "FGHIJ5678B",
        "aadhaar": "444455556666"
    },
    {
        "uid": "user_gamma",
        "firstName": "Charlie",
        "lastName": "Brown",
        "email": "charlie@example.com",
        "phone": "7654321098",
        "address": "789 Oak Lane, Toronto",
        "dob": "1992-03-08",
        "pan": "KLMNO9012C",
        "aadhaar": "777788889999"
    }
]

def seed():
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    collection = db["users"]
    
    for user in users:
        collection.update_one(
            {"uid": user["uid"]},
            {"$set": user},
            upsert=True
        )
        print(f"Seeded user: {user['email']} (UID: {user['uid']})")

if __name__ == "__main__":
    seed()