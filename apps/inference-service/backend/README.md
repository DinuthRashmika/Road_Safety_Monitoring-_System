# Inference Service Backend

## Local setup

Create `.env` in this folder. You can copy the starter values from `env.example`:

```powershell
Copy-Item env.example .env
```

For local development, the important required values are:

```env
MONGODB_URI=mongodb://localhost:27017/road_safety
MONGODB_DB=road_safety
JWT_SECRET=replace-with-a-long-random-secret
ENVIRONMENT=development
```

Then start the API:

```powershell
venv\Scripts\activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

MongoDB should be running locally before endpoints that use the database will work.
