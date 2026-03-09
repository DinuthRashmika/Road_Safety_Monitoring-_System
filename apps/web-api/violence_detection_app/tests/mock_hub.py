from fastapi import FastAPI, Request
import uvicorn
import json

app = FastAPI()

@app.post("/api/alerts")
async def receive_alert(request: Request):
    payload = await request.json()
    print("\n" + "="*60)
    print("ALERT RECEIVED FROM VIOLENCE DETECTION SYSTEM")
    print("="*60)
    print(json.dumps(payload, indent=2))
    print("="*60 + "\n")
    return {"success": True, "message": "Alert received"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9000)

# if an alert is sent to hub, mock server terminal will display alert payload