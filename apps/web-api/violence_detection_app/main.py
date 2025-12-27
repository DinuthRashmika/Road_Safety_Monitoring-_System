import uvicorn

if __name__ == "__main__":
    uvicorn.run("violence_detection_app.app.app:app", host="0.0.0.0", port=8000, reload=True)