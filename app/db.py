import os
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorGridFSBucket

client = AsyncIOMotorClient(os.environ["MONGODB_URI"])
db = client[os.environ.get("MONGODB_DB", "simply_yaswanth")]
blogs = db["blogs"]
profiles = db["profiles"]
uploads_bucket = AsyncIOMotorGridFSBucket(db, bucket_name="uploads")
