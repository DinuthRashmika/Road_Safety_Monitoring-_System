import { useState, useEffect, useRef } from "react"
import { useLocation, useNavigate } from "react-router-dom";
import Layout from "../layouts/Layout";
import './../styles/DetectionMonitering.css'

function Detection() {
    const location = useLocation();
    const navigate = useNavigate();
    
    // Get video source from navigation state
    const videoSource = location.state?.videoSource;
    const videoInfo = location.state?.videoInfo;
    const cameraInfo = location.state?.cameraInfo;
    const isCamera = location.state?.isCamera || false;

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

    // Redirect if no video source
    useEffect(() => {
        if (!videoSource) {
            alert("No video source selected!");
            navigate('/');
        }
    }, [videoSource, navigate]);

    // Auto-start detection when component mounts
    useEffect(() => {
        if (videoSource) {
            startProcessing();
        }
        
        // Cleanup on unmount
        return () => {
            if (wsRef.current) {
                wsRef.current.close();
            }
        };
    }, []); // Empty dependency to run once on mount

    // Send sourceurl and receive sessionId and websocket_url
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
                
                // Connect to WebSocket
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
                console.log("WebSocket connected");
                setIsConnected(true);
                setProcessingStatus("Connected. Processing...");
            };

            ws.onmessage = (event) => {
                const message = JSON.parse(event.data);
                console.log("Received:", message);

                switch (message.type) {
                    case "lrcn_result":
                        handleLrcnResult(message.data.lrcn);
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
            return newResults.slice(-50);
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

    const handleBackToSources = () => {
        if (isConnected) {
            const confirm = window.confirm("Detection is in progress. Are you sure you want to go back?");
            if (!confirm) return;
            stopProcessing();
        }
        navigate('/');
    };

    return (
        <Layout>
            <div className="detection-container">
                {/* Header with back button */}
                {/* <div className="detection-header">
                    <button className="btn-grey" onClick={handleBackToSources}>
                        ← Back to Sources
                    </button>
                    <h2>Real-Time Detection Monitor</h2>
                    {isConnected && (
                        <button className="btn-dark" onClick={stopProcessing}>
                            Stop Detection
                        </button>
                    )}
                </div> */}

                {/* Grid Layout: Left column (video + stats) and Right column (results) */}
                <div className="detection-grid">
                    
                    {/* LEFT COLUMN */}
                    <div className="left-column">
                        
                        {/* REC1: Video Player */}
                        <div className="video-section">
                            <h3>Video Stream</h3>
                            <div className="video-placeholder">
                                <div className="video-icon">📹</div>
                                <p>Video stream will display here</p>
                                <small>{isCamera ? "Camera Feed" : "Video File"}</small>
                            </div>
                        </div>

                        {/* REC2: Connection Status & Stats */}
                        <div className="stats-section">
                            <h3>Connection Status</h3>
                            
                            <div className="stat-row">
                                <span className="stat-label">Status:</span>
                                <span className={`stat-value ${isConnected ? 'status-connected' : 'status-disconnected'}`}>
                                    {isConnected ? "🟢 Connected" : "⚫ Disconnected"}
                                </span>
                            </div>

                            {videoProcessingInfo && (
                                <div className="stat-row">
                                    <span className="stat-label">Session ID:</span>
                                    <span className="stat-value">{videoProcessingInfo.session_id}</span>
                                </div>
                            )}

                            <div className="stat-row">
                                <span className="stat-label">Source:</span>
                                <span className="stat-value source-path">{videoSource}</span>
                            </div>

                            {videoInfo && (
                                <>
                                    <div className="stat-row">
                                        <span className="stat-label">FPS:</span>
                                        <span className="stat-value">{videoInfo.fps}</span>
                                    </div>

                                    <div className="stat-row">
                                        <span className="stat-label">Resolution:</span>
                                        <span className="stat-value">{videoInfo.width} × {videoInfo.height}</span>
                                    </div>
                                </>
                            )}

                            <div className="stat-row">
                                <span className="stat-label">Message:</span>
                                <span className="stat-value">{processingStatus || 'Waiting...'}</span>
                            </div>
                        </div>
                    </div>

                    {/* RIGHT COLUMN - REC3: Detection Results */}
                    <div className="right-column">
                        
                        {/* Current Detection */}
                        {currentAction && currentAction.ready ? (
                            <div className="detection-results">
                                <h3>Current Detection</h3>
                                
                                <div className={`current-detection ${currentAction.is_violent ? 'violent' : 'normal'}`}>
                                    <div className="detection-action">
                                        {currentAction.action.toUpperCase()}
                                    </div>

                                    <div className="detection-meta">
                                        <div className="meta-item">
                                            <span className="meta-label">Frame:</span>
                                            <span className="meta-value">{currentAction.frame_number}</span>
                                        </div>
                                        <div className="meta-item">
                                            <span className="meta-label">Confidence:</span>
                                            <span className="meta-value">{(currentAction.confidence * 100).toFixed(1)}%</span>
                                        </div>
                                        <div className="meta-item">
                                            <span className="meta-label">Violent:</span>
                                            <span className={`meta-value ${currentAction.is_violent ? 'violent-yes' : 'violent-no'}`}>
                                                {currentAction.is_violent ? "YES ⚠️" : "NO"}
                                            </span>
                                        </div>
                                    </div>

                                    {/* Probabilities */}
                                    <div className="probabilities">
                                        <h4>Action Probabilities</h4>
                                        {Object.entries(currentAction.all_probabilities).map(([action, prob]) => (
                                            <div key={action} className="prob-item">
                                                <div className="prob-header">
                                                    <span className="prob-name">{action}</span>
                                                    <span className="prob-percent">{(prob * 100).toFixed(1)}%</span>
                                                </div>
                                                <div className="prob-bar-container">
                                                    <div 
                                                        className="prob-bar-fill" 
                                                        style={{ width: `${prob * 100}%` }}
                                                    ></div>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>

                                {/* Statistics when complete */}
                                {statistics && (
                                    <div className="statistics">
                                        <h4>Processing Statistics</h4>
                                        <pre>{JSON.stringify(statistics, null, 2)}</pre>
                                    </div>
                                )}

                                {/* Recent History */}
                                {lrcnResults.length > 0 && (
                                    <div className="detection-history">
                                        <h4>Recent Detections ({lrcnResults.filter(r => r.ready).length})</h4>
                                        <div className="history-items">
                                            {lrcnResults.slice().reverse().slice(0, 8).map((result, index) => (
                                                result.ready && (
                                                    <div 
                                                        key={index}
                                                        className={`history-entry ${result.is_violent ? 'violent' : 'normal'}`}
                                                    >
                                                        <span className="history-frame">Frame {result.frame_number}</span>
                                                        <span className="history-action">{result.action.toUpperCase()}</span>
                                                        <span className="history-conf">{(result.confidence * 100).toFixed(1)}%</span>
                                                        {result.is_violent && <span className="history-warning">⚠️</span>}
                                                    </div>
                                                )
                                            ))}
                                        </div>
                                    </div>
                                )}
                            </div>
                        ) : (
                            <div className="detection-waiting">
                                <div className="waiting-icon">⏳</div>
                                <h3>Waiting for Detection Results</h3>
                                <p>{processingStatus || 'Initializing...'}</p>
                            </div>
                        )}
                    </div>
                </div>

                {/* Loading State */}
                {loading && (
                    <div className="loading-overlay">
                        <div className="loading-spinner"></div>
                        <p>Initializing detection...</p>
                    </div>
                )}
            </div>
        </Layout>
    )
}

export default Detection;