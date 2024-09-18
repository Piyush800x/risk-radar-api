from dotenv import load_dotenv
from pymongo import MongoClient
import os

load_dotenv()

URI = os.getenv("MONGODB_URI")

client = MongoClient(URI)

# DB
db = client["risk-radar"]

# # Collection
# collection = db["vendors"]

