import { useState, useEffect } from "react";
import Layout from "../layouts/Layout";
import "../styles/AlertsHistory.css";

const THREAT_COLORS = {
    CRITICAL: "#ff2d2d", HIGH: "#ff6b00", MEDIUM: "#f5c400",
    LOW: "#4ade80", NONE: "#6b7280"
};
const THREAT_BG = {
    CRITICAL: "rgba(255,45,45,0.10)", HIGH: "rgba(255,107,0,0.10)",
    MEDIUM: "rgba(245,196,0,0.10)", LOW: "rgba(74,222,128,0.10)",
    NONE: "rgba(107,114,128,0.08)"
};

const fmtPct  = (v) => v != null ? `${(v * 100).toFixed(0)}%` : "—";
const fmtTime = (iso) => {
    if (!iso) return "—";
    return new Date(iso).toLocaleString();
};

function AlertsHistory() {
    const [alerts, setAlerts]     = useState([]);
    const [loading, setLoading]   = useState(true);
    const [error, setError]       = useState(null);
    const [selected, setSelected] = useState(null);
    const [filter, setFilter]     = useState("ALL");
    const [search, setSearch]     = useState("");

    const getThreatColor = (l) => THREAT_COLORS[l] || "#6b7280";
    const getThreatBg    = (l) => THREAT_BG[l]     || "rgba(107,114,128,0.08)";

    useEffect(() => { fetchAlerts(); }, []);

    const fetchAlerts = async () => {
        setLoading(true);
        setError(null);
        try {
            const res = await fetch("http://127.0.0.1:8000/detection/alerts");
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const data = await res.json();
            setAlerts(data.alerts || []);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const filtered = alerts.filter(a => {
        const matchLevel  = filter === "ALL" || a.threat_level === filter;
        const matchSearch = search === "" ||
            a.action?.toLowerCase().includes(search.toLowerCase()) ||
            a.camera?.toLowerCase().includes(search.toLowerCase()) ||
            a.location?.toLowerCase().includes(search.toLowerCase()) ||
            a.human_summary?.toLowerCase().includes(search.toLowerCase());
        return matchLevel && matchSearch;
    });

    const counts = {
        ALL:      alerts.length,
        CRITICAL: alerts.filter(a => a.threat_level === "CRITICAL").length,
        HIGH:     alerts.filter(a => a.threat_level === "HIGH").length,
        MEDIUM:   alerts.filter(a => a.threat_level === "MEDIUM").length,
    };

    return (
        <Layout>
            <div className="ah-root">

                {/* Top Bar */}
                <div className="ah-header">
                    <div className="ah-header-left">
                        <span className="ah-title">Alert History</span>
                        <span className="ah-subtitle">Fired Alerts recorded in the system</span>
                    </div>
                    <div className="ah-header-right">
                        <span className="ah-count-badge">{alerts.length} TOTAL</span>
                        <button className="ah-refresh-btn" onClick={fetchAlerts}>↻ Refresh</button>
                    </div>
                </div>

                {/* Summary Cards */}
                <div className="ah-summary-row">
                    {["ALL", "CRITICAL", "HIGH", "MEDIUM"].map(level => (
                        <div
                            key={level}
                            onClick={() => setFilter(level)}
                            className={`ah-summary-card ${filter === level ? "ah-summary-card--active" : ""}`}
                            style={{
                                borderBottom: filter === level
                                    ? `2px solid ${getThreatColor(level === "ALL" ? "NONE" : level)}`
                                    : "2px solid transparent",
                            }}
                        >
                            <span
                                className="ah-summary-count"
                                style={{ color: getThreatColor(level === "ALL" ? "NONE" : level) }}
                            >
                                {counts[level]}
                            </span>
                            <span className="ah-summary-label">{level}</span>
                        </div>
                    ))}
                </div>

                {/* Search Bar */}
                <div className="ah-search-bar">
                    <input
                        className="ah-search-input"
                        placeholder="Search by action, camera, location, summary..."
                        value={search}
                        onChange={e => setSearch(e.target.value)}
                    />
                    {(filter !== "ALL" || search) && (
                        <button className="ah-clear-btn" onClick={() => { setFilter("ALL"); setSearch(""); }}>
                            Clear
                        </button>
                    )}
                    <span className="ah-result-count">{filtered.length} results</span>
                </div>

                {/* Content */}
                <div className="ah-content">
                    {loading ? (
                        <div className="ah-centered">
                            <div className="ah-spinner" />
                            <p className="ah-spinner-text">Loading alerts...</p>
                        </div>
                    ) : error ? (
                        <div className="ah-error-box">
                            <span>❌ Failed to load: {error}</span>
                            <button className="ah-retry-btn" onClick={fetchAlerts}>Retry</button>
                        </div>
                    ) : filtered.length === 0 ? (
                        <div className="ah-centered">
                            <span className="ah-empty-icon">📭</span>
                            <p className="ah-empty-text">No alerts found</p>
                        </div>
                    ) : (
                        <div className="ah-table-wrapper">
                            <table className="ah-table">
                                <thead>
                                    <tr className="ah-thead">
                                        <th className="ah-th">Level</th>
                                        <th className="ah-th">Time</th>
                                        <th className="ah-th">Action</th>
                                        <th className="ah-th">Objects</th>
                                        <th className="ah-th">Score</th>
                                        <th className="ah-th">Camera</th>
                                        <th className="ah-th">Location</th>
                                        <th className="ah-th">Sustained</th>
                                        <th className="ah-th">Details</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {filtered.map((alert, i) => (
                                        <tr
                                            key={alert._id || i}
                                            className="ah-tr"
                                            style={{
                                                background:  i % 2 === 0 ? "rgba(255,255,255,0.015)" : "transparent",
                                                borderLeft:  `3px solid ${getThreatColor(alert.threat_level)}`,
                                            }}
                                        >
                                            <td className="ah-td">
                                                <span
                                                    className="ah-level-badge"
                                                    style={{
                                                        background: getThreatBg(alert.threat_level),
                                                        color:      getThreatColor(alert.threat_level),
                                                        border:     `1px solid ${getThreatColor(alert.threat_level)}44`,
                                                    }}
                                                >
                                                    {alert.threat_level}
                                                </span>
                                            </td>
                                            <td className="ah-td ah-td--time">{fmtTime(alert.timestamp)}</td>
                                            <td className="ah-td" style={{ color: getThreatColor(alert.threat_level) }}>
                                                <span className="ah-action-name">{alert.action?.toUpperCase() || "—"}</span>
                                                <span className="ah-conf-tag">{fmtPct(alert.action_confidence)}</span>
                                            </td>
                                            <td className="ah-td">
                                                {alert.objects_detected?.length > 0
                                                    ? alert.objects_detected.map((o, j) => (
                                                        <span key={j} className="ah-obj-chip">
                                                            {o.object} {fmtPct(o.confidence)}
                                                        </span>
                                                    ))
                                                    : <span className="ah-none">—</span>
                                                }
                                            </td>
                                            <td className="ah-td ah-td--score" style={{ color: getThreatColor(alert.threat_level) }}>
                                                {fmtPct(alert.threat_score)}
                                            </td>
                                            <td className="ah-td ah-td--muted">{alert.camera || "—"}</td>
                                            <td className="ah-td ah-td--muted">{alert.location || "—"}</td>
                                            <td className="ah-td ah-td--time">
                                                {alert.sustained_seconds != null ? `${alert.sustained_seconds}s` : "—"}
                                            </td>
                                            <td className="ah-td">
                                                <button className="ah-view-btn" onClick={() => setSelected(alert)}>
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

                {/* Detail Modal */}
                {selected && (
                    <div className="ah-backdrop" onClick={() => setSelected(null)}>
                        <div
                            className="ah-modal"
                            style={{ borderColor: getThreatColor(selected.threat_level) }}
                            onClick={e => e.stopPropagation()}
                        >
                            {/* Header */}
                            <div
                                className="ah-modal-header"
                                style={{
                                    background:   getThreatBg(selected.threat_level),
                                    borderBottom: `1px solid ${getThreatColor(selected.threat_level)}33`,
                                }}
                            >
                                <div className="ah-modal-title-row">
                                    <span className="ah-modal-siren">🚨</span>
                                    <span className="ah-modal-title" style={{ color: getThreatColor(selected.threat_level) }}>
                                        {selected.threat_level} THREAT ALERT
                                    </span>
                                    <span className="ah-modal-id">#{selected.alert_number}</span>
                                    {selected.is_test && <span className="ah-test-tag">TEST</span>}
                                </div>
                                <p className="ah-modal-time">{fmtTime(selected.timestamp)}</p>
                            </div>

                            {/* Body */}
                            <div className="ah-modal-body">

                                <div
                                    className="ah-summary-box"
                                    style={{ borderLeftColor: getThreatColor(selected.threat_level) }}
                                >
                                    {selected.human_summary || "No summary available."}
                                </div>

                                <div className="ah-detail-grid">
                                    {[
                                        ["Camera",       selected.camera],
                                        ["Location",     selected.location],
                                        ["Action",       selected.action?.toUpperCase()],
                                        ["Confidence",   fmtPct(selected.action_confidence)],
                                        ["Threat Score", fmtPct(selected.threat_score)],
                                        ["Sustained",    selected.sustained_seconds != null ? `${selected.sustained_seconds}s` : "—"],
                                        ["Frame",        selected.frame_number],
                                        ["Session ID",   selected.session_id],
                                    ].map(([label, value]) => (
                                        <div key={label} className="ah-detail-item">
                                            <span className="ah-detail-label">{label}</span>
                                            <span className="ah-detail-value">{value || "—"}</span>
                                        </div>
                                    ))}
                                </div>

                                {selected.objects_detected?.length > 0 && (
                                    <div className="ah-section">
                                        <div className="ah-section-title">Objects Detected</div>
                                        <div className="ah-chip-row">
                                            {selected.objects_detected.map((o, i) => (
                                                <span key={i} className="ah-obj-chip-large">
                                                    {o.object?.toUpperCase()} — {fmtPct(o.confidence)}
                                                </span>
                                            ))}
                                        </div>
                                    </div>
                                )}

                                <div className="ah-section">
                                    <div className="ah-section-title">Score Breakdown</div>
                                    {[
                                        ["Action (LRCN)",  selected.action_contribution,  "#00d4ff"],
                                        ["Objects (YOLO)", selected.object_contribution,  "#ff3b3b"],
                                        ["Synergy Bonus",  selected.synergy_bonus,        "#f5c400"],
                                    ].map(([label, val, color]) => (
                                        <div key={label} className="ah-contrib-row">
                                            <span className="ah-contrib-label">{label}</span>
                                            <div className="ah-contrib-track">
                                                <div
                                                    className="ah-contrib-fill"
                                                    style={{ width: `${(val || 0) * 100}%`, background: color }}
                                                />
                                            </div>
                                            <span className="ah-contrib-pct" style={{ color }}>{fmtPct(val)}</span>
                                        </div>
                                    ))}
                                </div>

                                {selected.reasoning && (
                                    <div className="ah-section">
                                        <div className="ah-section-title">Fusion Reasoning</div>
                                        <div className="ah-reasoning-box">{selected.reasoning}</div>
                                    </div>
                                )}
                            </div>

                            {/* Footer */}
                            <div className="ah-modal-footer">
                                <button className="ah-close-btn" onClick={() => setSelected(null)}>
                                    Close
                                </button>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </Layout>
    );
}

export default AlertsHistory;