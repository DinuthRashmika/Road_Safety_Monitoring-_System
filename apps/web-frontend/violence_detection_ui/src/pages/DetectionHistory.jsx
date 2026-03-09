import { useState, useEffect } from "react";
import { createPortal } from "react-dom";
import Layout from "../layouts/Layout";
import "../styles/DetectionHistory.css";

const THREAT_COLORS = {
    CRITICAL: "#E4080A", HIGH: "#d97706", MEDIUM: "#ca8a04",
    LOW: "#16a34a", NONE: "#9ca3af"
};
const THREAT_BG = {
    CRITICAL: "#fdf5f5", HIGH: "#fffbeb", MEDIUM: "#fefce8",
    LOW: "#f0fdf4", NONE: "#f4f7f6"
};
const THREAT_BORDER = {
    CRITICAL: "rgba(228,8,10,0.2)", HIGH: "rgba(217,119,6,0.2)",
    MEDIUM: "rgba(202,138,4,0.2)", LOW: "rgba(22,163,74,0.2)", NONE: "#e0e0e0"
};

const CONF_COLORS = { low: "#9ca3af", medium: "#d97706", high: "#E4080A", critical: "#7c3aed" };

const fmtDate   = (iso) => iso ? new Date(iso).toLocaleString() : "—";
const fmtDur    = (s)   => s != null ? `${Number(s).toFixed(1)}s` : "—";
const fmtReason = (r)   => r ? r.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase()) : "—";

function getThreatColor (l) { return THREAT_COLORS[l]  || "#9ca3af"; }
function getThreatBg    (l) { return THREAT_BG[l]      || "#f4f7f6"; }
function getThreatBorder(l) { return THREAT_BORDER[l]  || "#e0e0e0"; }

