import { useState, useEffect } from "react"
import { useNavigate } from "react-router-dom";
import Layout from "../layouts/Layout";
import './../styles/VideoSources.css'
import SourcesPropsPanel from "../components/SourcePropsPanel";

function VideoSources() {
    const navigate = useNavigate();

    const [videoSource, setVideoSource] = useState("");
    const [isValid, setIsValid] = useState(false);
    const [videoInfo, setVideoInfo] = useState(null);
    const [loading, setLoading] = useState(false);

    //all sources
    const [cameras, setCameras] = useState([]);
    const [sourcesLoading, setSourcesLoading] = useState(false);
    const [error, setError] = useState(null);
    const [selectedCamera, setSelectedCamera] = useState(null);

    //-----------Panel states
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
            setIsPanelOpen(true);
            console.log("Video properties:", data);
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
            const res = await fetch("http://127.0.0.1:8000/source/cameras");
            const data = await res.json();
            setCameras(data.cameras);
        } catch (err) {
            setError(err.message);
        } finally {
            setSourcesLoading(false);
        }
    };

    // Navigate to detection page with video source
    const handleStartDetection = () => {
        if (!isValid) return;
        
        // Navigate to detection page with video source as state
        navigate('/detection-monitering', { 
            state: { 
                videoSource: videoSource,
                videoInfo: videoInfo 
            } 
        });
    };

    // Handle camera detection
    const handleCameraDetection = (camera) => {
        navigate('/detection', { 
            state: { 
                videoSource: camera.stream_url || camera.rtsp_url, // Adjust based on your camera object
                cameraInfo: camera,
                isCamera: true
            } 
        });
    };

    return (
        <Layout>
            <div className={`video-sources-container ${isPanelOpen ? 'panel-open' : ''}`}>
                <h2>Hybrid Violence Detection Module</h2>

                <div className="video-source-section">
                    <h2 className="page-title">Sources</h2>

                    {sourcesLoading && <p className="loading-text">Loading cameras...</p>}
                    {error && <p className="error-text">{error}</p>}

                    {/* Sources */}
                    <div className="camera-grid">
                        {cameras.map((cam) => (
                            <div
                                key={cam.id}
                                className={`camera-card status-${cam.status === "ONLINE" ? "online" : "offline"} ${selectedCamera?.id === cam.id ? "selected" : ""}`}
                            >
                                <div className="camera-card-header">
                                    <span className={`camera-status ${cam.status === "ONLINE" ? "online" : "offline"}`}>
                                        {cam.status}
                                    </span>
                                </div>
                                <div className="camera-card-content">
                                    <p className="source-name">{cam.location}</p>
                                    <p className="camera-id">Source Id: {cam.id}</p>
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
                                            background: cam.status === "ONLINE" ? "#707378" : "#ccc",
                                            borderColor: cam.status === "ONLINE" ? "#555556ff" : "#ccc"
                                        }}
                                        disabled={cam.status !== "ONLINE"}
                                    >
                                        Start Detection
                                    </button>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Video Source Input */}
                <div className="video-source-section">
                    <p className="or-text">Or</p>

                    <label className="video-source-label">
                        Enter Video Source Path:
                    </label>

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

            {/* Details Panel Component */}
            <SourcesPropsPanel 
                isOpen={isPanelOpen}
                onClose={closePanel}
                camera={selectedCamera}
                videoInfo={videoInfo}
                videoSource={videoSource}
            />
        </Layout>
    )
}

export default VideoSources;