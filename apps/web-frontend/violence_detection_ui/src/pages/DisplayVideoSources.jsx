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

    // all sources
    const [cameras, setCameras] = useState([]);
    const [sourcesLoading, setSourcesLoading] = useState(false);
    const [error, setError] = useState(null);
    const [selectedCamera, setSelectedCamera] = useState(null);
    const [showModal, setShowModal] = useState(false);

    // Panel states
    const [isPanelOpen, setIsPanelOpen] = useState(false);

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

    useEffect(() => {
        fetchCameras();
    }, []);

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

    // ── Called by AddRtspModal after saving — adds new camera instantly ──
    const handleCameraAdded = (newCamera) => {
        setCameras(prev => [...prev, newCamera]);
        setShowModal(false);
    };

    const handleStartDetection = () => {
        if (!isValid) return;
        navigate('/detection-monitering', {
            state: { videoSource, videoInfo }
        });
    };

    const handleCameraDetection = (camera) => {
        navigate('/detection', {
            state: {
                videoSource: camera.rtsp_url,
                cameraInfo:  camera,
                isCamera:    true,
            }
        });
    };

    return (
        <Layout>
            <div className={`video-sources-container ${isPanelOpen ? 'panel-open' : ''}`}>
                <h2>Hybrid Violence Detection Module</h2>

                {/* ── Add RTSP Camera button ── */}
                <button className="logout-button" onClick={() => setShowModal(true)}>
                    + Add Camera RTSP
                </button>

                {/* ── Modal — passes onCameraAdded so list updates instantly ── */}
                {showModal && (
                    <AddRtspModal
                        onClose={() => setShowModal(false)}
                        onCameraAdded={handleCameraAdded}
                    />
                )}

                {/* ── Camera list ── */}
                <div className="video-source-section">
                    <h2 className="page-title">Sources</h2>

                    {sourcesLoading && <p className="loading-text">Loading cameras...</p>}
                    {error && <p className="error-text">{error}</p>}

                    <div className="camera-grid">
                        {cameras.map((cam) => (
                            <div
                                key={cam.camera_id || cam.id}
                                className={`camera-card status-${
                                    cam.status === "online" || cam.status === "ONLINE"
                                        ? "online" : "offline"
                                } ${selectedCamera?.camera_id === cam.camera_id ? "selected" : ""}`}
                            >
                                <div className="camera-card-header">
                                    <span className={`camera-status ${
                                        cam.status === "online" || cam.status === "ONLINE"
                                            ? "online" : "offline"
                                    }`}>
                                        {cam.status?.toUpperCase() || "UNKNOWN"}
                                    </span>
                                </div>
                                <div className="camera-card-content">
                                    <p className="source-name">{cam.name || cam.location}</p>
                                    <p className="camera-id">
                                        {cam.location && `📍 ${cam.location}`}
                                    </p>
                                    <p className="camera-id">
                                        ID: {cam.camera_id || cam.id}
                                    </p>
                                </div>
                                <div style={{ display: 'flex', gap: '0.5rem' }}>
                                    <button
                                        className="btn-red"
                                        onClick={() => handleViewDetails(cam)}
                                        style={{ flex: 1 }}
                                    >
                                        View Details
                                    </button>
                                    <button
                                        className="btn-dark"
                                        onClick={() => handleCameraDetection(cam)}
                                        style={{
                                            flex: 1,
                                            background: cam.status === "online" ? "#555556" : "#ccc",
                                            borderColor: cam.status === "online" ? "#555556" : "#ccc",
                                        }}
                                        disabled={cam.status !== "online"}
                                    >
                                        Start Detection
                                    </button>
                                </div>
                            </div>
                        ))}

                        {/* Empty state */}
                        {!sourcesLoading && cameras.length === 0 && (
                            <div style={{
                                gridColumn: "1 / -1",
                                textAlign: "center",
                                padding: "32px",
                                background: "#fff",
                                borderRadius: 12,
                                border: "1px dashed #e5e7eb",
                                color: "#9ca3af",
                                fontSize: 14,
                            }}>
                                <div style={{ fontSize: 32, marginBottom: 8 }}>📷</div>
                                No cameras registered yet.
                                Click <strong style={{ color: "#E4080A" }}>+ Add Camera RTSP</strong> to add one.
                            </div>
                        )}
                    </div>
                </div>

                {/* ── Video file source input ── */}
                <div className="video-source-section">
                    <p className="or-text">Or</p>
                    <label className="video-source-label">Enter Video Source Path:</label>
                    <input
                        type="text"
                        className="video-source-input"
                        placeholder="Enter video path (e.g., E:/videos/test.mp4)"
                        value={videoSource}
                        onChange={handleChange}
                    />
                    <div className="video-source-actions">
                        <button
                            className={`btn-red ${!isValid || loading ? "disabled" : ""}`}
                            onClick={getVideoProperties}
                            disabled={!isValid || loading}
                        >
                            {loading ? "Loading..." : "View Details"}
                        </button>
                        <button
                            className={`btn-dark ${!isValid || loading ? "disabled" : ""}`}
                            onClick={handleStartDetection}
                            disabled={!isValid || loading}
                        >
                            Start Detection
                        </button>
                    </div>
                </div>
            </div>

            {/* Details Panel */}
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