function SessionModal({ selected, onClose }) {
    useEffect(() => {
        const onKey = (e) => { if (e.key === "Escape") onClose(); };
        document.addEventListener("keydown", onKey);
        document.body.style.overflow = "hidden";
        return () => {
            document.removeEventListener("keydown", onKey);
            document.body.style.overflow = "";
        };
    }, [onClose]);

    const confTotal = (dist) => {
        if (!dist) return 1;
        const t = Object.values(dist).reduce((a, v) => a + v, 0);
        return t || 1;
    };

    return createPortal(
        <div className="ds-backdrop" onClick={onClose}>
            <div className="ds-modal" onClick={e => e.stopPropagation()}>

                {/* Header */}
                <div
                    className="ds-modal-header"
                    style={{ borderLeft: `4px solid ${getThreatColor(selected.highest_threat_level)}` }}
                >
                    <div className="ds-modal-title-row">
                        <span className="ds-modal-icon">🎥</span>
                        <span className="ds-modal-title">Session Detail</span>
                        <span className="ds-modal-id">{selected.session_id}</span>
                    </div>
                    <div className="ds-modal-time">
                        {fmtDate(selected.started_at)} → {fmtDate(selected.ended_at)}
                    </div>
                </div>

                {/* Body */}
                <div className="ds-modal-body">

                    {/* Overview */}
                    <div className="ds-section">
                        <div className="ds-section-title">Overview</div>
                        <div className="ds-info-grid">
                            {[
                                ["Duration",       fmtDur(selected.duration_seconds), ""],
                                ["End Reason",     fmtReason(selected.end_reason),    ""],
                                ["Frames",         selected.camera?.total_frames_processed ?? "—", ""],
                                ["Highest Threat", selected.highest_threat_level || "NONE",
                                    selected.highest_threat_level === "CRITICAL" ? "red"
                                    : selected.highest_threat_level === "HIGH"   ? "orange"
                                    : selected.highest_threat_level === "NONE"   ? "" : "green"],
                                ["Total Alerts",   selected.total_alerts_fired ?? 0,
                                    selected.total_alerts_fired > 0 ? "red" : ""],
                                ["FPS",            selected.camera?.fps ?? "—", ""],
                            ].map(([label, value, color]) => (
                                <div key={label} className="ds-info-item">
                                    <span className="ds-info-label">{label}</span>
                                    <span className={`ds-info-value${color ? ` ds-info-value--${color}` : ""}`}>
                                        {String(value)}
                                    </span>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Camera */}
                    <div className="ds-section">
                        <div className="ds-section-title">Camera Info</div>
                        <div className="ds-camera-grid">
                            {[
                                ["Label",      selected.camera?.camera_label],
                                ["Resolution", selected.camera?.resolution_width && selected.camera?.resolution_height
                                    ? `${selected.camera.resolution_width} × ${selected.camera.resolution_height}`
                                    : "—"],
                                ["Source",     selected.camera?.source_path],
                            ].map(([label, value]) => (
                                <div key={label} className="ds-camera-item">
                                    <span className="ds-info-label">{label}</span>
                                    <span className="ds-info-value" style={{ fontSize: label === "Source" ? "11px" : "13px", wordBreak: "break-all" }}>
                                        {value || "—"}
                                    </span>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Detected Actions */}
                    <div className="ds-section">
                        <div className="ds-section-title">Detected Actions</div>
                        <div className="ds-tag-row">
                            {selected.detected_actions?.length > 0
                                ? selected.detected_actions.map((a, i) => (
                                    <span key={i} className="ds-action-tag">
                                        {typeof a === "object" ? a.action || JSON.stringify(a) : a}
                                    </span>
                                ))
                                : <span className="ds-none-tag">No actions detected</span>
                            }
                        </div>
                    </div>

                    {/* Detected Objects */}
                    <div className="ds-section">
                        <div className="ds-section-title">Detected Objects</div>
                        <div className="ds-tag-row">
                            {selected.detected_objects?.length > 0
                                ? selected.detected_objects.map((o, i) => (
                                    <span key={i} className="ds-object-tag">
                                        {typeof o === "object" ? o.object || o.label || o.name || JSON.stringify(o) : o}
                                    </span>
                                ))
                                : <span className="ds-none-tag">No objects detected</span>
                            }
                        </div>
                    </div>

                    {/* Action Confidence Distribution */}
                    {selected.action_confidence_distribution && (
                        <div className="ds-section">
                            <div className="ds-section-title">Action Confidence Distribution</div>
                            {Object.entries(selected.action_confidence_distribution).map(([level, count]) => {
                                const total = confTotal(selected.action_confidence_distribution);
                                return (
                                    <div key={level} className="ds-conf-row">
                                        <span style={{ textTransform: "capitalize" }}>{level}</span>
                                        <div className="ds-conf-track">
                                            <div
                                                className="ds-conf-fill"
                                                style={{
                                                    width: `${(count / total) * 100}%`,
                                                    background: CONF_COLORS[level] || "#9ca3af",
                                                }}
                                            />
                                        </div>
                                        <span className="ds-conf-pct" style={{ color: CONF_COLORS[level] || "#9ca3af" }}>
                                            {count}
                                        </span>
                                    </div>
                                );
                            })}
                        </div>
                    )}

                    {/* Object Confidence Distribution */}
                    {selected.object_confidence_distribution && (
                        <div className="ds-section">
                            <div className="ds-section-title">Object Confidence Distribution</div>
                            {Object.entries(selected.object_confidence_distribution).map(([level, count]) => {
                                const total = confTotal(selected.object_confidence_distribution);
                                return (
                                    <div key={level} className="ds-conf-row">
                                        <span style={{ textTransform: "capitalize" }}>{level}</span>
                                        <div className="ds-conf-track">
                                            <div
                                                className="ds-conf-fill"
                                                style={{
                                                    width: `${(count / total) * 100}%`,
                                                    background: CONF_COLORS[level] || "#9ca3af",
                                                }}
                                            />
                                        </div>
                                        <span className="ds-conf-pct" style={{ color: CONF_COLORS[level] || "#9ca3af" }}>
                                            {count}
                                        </span>
                                    </div>
                                );
                            })}
                        </div>
                    )}

                    {/* Alert IDs */}
                    {selected.alert_ids?.length > 0 && (
                        <div className="ds-section">
                            <div className="ds-section-title">Alert IDs Fired</div>
                            <div className="ds-tag-row">
                                {selected.alert_ids.map((id, i) => (
                                    <span key={i} className="ds-action-tag" style={{ fontSize: "11px", fontFamily: "monospace" }}>
                                        {id}
                                    </span>
                                ))}
                            </div>
                        </div>
                    )}

                </div>

                {/* Footer */}
                <div className="ds-modal-footer">
                    <button className="ds-close-btn" onClick={onClose}>Close</button>
                </div>
            </div>
        </div>,
        document.body
    );
}

function DetectionHistory() {
    const [sessions, setSessions] = useState([]);
    const [loading, setLoading]   = useState(true);
    const [error, setError]       = useState(null);
    const [selected, setSelected] = useState(null);
    const [search, setSearch]     = useState("");

    useEffect(() => { fetchSessions(); }, []);

    const fetchSessions = async () => {
        setLoading(true); setError(null);
        try {
            const res  = await fetch("http://127.0.0.1:8000/detection/detections");
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const data = await res.json();
            setSessions(data.sessions || []);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const filtered = sessions.filter(s => {
        if (!search) return true;
        const q = search.toLowerCase();
        return (
            s.session_id?.toLowerCase().includes(q) ||
            s.camera?.camera_label?.toLowerCase().includes(q) ||
            s.highest_threat_level?.toLowerCase().includes(q) ||
            s.end_reason?.toLowerCase().includes(q) ||
            s.detected_actions?.some(a =>
                (typeof a === "object" ? a.action : a)?.toLowerCase().includes(q)
            )
        );
    });

    const counts = {
        total:  sessions.length,
        alerts: sessions.filter(s => s.total_alerts_fired > 0).length,
        threat: sessions.filter(s => ["CRITICAL", "HIGH"].includes(s.highest_threat_level)).length,
        avgDur: sessions.length
            ? (sessions.reduce((a, s) => a + (s.duration_seconds || 0), 0) / sessions.length).toFixed(1)
            : "0",
    };

    return (
        <Layout>
            <div className="ds-root">

                {/* Header */}
                <div className="ds-header">
                    <div className="ds-header-left">
                        <span className="ds-title">Detection Sessions</span>
                        <span className="ds-subtitle">All recorded monitoring sessions</span>
                    </div>
                    <div className="ds-header-right">
                        <span className="ds-count-badge">{sessions.length} SESSIONS</span>
                        <button className="ds-refresh-btn" onClick={fetchSessions}>↻ Refresh</button>
                    </div>
                </div>

                {/* Summary Cards */}
                <div className="ds-summary-row">
                    <div className="ds-summary-card">
                        <span className="ds-summary-count">{counts.total}</span>
                        <span className="ds-summary-label">Total Sessions</span>
                    </div>
                    <div className="ds-summary-card">
                        <span className="ds-summary-count ds-summary-count--red">{counts.alerts}</span>
                        <span className="ds-summary-label">With Alerts</span>
                    </div>
                    <div className="ds-summary-card">
                        <span className="ds-summary-count ds-summary-count--orange">{counts.threat}</span>
                        <span className="ds-summary-label">High / Critical</span>
                    </div>
                    <div className="ds-summary-card">
                        <span className="ds-summary-count ds-summary-count--green">{counts.avgDur}s</span>
                        <span className="ds-summary-label">Avg Duration</span>
                    </div>
                </div>

                {/* Search Bar */}
                <div className="ds-search-bar">
                    <input
                        className="ds-search-input"
                        placeholder="Search by session ID, camera, threat level, action..."
                        value={search}
                        onChange={e => setSearch(e.target.value)}
                    />
                    {search && (
                        <button className="ds-clear-btn" onClick={() => setSearch("")}>Clear</button>
                    )}
                    <span className="ds-result-count">{filtered.length} results</span>
                </div>

                {/* Content */}
                <div className="ds-content">
                    {loading ? (
                        <div className="ds-centered">
                            <div className="ds-spinner" />
                            <p className="ds-spinner-text">Loading sessions...</p>
                        </div>
                    ) : error ? (
                        <div className="ds-error-box">
                            <span>❌ Failed to load: {error}</span>
                            <button className="ds-retry-btn" onClick={fetchSessions}>Retry</button>
                        </div>
                    ) : filtered.length === 0 ? (
                        <div className="ds-centered">
                            <span className="ds-empty-icon">📭</span>
                            <p className="ds-empty-text">No sessions found</p>
                        </div>
                    ) : (
                        <div className="ds-table-wrapper">
                            <table className="ds-table">
                                <thead>
                                    <tr className="ds-thead">
                                        <th className="ds-th">Session ID</th>
                                        <th className="ds-th">Started</th>
                                        <th className="ds-th">Duration</th>
                                        <th className="ds-th">Camera</th>
                                        <th className="ds-th">Frames</th>
                                        <th className="ds-th">Threat</th>
                                        <th className="ds-th">Alerts</th>
                                        <th className="ds-th">End Reason</th>
                                        <th className="ds-th">Details</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {filtered.map((s, i) => (
                                        <tr
                                            key={s._id || i}
                                            className="ds-tr"
                                            style={{
                                                background: i % 2 === 0 ? "rgba(0,0,0,0.012)" : "transparent",
                                                borderLeft: `3px solid ${getThreatColor(s.highest_threat_level)}`,
                                            }}
                                        >
                                            <td className="ds-td ds-td--mono">{s.session_id || "—"}</td>
                                            <td className="ds-td ds-td--time">{fmtDate(s.started_at)}</td>
                                            <td className="ds-td ds-td--muted">{fmtDur(s.duration_seconds)}</td>
                                            <td className="ds-td ds-td--muted">{s.camera?.camera_label || "—"}</td>
                                            <td className="ds-td ds-td--muted">{s.camera?.total_frames_processed ?? "—"}</td>
                                            <td className="ds-td">
                                                <span
                                                    className="ds-threat-badge"
                                                    style={{
                                                        background: getThreatBg(s.highest_threat_level),
                                                        color:      getThreatColor(s.highest_threat_level),
                                                        border:     `1px solid ${getThreatBorder(s.highest_threat_level)}`,
                                                    }}
                                                >
                                                    {s.highest_threat_level || "NONE"}
                                                </span>
                                            </td>
                                            <td className="ds-td">
                                                <span className={`ds-alert-count ${s.total_alerts_fired > 0 ? "ds-alert-count--has" : "ds-alert-count--none"}`}>
                                                    {s.total_alerts_fired ?? 0}
                                                </span>
                                            </td>
                                            <td className="ds-td">
                                                <span className="ds-end-reason">{fmtReason(s.end_reason)}</span>
                                            </td>
                                            <td className="ds-td">
                                                <button className="ds-view-btn" onClick={() => setSelected(s)}>
                                                    View
                                                </button>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                </div>

            </div>

            {/* Portal modal — renders into document.body, outside Layout */}
            {selected && (
                <SessionModal
                    selected={selected}
                    onClose={() => setSelected(null)}
                />
            )}
        </Layout>
    );
}

export default DetectionHistory;