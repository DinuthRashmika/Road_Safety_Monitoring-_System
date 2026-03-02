import { useState, useEffect, useRef } from "react"
import { useLocation, useNavigate } from "react-router-dom";
import Layout from "../layouts/Layout";
import './../styles/DetectionMonitering.css'

function Detection() {
    const location = useLocation();
    const navigate = useNavigate();

    const videoSource = location.state?.videoSource;
    const videoInfo = location.state?.videoInfo;
    const cameraInfo = location.state?.cameraInfo;
    const isCamera = location.state?.isCamera || false;

    const [videoProcessingInfo, setVideoProcessingInfo] = useState(null);
    const [loading, setLoading] = useState(false);

    const [isConnected, setIsConnected] = useState(false);
    const [lrcnResults, setLrcnResults] = useState([]);
    const [currentAction, setCurrentAction] = useState(null);
    const [processingStatus, setProcessingStatus] = useState("");
    const [statistics, setStatistics] = useState(null);

    // New states for the 4 sections
    const [currentFrame, setCurrentFrame] = useState(null);         // base64 video frame
    const [detectedActionsLog, setDetectedActionsLog] = useState([]); // unique action events
    const [detectedObjectsLog, setDetectedObjectsLog] = useState([]); // unique object events
    const [fusionResult, setFusionResult] = useState(null);          // threat score + level

    const wsRef = useRef(null);

    useEffect(() => {
        if (!videoSource) {
            alert("No video source selected!");
            navigate('/');
        }
    }, [videoSource, navigate]);

    useEffect(() => {
        if (videoSource) {
            startProcessing();
        }
        return () => {
            if (wsRef.current) wsRef.current.close();
        };
    }, []);

    const startProcessing = async () => {
        setLoading(true);
        setLrcnResults([]);
        setCurrentAction(null);
        setDetectedActionsLog([]);
        setDetectedObjectsLog([]);
        setFusionResult(null);
        setProcessingStatus("Starting...");

        try {
            const response = await fetch("http://127.0.0.1:8000/detection/lrcn_start", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ source_path: videoSource }),
            });

            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            const data = await response.json();

            if (data.success) {
                setVideoProcessingInfo(data);
                setProcessingStatus("Connected. Processing video...");
                connectWebSocket(data.websocket_url);
            } else {
                setProcessingStatus("Failed to start detection");
            }
        } catch (error) {
            setProcessingStatus(`Error: ${error.message}`);
            alert(`Error starting detection: ${error.message}`);
        } finally {
            setLoading(false);
        }
    };

    const connectWebSocket = (websocketUrl) => {
        if (wsRef.current) wsRef.current.close();

        try {
            const ws = new WebSocket(websocketUrl);
            wsRef.current = ws;

            ws.onopen = () => {
                setIsConnected(true);
                setProcessingStatus("Connected. Processing...");
            };

            ws.onmessage = (event) => {
                const message = JSON.parse(event.data);

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
                        setIsConnected(false);
                        break;
                    case "error":
                        setProcessingStatus(`Error: ${message.data.message}`);
                        break;
                    default:
                        break;
                }
            };

            ws.onerror = () => {
                setProcessingStatus("WebSocket error occurred");
                setIsConnected(false);
            };

            ws.onclose = (event) => {
                setIsConnected(false);
                if (!event.wasClean) setProcessingStatus("Connection closed unexpectedly");
            };
        } catch (error) {
            setProcessingStatus(`Failed to connect: ${error.message}`);
        }
    };

    const handleLrcnResult = (data) => {
        // Merge detection data
        const mergedData = {
            ...data.lrcn,
            frame_number: data.frame_number,
            timestamp: data.timestamp,
            buffer_progress: data.buffer_progress,
            buffer_size: data.buffer_size,
            yolo_detections: data.yolo?.detections || [],
            total_objects: data.yolo?.total_objects || 0,
        };

        setCurrentAction(mergedData);

        // Update video frame if present
        if (data.frame) {
            setCurrentFrame(`data:image/jpeg;base64,${data.frame}`);
        }

        // Update fusion threat result
        if (data.fusion) {
            setFusionResult(data.fusion);
        }

        setLrcnResults((prev) => [...prev, mergedData].slice(-50));

        // --- Section 3: Unique Action Events Log ---
        if (mergedData.ready && mergedData.is_violent) {
            const action = mergedData.action;
            const timestamp = new Date(mergedData.timestamp).toLocaleTimeString();

            setDetectedActionsLog((prev) => {
                // Only add if this action isn't already in the log
                const alreadyLogged = prev.some((e) => e.action === action);
                if (!alreadyLogged) {
                    return [...prev, { action, timestamp, confidence: mergedData.confidence }];
                }
                return prev;
            });
        }

        // --- Section 3: Unique Object Events Log ---
        if (mergedData.yolo_detections && mergedData.yolo_detections.length > 0) {
            const timestamp = new Date(mergedData.timestamp).toLocaleTimeString();

            mergedData.yolo_detections.forEach((det) => {
                setDetectedObjectsLog((prev) => {
                    const alreadyLogged = prev.some((e) => e.object === det.object);
                    if (!alreadyLogged) {
                        return [...prev, { object: det.object, timestamp, confidence: det.confidence }];
                    }
                    return prev;
                });
            });
        }

        if (mergedData.ready) {
            setProcessingStatus(
                `Frame ${mergedData.frame_number}: ${mergedData.action.toUpperCase()} (${(mergedData.confidence * 100).toFixed(1)}%)`
            );
        } else {
            setProcessingStatus(`Buffering... ${data.buffer_progress}/${data.buffer_size} frames`);
        }
    };

    const stopProcessing = async () => {
        if (!videoProcessingInfo?.session_id) return;

        try {
            await fetch("http://127.0.0.1:8000/detection/lrcn_stop", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ source_path: videoProcessingInfo.session_id }),
            });
        } catch (error) {
            console.error("Error stopping detection:", error);
        } finally {
            if (wsRef.current) {
                wsRef.current.close();
                wsRef.current = null;
            }
            setIsConnected(false);
            setProcessingStatus("Detection stopped by user");
        }
    };

    // Helper: threat level color
    const getThreatColor = (level) => {
        switch (level) {
            case "CRITICAL": return "#ff2d2d";
            case "HIGH":     return "#ff6b00";
            case "MEDIUM":   return "#f5c400";
            case "VERY LOW": return "#4ade80";
            case "NONE":     return "#6b7280";
            default:         return "#6b7280";
        }
    };

    const getThreatBg = (level) => {
        switch (level) {
            case "CRITICAL": return "rgba(255,45,45,0.12)";
            case "HIGH":     return "rgba(255,107,0,0.12)";
            case "MEDIUM":   return "rgba(245,196,0,0.12)";
            case "VERY LOW": return "rgba(74,222,128,0.12)";
            case "NONE":     return "rgba(107,114,128,0.10)";
            default:         return "rgba(107,114,128,0.10)";
        }
    };

    return (
        <Layout>
            <div className="dm-root">

                {/* ── Top bar ── */}
                <div className="dm-topbar">
                    <div className="dm-topbar-left">
                        <span className="dm-title">Violence Detection Monitor</span>
                        <span className={`dm-badge ${isConnected ? "badge-live" : "badge-off"}`}>
                            {isConnected ? "● LIVE" : "○ OFFLINE"}
                        </span>
                    </div>
                    <div className="dm-topbar-right">
                        <span className="dm-src">{videoSource}</span>
                        {videoProcessingInfo && (
                            <button
                                className={`dm-stop-btn ${!isConnected ? "dm-stop-btn--disabled" : ""}`}
                                onClick={stopProcessing}
                                disabled={!isConnected}
                            >
                                {isConnected ? "■ Stop" : "Stopped"}
                            </button>
                        )}
                    </div>
                </div>

                {/* ── Main grid ── */}
                <div className="dm-grid">

                    {/* ══ COL 1: Video feed ══ */}
                    <div className="dm-card dm-video-card">
                        <div className="dm-card-header">
                            <span className="dm-card-title">📹 Video Stream</span>
                            <span className="dm-card-sub">{isCamera ? "Camera" : "File"}</span>
                        </div>
                        <div className="dm-video-box">
                            {currentFrame ? (
                                <img
                                    src={currentFrame}
                                    alt="Live detection feed"
                                    className="dm-video-img"
                                />
                            ) : (
                                <div className="dm-video-placeholder">
                                    <div className="dm-cam-icon">📷</div>
                                    <p>Awaiting stream…</p>
                                    <small>{processingStatus}</small>
                                </div>
                            )}
                        </div>

                        {/* Status strip */}
                        <div className="dm-status-strip">
                            <span>{processingStatus || "Idle"}</span>
                            {videoInfo && (
                                <span>{videoInfo.width}×{videoInfo.height} @ {videoInfo.fps}fps</span>
                            )}
                        </div>
                    </div>

                    {/* ══ COL 2: Current Action + Current Objects ══ */}
                    <div className="dm-col">

                        {/* ── Section 1: Current Action ── */}
                        <div className="dm-card">
                            <div className="dm-card-header">
                                <span className="dm-card-title">⚡ Current Action</span>
                            </div>

                            {currentAction && currentAction.ready ? (
                                <div className={`dm-current-action ${currentAction.is_violent ? "state-violent" : "state-normal"}`}>
                                    <div className="dm-action-name">
                                        {currentAction.action.toUpperCase()}
                                    </div>
                                    <div className="dm-action-meta">
                                        <span>Frame {currentAction.frame_number}</span>
                                        <span className={`dm-violent-tag ${currentAction.is_violent ? "tag-yes" : "tag-no"}`}>
                                            {currentAction.is_violent ? "VIOLENT" : "NORMAL"}
                                        </span>
                                        <span>{(currentAction.confidence * 100).toFixed(1)}% conf</span>
                                    </div>

                                    {/* Probability bars */}
                                    <div className="dm-probs">
                                        {Object.entries(currentAction.all_probabilities).map(([act, prob]) => (
                                            <div key={act} className="dm-prob-row">
                                                <span className="dm-prob-label">{act}</span>
                                                <div className="dm-prob-track">
                                                    <div
                                                        className="dm-prob-fill"
                                                        style={{ width: `${prob * 100}%` }}
                                                    />
                                                </div>
                                                <span className="dm-prob-pct">{(prob * 100).toFixed(0)}%</span>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            ) : (
                                <div className="dm-waiting">
                                    <span className="dm-wait-icon">⏳</span>
                                    <span>{currentAction ? `Buffering ${currentAction.buffer_progress}/${currentAction.buffer_size}` : "Waiting for buffer…"}</span>
                                </div>
                            )}
                        </div>

                        {/* ── Section 2: Current Objects (always visible) ── */}
                        <div className="dm-card">
                            <div className="dm-card-header">
                                <span className="dm-card-title">🔍 Current Objects</span>
                                <span className="dm-card-sub">
                                    {currentAction?.total_objects
                                        ? `${currentAction.total_objects} detected`
                                        : "none this frame"}
                                </span>
                            </div>

                            <div className="dm-objects-body">
                                {currentAction?.yolo_detections && currentAction.yolo_detections.length > 0 ? (
                                    currentAction.yolo_detections.map((det, i) => (
                                        <div key={i} className="dm-obj-row">
                                            <span className="dm-obj-name">{det.object.toUpperCase()}</span>
                                            <div className="dm-obj-track">
                                                <div
                                                    className="dm-obj-fill"
                                                    style={{ width: `${det.confidence * 100}%` }}
                                                />
                                            </div>
                                            <span className="dm-obj-pct">{(det.confidence * 100).toFixed(0)}%</span>
                                        </div>
                                    ))
                                ) : (
                                    <div className="dm-objects-empty">
                                        <span>No violent objects detected this frame</span>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>

                    {/* ══ COL 3: Event Log + Threat Score ══ */}
                    <div className="dm-col">

                        {/* ── Section 3: Detection Event Log ── */}
                        <div className="dm-card dm-log-card">
                            <div className="dm-card-header">
                                <span className="dm-card-title">📋 Detection Log</span>
                                <span className="dm-card-sub">unique events only</span>
                            </div>

                            <div className="dm-log-body">

                                {/* Action events */}
                                <div className="dm-log-group">
                                    <div className="dm-log-group-title">Actions</div>
                                    {detectedActionsLog.length === 0 ? (
                                        <div className="dm-log-empty">No violent actions yet</div>
                                    ) : (
                                        detectedActionsLog.map((evt, i) => (
                                            <div key={i} className="dm-log-entry dm-log-action">
                                                <span className="dm-log-dot" />
                                                <div className="dm-log-content">
                                                    <span className="dm-log-name">
                                                        {evt.action.toUpperCase()} detected
                                                    </span>
                                                    <span className="dm-log-meta">
                                                        {evt.timestamp} · {(evt.confidence * 100).toFixed(0)}% conf
                                                    </span>
                                                </div>
                                            </div>
                                        ))
                                    )}
                                </div>

                                {/* Object events */}
                                <div className="dm-log-group">
                                    <div className="dm-log-group-title">Objects</div>
                                    {detectedObjectsLog.length === 0 ? (
                                        <div className="dm-log-empty">No violent objects yet</div>
                                    ) : (
                                        detectedObjectsLog.map((evt, i) => (
                                            <div key={i} className="dm-log-entry dm-log-object">
                                                <span className="dm-log-dot" />
                                                <div className="dm-log-content">
                                                    <span className="dm-log-name">
                                                        {evt.object.toUpperCase()} detected
                                                    </span>
                                                    <span className="dm-log-meta">
                                                        {evt.timestamp} · {(evt.confidence * 100).toFixed(0)}% conf
                                                    </span>
                                                </div>
                                            </div>
                                        ))
                                    )}
                                </div>
                            </div>
                        </div>

                        {/* ── Section 4: Threat Score (Fusion) ── */}
                        <div
                            className="dm-card dm-threat-card"
                            style={{
                                background: fusionResult ? getThreatBg(fusionResult.weight_level) : undefined,
                                borderColor: fusionResult ? getThreatColor(fusionResult.weight_level) : undefined,
                            }}
                        >
                            <div className="dm-card-header">
                                <span className="dm-card-title">⚠️ Threat Assessment</span>
                                <span className="dm-card-sub">fusion score</span>
                            </div>

                            {fusionResult ? (
                                <div className="dm-threat-body">
                                    {/* Big threat level badge */}
                                    <div
                                        className="dm-threat-level"
                                        style={{ color: getThreatColor(fusionResult.weight_level) }}
                                    >
                                        {fusionResult.weight_level}
                                    </div>

                                    {/* Score bar */}
                                    <div className="dm-threat-score-row">
                                        <span className="dm-threat-score-label">Threat Score</span>
                                        <span
                                            className="dm-threat-score-value"
                                            style={{ color: getThreatColor(fusionResult.weight_level) }}
                                        >
                                            {(fusionResult.threat_score * 100).toFixed(0)}%
                                        </span>
                                    </div>
                                    <div className="dm-threat-track">
                                        <div
                                            className="dm-threat-fill"
                                            style={{
                                                width: `${fusionResult.threat_score * 100}%`,
                                                background: getThreatColor(fusionResult.weight_level),
                                            }}
                                        />
                                    </div>

                                    {/* Breakdown */}
                                    {fusionResult.lrcn_contribution !== undefined && (
                                        <div className="dm-threat-breakdown">
                                            <div className="dm-breakdown-row">
                                                <span>Action (LRCN)</span>
                                                <span>{(fusionResult.lrcn_contribution * 100).toFixed(0)}%</span>
                                            </div>
                                            <div className="dm-breakdown-row">
                                                <span>Objects (YOLO)</span>
                                                <span>{(fusionResult.yolo_contribution * 100).toFixed(0)}%</span>
                                            </div>
                                            {fusionResult.synergy_bonus > 0 && (
                                                <div className="dm-breakdown-row dm-synergy">
                                                    <span>Synergy Bonus</span>
                                                    <span>+{(fusionResult.synergy_bonus * 100).toFixed(0)}%</span>
                                                </div>
                                            )}
                                        </div>
                                    )}
                                </div>
                            ) : (
                                <div className="dm-waiting">
                                    <span className="dm-wait-icon">🛡️</span>
                                    <span>Awaiting fusion data…</span>
                                </div>
                            )}
                        </div>
                    </div>
                </div>

                {loading && (
                    <div className="dm-overlay">
                        <div className="dm-spinner" />
                        <p>Initializing detection session…</p>
                    </div>
                )}
            </div>
        </Layout>
    );
}

export default Detection;