import os, re
from dotenv import load_dotenv

# Get absolute path of backend directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import FastAPI, HTTPException, UploadFile, File, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from gridfs.errors import NoFile
from pydantic import BaseModel

from .auth import create_token, admin_required
from .db import blogs, profiles, uploads_bucket
from .models import Blog, Profile

DEFAULT_CORS_ORIGINS = {
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://simply-yaswanth.vercel.app/"
}

def load_cors_origins():
    origins = set(DEFAULT_CORS_ORIGINS)
    for key in ("FRONTEND_ORIGINS", "FRONTEND_ORIGIN"):
        raw = os.environ.get(key)
        if not raw:
            continue
        origins.update(origin.strip() for origin in raw.split(",") if origin.strip())
    return sorted(origins)

origins = load_cors_origins()

app = FastAPI(title="simply-yaswanth")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class LoginBody(BaseModel):
    username: str
    password: str

@app.post("/api/login")
async def login(body: LoginBody):
    if body.username == os.environ["ADMIN_USERNAME"] and body.password == os.environ["ADMIN_PASSWORD"]:
        return {"token": create_token()}
    raise HTTPException(status_code=401, detail="Invalid credentials")

def slugify(s: str):
    return re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-')

# --- Public endpoints ---
@app.get("/api/blogs")
async def list_blogs():
    items = []
    async for b in blogs.find().sort("published_at", -1):
        b["id"] = str(b["_id"])
        b.pop("_id", None)
        items.append(b)
    return items

@app.get("/api/blogs/{slug}")
async def get_blog(slug: str):
    doc = await blogs.find_one({"slug": slug})
    if not doc: raise HTTPException(404)
    doc["id"] = str(doc["_id"])
    doc.pop("_id", None)
    return doc

@app.get("/api/profile")
async def get_profile():
    doc = await profiles.find_one({})
    if not doc:
        return {}
    doc["id"] = str(doc["_id"])
    doc.pop("_id", None)
    return doc

# --- Admin endpoints ---
@app.post("/api/blogs", dependencies=[Depends(admin_required)])
async def create_blog(b: Blog):
    b.slug = b.slug or slugify(b.title)
    await blogs.insert_one(b.model_dump(by_alias=True, exclude_none=True))
    return {"ok": True, "slug": b.slug}

@app.put("/api/blogs/{slug}", dependencies=[Depends(admin_required)])
async def update_blog(slug: str, b: Blog):
    b.slug = slug
    res = await blogs.update_one({"slug": slug}, {"$set": b.model_dump(by_alias=True, exclude_none=True)})
    if not res.matched_count: raise HTTPException(404)
    return {"ok": True}

@app.delete("/api/blogs/{slug}", dependencies=[Depends(admin_required)])
async def delete_blog(slug: str):
    await blogs.delete_one({"slug": slug})
    return {"ok": True}

@app.put("/api/profile", dependencies=[Depends(admin_required)])
async def upsert_profile(p: Profile):
    await profiles.update_one({}, {"$set": p.model_dump(by_alias=True, exclude_none=True)}, upsert=True)
    return {"ok": True}

@app.post("/api/uploads", dependencies=[Depends(admin_required)])
async def upload_image(request: Request, file: UploadFile = File(...)):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image uploads are supported")
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty file")
    file_id = await uploads_bucket.upload_from_stream(
        file.filename or "upload",
        data,
        metadata={"content_type": file.content_type},
    )
    public_path = f"/api/uploads/{file_id}"
    base_url = str(request.base_url).rstrip("/")
    public_url = f"{base_url}{public_path}"
    return {"file_id": str(file_id), "public_url": public_url, "public_path": public_path}

@app.get("/api/uploads/{file_id}")
async def get_upload(file_id: str):
    try:
        oid = ObjectId(file_id)
    except (InvalidId, TypeError):
        raise HTTPException(status_code=404, detail="File not found")
    try:
        grid_out = await uploads_bucket.open_download_stream(oid)
    except NoFile:
        raise HTTPException(status_code=404, detail="File not found")

    async def stream():
        while True:
            chunk = await grid_out.readchunk()
            if not chunk:
                break
            yield chunk

    metadata = grid_out.metadata or {}
    media_type = metadata.get("content_type") or "application/octet-stream"
    headers = {"Cache-Control": "public, max-age=31536000"}
    return StreamingResponse(stream(), media_type=media_type, headers=headers)
