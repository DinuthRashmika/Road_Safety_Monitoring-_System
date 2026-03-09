import React from 'react';
import './../styles/SourcePropsPanel.css';
import { useNavigate } from 'react-router-dom';

function SourcesPropsPanel({ isOpen, onClose, camera, videoInfo, videoSource }) {
    const navigate = useNavigate();

    const handleStartDetection = () => {
        let sourcePath = null;
        if (videoSource && videoInfo) {
            sourcePath = videoSource;
        } else if (camera) {
            sourcePath = camera.rtsp_url || camera.stream_url || camera.source_path;
        }
        if (!sourcePath) { alert("No source path available!"); return; }
        onClose();
        navigate('/detection-monitering', {
            state: { videoSource: sourcePath, videoInfo, cameraInfo: camera, isCamera: !!camera }
        });
    };

    const isOnline = camera && (camera.status === 'online' || camera.status === 'ONLINE');

    return (
        <div className={`sp-panel ${isOpen ? 'sp-open' : ''}`}>

            {/* ── Header ── */}
            <div className="sp-header">
                <div className="sp-header-left">
                    <div className="sp-header-icon">
                        {camera ? (
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                <path d="M15 10l4.553-2.277A1 1 0 0121 8.723v6.554a1 1 0 01-1.447.894L15 14M3 8a2 2 0 012-2h10a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2V8z"/>
                            </svg>
                        ) : (
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                <rect x="2" y="3" width="20" height="14" rx="2"/><path d="M8 21h8M12 17v4"/>
                            </svg>
                        )}
                    </div>
                    <div>
                        <p className="sp-header-title">{camera ? camera.name || 'Camera Details' : 'Video Properties'}</p>
                        <p className="sp-header-sub">{camera ? 'RTSP Camera Source' : 'Local File / Stream'}</p>
                    </div>
                </div>
                <button className="sp-close" onClick={onClose} aria-label="Close">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                        <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
                    </svg>
                </button>
            </div>

            {/* ── Body ── */}
            <div className="sp-body">

                {/* ── Camera block ── */}
                {camera && (
                    <>
                        {/* Status banner */}
                        <div className={`sp-status-banner ${isOnline ? 'sp-banner-online' : 'sp-banner-offline'}`}>
                            <span className="sp-status-dot-lg" />
                            <span>{isOnline ? 'Camera is Online' : 'Camera is Offline'}</span>
                        </div>

                        <div className="sp-group">
                            <p className="sp-group-label">Camera Info</p>
                            <div className="sp-rows">
                                <div className="sp-row">
                                    <span className="sp-lbl">Name</span>
                                    <span className="sp-val">{camera.name || '—'}</span>
                                </div>
                                <div className="sp-row">
                                    <span className="sp-lbl">Camera ID</span>
                                    <span className="sp-val sp-mono">{camera.camera_id || camera.id || '—'}</span>
                                </div>
                                <div className="sp-row">
                                    <span className="sp-lbl">Location</span>
                                    <span className="sp-val">{camera.location || '—'}</span>
                                </div>
                                <div className="sp-row">
                                    <span className="sp-lbl">IP Address</span>
                                    <span className="sp-val sp-mono">{camera.ip || '—'}</span>
                                </div>
                                <div className="sp-row">
                                    <span className="sp-lbl">Port</span>
                                    <span className="sp-val sp-mono">{camera.port || '—'}</span>
                                </div>
                                <div className="sp-row">
                                    <span className="sp-lbl">Stream Path</span>
                                    <span className="sp-val sp-mono">{camera.stream_path || '—'}</span>
                                </div>
                            </div>
                        </div>

                        {/* RTSP URL */}
                        <div className="sp-url-box">
                            <p className="sp-url-label">RTSP URL</p>
                            <p className="sp-url-value">{camera.rtsp_url || '—'}</p>
                        </div>
                    </>
                )}

                {/* ── Video file block ── */}
                {videoInfo && (
                    <div className="sp-group">
                        <p className="sp-group-label">Video Properties</p>
                        <div className="sp-stat-grid">
                            <div className="sp-stat">
                                <span className="sp-stat-val">{videoInfo.fps || '—'}</span>
                                <span className="sp-stat-lbl">FPS</span>
                            </div>
                            <div className="sp-stat">
                                <span className="sp-stat-val">{videoInfo.duration ? `${videoInfo.duration.toFixed(1)}s` : '—'}</span>
                                <span className="sp-stat-lbl">Duration</span>
                            </div>
                            <div className="sp-stat">
                                <span className="sp-stat-val">{videoInfo.total_frames || videoInfo.totalFrames || '—'}</span>
                                <span className="sp-stat-lbl">Frames</span>
                            </div>
                            <div className="sp-stat">
                                <span className="sp-stat-val">{videoInfo.width && videoInfo.height ? `${videoInfo.width}×${videoInfo.height}` : '—'}</span>
                                <span className="sp-stat-lbl">Resolution</span>
                            </div>
                        </div>
                        <div className="sp-rows" style={{marginTop: 8}}>
                            {videoInfo.codec && (
                                <div className="sp-row">
                                    <span className="sp-lbl">Codec</span>
                                    <span className="sp-val sp-mono">{videoInfo.codec}</span>
                                </div>
                            )}
                            {videoInfo.bitrate && (
                                <div className="sp-row">
                                    <span className="sp-lbl">Bitrate</span>
                                    <span className="sp-val sp-mono">{videoInfo.bitrate}</span>
                                </div>
                            )}
                        </div>
                    </div>
                )}
            </div>

            {/* ── Footer actions ── */}
            {(camera || videoInfo) && (
                <div className="sp-footer">
                    <button className="sp-btn-close" onClick={onClose}>Close</button>
                    <button
                        className="sp-btn-start"
                        onClick={handleStartDetection}
                        disabled={camera && !isOnline}
                    >
                        Start Detection →
                    </button>
                </div>
            )}
        </div>
    );
}

export default SourcesPropsPanel;