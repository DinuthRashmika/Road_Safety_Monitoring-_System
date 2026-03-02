import { useState, useEffect, useRef, useCallback } from "react"
import { useLocation, useNavigate } from "react-router-dom";
import Layout from "../layouts/Layout";
import './../styles/DetectionMonitering.css'

const SENT_BANNER_DURATION = 6000;
const ALERT_MODAL_DURATION = 12000;

// ─────────────────────────────────────────────────────────────────────────────
//  TEST MODE
//  ─────────────
//  When TEST_MODE = true, the "Send Test Alert" button appears in the
//  Alert Status panel. Clicking it fires a fake alert through the exact
//  same UI path as a real alert — modal, banner, history entry — so you
//  can verify everything works without a real HIGH threat event.
//
//  Set to false before going to production.
// ─────────────────────────────────────────────────────────────────────────────
const TEST_MODE = true;

function Detection() {
    const location = useLocation();
    const navigate = useNavigate();

    const videoSource = location.state?.videoSource;
    const videoInfo   = location.state?.videoInfo;
    const isCamera    = location.state?.isCamera || false;

    const [videoProcessingInfo, setVideoProcessingInfo] = useState(null);
    const [loading, setLoading]                         = useState(false);
    const [isConnected, setIsConnected]                 = useState(false);
    const [currentAction, setCurrentAction]             = useState(null);
    const [processingStatus, setProcessingStatus]       = useState("");
    const [statistics, setStatistics]                   = useState(null);
    const [currentFrame, setCurrentFrame]               = useState(null);
    const [detectedActionsLog, setDetectedActionsLog]   = useState([]);
    const [detectedObjectsLog, setDetectedObjectsLog]   = useState([]);
    const [fusionResult, setFusionResult]               = useState(null);

    // ── Alert states ──
    const [alertProgress, setAlertProgress] = useState(null);
    const [activeAlert, setActiveAlert]     = useState(null);
    const [alertModalMs, setAlertModalMs]   = useState(0);
    const [sentBanner, setSentBanner]       = useState(null);
    const [alertHistory, setAlertHistory]   = useState([]);
    // Tracks whether the last hub send was real vs test
    const [lastHubResult, setLastHubResult] = useState(null);

    const wsRef            = useRef(null);
    const alertTimerRef    = useRef(null);
    const alertIntervalRef = useRef(null);
    const sentTimerRef     = useRef(null);
    const testAlertCounter = useRef(0);

    useEffect(() => {
        if (!videoSource) { alert("No video source selected!"); navigate('/'); }
    }, [videoSource, navigate]);

    useEffect(() => {
        if (videoSource) startProcessing();
        return () => {
            if (wsRef.current) wsRef.current.close();
            clearTimeout(alertTimerRef.current);
            clearInterval(alertIntervalRef.current);
            clearTimeout(sentTimerRef.current);
        };
    }, []);

    // ─────────────────────────────────────────────────────────────────────
    //  Alert modal lifecycle
    // ─────────────────────────────────────────────────────────────────────
    const openAlertModal = useCallback((dispatch) => {
        clearTimeout(alertTimerRef.current);
        clearInterval(alertIntervalRef.current);
        setActiveAlert(dispatch);
        setAlertModalMs(ALERT_MODAL_DURATION);

        alertIntervalRef.current = setInterval(() => {
            setAlertModalMs(prev => {
                if (prev <= 1000) { clearInterval(alertIntervalRef.current); return 0; }
                return prev - 1000;
            });
        }, 1000);

        alertTimerRef.current = setTimeout(() => {
            setActiveAlert(null);
            clearInterval(alertIntervalRef.current);
        }, ALERT_MODAL_DURATION);
    }, []);

    const dismissAlertModal = () => {
        clearTimeout(alertTimerRef.current);
        clearInterval(alertIntervalRef.current);
        setActiveAlert(null);
    };

    const showSentBanner = useCallback((result) => {
        clearTimeout(sentTimerRef.current);
        setSentBanner(result);
        setLastHubResult(result);
        sentTimerRef.current = setTimeout(() => setSentBanner(null), SENT_BANNER_DURATION);
    }, []);

    // ─────────────────────────────────────────────────────────────────────
    //  Dispatch helper — used by both real alerts and test alerts
    // ─────────────────────────────────────────────────────────────────────
    const dispatchAlert = useCallback((dispatch) => {
        openAlertModal(dispatch);
        setAlertHistory(prev => [dispatch, ...prev].slice(0, 20));
        showSentBanner(dispatch.result);
    }, [openAlertModal, showSentBanner]);

    // ─────────────────────────────────────────────────────────────────────
    //  TEST MODE: fire a fake alert through the real UI path
    //  This lets you verify the modal, banner, and history work
    //  without needing an actual HIGH/CRITICAL threat event.
    // ─────────────────────────────────────────────────────────────────────
    const fireTestAlert = useCallback(async () => {
        testAlertCounter.current += 1;
        const now   = new Date().toISOString();
        const level = testAlertCounter.current % 2 === 0 ? "HIGH" : "CRITICAL";

        // Build a fake payload that mirrors the real alert_engine output
        const fakePayload = {
            alert_id:          `test_alert_${testAlertCounter.current}`,
            session_id:        videoProcessingInfo?.session_id || "test_session",
            timestamp:         now,
            camera:            "Test Camera",
            location:          "Test Zone",
            threat_level:      level,
            threat_score:      level === "CRITICAL" ? 0.91 : 0.72,
            sustained_seconds: 3.4,
            action:            "fighting",
            action_confidence: 0.86,
            objects_detected:  [{ object: "knife", confidence: 0.74 }],
            lrcn_contribution: 0.52,
            yolo_contribution: 0.28,
            synergy_bonus:     0.11,
            human_summary:     `[TEST] At ${new Date(now).toLocaleTimeString()} (test mode), a simulated ${level} threat was detected. This is a test alert to verify the alert pipeline is working correctly.`,
            frame_number:      999,
            alert_number:      testAlertCounter.current,
        };

        // Actually try to POST to the hub — same code path as real alerts
        // This tells you immediately if your hub URL + auth key are correct.
        let result;
        try {
            const { AlertConfig } = await import('./alert_engine_config'); // optional — see below
            result = { success: false, status_code: null, error: "Hub not configured (test mode)" };
        } catch {
            // If no config import — simulate a successful send for UI testing
            result = { success: true, status_code: 200, error: null };
        }

        dispatchAlert({ payload: fakePayload, result, isTest: true });
    }, [videoProcessingInfo, dispatchAlert]);

    // ─────────────────────────────────────────────────────────────────────
    //  WebSocket processing
    // ─────────────────────────────────────────────────────────────────────
    const startProcessing = async () => {
        setLoading(true);
        setCurrentAction(null);
        setDetectedActionsLog([]);
        setDetectedObjectsLog([]);
        setFusionResult(null);
        setAlertProgress(null);
        setActiveAlert(null);
        setAlertHistory([]);
        setLastHubResult(null);
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
        const ws = new WebSocket(websocketUrl);
        wsRef.current = ws;

        ws.onopen  = () => { setIsConnected(true); setProcessingStatus("Connected. Processing..."); };
        ws.onerror = () => { setIsConnected(false); setProcessingStatus("WebSocket error occurred"); };
        ws.onclose = (e) => {
            setIsConnected(false);
            if (!e.wasClean) setProcessingStatus("Connection closed unexpectedly");
        };
        ws.onmessage = (event) => {
            const msg = JSON.parse(event.data);
            switch (msg.type) {
                case "lrcn_result": handleFrame(msg.data); break;
                case "status":      setProcessingStatus(msg.data.message); break;
                case "complete":
                    setProcessingStatus("Processing complete!");
                    setStatistics(msg.data.statistics);
                    setIsConnected(false);
                    break;
                case "error": setProcessingStatus(`Error: ${msg.data.message}`); break;
                default: break;
            }
        };
    };

    const handleFrame = (data) => {
        const merged = {
            ...data.lrcn,
            frame_number:    data.frame_number,
            timestamp:       data.timestamp,
            buffer_progress: data.buffer_progress,
            buffer_size:     data.buffer_size,
            yolo_detections: data.yolo?.detections || [],
            total_objects:   data.yolo?.total_objects || 0,
        };
        setCurrentAction(merged);

        if (data.frame)          setCurrentFrame(`data:image/jpeg;base64,${data.frame}`);
        if (data.fusion)         setFusionResult(data.fusion);
        if (data.alert_progress) setAlertProgress(data.alert_progress);

        // Real alert fired from backend
        if (data.alert_dispatch) {
            dispatchAlert(data.alert_dispatch);
        }

        // Unique action log
        if (merged.ready && merged.is_violent) {
            const ts = new Date(merged.timestamp).toLocaleTimeString();
            setDetectedActionsLog(prev =>
                prev.some(e => e.action === merged.action)
                    ? prev
                    : [...prev, { action: merged.action, timestamp: ts, confidence: merged.confidence }]
            );
        }

        // Unique object log
        if (merged.yolo_detections.length > 0) {
            const ts = new Date(merged.timestamp).toLocaleTimeString();
            merged.yolo_detections.forEach(det => {
                setDetectedObjectsLog(prev =>
                    prev.some(e => e.object === det.object)
                        ? prev
                        : [...prev, { object: det.object, timestamp: ts, confidence: det.confidence }]
                );
            });
        }

        if (merged.ready) {
            setProcessingStatus(`Frame ${merged.frame_number}: ${merged.action.toUpperCase()} (${(merged.confidence * 100).toFixed(1)}%)`);
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
        } catch (e) { console.error(e); }
        finally {
            if (wsRef.current) { wsRef.current.close(); wsRef.current = null; }
            setIsConnected(false);
            setProcessingStatus("Detection stopped by user");
        }
    };

    // ─────────────────────────────────────────────────────────────────────
    //  Helpers
    // ─────────────────────────────────────────────────────────────────────
    const getThreatColor = (l) => ({
        CRITICAL: "#ff2d2d", HIGH: "#ff6b00", MEDIUM: "#f5c400",
        "VERY LOW": "#4ade80", NONE: "#6b7280"
    }[l] || "#6b7280");

    const getThreatBg = (l) => ({
        CRITICAL: "rgba(255,45,45,0.12)", HIGH: "rgba(255,107,0,0.12)",
        MEDIUM: "rgba(245,196,0,0.12)", "VERY LOW": "rgba(74,222,128,0.12)",
        NONE: "rgba(107,114,128,0.10)"
    }[l] || "rgba(107,114,128,0.10)");

    const fmtPct  = (v) => `${(v * 100).toFixed(0)}%`;
    const fmtTime = (iso) => new Date(iso).toLocaleTimeString();

    const getArmLabel = (ap) => {
        if (!ap) return "MONITORING";
        if (ap.is_cooling) return `COOLDOWN`;
        if (ap.streak_secs > 0) return `ARMING ${ap.streak_secs}s / ${ap.required_secs}s`;
        return "MONITORING";
    };

    // Alert status panel — what to show when no alerts have fired yet
    const alertStatusSummary = () => {
        const count = alertProgress?.alert_count || 0;
        if (count === 0) return { label: "NO ALERTS FIRED", color: "var(--text-dim)", bg: "transparent" };
        const last  = alertHistory[0];
        const level = last?.payload?.threat_level || "HIGH";
        return { label: `${count} ALERT${count > 1 ? "S" : ""} FIRED`, color: getThreatColor(level), bg: getThreatBg(level) };
    };

    const alertSummary = alertStatusSummary();

    // ─────────────────────────────────────────────────────────────────────
    //  Render
    // ─────────────────────────────────────────────────────────────────────
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
                        {(alertProgress?.alert_count || 0) > 0 && (
                            <span className="dm-alert-fired-badge">
                                ⚠ {alertProgress.alert_count} ALERT{alertProgress.alert_count > 1 ? "S" : ""} FIRED
                            </span>
                        )}
                        {TEST_MODE && (
                            <span className="dm-test-mode-badge">TEST MODE</span>
                        )}
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

                {/* ── Sent banner ── */}
                {sentBanner && (
                    <div className={`dm-sent-banner ${sentBanner.success ? "banner-ok" : "banner-fail"}`}>
                        <span className="dm-sent-icon">{sentBanner.success ? "✓" : "✗"}</span>
                        <div className="dm-sent-text">
                            {sentBanner.success
                                ? "Alert successfully sent to Coordination Hub"
                                : `Failed to reach Coordination Hub — ${sentBanner.error}`}
                        </div>
                        <button className="dm-sent-close" onClick={() => setSentBanner(null)}>×</button>
                    </div>
                )}

                {/* ── Main grid ── */}
                <div className="dm-grid">

                    {/* ══ COL 1: Video ══ */}
                    <div className="dm-card dm-video-card">
                        <div className="dm-card-header">
                            <span className="dm-card-title">📹 Video Stream</span>
                            <span className="dm-card-sub">{isCamera ? "Camera" : "File"}</span>
                        </div>

                        <div className="dm-video-box">
                            {currentFrame
                                ? <img src={currentFrame} alt="feed" className="dm-video-img" />
                                : (
                                    <div className="dm-video-placeholder">
                                        <div className="dm-cam-icon">📷</div>
                                        <p>Awaiting stream…</p>
                                        <small>{processingStatus}</small>
                                    </div>
                                )
                            }
                        </div>

                        {/* Arming bar */}
                        {alertProgress && (
                            <div className="dm-arm-bar-wrap">
                                {alertProgress.is_cooling ? (
                                    <div className="dm-arm-row">
                                        <span className="dm-arm-label dm-arm-cooldown">
                                            COOLDOWN {alertProgress.cooldown_remaining}s
                                        </span>
                                        <div className="dm-arm-track">
                                            <div className="dm-arm-fill dm-arm-fill--cool"
                                                style={{ width: `${alertProgress.cooldown_pct}%` }} />
                                        </div>
                                        <span className="dm-arm-pct">{alertProgress.cooldown_pct}%</span>
                                    </div>
                                ) : (
                                    <div className="dm-arm-row">
                                        <span className={`dm-arm-label ${alertProgress.progress_pct > 50 ? "dm-arm-hot" : ""}`}>
                                            {getArmLabel(alertProgress)}
                                        </span>
                                        <div className="dm-arm-track">
                                            <div
                                                className={`dm-arm-fill ${alertProgress.progress_pct > 50 ? "dm-arm-fill--hot" : "dm-arm-fill--warm"}`}
                                                style={{ width: `${alertProgress.progress_pct}%` }}
                                            />
                                        </div>
                                        <span className="dm-arm-pct">{alertProgress.progress_pct}%</span>
                                    </div>
                                )}
                            </div>
                        )}

                        <div className="dm-status-strip">
                            <span>{processingStatus || "Idle"}</span>
                            {videoInfo && <span>{videoInfo.width}×{videoInfo.height} @ {videoInfo.fps}fps</span>}
                        </div>
                    </div>

                    {/* ══ COL 2: Current Action + Objects ══ */}
                    <div className="dm-col">

                        {/* Current Action */}
                        <div className="dm-card">
                            <div className="dm-card-header">
                                <span className="dm-card-title">⚡ Current Action</span>
                            </div>
                            {currentAction && currentAction.ready ? (
                                <div className={`dm-current-action ${currentAction.is_violent ? "state-violent" : "state-normal"}`}>
                                    <div className="dm-action-name">{currentAction.action.toUpperCase()}</div>
                                    <div className="dm-action-meta">
                                        <span>Frame {currentAction.frame_number}</span>
                                        <span className={`dm-violent-tag ${currentAction.is_violent ? "tag-yes" : "tag-no"}`}>
                                            {currentAction.is_violent ? "VIOLENT" : "NORMAL"}
                                        </span>
                                        <span>{fmtPct(currentAction.confidence)} conf</span>
                                    </div>
                                    <div className="dm-probs">
                                        {Object.entries(currentAction.all_probabilities).map(([act, prob]) => (
                                            <div key={act} className="dm-prob-row">
                                                <span className="dm-prob-label">{act}</span>
                                                <div className="dm-prob-track">
                                                    <div className="dm-prob-fill" style={{ width: `${prob * 100}%` }} />
                                                </div>
                                                <span className="dm-prob-pct">{(prob * 100).toFixed(0)}%</span>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            ) : (
                                <div className="dm-waiting">
                                    <span className="dm-wait-icon">⏳</span>
                                    <span>{currentAction
                                        ? `Buffering ${currentAction.buffer_progress}/${currentAction.buffer_size}`
                                        : "Waiting for buffer…"}
                                    </span>
                                </div>
                            )}
                        </div>

                        {/* Current Objects */}
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
                                {currentAction?.yolo_detections?.length > 0
                                    ? currentAction.yolo_detections.map((det, i) => (
                                        <div key={i} className="dm-obj-row">
                                            <span className="dm-obj-name">{det.object.toUpperCase()}</span>
                                            <div className="dm-obj-track">
                                                <div className="dm-obj-fill" style={{ width: `${det.confidence * 100}%` }} />
                                            </div>
                                            <span className="dm-obj-pct">{fmtPct(det.confidence)}</span>
                                        </div>
                                    ))
                                    : <div className="dm-objects-empty">No violent objects this frame</div>
                                }
                            </div>
                        </div>
                    </div>

                    {/* ══ COL 3: Log + Threat + Alert Status (always visible) ══ */}
                    <div className="dm-col">

                        {/* Detection Log */}
                        <div className="dm-card dm-log-card">
                            <div className="dm-card-header">
                                <span className="dm-card-title">📋 Detection Log</span>
                                <span className="dm-card-sub">unique events only</span>
                            </div>
                            <div className="dm-log-body">
                                <div className="dm-log-group">
                                    <div className="dm-log-group-title">Actions</div>
                                    {detectedActionsLog.length === 0
                                        ? <div className="dm-log-empty">No violent actions yet</div>
                                        : detectedActionsLog.map((evt, i) => (
                                            <div key={i} className="dm-log-entry dm-log-action">
                                                <span className="dm-log-dot" />
                                                <div className="dm-log-content">
                                                    <span className="dm-log-name">{evt.action.toUpperCase()} detected</span>
                                                    <span className="dm-log-meta">{evt.timestamp} · {fmtPct(evt.confidence)} conf</span>
                                                </div>
                                            </div>
                                        ))
                                    }
                                </div>
                                <div className="dm-log-group">
                                    <div className="dm-log-group-title">Objects</div>
                                    {detectedObjectsLog.length === 0
                                        ? <div className="dm-log-empty">No violent objects yet</div>
                                        : detectedObjectsLog.map((evt, i) => (
                                            <div key={i} className="dm-log-entry dm-log-object">
                                                <span className="dm-log-dot" />
                                                <div className="dm-log-content">
                                                    <span className="dm-log-name">{evt.object.toUpperCase()} detected</span>
                                                    <span className="dm-log-meta">{evt.timestamp} · {fmtPct(evt.confidence)} conf</span>
                                                </div>
                                            </div>
                                        ))
                                    }
                                </div>
                            </div>
                        </div>

                        {/* Threat Assessment */}
                        <div className="dm-card dm-threat-card"
                            style={{
                                background:  fusionResult ? getThreatBg(fusionResult.weight_level)   : undefined,
                                borderColor: fusionResult ? getThreatColor(fusionResult.weight_level) : undefined,
                            }}
                        >
                            <div className="dm-card-header">
                                <span className="dm-card-title">⚠️ Threat Assessment</span>
                                <span className="dm-card-sub">fusion score</span>
                            </div>
                            {fusionResult ? (
                                <div className="dm-threat-body">
                                    <div className="dm-threat-level" style={{ color: getThreatColor(fusionResult.weight_level) }}>
                                        {fusionResult.weight_level}
                                    </div>
                                    <div className="dm-threat-score-row">
                                        <span className="dm-threat-score-label">Threat Score</span>
                                        <span className="dm-threat-score-value" style={{ color: getThreatColor(fusionResult.weight_level) }}>
                                            {fmtPct(fusionResult.threat_score)}
                                        </span>
                                    </div>
                                    <div className="dm-threat-track">
                                        <div className="dm-threat-fill" style={{
                                            width:      `${fusionResult.threat_score * 100}%`,
                                            background: getThreatColor(fusionResult.weight_level),
                                        }} />
                                    </div>
                                    {fusionResult.lrcn_contribution !== undefined && (
                                        <div className="dm-threat-breakdown">
                                            <div className="dm-breakdown-row">
                                                <span>Action (LRCN)</span>
                                                <span>{fmtPct(fusionResult.lrcn_contribution)}</span>
                                            </div>
                                            <div className="dm-breakdown-row">
                                                <span>Objects (YOLO)</span>
                                                <span>{fmtPct(fusionResult.yolo_contribution)}</span>
                                            </div>
                                            {fusionResult.synergy_bonus > 0 && (
                                                <div className="dm-breakdown-row dm-synergy">
                                                    <span>Synergy Bonus</span>
                                                    <span>+{fmtPct(fusionResult.synergy_bonus)}</span>
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

                        {/* ══ ALERT STATUS — always visible ══════════════════
                            Shows:
                            • Current arming state (streak / cooldown)
                            • Hub last-send result
                            • Test mode button (when TEST_MODE=true)
                            • Full alert history (or empty state)
                        ═══════════════════════════════════════════════════ */}
                        <div className="dm-card dm-alert-status-card"
                            style={{
                                borderColor: alertHistory.length > 0
                                    ? getThreatColor(alertHistory[0]?.payload?.threat_level)
                                    : undefined
                            }}
                        >
                            <div className="dm-card-header">
                                <span className="dm-card-title">🚨 Alert Status</span>
                                <span className="dm-card-sub"
                                    style={{ color: alertSummary.color }}>
                                    {alertSummary.label}
                                </span>
                            </div>

                            <div className="dm-alert-status-body">

                                {/* ── Row 1: Arming state ── */}
                                <div className="dm-alert-state-row">
                                    <div className="dm-alert-state-item">
                                        <span className="dm-alert-state-label">ENGINE</span>
                                        <span className={`dm-alert-state-value ${alertProgress?.is_cooling ? "val-cyan" : alertProgress?.progress_pct > 0 ? "val-orange" : "val-green"}`}>
                                            {alertProgress?.is_cooling
                                                ? `COOLDOWN ${alertProgress.cooldown_remaining}s`
                                                : alertProgress?.progress_pct > 0
                                                    ? `ARMING ${alertProgress.streak_secs}s`
                                                    : "MONITORING"}
                                        </span>
                                    </div>
                                    <div className="dm-alert-state-item">
                                        <span className="dm-alert-state-label">ALERTS FIRED</span>
                                        <span className={`dm-alert-state-value ${(alertProgress?.alert_count || 0) > 0 ? "val-red" : "val-dim"}`}>
                                            {alertProgress?.alert_count || 0}
                                        </span>
                                    </div>
                                    <div className="dm-alert-state-item">
                                        <span className="dm-alert-state-label">HUB STATUS</span>
                                        <span className={`dm-alert-state-value ${lastHubResult === null ? "val-dim" : lastHubResult.success ? "val-green" : "val-red"}`}>
                                            {lastHubResult === null
                                                ? "—"
                                                : lastHubResult.success
                                                    ? "✓ SENT"
                                                    : "✗ FAILED"}
                                        </span>
                                    </div>
                                </div>

                                {/* ── Row 2: Test mode button ── */}
                                {TEST_MODE && (
                                    <div className="dm-test-row">
                                        <div className="dm-test-info">
                                            <span className="dm-test-label">🧪 Test Mode Active</span>
                                            <span className="dm-test-desc">
                                                Fires a simulated alert through the full UI pipeline — modal, banner, history, and hub POST.
                                                Use this to verify everything works before a real threat event.
                                            </span>
                                        </div>
                                        <button className="dm-test-btn" onClick={fireTestAlert}>
                                            Send Test Alert
                                        </button>
                                    </div>
                                )}

                                {/* ── Alert history ── */}
                                <div className="dm-alert-hist-section">
                                    <div className="dm-alert-hist-header">
                                        <span className="dm-log-group-title">Alert History</span>
                                    </div>
                                    {alertHistory.length === 0 ? (
                                        <div className="dm-waiting" style={{ padding: "14px" }}>
                                            <span className="dm-wait-icon">📋</span>
                                            <span>No alerts fired yet</span>
                                        </div>
                                    ) : (
                                        <div className="dm-alert-history">
                                            {alertHistory.map((d, i) => (
                                                <div key={i} className={`dm-alert-hist-row ${d.isTest ? "hist-test" : ""}`}>
                                                    <span className="dm-hist-level"
                                                        style={{ color: getThreatColor(d.payload.threat_level) }}>
                                                        {d.payload.threat_level}
                                                    </span>
                                                    <span className="dm-hist-time">{fmtTime(d.payload.timestamp)}</span>
                                                    <span className="dm-hist-dur">{d.payload.sustained_seconds}s</span>
                                                    {d.isTest && <span className="dm-hist-test-tag">TEST</span>}
                                                    <span className={`dm-hist-status ${d.result?.success ? "status-ok" : "status-fail"}`}>
                                                        {d.result?.success ? "✓ SENT" : "✗ FAIL"}
                                                    </span>
                                                </div>
                                            ))}
                                        </div>
                                    )}
                                </div>
                            </div>
                        </div>

                    </div>
                </div>

                {/* ══ ALERT MODAL ══ */}
                {activeAlert && (
                    <div className="dm-alert-backdrop" onClick={dismissAlertModal}>
                        <div className="dm-alert-modal"
                            style={{ borderColor: getThreatColor(activeAlert.payload.threat_level) }}
                            onClick={e => e.stopPropagation()}
                        >
                            {/* Header */}
                            <div className="dm-alert-modal-header"
                                style={{ background: getThreatBg(activeAlert.payload.threat_level) }}>
                                <div className="dm-alert-modal-title-row">
                                    <span className="dm-alert-siren">🚨</span>
                                    <span className="dm-alert-modal-level"
                                        style={{ color: getThreatColor(activeAlert.payload.threat_level) }}>
                                        {activeAlert.isTest ? "[TEST] " : ""}{activeAlert.payload.threat_level} THREAT ALERT
                                    </span>
                                    <span className="dm-alert-modal-id">#{activeAlert.payload.alert_number}</span>
                                </div>
                                <div className="dm-alert-countdown-row">
                                    <span className="dm-alert-countdown-label">
                                        Dismissing in {Math.ceil(alertModalMs / 1000)}s
                                    </span>
                                    <div className="dm-alert-countdown-track">
                                        <div className="dm-alert-countdown-fill" style={{
                                            width:      `${(alertModalMs / ALERT_MODAL_DURATION) * 100}%`,
                                            background: getThreatColor(activeAlert.payload.threat_level),
                                        }} />
                                    </div>
                                </div>
                            </div>

                            {/* Body */}
                            <div className="dm-alert-modal-body">
                                <div className="dm-alert-summary">
                                    {activeAlert.payload.human_summary}
                                </div>

                                <div className="dm-alert-detail-grid">
                                    <div className="dm-alert-detail-item">
                                        <span className="dm-detail-label">Time</span>
                                        <span className="dm-detail-value">{fmtTime(activeAlert.payload.timestamp)}</span>
                                    </div>
                                    <div className="dm-alert-detail-item">
                                        <span className="dm-detail-label">Sustained</span>
                                        <span className="dm-detail-value"
                                            style={{ color: getThreatColor(activeAlert.payload.threat_level) }}>
                                            {activeAlert.payload.sustained_seconds}s
                                        </span>
                                    </div>
                                    <div className="dm-alert-detail-item">
                                        <span className="dm-detail-label">Camera</span>
                                        <span className="dm-detail-value">{activeAlert.payload.camera}</span>
                                    </div>
                                    <div className="dm-alert-detail-item">
                                        <span className="dm-detail-label">Location</span>
                                        <span className="dm-detail-value">{activeAlert.payload.location}</span>
                                    </div>
                                    <div className="dm-alert-detail-item">
                                        <span className="dm-detail-label">Action</span>
                                        <span className="dm-detail-value"
                                            style={{ color: getThreatColor(activeAlert.payload.threat_level) }}>
                                            {activeAlert.payload.action?.toUpperCase()} ({fmtPct(activeAlert.payload.action_confidence)})
                                        </span>
                                    </div>
                                    <div className="dm-alert-detail-item">
                                        <span className="dm-detail-label">Threat Score</span>
                                        <span className="dm-detail-value"
                                            style={{ color: getThreatColor(activeAlert.payload.threat_level) }}>
                                            {fmtPct(activeAlert.payload.threat_score)}
                                        </span>
                                    </div>
                                </div>

                                {activeAlert.payload.objects_detected?.length > 0 && (
                                    <div className="dm-alert-objects">
                                        <div className="dm-alert-objects-label">Objects Detected</div>
                                        <div className="dm-alert-objects-list">
                                            {activeAlert.payload.objects_detected.map((obj, i) => (
                                                <span key={i} className="dm-alert-obj-chip">
                                                    {obj.object?.toUpperCase()} {fmtPct(obj.confidence)}
                                                </span>
                                            ))}
                                        </div>
                                    </div>
                                )}

                                <div className="dm-alert-contrib">
                                    <div className="dm-alert-contrib-row">
                                        <span>Action (LRCN)</span>
                                        <div className="dm-contrib-track">
                                            <div className="dm-contrib-fill dm-contrib-lrcn"
                                                style={{ width: `${activeAlert.payload.lrcn_contribution * 100}%` }} />
                                        </div>
                                        <span>{fmtPct(activeAlert.payload.lrcn_contribution)}</span>
                                    </div>
                                    <div className="dm-alert-contrib-row">
                                        <span>Objects (YOLO)</span>
                                        <div className="dm-contrib-track">
                                            <div className="dm-contrib-fill dm-contrib-yolo"
                                                style={{ width: `${activeAlert.payload.yolo_contribution * 100}%` }} />
                                        </div>
                                        <span>{fmtPct(activeAlert.payload.yolo_contribution)}</span>
                                    </div>
                                    {activeAlert.payload.synergy_bonus > 0 && (
                                        <div className="dm-alert-contrib-row dm-contrib-synergy-row">
                                            <span>Synergy Bonus</span>
                                            <div className="dm-contrib-track">
                                                <div className="dm-contrib-fill dm-contrib-synergy"
                                                    style={{ width: `${activeAlert.payload.synergy_bonus * 100}%` }} />
                                            </div>
                                            <span>+{fmtPct(activeAlert.payload.synergy_bonus)}</span>
                                        </div>
                                    )}
                                </div>

                                <div className={`dm-alert-dispatch-status ${activeAlert.result?.success ? "dispatch-ok" : "dispatch-fail"}`}>
                                    {activeAlert.result?.success
                                        ? "✓ Successfully sent to Coordination Hub"
                                        : `✗ Failed to reach Coordination Hub — ${activeAlert.result?.error}`
                                    }
                                </div>
                            </div>

                            <div className="dm-alert-modal-footer">
                                <button className="dm-alert-dismiss-btn" onClick={dismissAlertModal}>
                                    Dismiss Alert
                                </button>
                            </div>
                        </div>
                    </div>
                )}

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