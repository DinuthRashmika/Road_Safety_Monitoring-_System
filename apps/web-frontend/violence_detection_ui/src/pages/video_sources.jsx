import { useState, useEffect, useRef } from "react"

function VideoSources() {

    const [videoSource, setVideoSource] = useState("");
    const [isValid, setIsValid] = useState(false);
    const [videoInfo, setVideoInfo] = useState(null);

    const [videoProcessingInfo, setVideoProcessingInfo] = useState(null);
    const [loading, setLoading] = useState(false);
    
    // WebSocket states
    const [isConnected, setIsConnected] = useState(false);
    const [lrcnResults, setLrcnResults] = useState([]);
    const [currentAction, setCurrentAction] = useState(null);
    const [processingStatus, setProcessingStatus] = useState("");
    const [statistics, setStatistics] = useState(null);
    
    // store your WebSocket connection
    const wsRef = useRef(null);

    const handleChange = (e) => {
        const value = e.target.value;
        setVideoSource(value);
        setIsValid(value.trim().length > 0);
    };

    const getVideoProperties = async () => {
        setLoading(true);

        try {
            const response = await fetch("http://127.0.0.1:8000/source/properties", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    source_path: videoSource,
                }),
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            setVideoInfo(data);
            console.log("Video properties:", data);
        } catch (error) {
            console.error("Backend error:", error);
            alert(`Error: ${error.message}`);
        } finally {
            setLoading(false);
        }
    };

    const startProcessing = async () => {
        setLoading(true);
        setLrcnResults([]);
        setCurrentAction(null);
        setProcessingStatus("Starting...");

        try {
            const response = await fetch("http://127.0.0.1:8000/detection/lrcn_start", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    source_path: videoSource, 
                }),
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            console.log("Detection started:", data);
            
            if (data.success) {
                setVideoProcessingInfo(data);
                setProcessingStatus("Connected. Processing video...");
                
                // 2. Connect to WebSocket
                connectWebSocket(data.websocket_url);
            } else {
                setProcessingStatus("Failed to start detection");
                console.error("Failed to start detection:", data);
            }
            
        } catch (error) {
            console.error("Backend error:", error);
            setProcessingStatus(`Error: ${error.message}`);
            alert(`Error starting detection: ${error.message}`);
        } finally {
            setLoading(false);
        }
    };

    const connectWebSocket = (websocketUrl) => {
        console.log("🔌 Connecting to WebSocket:", websocketUrl);
        
        // Close existing connection if any
        if (wsRef.current) {
            wsRef.current.close();
        }

        try {
            // Create new WebSocket connection
            const ws = new WebSocket(websocketUrl);
            wsRef.current = ws;

            ws.onopen = () => {
                console.log("✅ WebSocket connected");
                setIsConnected(true);
                setProcessingStatus("Connected. Processing...");
            };

            ws.onmessage = (event) => {
                const message = JSON.parse(event.data);
                console.log("Received:", message);

                switch (message.type) {
                    case "lrcn_result":
                        handleLrcnResult(message.data);
                        break;

                    case "status":
                        setProcessingStatus(message.data.message);
                        break;

                    case "complete":
                        setProcessingStatus("Processing complete!");
                        setStatistics(message.data.statistics);
                        console.log("Complete:", message.data);
                        setIsConnected(false);
                        break;

                    case "error":
                        setProcessingStatus(`Error: ${message.data.message}`);
                        console.error("Error:", message.data);
                        break;

                    default:
                        console.log("Unknown message type:", message.type);
                }
            };

            ws.onerror = (error) => {
                console.error("WebSocket error:", error);
                setProcessingStatus("WebSocket error occurred");
                setIsConnected(false);
            };

            ws.onclose = (event) => {
                console.log("🔌 WebSocket closed", event.code, event.reason);
                setIsConnected(false);
                if (!event.wasClean) {
                    setProcessingStatus("Connection closed unexpectedly");
                }
            };
        } catch (error) {
            console.error("Failed to create WebSocket:", error);
            setProcessingStatus(`Failed to connect: ${error.message}`);
        }
    };

    const handleLrcnResult = (data) => {
        // Update current action (most recent)
        setCurrentAction(data);

        // Add to results history (keep last 50 for performance)
        setLrcnResults((prev) => {
            const newResults = [...prev, data];
            return newResults.slice(-50); // Keep only last 50 results
        });

        // Update status
        if (data.ready) {
            setProcessingStatus(
                `Frame ${data.frame_number}: ${data.action.toUpperCase()} (${(data.confidence * 100).toFixed(1)}%)`
            );
        } else {
            setProcessingStatus(
                `Buffering... ${data.buffer_progress}/${data.buffer_size} frames`
            );
        }
    };

    const stopProcessing = () => {
        if (wsRef.current) {
            console.log("Stopping processing...");
            wsRef.current.close();
            wsRef.current = null;
        }
        setIsConnected(false);
        setProcessingStatus("Stopped by user");
    };

    // Cleanup on unmount
    useEffect(() => {
        return () => {
            if (wsRef.current) {
                wsRef.current.close();
            }
        };
    }, []);

    
    return (
        <div style={{ padding: "20px", maxWidth: "900px", margin: "0 auto" }}>
            <h2>HVD</h2>

            {/* Video Source Input */}
            <div style={{ marginBottom: "20px" }}>
                <label style={{ display: "block", marginBottom: "5px", fontWeight: "bold" }}>
                    Video Source Path:
                </label>
                <input
                    type="text"
                    placeholder="Enter video path (e.g., E:/videos/test.mp4)"
                    value={videoSource}
                    onChange={handleChange}
                    style={{ 
                        width: "100%", 
                        padding: "12px",
                        marginBottom: "10px",
                        fontSize: "14px",
                        border: "2px solid #ddd",
                        borderRadius: "5px"
                    }}
                />

                <div style={{ display: "flex", gap: "10px", flexWrap: "wrap" }}>
                    <button
                        onClick={getVideoProperties}
                        disabled={!isValid || loading}
                        style={{ 
                            padding: "12px 24px",
                            backgroundColor: isValid && !loading ? "#4CAF50" : "#ccc",
                            color: "white",
                            border: "none",
                            borderRadius: "5px",
                            cursor: isValid && !loading ? "pointer" : "not-allowed",
                            fontWeight: "bold"
                        }}
                    >
                        {loading ? "Loading..." : "Get Video Properties"}
                    </button>

                    <button
                        onClick={startProcessing}
                        disabled={!isValid || loading || isConnected}
                        style={{ 
                            padding: "12px 24px",
                            backgroundColor: isValid && !loading && !isConnected ? "#2196F3" : "#ccc",
                            color: "white",
                            border: "none",
                            borderRadius: "5px",
                            cursor: isValid && !loading && !isConnected ? "pointer" : "not-allowed",
                            fontWeight: "bold"
                        }}
                    >
                        {loading ? "Starting..." : "Start Detection"}
                    </button>

                    {isConnected && (
                        <button
                            onClick={stopProcessing}
                            style={{ 
                                padding: "12px 24px",
                                backgroundColor: "#f44336",
                                color: "white",
                                border: "none",
                                borderRadius: "5px",
                                cursor: "pointer",
                                fontWeight: "bold"
                            }}
                        >
                            Stop
                        </button>
                    )}
                </div>
            </div>

            {/* Connection Status */}
            {videoProcessingInfo && (
                <div style={{ 
                    marginTop: "20px",
                    padding: "15px",
                    backgroundColor: isConnected ? "#e8f5e9" : "#fff3e0",
                    borderRadius: "8px",
                    border: `2px solid ${isConnected ? "#4CAF50" : "#ff9800"}`
                }}>
                    <h3>Connection Status</h3>
                    <p><strong>Session ID:</strong> <code>{videoProcessingInfo.session_id}</code></p>
                    <p><strong>Status:</strong> {isConnected ? "🟢 Connected" : "🔴 Disconnected"}</p>
                    <p><strong>Message:</strong> {processingStatus}</p>
                </div>
            )}

            {/* Current Action Display */}
            {currentAction && currentAction.ready && (
                <div style={{ 
                    marginTop: "20px",
                    padding: "20px",
                    // backgroundColor: currentAction.is_violent ? "#ffebee" : "#e8f5e9",
                    borderRadius: "8px",
                    // border: currentAction.is_violent ? "3px solid #f44336" : "3px solid #4CAF50"
                }}>
                    <h3>Current Detection</h3>
                    <div style={{ 
                        fontSize: "25px", 
                        fontWeight: "bold", 
                        marginBottom: "10px",
                        // color: currentAction.is_violent ? "#f44336" : "#4CAF50"
                    }}>
                        {currentAction.is_violent && ""}
                        {currentAction.action.toUpperCase()}
                    </div>
                    <p><strong>Frame:</strong> {currentAction.frame_number}</p>
                    <p><strong>Confidence:</strong> {(currentAction.confidence * 100).toFixed(1)}%</p>
                    <p><strong>Violent:</strong> <strong style={{color: currentAction.is_violent ? "#f44336" : "#4CAF50"}}>
                        {currentAction.is_violent ? "YES" : "NO"}
                    </strong></p>
                    
                    {/* Confidence Bar
                    <div style={{ 
                        width: "100%", 
                        height: "30px", 
                        backgroundColor: "#ddd",
                        borderRadius: "15px",
                        marginTop: "15px",
                        overflow: "hidden",
                        position: "relative"
                    }}>
                        <div style={{
                            width: `${currentAction.confidence * 100}%`,
                            height: "100%",
                            backgroundColor: currentAction.is_violent ? "#f44336" : "#4CAF50",
                            transition: "width 0.3s ease",
                            display: "flex",
                            alignItems: "center",
                            justifyContent: "center",
                            color: "white",
                            fontWeight: "bold"
                        }}>
                            {(currentAction.confidence * 100).toFixed(1)}%
                        </div>
                    </div> */}

                    {/* All Probabilities */}
                    <div style={{ marginTop: "20px", padding: "10px", backgroundColor: "white", borderRadius: "5px" }}>
                        <h4 style={{ marginBottom: "10px" }}>AProbabilities:</h4>
                        {Object.entries(currentAction.all_probabilities).map(([action, prob]) => (
                            <div key={action} style={{ 
                                marginBottom: "8px",
                                display: "flex",
                                justifyContent: "space-between",
                                padding: "5px"
                            }}>
                                <span style={{ fontWeight: "bold", textTransform: "capitalize" }}>
                                    {action}:
                                </span>
                                <span>{(prob * 100).toFixed(1)}%</span>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Video Properties */}
            {videoInfo && (
                <div style={{ 
                    marginTop: "20px",
                    padding: "15px",
                    backgroundColor: "#f5f5f5",
                    borderRadius: "8px",
                    border: "2px solid #ddd"
                }}>
                    <h3>Video Properties</h3>
                    <pre style={{ 
                        overflow: "auto",
                        backgroundColor: "white",
                        padding: "15px",
                        borderRadius: "5px",
                        fontSize: "12px"
                    }}>
                        {JSON.stringify(videoInfo, null, 2)}
                    </pre>
                </div>
            )}

            {/* Statistics (when complete) */}
            {statistics && (
                <div style={{ 
                    marginTop: "20px",
                    padding: "15px",
                    backgroundColor: "#e3f2fd",
                    borderRadius: "8px",
                    border: "2px solid #2196F3"
                }}>
                    <h3>Stats</h3>
                    <pre style={{ 
                        overflow: "auto",
                        backgroundColor: "white",
                        padding: "15px",
                        borderRadius: "5px",
                        fontSize: "12px"
                    }}>
                        {JSON.stringify(statistics, null, 2)}
                    </pre>
                </div>
            )}

            {/* Recent Results History */}
            {lrcnResults.length > 0 && (
                <div style={{ 
                    marginTop: "20px",
                    padding: "15px",
                    backgroundColor: "#f5f5f5",
                    borderRadius: "8px",
                    maxHeight: "400px",
                    overflow: "auto",
                    border: "2px solid #ddd"
                }}>
                    <h3>Recent Detections ({lrcnResults.filter(r => r.ready).length})</h3>
                    {/* {lrcnResults.slice().reverse().slice(0, 10).map((result, index) => (
                        result.ready && (
                            <div 
                                key={index}
                                style={{ 
                                    padding: "10px",
                                    marginBottom: "8px",
                                    backgroundColor: result.is_violent ? "#ffebee" : "white",
                                    borderRadius: "5px",
                                    fontSize: "13px",
                                    border: result.is_violent ? "1px solid #f44336" : "1px solid #ddd"
                                }}
                            >
                                <strong>Frame {result.frame_number}:</strong> {result.action.toUpperCase()} 
                                ({(result.confidence * 100).toFixed(1)}%)
                                {result.is_violent && " "}
                                <div style={{ fontSize: "11px", color: "#666", marginTop: "3px" }}>
                                    {new Date(result.timestamp).toLocaleTimeString()}
                                </div>
                            </div>
                        )
                    ))} */}
                </div>
            )}
        </div>
    )
}

export default VideoSources;
