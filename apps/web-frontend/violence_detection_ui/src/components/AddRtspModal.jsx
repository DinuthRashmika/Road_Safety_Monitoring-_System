import { useState } from "react";
import "../styles/AddRtspModal.css";

const API = "http://127.0.0.1:8000";

const EMPTY_FORM = {
    name:        "",
    ip:          "",
    port:        554,
    username:    "",
    password:    "",
    stream_path: "/stream1",
    location:    "",
    camera_risk_class:  "medium",   
};

export default function AddRtspModal({ onClose, onCameraAdded }) {
    const [form, setForm]             = useState(EMPTY_FORM);
    const [showPass, setShowPass]     = useState(false);
    const [step, setStep]             = useState("form"); // "form" | "testing" | "success" | "error"
    const [testResult, setTestResult] = useState(null);
    const [saving, setSaving]         = useState(false);
    const [errorMsg, setErrorMsg]     = useState("");

    const setField = (k, v) => setForm(prev => ({ ...prev, [k]: v }));

    // ── Preview URL ──────────────────────────────────────────────
    const previewUrl = () => {
        if (!form.ip) return "rtsp://...";
        const path = form.stream_path?.startsWith("/")
            ? form.stream_path : `/${form.stream_path}`;
        if (form.username && form.password)
            return `rtsp://${form.username}:***@${form.ip}:${form.port}${path}`;
        return `rtsp://${form.ip}:${form.port}${path}`;
    };

    // ── Step 1: Test connection ──────────────────────────────────
    const handleTest = async () => {
        if (!form.name.trim() || !form.ip.trim()) {
            setErrorMsg("Camera name and IP address are required.");
            return;
        }
        setErrorMsg("");
        setStep("testing");
        setTestResult(null);

        try {
            const res = await fetch(`${API}/cameras/test`, {
                method:  "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    ...form,
                    port:     Number(form.port),
                    username: form.username || null,
                    password: form.password || null,
                }),
            });
            const data = await res.json();
            setTestResult(data);
            setStep(data.success ? "success" : "error");
        } catch (e) {
            setTestResult({ success: false, message: "Request failed — is the server running?" });
            setStep("error");
        }
    };

    // ── Step 2: Save camera after successful test ────────────────
    const handleSave = async () => {
        setSaving(true);
        try {
            const res = await fetch(`${API}/cameras`, {
                method:  "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    ...form,
                    port:     Number(form.port),
                    username: form.username || null,
                    password: form.password || null,
                }),
            });
            const data = await res.json();
            if (!res.ok) throw new Error(data.detail || "Failed to save camera");

            // Notify parent to refresh camera list
            if (onCameraAdded) onCameraAdded(data.camera);
            onClose();
        } catch (e) {
            setErrorMsg(e.message);
        } finally {
            setSaving(false);
        }
    };

    const handleRetry = () => {
        setStep("form");
        setTestResult(null);
        setErrorMsg("");
    };

    // ── Close on backdrop click ──────────────────────────────────
    const handleBackdrop = (e) => {
        if (e.target === e.currentTarget) onClose();
    };

    return (
        <div className="rtsp-backdrop" onClick={handleBackdrop}>
            <div className="rtsp-modal">

                {/* ── Header ── */}
                <div className="rtsp-modal-header">
                    <div className="rtsp-modal-title-row">
                        <span className="rtsp-modal-title">Add RTSP Camera</span>
                        <button className="rtsp-close-btn" onClick={onClose}>×</button>
                    </div>
                    {/* Step indicator */}
                    <div className="rtsp-steps">
                        <div className={`rtsp-step ${step !== "form" ? "step-done" : "step-active"}`}>
                            <span className="step-dot">1</span>
                            <span className="step-label">Enter Details</span>
                        </div>
                        <div className="step-line" />
                        <div className={`rtsp-step ${
                            step === "testing" ? "step-active" :
                            step === "success" || step === "error" ? "step-done" : "step-idle"
                        }`}>
                            <span className="step-dot">2</span>
                            <span className="step-label">Test Connection</span>
                        </div>
                        <div className="step-line" />
                        <div className={`rtsp-step ${step === "success" ? "step-active" : "step-idle"}`}>
                            <span className="step-dot">3</span>
                            <span className="step-label">Save Camera</span>
                        </div>
                    </div>
                </div>

                {/* ── Body ── */}
                <div className="rtsp-modal-body">

                    {/* ══ FORM (step 1) ══ */}
                    {(step === "form" || step === "testing") && (
                        <div className="rtsp-form">

                            {/* Name */}
                            <div className="rtsp-field">
                                <label className="rtsp-label">Camera Name *</label>
                                <input
                                    className="rtsp-input"
                                    placeholder="e.g. Front Gate Camera"
                                    value={form.name}
                                    onChange={e => setField("name", e.target.value)}
                                />
                            </div>

                            {/* IP + Port */}
                            <div className="rtsp-row">
                                <div className="rtsp-field rtsp-field-grow">
                                    <label className="rtsp-label">IP Address *</label>
                                    <input
                                        className="rtsp-input"
                                        placeholder="192.168.1.64"
                                        value={form.ip}
                                        onChange={e => setField("ip", e.target.value)}
                                    />
                                </div>
                                <div className="rtsp-field rtsp-field-port">
                                    <label className="rtsp-label">Port</label>
                                    <input
                                        className="rtsp-input"
                                        type="number"
                                        placeholder="554"
                                        value={form.port}
                                        onChange={e => setField("port", e.target.value)}
                                    />
                                </div>
                            </div>

                            {/* Username + Password */}
                            <div className="rtsp-row">
                                <div className="rtsp-field rtsp-field-grow">
                                    <label className="rtsp-label">Username <span className="rtsp-optional">(optional)</span></label>
                                    <input
                                        className="rtsp-input"
                                        placeholder="admin"
                                        value={form.username}
                                        onChange={e => setField("username", e.target.value)}
                                    />
                                </div>
                                <div className="rtsp-field rtsp-field-grow">
                                    <label className="rtsp-label">Password <span className="rtsp-optional">(optional)</span></label>
                                    <div className="rtsp-pass-wrap">
                                        <input
                                            className="rtsp-input"
                                            type={showPass ? "text" : "password"}
                                            placeholder="••••••••"
                                            value={form.password}
                                            onChange={e => setField("password", e.target.value)}
                                        />
                                        <button
                                            className="rtsp-pass-toggle"
                                            onClick={() => setShowPass(p => !p)}
                                            type="button"
                                        >
                                            {showPass ? "Hide" : "Show"}
                                        </button>
                                    </div>
                                </div>
                            </div>

                            {/* Stream path */}
                            <div className="rtsp-field">
                                <label className="rtsp-label">Stream Path</label>
                                <input
                                    className="rtsp-input"
                                    placeholder="/stream1"
                                    value={form.stream_path}
                                    onChange={e => setField("stream_path", e.target.value)}
                                />
                                <span className="rtsp-hint">
                                    Common paths: /stream1 · /Streaming/Channels/101 · /live/ch0
                                </span>
                            </div>

                            {/* Location */}
                            <div className="rtsp-field">
                                <label className="rtsp-label">Location / Zone <span className="rtsp-optional">(optional)</span></label>
                                <input
                                    className="rtsp-input"
                                    placeholder="e.g. Zone A - Entrance"
                                    value={form.location}
                                    onChange={e => setField("location", e.target.value)}
                                />
                            </div>

                            {/* Camera Risk Level */}
                            <div className="rtsp-field">
                                <label className="rtsp-label">Risk Level</label>
                                <select
                                    className="rtsp-input"
                                    value={form.camera_risk_class}
                                    onChange={e => setField("camera_risk_class", e.target.value)}
                                >
                                    <option value="low">Low</option>
                                    <option value="medium">Medium</option>
                                    <option value="high">High</option>
                                    <option value="critical">Critical</option>
                                </select>
                            </div>

                            {/* URL Preview */}
                            <div className="rtsp-url-preview">
                                <span className="rtsp-url-preview-label">Generated URL</span>
                                <span className="rtsp-url-preview-value">{previewUrl()}</span>
                            </div>

                            {/* Error */}
                            {errorMsg && (
                                <div className="rtsp-error-msg">⚠ {errorMsg}</div>
                            )}
                        </div>
                    )}

                    {/* ══ TESTING (loading state) ══ */}
                    {step === "testing" && (
                        <div className="rtsp-testing-state">
                            <div className="rtsp-spinner" />
                            <p className="rtsp-testing-text">Testing connection to {form.ip}…</p>
                            <p className="rtsp-testing-sub">This may take up to 10 seconds</p>
                        </div>
                    )}

                    {/* ══ SUCCESS ══ */}
                    {step === "success" && testResult && (
                        <div className="rtsp-result rtsp-result-success">
                            <div className="rtsp-result-icon">✓</div>
                            <h3 className="rtsp-result-title">Connection Successful</h3>
                            <p className="rtsp-result-msg">{testResult.message}</p>

                            {/* Stream info */}
                            <div className="rtsp-stream-info">
                                {testResult.frame_width && (
                                    <div className="rtsp-stream-chip">
                                        📐 {testResult.frame_width}×{testResult.frame_height}
                                    </div>
                                )}
                                {testResult.fps && (
                                    <div className="rtsp-stream-chip">
                                        🎞 {testResult.fps} fps
                                    </div>
                                )}
                                <div className="rtsp-stream-chip">📷 {form.name}</div>
                                {form.location && (
                                    <div className="rtsp-stream-chip">📍 {form.location}</div>
                                )}
                            </div>

                            <div className="rtsp-url-preview rtsp-url-preview-success">
                                <span className="rtsp-url-preview-label">RTSP URL</span>
                                <span className="rtsp-url-preview-value">{testResult.rtsp_url}</span>
                            </div>
                        </div>
                    )}

                    {/* ══ ERROR ══ */}
                    {step === "error" && testResult && (
                        <div className="rtsp-result rtsp-result-error">
                            <div className="rtsp-result-icon rtsp-result-icon-fail">✗</div>
                            <h3 className="rtsp-result-title">Connection Failed</h3>
                            <p className="rtsp-result-msg">{testResult.message}</p>

                            <div className="rtsp-error-tips">
                                <p className="rtsp-tips-title">Things to check:</p>
                                <ul className="rtsp-tips-list">
                                    <li>IP address is reachable from this machine</li>
                                    <li>Port 554 is open and not blocked by firewall</li>
                                    <li>Username and password are correct</li>
                                    <li>Stream path matches your camera model</li>
                                </ul>
                            </div>
                        </div>
                    )}

                </div>

                {/* ── Footer buttons ── */}
                <div className="rtsp-modal-footer">
                    {(step === "form" || step === "testing") && (
                        <>
                            <button className="btn-grey" onClick={onClose}>
                                Cancel
                            </button>
                            <button
                                className="btn-red"
                                onClick={handleTest}
                                disabled={step === "testing" || !form.name || !form.ip}
                                style={{ opacity: step === "testing" || !form.name || !form.ip ? 0.55 : 1 }}
                            >
                                {step === "testing" ? "Testing…" : "Test Connection"}
                            </button>
                        </>
                    )}

                    {step === "success" && (
                        <>
                            <button className="btn-grey" onClick={handleRetry}>
                                Edit Details
                            </button>
                            <button
                                className="btn-red"
                                onClick={handleSave}
                                disabled={saving}
                                style={{ opacity: saving ? 0.55 : 1 }}
                            >
                                {saving ? "Saving…" : "Save Camera ✓"}
                            </button>
                        </>
                    )}

                    {step === "error" && (
                        <>
                            <button className="btn-grey" onClick={onClose}>
                                Cancel
                            </button>
                            <button className="btn-dark" onClick={handleRetry}>
                                Fix Details
                            </button>
                        </>
                    )}
                </div>

            </div>
        </div>
    );
}