import { useState, useEffect } from "react"
import { useNavigate } from "react-router-dom";
import Layout from "../layouts/Layout";
import './../styles/DisplayVideoSources.css'
import SourcesPropsPanel from "../components/SourcePropsPanel";
import AddRtspModal from "../components/AddRtspModal";
import "../styles/AddRtspModal.css";

function VideoSources() {
    const navigate = useNavigate();

    const [videoSource, setVideoSource] = useState("");
    const [isValid, setIsValid] = useState(false);
    const [videoInfo, setVideoInfo] = useState(null);
    const [loading, setLoading] = useState(false);

    const [cameras, setCameras] = useState([]);
    const [sourcesLoading, setSourcesLoading] = useState(false);
    const [error, setError] = useState(null);
    const [selectedCamera, setSelectedCamera] = useState(null);
    const [showModal, setShowModal] = useState(false);
    const [isPanelOpen, setIsPanelOpen] = useState(false);
    const [startingCameraId, setStartingCameraId] = useState(null);

    const handleViewDetails = (cam) => {
        setSelectedCamera(cam);
        setIsPanelOpen(true);
    };

    const closePanel = () => {
        setIsPanelOpen(false);
        setSelectedCamera(null);
        setVideoInfo(null);
    };

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
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ source_path: videoSource }),
            });
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            const data = await response.json();
            setVideoInfo(data);
            setIsPanelOpen(true);
        } catch (error) {
            console.error("Backend error:", error);
            alert(`Error: ${error.message}`);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => { fetchCameras(); }, []);

    const fetchCameras = async () => {
        setSourcesLoading(true);
        setError(null);
        try {
            const res  = await fetch("http://127.0.0.1:8000/cameras");
            const data = await res.json();
            setCameras(data.cameras || []);
        } catch (err) {
            setError(err.message);
        } finally {
            setSourcesLoading(false);
        }
    };

    const handleCameraAdded = (newCamera) => {
        setCameras(prev => [...prev, newCamera]);
        setShowModal(false);
    };

    const handleStartDetection = () => {
        if (!isValid) return;
        navigate('/detection-monitering', { state: { videoSource, videoInfo } });
    };

    const handleCameraDetection = async (camera) => {
        setStartingCameraId(camera.camera_id);
        try {
            const res  = await fetch(
                `http://127.0.0.1:8000/cameras/${camera.camera_id}/start-detection`,
                { method: "POST" }
            );
            const data = await res.json();
            if (!res.ok) throw new Error(data.detail || "Failed to start detection");
            navigate('/detection-monitering', {
                state: {
                    videoSource:  `Camera: ${data.camera.name}`,
                    videoInfo:    data.camera,
                    sessionId:    data.session_id,
                    websocketUrl: data.websocket_url,
                    isCamera:     true,
                }
            });
        } catch (err) {
            alert(`Could not start detection: ${err.message}`);
        } finally {
            setStartingCameraId(null);
        }
    };

    const isOnline = (cam) => cam.status === "online" || cam.status === "ONLINE";

    return (
        <Layout>
            <div className={`vs-page ${isPanelOpen ? 'panel-open' : ''}`}>

                {/* ── Page header ── */}
                <div className="vs-page-header">
                    <div>
                        <h1 className="vs-page-title">Detection Sources</h1>
                        <p className="vs-page-sub">Select a live camera or provide a video path to begin analysis</p>
                    </div>
                    <button className="vs-add-btn" onClick={() => setShowModal(true)}>
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                            <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
                        </svg>
                        Add RTSP Camera
                    </button>
                </div>

                {showModal && (
                    <AddRtspModal
                        onClose={() => setShowModal(false)}
                        onCameraAdded={handleCameraAdded}
                    />
                )}

                {/* ── Camera sources ── */}
                <section className="vs-section">
                    <div className="vs-section-label">
                        <span>Live Camera Sources</span>
                        <span className="vs-count-badge">{cameras.length}</span>
                    </div>

                    {sourcesLoading && (
                        <div className="vs-loading">
                            <div className="vs-spinner" />
                            <span>Loading cameras…</span>
                        </div>
                    )}
                    {error && <div className="vs-error-bar">⚠ {error}</div>}

                    <div className="vs-camera-grid">
                        {cameras.map((cam) => (
                            <div
                                key={cam.camera_id || cam.id}
                                className={`vs-cam-card ${isOnline(cam) ? '' : 'vs-cam-offline'} ${selectedCamera?.camera_id === cam.camera_id ? 'vs-cam-selected' : ''}`}
                            >
                                {/* Red left accent */}
                                <div className="vs-cam-accent" />

                                <div className="vs-cam-body">
                                    {/* Top: icon + status */}
                                    <div className="vs-cam-top">
                                        <div className="vs-cam-icon">
                                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                                                <path d="M15 10l4.553-2.277A1 1 0 0121 8.723v6.554a1 1 0 01-1.447.894L15 14M3 8a2 2 0 012-2h10a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2V8z"/>
                                            </svg>
                                        </div>
                                        <span className={`vs-status-pill ${isOnline(cam) ? 'vs-pill-online' : 'vs-pill-offline'}`}>
                                            <span className="vs-pill-dot" />
                                            {isOnline(cam) ? 'Online' : 'Offline'}
                                        </span>
                                    </div>

                                    {/* Info */}
                                    <p className="vs-cam-name">{cam.name || 'Unnamed Camera'}</p>
                                    {cam.location && (
                                        <p className="vs-cam-meta">
                                            <svg width="10" height="10" viewBox="0 0 24 24" fill="currentColor">
                                                <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/>
                                            </svg>
                                            {cam.location}
                                        </p>
                                    )}
                                    <p className="vs-cam-ip">{cam.ip}:{cam.port}</p>
                                </div>

                                {/* Actions */}
                                <div className="vs-cam-actions">
                                    <button className="vs-cam-btn-outline" onClick={() => handleViewDetails(cam)}>
                                        Details
                                    </button>
                                    <button
                                        className={`vs-cam-btn-primary ${!isOnline(cam) || startingCameraId === cam.camera_id ? 'vs-cam-btn-disabled' : ''}`}
                                        onClick={() => handleCameraDetection(cam)}
                                        disabled={!isOnline(cam) || startingCameraId === cam.camera_id}
                                    >
                                        {startingCameraId === cam.camera_id
                                            ? <><span className="vs-inline-spin" /> Starting…</>
                                            : 'Start Detection'
                                        }
                                    </button>
                                </div>
                            </div>
                        ))}

                        {!sourcesLoading && cameras.length === 0 && (
                            <div className="vs-empty">
                                <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="#d1d5db" strokeWidth="1">
                                    <path d="M15 10l4.553-2.277A1 1 0 0121 8.723v6.554a1 1 0 01-1.447.894L15 14M3 8a2 2 0 012-2h10a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2V8z"/>
                                </svg>
                                <p className="vs-empty-title">No sources registered yet</p>
                                <p className="vs-empty-sub">Click <strong style={{color:'#E4080A'}}>+ Add RTSP Camera</strong> to connect one</p>
                            </div>
                        )}
                    </div>
                </section>

                {/* ── Manual source ── */}
                <section className="vs-manual-section">
                    <div className="vs-divider">
                        <span className="vs-divider-line" />
                        <span className="vs-divider-label">or manually add a video source</span>
                        <span className="vs-divider-line" />
                    </div>

                    <div className="vs-manual-card">
                        <div className="vs-manual-icon">
                            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#E4080A" strokeWidth="1.5">
                                <rect x="2" y="3" width="20" height="14" rx="2"/><path d="M8 21h8M12 17v4"/>
                            </svg>
                        </div>
                        <p className="vs-manual-title">Video File or Stream URL</p>
                        <p className="vs-manual-sub">Local file path or any compatible video stream URL</p>

                        <input
                            type="text"
                            className="vs-manual-input"
                            placeholder="E:/videos/footage.mp4  or  rtsp://192.168.1.x/stream"
                            value={videoSource}
                            onChange={handleChange}
                        />

                        <div className="vs-manual-actions">
                            <button
                                className="vs-manual-btn-outline"
                                onClick={getVideoProperties}
                                disabled={!isValid || loading}
                            >
                                {loading
                                    ? <><span className="vs-inline-spin vs-spin-red" /> Loading…</>
                                    : 'View Properties'
                                }
                            </button>
                            <button
                                className="vs-manual-btn-primary"
                                onClick={handleStartDetection}
                                disabled={!isValid || loading}
                            >
                                Start Detection
                            </button>
                        </div>
                    </div>
                </section>

            </div>

            <SourcesPropsPanel
                isOpen={isPanelOpen}
                onClose={closePanel}
                camera={selectedCamera}
                videoInfo={videoInfo}
                videoSource={videoSource}
            />
        </Layout>
    );
}

export default VideoSources;