# simply-yaswanth backend

FastAPI backend for the simply-yaswanth personal site. It exposes public endpoints for blogs and profile data, and protected admin endpoints for managing that content and uploading images directly into MongoDB GridFS.

## Requirements
- Python 3.10+
- MongoDB database (Atlas or self-hosted)

## Setup
1. Create a virtual environment and install dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. Copy `.env.example` to `.env` and fill in the values:
   - `ADMIN_USERNAME`, `ADMIN_PASSWORD`, `JWT_SECRET`
   - `MONGODB_URI`, `MONGODB_DB`
3. Start the API:
   ```bash
   uvicorn app.main:app --reload
   ```

## Environment variables
| Key | Description |
| --- | ----------- |
| `ADMIN_USERNAME` | Admin login username |
| `ADMIN_PASSWORD` | Admin login password |
| `JWT_SECRET` | Secret used to sign admin JWTs |
| `JWT_EXPIRE_MIN` | (optional) Token lifetime in minutes, defaults to 43200 |
| `MONGODB_URI` | MongoDB connection string |
| `MONGODB_DB` | (optional) Database name, defaults to `simply_yaswanth` |
| `FRONTEND_ORIGIN` / `FRONTEND_ORIGINS` | (optional) Comma-separated origins allowed by CORS |

## API overview
- `GET /api/blogs` – list published blogs
- `GET /api/blogs/{slug}` – fetch a blog by slug
- `GET /api/profile` – fetch profile data
- `POST /api/login` – obtain an admin JWT
- `POST /api/blogs` – create a blog (auth required)
- `PUT /api/blogs/{slug}` – update a blog (auth required)
- `DELETE /api/blogs/{slug}` – delete a blog (auth required)
- `PUT /api/profile` – upsert profile info (auth required)
- `POST /api/uploads` – upload an image to MongoDB GridFS (auth required)
- `GET /api/uploads/{file_id}` – stream a stored image

### Image uploads
Admin clients can `POST /api/uploads` with multipart form data field `file`. The response includes a `public_url` that can be stored in blog/profile records. Images are persisted inside MongoDB via GridFS, removing the dependency on external storage.

## Development tips
- Run with `--reload` for auto-refresh during development.
- When deploying behind a proxy, ensure the proxy forwards headers needed by FastAPI/uvicorn.
- Consider adding limits or validation around image size and type if you expect untrusted uploads.
