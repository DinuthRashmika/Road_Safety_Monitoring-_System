->fast API for web application

->websocket API test
// Replace with your websocket URL from /lrcn_start
const ws = new WebSocket("ws://localhost:8000/ws/detection/session_abc123");

// Event: connection opened
ws.onopen = () => {
  console.log("✅ WebSocket connected");
};

// Event: receiving messages
ws.onmessage = (event) => {
  console.log("📨 Received:", JSON.parse(event.data));
};

// Event: error
ws.onerror = (err) => {
  console.error("❌ WebSocket error", err);
};

// Event: closed
ws.onclose = () => {
  console.log("🔌 WebSocket closed");
};
