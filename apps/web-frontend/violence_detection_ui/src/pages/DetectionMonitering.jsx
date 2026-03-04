import { useState, useEffect, useRef, useCallback } from "react"
import { useLocation, useNavigate } from "react-router-dom";
import Layout from "../layouts/Layout";
import './../styles/DetectionMonitering.css'

const SENT_BANNER_DURATION = 6000;
const ALERT_MODAL_DURATION = 12000;
const COUNTDOWN_STAGES = ["DETECTED", "SENDING", "SENT"];  // 1s each
const TEST_MODE = true;

// Threat level color/bg helpers (defined outside so CSS can use them too)
const THREAT_COLORS = {
    CRITICAL: "#ff2d2d", HIGH: "#ff6b00", MEDIUM: "#f5c400",
    LOW: "#4ade80", NONE: "#6b7280"
};
const THREAT_BG = {
    CRITICAL: "rgba(255,45,45,0.12)", HIGH: "rgba(255,107,0,0.12)",
    MEDIUM: "rgba(245,196,0,0.12)",   LOW: "rgba(74,222,128,0.12)",
    NONE: "rgba(107,114,128,0.10)"
};

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
    const [alertProgress, setAlertProgress]       = useState(null);
    const [activeAlert, setActiveAlert]           = useState(null);
    const [alertModalMs, setAlertModalMs]         = useState(0);
    const [alertHistory, setAlertHistory]         = useState([]);
    const [lastHubResult, setLastHubResult]       = useState(null);

    // ── NEW: Top banner (replaces old sentBanner) ──
    const [topBanner, setTopBanner]               = useState(null); // { level, success, error }

    // ── NEW: Visual countdown state for instant threats ──
    // { level, stage: 0|1|2 } where 0=DETECTED, 1=SENDING, 2=SENT
    const [alertCountdown, setAlertCountdown]     = useState(null);

    const wsRef              = useRef(null);
    const alertTimerRef      = useRef(null);
    const alertIntervalRef   = useRef(null);
    const topBannerTimerRef  = useRef(null);
    const countdownTimerRef  = useRef(null);
    const testAlertCounter   = useRef(0);

    useEffect(() => {
        if (!videoSource) { alert("No video source selected!"); navigate('/'); }
    }, [videoSource, navigate]);

    useEffect(() => {
        if (videoSource) startProcessing();
        return () => {
            if (wsRef.current) wsRef.current.close();
            clearTimeout(alertTimerRef.current);
            clearInterval(alertIntervalRef.current);
            clearTimeout(topBannerTimerRef.current);
            clearTimeout(countdownTimerRef.current);
        };
    }, []);

    // ─────────────────────────────────────────────────────────────────
    //  Top banner (big colored bar under topbar)
    // ─────────────────────────────────────────────────────────────────
    const showTopBanner = useCallback((level, success, error = null) => {
        clearTimeout(topBannerTimerRef.current);
        setTopBanner({ level, success, error });
        topBannerTimerRef.current = setTimeout(
            () => setTopBanner(null),
            SENT_BANNER_DURATION
        );
    }, []);

    // ─────────────────────────────────────────────────────────────────
    //  Visual countdown: DETECTED → SENDING → SENT (1s each)
    //  Then opens the modal
    // ─────────────────────────────────────────────────────────────────
    const runCountdown = useCallback((level, onComplete) => {
        setAlertCountdown({ level, stage: 0 }); // DETECTED

        countdownTimerRef.current = setTimeout(() => {
            setAlertCountdown({ level, stage: 1 }); // SENDING

            countdownTimerRef.current = setTimeout(() => {
                setAlertCountdown({ level, stage: 2 }); // SENT

                countdownTimerRef.current = setTimeout(() => {
                    setAlertCountdown(null);
                    onComplete();
                }, 1000);
            }, 1000);
        }, 1000);
    }, []);

    // ─────────────────────────────────────────────────────────────────
    //  Alert modal lifecycle
    // ─────────────────────────────────────────────────────────────────
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

    // ─────────────────────────────────────────────────────────────────
    //  Dispatch helper — runs countdown then opens modal + banner
    // ─────────────────────────────────────────────────────────────────
    const dispatchAlert = useCallback((dispatch) => {
        const level = dispatch.payload.threat_level;
        setAlertHistory(prev => [dispatch, ...prev].slice(0, 20));
        setLastHubResult(dispatch.result);

        // Always run the 3-stage countdown, then open modal + top banner
        runCountdown(level, () => {
            openAlertModal(dispatch);
            showTopBanner(level, dispatch.result?.success, dispatch.result?.error);
        });
    }, [runCountdown, openAlertModal, showTopBanner]);

    // ─────────────────────────────────────────────────────────────────
    //  TEST MODE
    // ─────────────────────────────────────────────────────────────────
    const fireTestAlert = useCallback(async () => {
        testAlertCounter.current += 1;
        const now   = new Date().toISOString();
        const level = testAlertCounter.current % 2 === 0 ? "HIGH" : "CRITICAL";

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
            action_contribution: 0.52,
            object_contribution: 0.28,
            synergy_bonus:     0.11,
            human_summary:     `[TEST] At ${new Date(now).toLocaleTimeString()}, a simulated ${level} threat was detected. This is a test alert to verify the alert pipeline.`,
            frame_number:      999,
            alert_number:      testAlertCounter.current,
        };

        const result = { success: true, status_code: 200, error: null };
        dispatchAlert({ payload: fakePayload, result, isTest: true });
    }, [videoProcessingInfo, dispatchAlert]);

    // ─────────────────────────────────────────────────────────────────
    //  WebSocket
    // ─────────────────────────────────────────────────────────────────
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
        setTopBanner(null);
        setAlertCountdown(null);
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

        if (data.alert_dispatch) {
            dispatchAlert(data.alert_dispatch);
        }

        if (merged.ready && merged.is_violent) {
            const ts = new Date(merged.timestamp).toLocaleTimeString();
            setDetectedActionsLog(prev =>
                prev.some(e => e.action === merged.action)
                    ? prev
                    : [...prev, { action: merged.action, timestamp: ts, confidence: merged.confidence }]
            );
        }

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

    // ─────────────────────────────────────────────────────────────────
    //  Helpers
    // ─────────────────────────────────────────────────────────────────
    const getThreatColor = (l) => THREAT_COLORS[l] || "#6b7280";
    const getThreatBg    = (l) => THREAT_BG[l]     || "rgba(107,114,128,0.10)";

    const getActionColor = (action, fusionLevel) => {
    // Threat level wins if fusion data exists
        if (fusionLevel && fusionLevel !== "NONE") return getThreatColor(fusionLevel);

        if (!action) 
            return "#6b7280";
        const a = action.toLowerCase();
        if (a === "shooting")
            return "#ff2d2d"; // red
        if (a === "attacking" || a === "fighting")
            return "#39d98a"; // green
        if (a === "running")                     
            return "#6b7280"; // grey
        return "#6b7280";
    };

    const fmtPct  = (v) => `${(v * 100).toFixed(0)}%`;
    const fmtTime = (iso) => new Date(iso).toLocaleTimeString();

    const getArmLabel = (ap) => {
        if (!ap) return "MONITORING";
        if (ap.is_cooling) return `COOLDOWN ${ap.cooldown_remaining}s`;
        if (ap.streak_secs > 0) return `ARMING ${ap.streak_secs}s / ${ap.required_secs}s`;
        return "MONITORING";
    };

    const alertStatusSummary = () => {
        const count = alertProgress?.alert_count || 0;
        if (count === 0) return { label: "NO ALERTS FIRED", color: "var(--text-dim)", bg: "transparent" };
        const level = alertHistory[0]?.payload?.threat_level || "HIGH";
        return { label: `${count} ALERT${count > 1 ? "S" : ""} FIRED`, color: getThreatColor(level), bg: getThreatBg(level) };
    };
    const alertSummary = alertStatusSummary();

    // Countdown stage label + color
    const countdownStageLabel = alertCountdown
        ? COUNTDOWN_STAGES[alertCountdown.stage]
        : null;

    // ─────────────────────────────────────────────────────────────────
    //  Render
    // ─────────────────────────────────────────────────────────────────
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
                        {TEST_MODE && <span className="dm-test-mode-badge">TEST MODE</span>}
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

                {/* ══════════════════════════════════════════════════
                    FULL-WIDTH ARMING BAR — below topbar, above grid
                ══════════════════════════════════════════════════ */}
                <div className="dm-global-arm-bar">
                    {alertProgress ? (
                        alertProgress.is_cooling ? (
                            <>
                                <span className="dm-garm-label dm-garm-cooling">
                                    ❄ COOLDOWN — next alert in {alertProgress.cooldown_remaining}s
                                </span>
                                <div className="dm-garm-track">
                                    <div className="dm-garm-fill dm-garm-fill--cool"
                                        style={{ width: `${alertProgress.cooldown_pct}%` }} />
                                </div>
                                <span className="dm-garm-pct">{alertProgress.cooldown_pct}%</span>
                            </>
                        ) : alertProgress.streak_secs > 0 ? (
                            <>
                                <span className={`dm-garm-label ${alertProgress.progress_pct > 60 ? "dm-garm-hot" : "dm-garm-warm"}`}>
                                    ⚡ ARMING — {alertProgress.streak_secs}s / {alertProgress.required_secs}s sustained
                                </span>
                                <div className="dm-garm-track">
                                    <div
                                        className={`dm-garm-fill ${alertProgress.progress_pct > 60 ? "dm-garm-fill--hot" : "dm-garm-fill--warm"}`}
                                        style={{ width: `${alertProgress.progress_pct}%` }}
                                    />
                                </div>
                                <span className="dm-garm-pct">{alertProgress.progress_pct}%</span>
                            </>
                        ) : (
                            <>
                                <span className="dm-garm-label dm-garm-idle">● MONITORING</span>
                                <div className="dm-garm-track">
                                    <div className="dm-garm-fill" style={{ width: "0%" }} />
                                </div>
                                <span className="dm-garm-pct">—</span>
                            </>
                        )
                    ) : (
                        <>
                            <span className="dm-garm-label dm-garm-idle">● MONITORING</span>
                            <div className="dm-garm-track"><div className="dm-garm-fill" style={{ width: "0%" }} /></div>
                            <span className="dm-garm-pct">—</span>
                        </>
                    )}
                </div>

                {/* ══════════════════════════════════════════════════
                    VISUAL COUNTDOWN BANNER
                    Shows: DETECTED → SENDING → SENT (1s each)
                    Appears above main grid, below arm bar
                ══════════════════════════════════════════════════ */}
                {alertCountdown && (
                    <div
                        className="dm-countdown-banner"
                        style={{
                            background:   getThreatBg(alertCountdown.level),
                            borderColor:  getThreatColor(alertCountdown.level),
                            color:        getThreatColor(alertCountdown.level),
                        }}
                    >
                        <span className="dm-countdown-siren">🚨</span>
                        <span className="dm-countdown-level">{alertCountdown.level}</span>
                        <span className="dm-countdown-arrow">›</span>

                        {COUNTDOWN_STAGES.map((stage, i) => (
                            <span
                                key={stage}
                                className={`dm-countdown-stage ${
                                    i < alertCountdown.stage  ? "stage-done" :
                                    i === alertCountdown.stage ? "stage-active" : "stage-pending"
                                }`}
                            >
                                {i < alertCountdown.stage ? "✓" : ""} {stage}
                                {i < COUNTDOWN_STAGES.length - 1 && (
                                    <span className="dm-countdown-dot">·</span>
                                )}
                            </span>
                        ))}
                    </div>
                )}

                {/* ══════════════════════════════════════════════════
                    TOP BANNER — big colored bar after alert fires
                    'CRITICAL ALERT SENT' or '✗ FAILED'
                ══════════════════════════════════════════════════ */}
                {topBanner && (
                    <div
                        className="dm-top-banner"
                        style={{
                            background:  topBanner.success ? getThreatBg(topBanner.level)   : "rgba(255,59,59,0.12)",
                            borderColor: topBanner.success ? getThreatColor(topBanner.level) : "#ff3b3b",
                            color:       topBanner.success ? getThreatColor(topBanner.level) : "#ff3b3b",
                        }}
                    >
                        <span className="dm-top-banner-icon">{topBanner.success ? "🚨" : "✗"}</span>
                        <span className="dm-top-banner-text">
                            {topBanner.success
                                ? `${topBanner.level} ALERT SENT TO COORDINATION HUB`
                                : `ALERT DISPATCH FAILED — ${topBanner.error}`
                            }
                        </span>
                        <button className="dm-top-banner-close" onClick={() => setTopBanner(null)}>×</button>
                    </div>
                )}

                {/* ── Main grid ── */}
                <div className="dm-grid">

                    {/* ══ COL 1: Video ══ */}
                    <div className="dm-card dm-video-card">
                        <div className="dm-card-header">
                            <span className="dm-card-title">Video Stream</span>
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

                        <div className="dm-status-strip">
                            <span>{processingStatus || "Idle"}</span>
                            {videoInfo && <span>{videoInfo.width}×{videoInfo.height} @ {videoInfo.fps}fps</span>}
                        </div>
                    </div>

                    {/* ══ COL 2: Current Action + Objects ══ */}
                    <div className="dm-col">
                        <div className="dm-card">
                            <div className="dm-card-header">
                                <span className="dm-card-title">⚡ Current Action</span>
                            </div>
                            {currentAction && currentAction.ready ? (
                                <div
                                    className={`dm-current-action ${currentAction.is_violent ? "state-violent" : "state-normal"}`}
                                    style={{ borderLeftColor: getActionColor(currentAction.action, fusionResult?.weight_level) }}
                                >
                                    <div
                                        className="dm-action-name"
                                        style={{ color: getActionColor(currentAction.action, fusionResult?.weight_level) }}
                                    >
                                        {currentAction.action.toUpperCase()}
                                    </div>
                                    <div className="dm-action-meta">
                                        <span>Frame {currentAction.frame_number}</span>
                                        {/* <span className={`dm-violent-tag ${currentAction.is_violent ? "tag-yes" : "tag-no"}`}>
                                            {currentAction.is_violent ? "VIOLENT" : "NORMAL"}
                                        </span> */}
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

                        <div className="dm-card">
                            <div className="dm-card-header">
                                <span className="dm-card-title">Current Objects</span>
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

                    {/* ══ COL 3: Log + Threat + Alert Status ══ */}
                    <div className="dm-col">

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
                                    {fusionResult.action_contribution !== undefined && (
                                        <div className="dm-threat-breakdown">
                                            <div className="dm-breakdown-row">
                                                <span>Action (LRCN)</span>
                                                <span>{fmtPct(fusionResult.action_contribution)}</span>
                                            </div>
                                            <div className="dm-breakdown-row">
                                                <span>Objects (YOLO)</span>
                                                <span>{fmtPct(fusionResult.object_contribution)}</span>
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

                        <div className="dm-card dm-alert-status-card"
                            style={{
                                borderColor: alertHistory.length > 0
                                    ? getThreatColor(alertHistory[0]?.payload?.threat_level)
                                    : undefined
                            }}
                        >
                            <div className="dm-card-header">
                                <span className="dm-card-title">🚨 Alert Status</span>
                                <span className="dm-card-sub" style={{ color: alertSummary.color }}>
                                    {alertSummary.label}
                                </span>
                            </div>

                            <div className="dm-alert-status-body">
                                <div className="dm-alert-state-row">
                                    <div className="dm-alert-state-item">
                                        <span className="dm-alert-state-label">ENGINE</span>
                                        <span className={`dm-alert-state-value ${
                                            alertProgress?.is_cooling      ? "val-cyan"   :
                                            alertProgress?.progress_pct > 0 ? "val-orange" : "val-green"
                                        }`}>
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
                                        <span className={`dm-alert-state-value ${
                                            lastHubResult === null ? "val-dim" :
                                            lastHubResult.success  ? "val-green" : "val-red"
                                        }`}>
                                            {lastHubResult === null ? "—" : lastHubResult.success ? "✓ SENT" : "✗ FAILED"}
                                        </span>
                                    </div>
                                </div>

                                {TEST_MODE && (
                                    <div className="dm-test-row">
                                        <div className="dm-test-info">
                                            <span className="dm-test-label">🧪 Test Mode Active</span>
                                            <span className="dm-test-desc">
                                                Fires a simulated alert through the full UI pipeline including countdown, modal, banner, and history.
                                            </span>
                                        </div>
                                        <button className="dm-test-btn" onClick={fireTestAlert}>
                                            Send Test Alert
                                        </button>
                                    </div>
                                )}

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

                            <div className="dm-alert-modal-body">
                                <div className="dm-alert-summary"
                                    style={{ borderLeftColor: getThreatColor(activeAlert.payload.threat_level) }}>
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
                                                style={{ width: `${activeAlert.payload.action_contribution * 100}%` }} />
                                        </div>
                                        <span>{fmtPct(activeAlert.payload.action_contribution)}</span>
                                    </div>
                                    <div className="dm-alert-contrib-row">
                                        <span>Objects (YOLO)</span>
                                        <div className="dm-contrib-track">
                                            <div className="dm-contrib-fill dm-contrib-yolo"
                                                style={{ width: `${activeAlert.payload.object_contribution * 100}%` }} />
                                        </div>
                                        <span>{fmtPct(activeAlert.payload.object_contribution)}</span>
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